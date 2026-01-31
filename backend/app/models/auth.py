"""
Authentication data models for the Multilingual Mandi Marketplace Platform.

This module contains all authentication-related Pydantic models including
credentials, tokens, and authentication requests/responses.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, validator

from .user import UserRole, SupportedLanguage


class AuthMethod(str, Enum):
    """Supported authentication methods."""
    EMAIL = "email"
    PHONE = "phone"
    GOOGLE = "google"
    AADHAAR = "aadhaar"


class TokenType(str, Enum):
    """JWT token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFICATION = "verification"


class AuthCredentials(BaseModel):
    """Base authentication credentials."""
    method: AuthMethod = Field(..., description="Authentication method")
    identifier: str = Field(..., description="Email, phone, or OAuth identifier")
    password: Optional[str] = Field(None, description="Password (not required for OAuth)")
    
    @validator("password")
    def validate_password(cls, v, values):
        method = values.get("method")
        if method in [AuthMethod.EMAIL, AuthMethod.PHONE] and not v:
            raise ValueError("Password is required for email/phone authentication")
        return v


class LoginRequest(BaseModel):
    """User login request."""
    method: AuthMethod = Field(..., description="Authentication method")
    identifier: str = Field(..., description="Email, phone, or OAuth identifier")
    password: Optional[str] = Field(None, description="Password (not required for OAuth)")
    remember_me: bool = Field(default=False, description="Whether to extend token validity")
    
    @validator("identifier")
    def validate_identifier(cls, v, values):
        method = values.get("method")
        if method == AuthMethod.EMAIL:
            # Basic email validation (Pydantic EmailStr will handle full validation)
            if "@" not in v:
                raise ValueError("Invalid email format")
        elif method == AuthMethod.PHONE:
            # Basic phone validation
            if not v.startswith("+") and not v.isdigit():
                raise ValueError("Invalid phone format")
        return v


class RegisterRequest(BaseModel):
    """User registration request."""
    method: AuthMethod = Field(..., description="Registration method")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")
    phone: Optional[str] = Field(None, description="User's phone number")
    role: UserRole = Field(..., description="User role")
    preferred_language: SupportedLanguage = Field(
        default=SupportedLanguage.ENGLISH,
        description="Primary preferred language"
    )
    
    # Basic profile information
    full_name: str = Field(..., description="User's full name")
    location_city: str = Field(..., description="User's city")
    location_state: str = Field(..., description="User's state")
    location_pincode: str = Field(..., description="Location pincode (any format accepted)")
    
    # Vendor-specific fields
    business_name: Optional[str] = Field(None, description="Business name (required for vendors)")
    business_type: Optional[str] = Field(None, description="Business type (required for vendors)")
    product_categories: Optional[List[str]] = Field(None, description="Product categories for vendors")
    market_location: Optional[str] = Field(None, description="Market location for vendors")
    
    # Buyer-specific fields
    preferred_categories: Optional[List[str]] = Field(None, description="Preferred categories for buyers")
    
    # Terms and conditions
    accept_terms: bool = Field(..., description="User must accept terms and conditions")
    accept_privacy: bool = Field(..., description="User must accept privacy policy")
    
    @validator("accept_terms")
    def validate_terms(cls, v):
        if not v:
            raise ValueError("You must accept the terms and conditions")
        return v
    
    @validator("accept_privacy")
    def validate_privacy(cls, v):
        if not v:
            raise ValueError("You must accept the privacy policy")
        return v
    
    @validator("business_name")
    def validate_vendor_business_name(cls, v, values):
        if values.get("role") == UserRole.VENDOR and not v:
            raise ValueError("Business name is required for vendors")
        return v
    
    @validator("business_type")
    def validate_vendor_business_type(cls, v, values):
        if values.get("role") == UserRole.VENDOR and not v:
            raise ValueError("Business type is required for vendors")
        return v


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str = Field(..., description="Valid refresh token")


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr = Field(..., description="User's email address")
    new_password: str = Field(..., min_length=8, description="New password")
    reset_token: str = Field(..., description="Password reset token")


class OAuthCredentials(BaseModel):
    """OAuth authentication credentials."""
    provider: str = Field(..., description="OAuth provider (e.g., 'google')")
    access_token: str = Field(..., description="OAuth access token")
    id_token: Optional[str] = Field(None, description="OAuth ID token")
    user_info: Dict[str, Any] = Field(..., description="User information from OAuth provider")


class AadhaarCredentials(BaseModel):
    """Aadhaar authentication credentials."""
    aadhaar_number: str = Field(..., pattern=r"^\d{12}$", description="12-digit Aadhaar number")
    otp: str = Field(..., pattern=r"^\d{6}$", description="6-digit OTP")
    transaction_id: str = Field(..., description="Aadhaar authentication transaction ID")


class TokenData(BaseModel):
    """JWT token payload data."""
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: UserRole = Field(..., description="User role")
    token_type: TokenType = Field(..., description="Token type")
    issued_at: datetime = Field(..., description="Token issue timestamp")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    jti: str = Field(..., description="JWT ID for token revocation")


class AuthResult(BaseModel):
    """Authentication result."""
    success: bool = Field(..., description="Whether authentication was successful")
    user_id: Optional[str] = Field(None, description="User ID (if successful)")
    access_token: Optional[str] = Field(None, description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration time in seconds")
    user_info: Optional[Dict[str, Any]] = Field(None, description="Basic user information")
    message: Optional[str] = Field(None, description="Authentication message or error")
    requires_verification: bool = Field(default=False, description="Whether user needs verification")
    verification_method: Optional[str] = Field(None, description="Required verification method")


class VerificationData(BaseModel):
    """User verification data."""
    verification_type: str = Field(..., description="Type of verification (email, phone, aadhaar)")
    verification_code: str = Field(..., description="Verification code or OTP")
    verification_token: Optional[str] = Field(None, description="Verification token")
    additional_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional verification data"
    )


class AuthSession(BaseModel):
    """User authentication session."""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    device_info: Dict[str, Any] = Field(..., description="Device information")
    ip_address: str = Field(..., description="IP address")
    user_agent: str = Field(..., description="User agent string")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    expires_at: datetime = Field(..., description="Session expiration time")
    is_active: bool = Field(default=True, description="Whether session is active")


class SecurityEvent(BaseModel):
    """Security event for audit logging."""
    event_type: str = Field(..., description="Type of security event")
    user_id: Optional[str] = Field(None, description="User ID (if applicable)")
    ip_address: str = Field(..., description="IP address")
    user_agent: str = Field(..., description="User agent string")
    event_data: Dict[str, Any] = Field(..., description="Event-specific data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    severity: str = Field(default="info", description="Event severity level")


class RateLimitInfo(BaseModel):
    """Rate limiting information."""
    identifier: str = Field(..., description="Rate limit identifier (IP, user ID, etc.)")
    limit_type: str = Field(..., description="Type of rate limit")
    current_count: int = Field(..., description="Current request count")
    limit: int = Field(..., description="Maximum allowed requests")
    window_start: datetime = Field(..., description="Rate limit window start time")
    window_end: datetime = Field(..., description="Rate limit window end time")
    reset_time: datetime = Field(..., description="When the limit resets")


# Response models
class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: Dict[str, Any] = Field(..., description="User information")


class RegisterResponse(BaseModel):
    """Registration response model."""
    user_id: str = Field(..., description="Created user ID")
    message: str = Field(..., description="Registration success message")
    requires_verification: bool = Field(default=False, description="Whether verification is required")
    verification_method: Optional[str] = Field(None, description="Required verification method")


class TokenRefreshResponse(BaseModel):
    """Token refresh response model."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class VerificationResponse(BaseModel):
    """Verification response model."""
    success: bool = Field(..., description="Whether verification was successful")
    message: str = Field(..., description="Verification result message")
    user_id: Optional[str] = Field(None, description="User ID (if successful)")
    next_step: Optional[str] = Field(None, description="Next step in verification process")


class LogoutResponse(BaseModel):
    """Logout response model."""
    message: str = Field(default="Successfully logged out", description="Logout message")
    logged_out_at: datetime = Field(default_factory=datetime.utcnow, description="Logout timestamp")