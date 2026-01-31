"""
FastAPI dependencies for the Multilingual Mandi Marketplace Platform.

This module provides dependency injection functions for authentication,
authorization, and other common requirements.
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from app.core.security import JWTManager, verify_token_and_get_user_id
from app.core.database import get_database
from app.models.auth import TokenData, TokenType
from app.models.user import UserRole, UserResponse
from app.services.user_service import UserService

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> str:
    """
    Get current user ID from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        user_id = verify_token_and_get_user_id(token, TokenType.ACCESS)
        
        if user_id is None:
            raise credentials_exception
            
        return user_id
        
    except JWTError:
        raise credentials_exception


import logging

logger = logging.getLogger(__name__)


async def get_current_user(
    user_id: Annotated[str, Depends(get_current_user_id)]
) -> UserResponse:
    """
    Get current user profile.
    
    Args:
        user_id: Current user ID
        
    Returns:
        User profile
        
    Raises:
        HTTPException: If user not found or inactive
    """
    logger.info(f"Looking up user with ID: {user_id}")
    user_service = UserService()
    user = await user_service.get_user_by_id(user_id)
    
    if user is None:
        logger.error(f"User not found for ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
) -> UserResponse:
    """
    Get current active user (alias for get_current_user for clarity).
    
    Args:
        current_user: Current user
        
    Returns:
        Active user profile
    """
    return current_user


def require_role(required_role: UserRole):
    """
    Create a dependency that requires a specific user role.
    
    Args:
        required_role: Required user role
        
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: Annotated[UserResponse, Depends(get_current_active_user)]
    ) -> UserResponse:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    
    return role_checker


def require_roles(*required_roles: UserRole):
    """
    Create a dependency that requires one of multiple user roles.
    
    Args:
        required_roles: Required user roles
        
    Returns:
        Dependency function
    """
    async def roles_checker(
        current_user: Annotated[UserResponse, Depends(get_current_active_user)]
    ) -> UserResponse:
        if current_user.role not in required_roles:
            roles_str = ", ".join([role.value for role in required_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {roles_str}"
            )
        return current_user
    
    return roles_checker


# Specific role dependencies
require_vendor = require_role(UserRole.VENDOR)
require_buyer = require_role(UserRole.BUYER)
require_admin = require_role(UserRole.ADMIN)
require_vendor_or_buyer = require_roles(UserRole.VENDOR, UserRole.BUYER)


async def get_optional_current_user(
    request: Request
) -> Optional[UserResponse]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that work for both authenticated and anonymous users.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User profile if authenticated, None otherwise
    """
    try:
        # Try to get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        user_id = verify_token_and_get_user_id(token, TokenType.ACCESS)
        
        if user_id is None:
            return None
        
        user_service = UserService()
        user = await user_service.get_user_by_id(user_id)
        
        if user is None or not user.is_active:
            return None
        
        return user
        
    except Exception:
        # If any error occurs, return None (anonymous user)
        return None


async def get_request_info(request: Request) -> Request:
    """
    Extract request information for logging and security.
    
    Args:
        request: FastAPI request object
        
    Returns:
        The request object itself
    """
    return request


class RateLimiter:
    """Rate limiting dependency."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def __call__(self, request: Request) -> None:
        """
        Check rate limit for the request.
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        # TODO: Implement rate limiting using Redis
        # For now, this is a placeholder
        pass


# Common rate limiters
rate_limit_auth = RateLimiter(max_requests=5, window_seconds=60)  # 5 requests per minute for auth
rate_limit_api = RateLimiter(max_requests=100, window_seconds=60)  # 100 requests per minute for API


async def validate_content_type(request: Request, expected_type: str = "application/json") -> None:
    """
    Validate request content type.
    
    Args:
        request: FastAPI request object
        expected_type: Expected content type
        
    Raises:
        HTTPException: If content type is invalid
    """
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith(expected_type):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Content-Type must be {expected_type}"
        )


async def get_pagination_params(
    page: int = 1,
    limit: int = 20,
    max_limit: int = 100
) -> dict:
    """
    Get pagination parameters with validation.
    
    Args:
        page: Page number (1-based)
        limit: Items per page
        max_limit: Maximum allowed limit
        
    Returns:
        Dictionary with pagination parameters
        
    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be >= 1"
        )
    
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be >= 1"
        )
    
    if limit > max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limit cannot exceed {max_limit}"
        )
    
    skip = (page - 1) * limit
    
    return {
        "page": page,
        "limit": limit,
        "skip": skip
    }


async def get_language_preference(
    request: Request,
    current_user: Optional[UserResponse] = None
) -> str:
    """
    Get user's language preference from user profile or Accept-Language header.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user (optional)
        
    Returns:
        Language code (e.g., 'en', 'hi')
    """
    # If user is authenticated, use their preferred language
    if current_user and current_user.preferred_languages:
        return current_user.preferred_languages[0].value
    
    # Otherwise, try to get from Accept-Language header
    accept_language = request.headers.get("accept-language", "")
    if accept_language:
        # Parse Accept-Language header (simplified)
        languages = accept_language.split(",")
        for lang in languages:
            lang_code = lang.split(";")[0].strip().lower()
            # Map common language codes to supported languages
            if lang_code.startswith("hi"):
                return "hi"
            elif lang_code.startswith("ta"):
                return "ta"
            elif lang_code.startswith("te"):
                return "te"
            elif lang_code.startswith("kn"):
                return "kn"
            elif lang_code.startswith("ml"):
                return "ml"
            elif lang_code.startswith("gu"):
                return "gu"
            elif lang_code.startswith("pa"):
                return "pa"
            elif lang_code.startswith("bn"):
                return "bn"
            elif lang_code.startswith("mr"):
                return "mr"
    
    # Default to English
    return "en"