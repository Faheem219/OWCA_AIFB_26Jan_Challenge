"""
Vendor registration and verification API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Dict, Any, List
import logging

from app.api.deps import get_current_active_user, get_current_vendor, get_auth_service
from app.services.vendor_verification_service import VendorVerificationService
from app.services.auth_service import AuthService
from app.models.user import (
    UserInDB, 
    VendorRegistrationRequest, 
    DocumentUploadRequest,
    DocumentUploadResponse,
    AdminVerificationAction,
    DocumentType
)
from app.models.common import APIResponse
from app.db.mongodb import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_vendor_verification_service(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> VendorVerificationService:
    """Get vendor verification service instance."""
    return VendorVerificationService(db)


@router.post("/register", response_model=APIResponse)
async def register_vendor(
    registration_data: VendorRegistrationRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    verification_service: VendorVerificationService = Depends(get_vendor_verification_service)
):
    """Register as a vendor and initiate verification process."""
    try:
        result = await verification_service.initiate_vendor_registration(
            str(current_user.id),
            registration_data
        )
        
        return APIResponse(
            success=True,
            message="Vendor registration initiated successfully",
            data=result
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Vendor registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vendor registration failed"
        )


@router.post("/request-document-upload", response_model=APIResponse)
async def request_document_upload(
    document_request: DocumentUploadRequest,
    current_user: UserInDB = Depends(get_current_vendor),
    verification_service: VendorVerificationService = Depends(get_vendor_verification_service)
):
    """Request document upload for verification."""
    try:
        upload_response = await verification_service.request_document_upload(
            str(current_user.id),
            document_request
        )
        
        return APIResponse(
            success=True,
            message="Document upload requested successfully",
            data=upload_response.dict()
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Document upload request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload request failed"
        )


@router.post("/upload-document/{document_id}", response_model=APIResponse)
async def upload_document(
    document_id: str,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_vendor),
    verification_service: VendorVerificationService = Depends(get_vendor_verification_service)
):
    """Upload document file for verification."""
    try:
        result = await verification_service.upload_document(
            str(current_user.id),
            document_id,
            file
        )
        
        return APIResponse(
            success=True,
            message="Document uploaded successfully",
            data=result
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload failed"
        )


@router.post("/verify-government-id/{document_id}", response_model=APIResponse)
async def verify_government_id(
    document_id: str,
    current_user: UserInDB = Depends(get_current_vendor),
    verification_service: VendorVerificationService = Depends(get_vendor_verification_service)
):
    """Verify government ID document."""
    try:
        result = await verification_service.verify_government_id(
            str(current_user.id),
            document_id
        )
        
        return APIResponse(
            success=True,
            message="Government ID verification completed",
            data=result
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Government ID verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Government ID verification failed"
        )


@router.get("/verification-status", response_model=APIResponse)
async def get_verification_status(
    current_user: UserInDB = Depends(get_current_vendor),
    verification_service: VendorVerificationService = Depends(get_vendor_verification_service)
):
    """Get vendor verification status."""
    try:
        status_data = await verification_service.get_verification_status(
            str(current_user.id)
        )
        
        return APIResponse(
            success=True,
            message="Verification status retrieved successfully",
            data=status_data
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get verification status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get verification status"
        )


@router.get("/profile", response_model=APIResponse)
async def get_vendor_profile(
    current_user: UserInDB = Depends(get_current_vendor)
):
    """Get vendor profile information."""
    try:
        if not current_user.vendor_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor profile not found"
            )
        
        return APIResponse(
            success=True,
            message="Vendor profile retrieved successfully",
            data=current_user.vendor_profile.dict() if current_user.vendor_profile else None
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get vendor profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vendor profile"
        )


@router.put("/profile", response_model=APIResponse)
async def update_vendor_profile(
    profile_data: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_vendor),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update vendor profile information."""
    try:
        # Only allow updating certain fields after verification
        allowed_fields = [
            "business_hours", "description", "specializations", 
            "languages_spoken"
        ]
        
        # Filter update data to only allowed fields
        filtered_data = {}
        for field in allowed_fields:
            if field in profile_data:
                filtered_data[f"vendor_profile.{field}"] = profile_data[field]
        
        if not filtered_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        updated_user = await auth_service.update_user_profile(
            str(current_user.id),
            filtered_data
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return APIResponse(
            success=True,
            message="Vendor profile updated successfully",
            data=updated_user.vendor_profile.dict() if updated_user.vendor_profile else None
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Update vendor profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vendor profile"
        )


# Admin endpoints for vendor verification management
@router.post("/admin/review/{vendor_id}", response_model=APIResponse)
async def admin_review_vendor(
    vendor_id: str,
    action: AdminVerificationAction,
    current_user: UserInDB = Depends(get_current_active_user),
    verification_service: VendorVerificationService = Depends(get_vendor_verification_service)
):
    """Admin endpoint to review and approve/reject vendor applications."""
    try:
        # TODO: Add admin role check
        # For now, any authenticated user can perform admin actions
        # In production, add proper role-based access control
        
        result = await verification_service.admin_review_vendor(
            vendor_id,
            action,
            str(current_user.id)
        )
        
        return APIResponse(
            success=True,
            message="Vendor review completed successfully",
            data=result
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Admin vendor review error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin vendor review failed"
        )


@router.get("/admin/pending-verifications", response_model=APIResponse)
async def get_pending_verifications(
    current_user: UserInDB = Depends(get_current_active_user),
    verification_service: VendorVerificationService = Depends(get_vendor_verification_service)
):
    """Admin endpoint to get list of pending vendor verifications."""
    try:
        # TODO: Add admin role check
        # This is a placeholder implementation
        
        return APIResponse(
            success=True,
            message="Pending verifications retrieved successfully",
            data={"pending_verifications": []}  # Placeholder
        )
        
    except Exception as e:
        logger.error(f"Get pending verifications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending verifications"
        )


@router.get("/required-documents/{business_type}", response_model=APIResponse)
async def get_required_documents(business_type: str):
    """Get list of required documents for a business type."""
    try:
        from app.services.vendor_verification_service import VendorVerificationService
        required_docs = VendorVerificationService._get_required_documents(business_type)
        
        return APIResponse(
            success=True,
            message="Required documents retrieved successfully",
            data={
                "business_type": business_type,
                "required_documents": required_docs
            }
        )
        
    except Exception as e:
        logger.error(f"Get required documents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get required documents"
        )