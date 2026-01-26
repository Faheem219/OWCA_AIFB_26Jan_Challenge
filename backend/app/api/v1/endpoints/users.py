"""
User management endpoints for profile operations.
"""

import logging
from typing import Dict, Any, List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import ValidationError

from app.core.dependencies import (
    get_current_user,
    get_current_user_id,
    require_vendor,
    require_buyer,
    require_vendor_or_buyer
)
from app.models.user import (
    UserResponse,
    UserUpdateRequest,
    UserPreferences,
    Address,
    DocumentReference,
    UserRole
)
from app.services.user_service import UserService
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    AuthorizationException
)

logger = logging.getLogger(__name__)

router = APIRouter()
user_service = UserService()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
) -> UserResponse:
    """
    Get current user's profile information.
    
    Returns:
        User profile data
    """
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_updates: UserUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
) -> UserResponse:
    """
    Update current user's profile information.
    
    Args:
        profile_updates: Updated profile data
        current_user: Current authenticated user
        
    Returns:
        Updated profile information
        
    Raises:
        HTTPException: If update fails or validation errors occur
    """
    try:
        updated_user = await user_service.update_user_profile(
            current_user.user_id,
            profile_updates,
            current_user.user_id
        )
        return updated_user
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/profile/completeness")
async def get_profile_completeness(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
) -> Dict[str, Any]:
    """
    Get current user's profile completeness status.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Profile completeness information
    """
    try:
        completeness = await user_service.validate_profile_completeness(current_user.user_id)
        return completeness
        
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
) -> UserPreferences:
    """
    Get current user's preferences.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User preferences
    """
    try:
        preferences = await user_service.get_user_preferences(current_user.user_id)
        return preferences
        
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
) -> UserPreferences:
    """
    Update current user's preferences.
    
    Args:
        preferences: Updated preferences
        current_user: Current authenticated user
        
    Returns:
        Updated preferences
    """
    try:
        updated_preferences = await user_service.update_user_preferences(
            current_user.user_id,
            preferences,
            current_user.user_id
        )
        return updated_preferences
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/addresses", response_model=List[Address])
async def add_delivery_address(
    address: Address,
    current_user: Annotated[UserResponse, Depends(require_buyer)]
) -> List[Address]:
    """
    Add delivery address for buyer.
    
    Args:
        address: Address to add
        current_user: Current authenticated buyer
        
    Returns:
        Updated list of delivery addresses
    """
    try:
        addresses = await user_service.add_delivery_address(
            current_user.user_id,
            address,
            current_user.user_id
        )
        return addresses
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/verification-documents", response_model=List[DocumentReference])
async def add_verification_document(
    document_type: str,
    document_url: str,
    current_user: Annotated[UserResponse, Depends(require_vendor)]
) -> List[DocumentReference]:
    """
    Add verification document for vendor.
    
    Args:
        document_type: Type of document (aadhaar, pan, gst, trade_license, bank_statement)
        document_url: URL to the uploaded document
        current_user: Current authenticated vendor
        
    Returns:
        Updated list of verification documents
    """
    try:
        documents = await user_service.add_verification_document(
            current_user.user_id,
            document_type,
            document_url,
            current_user.user_id
        )
        return documents
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/verification-status")
async def get_verification_status(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
) -> Dict[str, Any]:
    """
    Get current user's verification status and requirements.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Verification status information
    """
    verification_info = {
        "verification_status": current_user.verification_status,
        "is_verified": current_user.verification_status.value == "verified",
        "user_role": current_user.role.value
    }
    
    # Add role-specific verification requirements
    if current_user.role == UserRole.VENDOR:
        verification_info.update({
            "required_documents": ["aadhaar", "pan", "gst", "trade_license"],
            "optional_documents": ["bank_statement"],
            "uploaded_documents": getattr(current_user, 'verification_documents', [])
        })
    elif current_user.role == UserRole.BUYER:
        verification_info.update({
            "required_documents": ["aadhaar"],
            "optional_documents": ["pan"],
            "uploaded_documents": []
        })
    
    return verification_info


@router.get("/dashboard")
async def get_user_dashboard(
    current_user: Annotated[UserResponse, Depends(require_vendor_or_buyer)]
) -> Dict[str, Any]:
    """
    Get role-specific dashboard data for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dashboard data based on user role
    """
    dashboard_data = {
        "user_info": {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "role": current_user.role.value,
            "verification_status": current_user.verification_status.value,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at,
            "last_login": current_user.last_login
        }
    }
    
    # Add role-specific dashboard data
    if current_user.role == UserRole.VENDOR:
        dashboard_data.update({
            "vendor_stats": {
                "business_name": getattr(current_user, 'business_name', None),
                "business_type": getattr(current_user, 'business_type', None),
                "product_categories": getattr(current_user, 'product_categories', []),
                "market_location": getattr(current_user, 'market_location', None),
                "rating": getattr(current_user, 'rating', 0.0),
                "total_transactions": getattr(current_user, 'total_transactions', 0)
            },
            "quick_actions": [
                {"action": "add_product", "label": "Add New Product", "url": "/products/create"},
                {"action": "view_orders", "label": "View Orders", "url": "/vendor/orders"},
                {"action": "analytics", "label": "View Analytics", "url": "/vendor/analytics"}
            ]
        })
    elif current_user.role == UserRole.BUYER:
        dashboard_data.update({
            "buyer_stats": {
                "preferred_categories": getattr(current_user, 'preferred_categories', []),
                "total_purchases": getattr(current_user, 'total_purchases', 0),
                "budget_range": getattr(current_user, 'budget_range', None)
            },
            "quick_actions": [
                {"action": "browse_products", "label": "Browse Products", "url": "/products"},
                {"action": "view_orders", "label": "My Orders", "url": "/buyer/orders"},
                {"action": "wishlist", "label": "My Wishlist", "url": "/buyer/wishlist"}
            ]
        })
    
    return dashboard_data


@router.get("/search")
async def search_users(
    query: str = "",
    role: str = None,
    location: str = None,
    limit: int = 20,
    skip: int = 0,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None
) -> Dict[str, Any]:
    """
    Search users by various criteria.
    
    Args:
        query: Search query (name, email, business name)
        role: Filter by user role (vendor, buyer)
        location: Filter by location
        limit: Maximum results to return
        skip: Number of results to skip
        current_user: Current authenticated user
        
    Returns:
        Search results with pagination info
    """
    try:
        # Convert role string to UserRole enum if provided
        role_filter = None
        if role:
            try:
                role_filter = UserRole(role.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}. Must be 'vendor' or 'buyer'"
                )
        
        # Validate pagination parameters
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip must be >= 0"
            )
        
        # Perform search
        users = await user_service.search_users(
            query=query,
            role=role_filter,
            location=location,
            limit=limit,
            skip=skip
        )
        
        return {
            "users": users,
            "pagination": {
                "limit": limit,
                "skip": skip,
                "count": len(users),
                "has_more": len(users) == limit
            },
            "filters": {
                "query": query,
                "role": role,
                "location": location
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )