"""
Authentication endpoints for user registration, login, and token management.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import (
    get_current_user_id,
    security
)
from app.core.exceptions import (
    AuthenticationException,
    ValidationException,
    ExternalServiceException
)
from app.models.auth import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    OAuthCredentials,
    AadhaarCredentials,
    VerificationData,
    LoginResponse,
    RegisterResponse,
    TokenRefreshResponse,
    VerificationResponse,
    LogoutResponse,
    AuthMethod
)
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
async def register_user(
    request: RegisterRequest
) -> RegisterResponse:
    """
    Register a new user account.
    
    Supports multiple authentication methods:
    - Email and password
    - Phone and password
    - Google OAuth (requires additional profile completion)
    - Aadhaar (requires OTP verification)
    
    Args:
        request: User registration data
        req_info: Request information for logging
        
    Returns:
        Registration response with user info and tokens
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        auth_service = AuthService()
        result = await auth_service.register_user(request)
        
        if result.success:
            return RegisterResponse(
                user_id=result.user_id,
                message=result.message,
                requires_verification=result.requires_verification,
                verification_method=result.verification_method
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
            
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: LoginRequest
) -> LoginResponse:
    """
    Authenticate user and return access tokens.
    
    Supports multiple authentication methods:
    - Email and password
    - Phone and password
    
    Args:
        request: User login credentials
        req_info: Request information for logging
        
    Returns:
        Authentication response with tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        auth_service = AuthService()
        result = await auth_service.login_user(request)
        
        if result.success:
            return LoginResponse(
                access_token=result.access_token,
                refresh_token=result.refresh_token,
                token_type=result.token_type,
                expires_in=result.expires_in,
                user=result.user_info
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message
            )
            
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(request: RefreshTokenRequest) -> TokenRefreshResponse:
    """
    Refresh access token using refresh token.
    
    Args:
        request: Token refresh request containing refresh token
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        auth_service = AuthService()
        result = await auth_service.refresh_token(request)
        
        return TokenRefreshResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"]
        )
        
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> LogoutResponse:
    """
    Logout user and invalidate tokens.
    
    Args:
        credentials: User's access token
        
    Returns:
        Logout confirmation
    """
    try:
        auth_service = AuthService()
        result = await auth_service.logout_user(credentials.credentials)
        
        return LogoutResponse(
            message=result["message"],
            logged_out_at=result["logged_out_at"]
        )
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        # Return success even if logout fails to avoid user confusion
        return LogoutResponse()


@router.post("/oauth/google", response_model=LoginResponse)
async def authenticate_with_google(
    oauth_credentials: OAuthCredentials
) -> LoginResponse:
    """
    Authenticate user with Google OAuth.
    
    Args:
        oauth_credentials: Google OAuth credentials
        req_info: Request information for logging
        
    Returns:
        Authentication response with tokens
        
    Raises:
        HTTPException: If OAuth authentication fails
    """
    try:
        auth_service = AuthService()
        result = await auth_service.authenticate_with_google(oauth_credentials)
        
        if result.success:
            return LoginResponse(
                access_token=result.access_token,
                refresh_token=result.refresh_token,
                token_type=result.token_type,
                expires_in=result.expires_in,
                user=result.user_info
            )
        else:
            # User needs to complete registration
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail={
                    "message": result.message,
                    "user_info": result.user_info,
                    "requires_registration": True
                }
            )
            
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ExternalServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Google authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed"
        )


@router.post("/aadhaar", response_model=LoginResponse)
async def authenticate_with_aadhaar(
    aadhaar_credentials: AadhaarCredentials
) -> LoginResponse:
    """
    Authenticate user with Aadhaar.
    
    Args:
        aadhaar_credentials: Aadhaar authentication credentials
        req_info: Request information for logging
        
    Returns:
        Authentication response with tokens
        
    Raises:
        HTTPException: If Aadhaar authentication fails
    """
    try:
        auth_service = AuthService()
        result = await auth_service.authenticate_with_aadhaar(aadhaar_credentials)
        
        if result.success:
            return LoginResponse(
                access_token=result.access_token,
                refresh_token=result.refresh_token,
                token_type=result.token_type,
                expires_in=result.expires_in,
                user=result.user_info
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message
            )
            
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ExternalServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Aadhaar authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Aadhaar authentication failed"
        )


@router.post("/verify", response_model=VerificationResponse)
async def verify_user(verification_data: VerificationData) -> VerificationResponse:
    """
    Verify user account using verification code.
    
    Supports email and phone verification.
    
    Args:
        verification_data: Verification data including code and type
        
    Returns:
        Verification result
        
    Raises:
        HTTPException: If verification fails
    """
    try:
        auth_service = AuthService()
        result = await auth_service.verify_user(verification_data)
        
        return VerificationResponse(
            success=result["success"],
            message=result["message"],
            user_id=result.get("user_id")
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )


@router.post("/password-reset/request")
async def request_password_reset(email_request: Dict[str, str]) -> Dict[str, str]:
    """
    Request password reset for user.
    
    Args:
        email_request: Dictionary containing user's email
        
    Returns:
        Reset request confirmation
    """
    try:
        email = email_request.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        auth_service = AuthService()
        result = await auth_service.request_password_reset(email)
        
        return result
        
    except Exception as e:
        logger.error(f"Password reset request failed: {e}")
        # Always return success to avoid email enumeration
        return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm")
async def reset_password(request: PasswordResetRequest) -> Dict[str, str]:
    """
    Reset user password using reset token.
    
    Args:
        request: Password reset request with token and new password
        
    Returns:
        Reset confirmation
        
    Raises:
        HTTPException: If reset fails
    """
    try:
        auth_service = AuthService()
        result = await auth_service.reset_password(request)
        
        return result
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.get("/me")
async def get_current_user_info(
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Get current authenticated user information.
    
    Args:
        current_user_id: Current user ID from JWT token
        
    Returns:
        Current user information
        
    Raises:
        HTTPException: If user not found
    """
    try:
        from app.services.user_service import UserService
        
        user_service = UserService()
        user = await user_service.get_user_by_id(current_user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "verification_status": user.verification_status.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )