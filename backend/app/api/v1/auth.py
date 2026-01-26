"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import get_auth_service, get_current_active_user
from app.services.auth_service import AuthService
from app.models.user import UserCreate, UserResponse, Token, UserInDB
from app.models.common import APIResponse
from typing import Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=APIResponse)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    try:
        user = await auth_service.create_user(user_data)
        return APIResponse(
            success=True,
            message="User registered successfully",
            data=user.dict()
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=APIResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return JWT tokens."""
    try:
        token = await auth_service.login(form_data.username, form_data.password)
        return APIResponse(
            success=True,
            message="Login successful",
            data=token.dict()
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/login/email", response_model=APIResponse)
async def login_with_email(
    email: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user with email and password."""
    try:
        token = await auth_service.login(email, password)
        return APIResponse(
            success=True,
            message="Login successful",
            data=token.dict()
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Email login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=APIResponse)
async def refresh_token(
    refresh_token: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token."""
    try:
        token = await auth_service.refresh_token(refresh_token)
        return APIResponse(
            success=True,
            message="Token refreshed successfully",
            data=token.dict()
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=APIResponse)
async def logout(
    session_id: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Logout user and invalidate session."""
    try:
        success = await auth_service.logout(session_id)
        return APIResponse(
            success=success,
            message="Logout successful" if success else "Logout failed"
        )
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=APIResponse)
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get current user information."""
    user_response = UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone=current_user.phone,
        full_name=current_user.full_name,
        preferred_language=current_user.preferred_language,
        user_type=current_user.user_type,
        is_active=current_user.is_active,
        vendor_profile=current_user.vendor_profile,
        buyer_profile=current_user.buyer_profile,
        created_at=current_user.created_at,
        last_active=current_user.last_active
    )
    
    return APIResponse(
        success=True,
        message="User information retrieved successfully",
        data=user_response.dict()
    )


@router.put("/profile", response_model=APIResponse)
async def update_profile(
    update_data: Dict,
    current_user: UserInDB = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update user profile."""
    try:
        updated_user = await auth_service.update_user_profile(
            str(current_user.id), 
            update_data
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return APIResponse(
            success=True,
            message="Profile updated successfully",
            data=updated_user.dict()
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/verify-credentials", response_model=APIResponse)
async def verify_credentials(
    credentials: Dict,
    current_user: UserInDB = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify user credentials for vendor profile."""
    try:
        is_verified = await auth_service.verify_user_credentials(
            str(current_user.id),
            credentials
        )
        
        return APIResponse(
            success=True,
            message="Credentials verified" if is_verified else "Credentials verification failed",
            data={"verified": is_verified}
        )
        
    except Exception as e:
        logger.error(f"Credentials verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credentials verification failed"
        )