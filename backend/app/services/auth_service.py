"""
Authentication service for the Multilingual Mandi Marketplace Platform.

This service handles user authentication, registration, token management,
and various authentication methods including email, phone, Google OAuth, and Aadhaar.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import httpx
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.config import settings
from app.core.database import get_database
from app.core.security import SecurityUtils, JWTManager, create_user_tokens, PasswordValidator
from app.core.exceptions import (
    AuthenticationException,
    ValidationException,
    ExternalServiceException,
    NotFoundException
)
from app.models.auth import (
    AuthCredentials,
    AuthResult,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    OAuthCredentials,
    AadhaarCredentials,
    VerificationData,
    AuthMethod,
    TokenType,
    SecurityEvent
)
from app.models.user import (
    UserProfile,
    VendorProfile,
    BuyerProfile,
    UserRole,
    VerificationStatus,
    BusinessType,
    ProductCategory,
    LocationData,
    UserPreferences,
    SupportedLanguage,
    UserCreateRequest
)
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service class."""
    
    def __init__(self):
        self.security_utils = SecurityUtils()
        self.jwt_manager = JWTManager()
        self.password_validator = PasswordValidator()
        self.user_service = UserService()
    
    async def register_user(self, request: RegisterRequest) -> AuthResult:
        """
        Register a new user account.
        
        Args:
            request: User registration request
            
        Returns:
            Authentication result with user info and tokens
            
        Raises:
            ValidationException: If registration data is invalid
            AuthenticationException: If registration fails
        """
        try:
            # Validate password strength
            password_validation = self.password_validator.validate_password_strength(request.password)
            if not password_validation["is_valid"]:
                raise ValidationException(
                    f"Password validation failed: {', '.join(password_validation['errors'])}"
                )
            
            # Hash password
            hashed_password = self.security_utils.hash_password(request.password)
            
            # Create location data
            location_data = LocationData(
                address=f"{request.location_city}, {request.location_state}",
                city=request.location_city,
                state=request.location_state,
                pincode=request.location_pincode,
                country="India"
            )
            
            # Create user creation request
            user_create_request = UserCreateRequest(
                email=request.email,
                password=request.password,  # Will be hashed by user service
                phone=request.phone,
                role=request.role,
                preferred_languages=[request.preferred_language],
                location=location_data,
                business_name=request.business_name,
                business_type=request.business_type,
                product_categories=getattr(request, 'product_categories', []),
                market_location=f"{request.location_city}, {request.location_state}",
                preferred_categories=getattr(request, 'preferred_categories', []),
                budget_range=getattr(request, 'budget_range', None)
            )
            
            # Create user profile using user service
            user_response = await self.user_service.create_user_profile(user_create_request)
            
            # Store password hash separately (since user service doesn't handle passwords)
            db = await get_database()
            await db.users.update_one(
                {"user_id": user_response.user_id},
                {"$set": {"password_hash": hashed_password}}
            )
            
            # Log security event
            await self._log_security_event(
                "user_registered",
                user_id=user_response.user_id,
                event_data={
                    "email": request.email,
                    "role": request.role.value,
                    "method": request.method.value
                }
            )
            
            # Create tokens
            tokens = create_user_tokens(user_response.user_id, request.email, request.role)
            
            # Determine if verification is required
            requires_verification = request.method in [AuthMethod.EMAIL, AuthMethod.PHONE]
            verification_method = None
            
            if requires_verification:
                verification_method = "email" if request.method == AuthMethod.EMAIL else "phone"
                # Send verification (implementation depends on notification service)
                await self._send_verification(user_response.user_id, request.email, verification_method)
            
            return AuthResult(
                success=True,
                user_id=user_response.user_id,
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type=tokens["token_type"],
                expires_in=tokens["expires_in"],
                user_info={
                    "user_id": user_response.user_id,
                    "email": request.email,
                    "role": request.role.value,
                    "full_name": request.full_name,
                    "verification_status": VerificationStatus.UNVERIFIED.value
                },
                message="User registered successfully",
                requires_verification=requires_verification,
                verification_method=verification_method
            )
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            raise AuthenticationException("Registration failed")
    
    async def login_user(self, request: LoginRequest) -> AuthResult:
        """
        Authenticate user and return access tokens.
        
        Args:
            request: User login request
            
        Returns:
            Authentication result with tokens
            
        Raises:
            AuthenticationException: If authentication fails
        """
        try:
            db = await get_database()
            
            # Find user by identifier
            query = {}
            if request.method == AuthMethod.EMAIL:
                query = {"email": request.identifier}
            elif request.method == AuthMethod.PHONE:
                query = {"phone": request.identifier}
            else:
                raise AuthenticationException("Unsupported authentication method")
            
            user = await db.users.find_one(query)
            if not user:
                raise AuthenticationException("Invalid credentials")
            
            # Check if account is active
            if not user.get("is_active", True):
                raise AuthenticationException("Account is deactivated")
            
            # Verify password
            if not self.security_utils.verify_password(request.password, user["password_hash"]):
                # Log failed login attempt
                await self._log_security_event(
                    "login_failed",
                    user_id=user.get("user_id"),
                    event_data={
                        "reason": "invalid_password",
                        "identifier": request.identifier,
                        "method": request.method.value
                    }
                )
                raise AuthenticationException("Invalid credentials")
            
            # Update last login
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            # Create tokens
            user_role = UserRole(user["role"])
            tokens = create_user_tokens(user["user_id"], user["email"], user_role)
            
            # Extend token validity if remember_me is True
            if request.remember_me:
                # Create longer-lived tokens
                access_token = self.jwt_manager.create_access_token(
                    user["user_id"],
                    user["email"],
                    user_role,
                    expires_delta=timedelta(days=7)  # 7 days for remember me
                )
                refresh_token = self.jwt_manager.create_refresh_token(
                    user["user_id"],
                    user["email"],
                    user_role,
                    expires_delta=timedelta(days=30)  # 30 days for remember me
                )
                tokens.update({
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": 7 * 24 * 60 * 60  # 7 days in seconds
                })
            
            # Log successful login
            await self._log_security_event(
                "login_successful",
                user_id=user["user_id"],
                event_data={
                    "method": request.method.value,
                    "remember_me": request.remember_me
                }
            )
            
            # Build comprehensive user_info for frontend
            user_info = {
                "user_id": user["user_id"],
                "id": user["user_id"],  # Frontend expects 'id'
                "email": user["email"],
                "phone": user.get("phone"),
                "role": user["role"].upper() if user["role"] else "BUYER",  # Frontend expects uppercase
                "preferred_languages": user.get("preferred_languages", ["en"]),
                "location": user.get("location", {"type": "Point", "coordinates": [0, 0]}),
                "full_name": user.get("full_name"),
                "verification_status": user.get("verification_status", "unverified"),
                "is_active": user.get("is_active", True),
                "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
                "updated_at": user.get("updated_at").isoformat() if user.get("updated_at") else None,
                # Vendor-specific
                "business_name": user.get("business_name"),
                "business_type": user.get("business_type"),
                "product_categories": user.get("product_categories"),
                "market_location": user.get("market_location"),
                "rating": user.get("rating"),
                "total_transactions": user.get("total_transactions"),
                # Buyer-specific
                "preferred_categories": user.get("preferred_categories"),
                "budget_range": user.get("budget_range"),
                "total_purchases": user.get("total_purchases")
            }
            
            return AuthResult(
                success=True,
                user_id=user["user_id"],
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type=tokens["token_type"],
                expires_in=tokens["expires_in"],
                user_info=user_info,
                message="Login successful"
            )
            
        except AuthenticationException:
            raise
        except Exception as e:
            logger.error(f"User login failed: {e}")
            raise AuthenticationException("Login failed")
    
    async def refresh_token(self, request: RefreshTokenRequest) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            request: Token refresh request
            
        Returns:
            New access token data
            
        Raises:
            AuthenticationException: If refresh token is invalid
        """
        try:
            # Decode refresh token
            token_data = self.jwt_manager.decode_token(request.refresh_token)
            
            if not token_data or token_data.token_type != TokenType.REFRESH:
                raise AuthenticationException("Invalid refresh token")
            
            if self.jwt_manager.is_token_blacklisted(token_data.jti):
                raise AuthenticationException("Token has been revoked")
            
            # Get user from database to ensure they still exist and are active
            db = await get_database()
            user = await db.users.find_one({"user_id": token_data.user_id})
            
            if not user or not user.get("is_active", True):
                raise AuthenticationException("User account is not active")
            
            # Create new access token
            access_token = self.jwt_manager.create_access_token(
                token_data.user_id,
                token_data.email,
                token_data.role
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        except AuthenticationException:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise AuthenticationException("Token refresh failed")
    
    async def logout_user(self, access_token: str) -> Dict[str, str]:
        """
        Logout user and invalidate tokens.
        
        Args:
            access_token: User's access token
            
        Returns:
            Logout confirmation
        """
        try:
            # Decode token to get user info
            token_data = self.jwt_manager.decode_token(access_token)
            
            if token_data:
                # Blacklist the token
                self.jwt_manager.blacklist_token(token_data.jti, token_data.expires_at)
                
                # Log logout event
                await self._log_security_event(
                    "user_logout",
                    user_id=token_data.user_id,
                    event_data={"token_jti": token_data.jti}
                )
            
            return {
                "message": "Successfully logged out",
                "logged_out_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            # Even if logout fails, return success to avoid user confusion
            return {
                "message": "Logged out",
                "logged_out_at": datetime.utcnow().isoformat()
            }
    
    async def authenticate_with_google(self, oauth_credentials: OAuthCredentials) -> AuthResult:
        """
        Authenticate user with Google OAuth.
        
        Args:
            oauth_credentials: Google OAuth credentials
            
        Returns:
            Authentication result
            
        Raises:
            AuthenticationException: If OAuth authentication fails
        """
        try:
            # Verify Google ID token
            id_info = id_token.verify_oauth2_token(
                oauth_credentials.id_token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
            
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise AuthenticationException("Invalid Google token issuer")
            
            email = id_info.get('email')
            google_id = id_info.get('sub')
            name = id_info.get('name')
            
            if not email or not google_id:
                raise AuthenticationException("Invalid Google user information")
            
            db = await get_database()
            
            # Check if user exists
            user = await db.users.find_one({"email": email})
            
            if user:
                # Existing user - update Google ID if not set
                if not user.get("google_id"):
                    await db.users.update_one(
                        {"_id": user["_id"]},
                        {"$set": {"google_id": google_id, "last_login": datetime.utcnow()}}
                    )
                else:
                    await db.users.update_one(
                        {"_id": user["_id"]},
                        {"$set": {"last_login": datetime.utcnow()}}
                    )
                
                # Create tokens
                user_role = UserRole(user["role"])
                tokens = create_user_tokens(user["user_id"], user["email"], user_role)
                
                return AuthResult(
                    success=True,
                    user_id=user["user_id"],
                    access_token=tokens["access_token"],
                    refresh_token=tokens["refresh_token"],
                    token_type=tokens["token_type"],
                    expires_in=tokens["expires_in"],
                    user_info={
                        "user_id": user["user_id"],
                        "email": user["email"],
                        "role": user["role"],
                        "full_name": user.get("full_name", name)
                    },
                    message="Google authentication successful"
                )
            else:
                # New user - return info for registration completion
                return AuthResult(
                    success=False,
                    message="Account not found. Please complete registration.",
                    user_info={
                        "email": email,
                        "full_name": name,
                        "google_id": google_id,
                        "requires_registration": True
                    }
                )
                
        except AuthenticationException:
            raise
        except Exception as e:
            logger.error(f"Google authentication failed: {e}")
            raise AuthenticationException("Google authentication failed")
    
    async def authenticate_with_aadhaar(self, aadhaar_credentials: AadhaarCredentials) -> AuthResult:
        """
        Authenticate user with Aadhaar.
        
        Args:
            aadhaar_credentials: Aadhaar authentication credentials
            
        Returns:
            Authentication result
            
        Raises:
            AuthenticationException: If Aadhaar authentication fails
            ExternalServiceException: If Aadhaar service is unavailable
        """
        try:
            # Verify Aadhaar OTP (mock implementation)
            # In production, this would integrate with UIDAI APIs
            is_valid = await self._verify_aadhaar_otp(
                aadhaar_credentials.aadhaar_number,
                aadhaar_credentials.otp,
                aadhaar_credentials.transaction_id
            )
            
            if not is_valid:
                raise AuthenticationException("Invalid Aadhaar OTP")
            
            db = await get_database()
            
            # Find user by Aadhaar number
            user = await db.users.find_one({"aadhaar_number": aadhaar_credentials.aadhaar_number})
            
            if not user:
                raise AuthenticationException("No account found with this Aadhaar number")
            
            if not user.get("is_active", True):
                raise AuthenticationException("Account is deactivated")
            
            # Update last login
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            # Create tokens
            user_role = UserRole(user["role"])
            tokens = create_user_tokens(user["user_id"], user["email"], user_role)
            
            return AuthResult(
                success=True,
                user_id=user["user_id"],
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type=tokens["token_type"],
                expires_in=tokens["expires_in"],
                user_info={
                    "user_id": user["user_id"],
                    "email": user["email"],
                    "role": user["role"],
                    "full_name": user.get("full_name")
                },
                message="Aadhaar authentication successful"
            )
            
        except AuthenticationException:
            raise
        except Exception as e:
            logger.error(f"Aadhaar authentication failed: {e}")
            raise ExternalServiceException("Aadhaar authentication service unavailable")
    
    async def verify_user(self, verification_data: VerificationData) -> Dict[str, Any]:
        """
        Verify user account using verification code.
        
        Args:
            verification_data: Verification data
            
        Returns:
            Verification result
            
        Raises:
            ValidationException: If verification fails
        """
        try:
            db = await get_database()
            
            # For email verification
            if verification_data.verification_type == "email":
                # Decode verification token
                if not verification_data.verification_token:
                    raise ValidationException("Verification token is required")
                
                token_data = self.jwt_manager.decode_token(verification_data.verification_token)
                if not token_data or token_data.token_type != TokenType.VERIFICATION:
                    raise ValidationException("Invalid verification token")
                
                # Update user verification status
                result = await db.users.update_one(
                    {"user_id": token_data.user_id},
                    {"$set": {
                        "verification_status": VerificationStatus.VERIFIED.value,
                        "email_verified": True,
                        "verified_at": datetime.utcnow()
                    }}
                )
                
                if result.modified_count == 0:
                    raise ValidationException("User not found or already verified")
                
                return {
                    "success": True,
                    "message": "Email verified successfully",
                    "user_id": token_data.user_id
                }
            
            # For phone verification
            elif verification_data.verification_type == "phone":
                # Verify OTP (mock implementation)
                # In production, this would verify with SMS service
                if verification_data.verification_code != "123456":  # Mock OTP
                    raise ValidationException("Invalid verification code")
                
                # Find user by phone (would need phone number in additional_data)
                phone = verification_data.additional_data.get("phone") if verification_data.additional_data else None
                if not phone:
                    raise ValidationException("Phone number is required for phone verification")
                
                result = await db.users.update_one(
                    {"phone": phone},
                    {"$set": {
                        "verification_status": VerificationStatus.VERIFIED.value,
                        "phone_verified": True,
                        "verified_at": datetime.utcnow()
                    }}
                )
                
                if result.modified_count == 0:
                    raise ValidationException("User not found or already verified")
                
                return {
                    "success": True,
                    "message": "Phone verified successfully"
                }
            
            else:
                raise ValidationException("Unsupported verification type")
                
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"User verification failed: {e}")
            raise ValidationException("Verification failed")
    
    async def request_password_reset(self, email: str) -> Dict[str, str]:
        """
        Request password reset for user.
        
        Args:
            email: User's email address
            
        Returns:
            Reset request confirmation
            
        Raises:
            NotFoundException: If user not found
        """
        try:
            db = await get_database()
            
            user = await db.users.find_one({"email": email})
            if not user:
                # Don't reveal if email exists or not for security
                return {"message": "If the email exists, a reset link has been sent"}
            
            # Create reset token
            reset_token = self.jwt_manager.create_reset_token(user["user_id"], email)
            
            # Store reset token hash in database
            reset_token_hash = self.security_utils.hash_token(reset_token)
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "reset_token_hash": reset_token_hash,
                    "reset_token_created": datetime.utcnow()
                }}
            )
            
            # Send reset email (implementation depends on email service)
            await self._send_password_reset_email(email, reset_token)
            
            return {"message": "Password reset link has been sent to your email"}
            
        except Exception as e:
            logger.error(f"Password reset request failed: {e}")
            return {"message": "If the email exists, a reset link has been sent"}
    
    async def reset_password(self, request: PasswordResetRequest) -> Dict[str, str]:
        """
        Reset user password using reset token.
        
        Args:
            request: Password reset request
            
        Returns:
            Reset confirmation
            
        Raises:
            ValidationException: If reset fails
        """
        try:
            # Validate new password
            password_validation = self.password_validator.validate_password_strength(request.new_password)
            if not password_validation["is_valid"]:
                raise ValidationException(
                    f"Password validation failed: {', '.join(password_validation['errors'])}"
                )
            
            # Decode reset token
            token_data = self.jwt_manager.decode_token(request.reset_token)
            if not token_data or token_data.token_type != TokenType.RESET:
                raise ValidationException("Invalid or expired reset token")
            
            db = await get_database()
            
            # Verify token hash in database
            reset_token_hash = self.security_utils.hash_token(request.reset_token)
            user = await db.users.find_one({
                "user_id": token_data.user_id,
                "email": request.email,
                "reset_token_hash": reset_token_hash
            })
            
            if not user:
                raise ValidationException("Invalid reset token")
            
            # Check if token is not too old (additional security)
            reset_created = user.get("reset_token_created")
            if reset_created and (datetime.utcnow() - reset_created).total_seconds() > 3600:  # 1 hour
                raise ValidationException("Reset token has expired")
            
            # Hash new password
            new_password_hash = self.security_utils.hash_password(request.new_password)
            
            # Update password and clear reset token
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "password_hash": new_password_hash,
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "reset_token_hash": "",
                    "reset_token_created": ""
                }}
            )
            
            # Log security event
            await self._log_security_event(
                "password_reset",
                user_id=user["user_id"],
                event_data={"email": request.email}
            )
            
            return {"message": "Password has been reset successfully"}
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            raise ValidationException("Password reset failed")
    
    # Helper methods
    async def _log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: str = "unknown",
        user_agent: str = "unknown"
    ) -> None:
        """Log security events for audit purposes."""
        try:
            db = await get_database()
            
            security_event = SecurityEvent(
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                event_data=event_data or {},
                timestamp=datetime.utcnow(),
                severity="info"
            )
            
            await db.security_events.insert_one(security_event.dict())
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    async def _send_verification(self, user_id: str, email: str, method: str) -> None:
        """Send verification email or SMS."""
        # Mock implementation - in production, integrate with email/SMS service
        logger.info(f"Sending {method} verification to {email} for user {user_id}")
    
    async def _send_password_reset_email(self, email: str, reset_token: str) -> None:
        """Send password reset email."""
        # Mock implementation - in production, integrate with email service
        logger.info(f"Sending password reset email to {email}")
    
    async def _verify_aadhaar_otp(self, aadhaar_number: str, otp: str, transaction_id: str) -> bool:
        """Verify Aadhaar OTP with UIDAI."""
        # Mock implementation - in production, integrate with UIDAI APIs
        logger.info(f"Verifying Aadhaar OTP for {aadhaar_number}")
        return otp == "123456"  # Mock verification