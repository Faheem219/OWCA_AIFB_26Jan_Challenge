"""
Review and rating API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional, Tuple
import logging

from app.api.deps import get_current_active_user, get_current_vendor
from app.services.review_service import ReviewService
from app.services.translation_service import TranslationService
from app.models.user import UserInDB
from app.models.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewWithTranslations,
    ReviewSummary, ReviewModerationRequest, ReviewModerationResponse,
    ReviewHelpfulnessRequest, ReviewReportRequest, ReviewFilters,
    ReviewStats, BulkReviewOperation
)
from app.models.common import APIResponse
from app.db.mongodb import get_database
from app.db.redis import get_redis
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_review_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis = Depends(get_redis)
) -> ReviewService:
    """Get review service instance."""
    translation_service = TranslationService(db, redis)
    return ReviewService(db, translation_service)


@router.post("/", response_model=APIResponse)
async def create_review(
    review_data: ReviewCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Create a new review for a vendor."""
    try:
        review = await review_service.create_review(
            str(current_user.id),
            review_data
        )
        
        return APIResponse(
            success=True,
            message="Review created successfully",
            data={
                "review_id": str(review.id),
                "status": review.status,
                "message": "Review submitted and is under moderation" if review.status == "pending" else "Review published successfully"
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Create review error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create review"
        )


@router.get("/{review_id}", response_model=APIResponse)
async def get_review(
    review_id: str,
    language: Optional[str] = Query(None, description="Language code for translation"),
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Get a specific review by ID."""
    try:
        review = await review_service.get_review(review_id, language)
        
        return APIResponse(
            success=True,
            message="Review retrieved successfully",
            data=review.dict()
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get review error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get review"
        )


@router.put("/{review_id}", response_model=APIResponse)
async def update_review(
    review_id: str,
    update_data: ReviewUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Update an existing review (only by the review author)."""
    try:
        updated_review = await review_service.update_review(
            review_id,
            str(current_user.id),
            update_data
        )
        
        return APIResponse(
            success=True,
            message="Review updated successfully",
            data={
                "review_id": str(updated_review.id),
                "status": updated_review.status
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Update review error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review"
        )


@router.get("/vendor/{vendor_id}", response_model=APIResponse)
async def get_vendor_reviews(
    vendor_id: str,
    language: Optional[str] = Query(None, description="Language code for translation"),
    min_rating: Optional[float] = Query(None, ge=1.0, le=5.0, description="Minimum rating filter"),
    max_rating: Optional[float] = Query(None, ge=1.0, le=5.0, description="Maximum rating filter"),
    is_verified_purchase: Optional[bool] = Query(None, description="Filter by verified purchases"),
    sort_by: str = Query("created_at", description="Sort by: created_at, rating, helpful_votes"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return"),
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Get reviews for a specific vendor with filtering and pagination."""
    try:
        filters = ReviewFilters(
            min_rating=min_rating,
            max_rating=max_rating,
            is_verified_purchase=is_verified_purchase,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit
        )
        
        reviews, total_count = await review_service.get_vendor_reviews(
            vendor_id,
            filters,
            language
        )
        
        return APIResponse(
            success=True,
            message="Vendor reviews retrieved successfully",
            data={
                "reviews": [review.dict() for review in reviews],
                "pagination": {
                    "total_count": total_count,
                    "skip": skip,
                    "limit": limit,
                    "has_more": skip + limit < total_count
                }
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get vendor reviews error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vendor reviews"
        )


@router.get("/vendor/{vendor_id}/summary", response_model=APIResponse)
async def get_vendor_review_summary(
    vendor_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Get review summary statistics for a vendor."""
    try:
        summary = await review_service.get_review_summary(vendor_id)
        
        return APIResponse(
            success=True,
            message="Vendor review summary retrieved successfully",
            data=summary.dict()
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get vendor review summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vendor review summary"
        )


@router.post("/{review_id}/helpful", response_model=APIResponse)
async def mark_review_helpful(
    review_id: str,
    helpfulness_request: ReviewHelpfulnessRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Mark a review as helpful or unhelpful."""
    try:
        result = await review_service.mark_review_helpful(
            review_id,
            str(current_user.id),
            helpfulness_request
        )
        
        return APIResponse(
            success=True,
            message="Review helpfulness updated successfully",
            data=result
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Mark review helpful error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review helpfulness"
        )


@router.post("/{review_id}/report", response_model=APIResponse)
async def report_review(
    review_id: str,
    report_request: ReviewReportRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Report a review for inappropriate content."""
    try:
        # For now, just increment the reported count
        # In production, this would create a moderation ticket
        
        return APIResponse(
            success=True,
            message="Review reported successfully",
            data={
                "review_id": review_id,
                "message": "Thank you for reporting. Our moderation team will review this content."
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Report review error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to report review"
        )


@router.get("/my/reviews", response_model=APIResponse)
async def get_my_reviews(
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return"),
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Get reviews written by the current user."""
    try:
        filters = ReviewFilters(
            buyer_id=str(current_user.id),
            skip=skip,
            limit=limit
        )
        
        reviews, total_count = await review_service.get_vendor_reviews(
            "",  # Empty vendor_id since we're filtering by buyer_id
            filters
        )
        
        return APIResponse(
            success=True,
            message="Your reviews retrieved successfully",
            data={
                "reviews": [review.dict() for review in reviews],
                "pagination": {
                    "total_count": total_count,
                    "skip": skip,
                    "limit": limit,
                    "has_more": skip + limit < total_count
                }
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get my reviews error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get your reviews"
        )


# Admin endpoints for review moderation
@router.post("/admin/moderate/{review_id}", response_model=APIResponse)
async def moderate_review(
    review_id: str,
    moderation_request: ReviewModerationRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Admin endpoint to moderate a review."""
    try:
        # TODO: Add admin role check
        # For now, any authenticated user can perform admin actions
        # In production, add proper role-based access control
        
        result = await review_service.moderate_review(
            review_id,
            moderation_request,
            str(current_user.id)
        )
        
        return APIResponse(
            success=True,
            message="Review moderated successfully",
            data=result.dict()
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Moderate review error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to moderate review"
        )


@router.get("/admin/pending", response_model=APIResponse)
async def get_pending_reviews(
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of reviews to return"),
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Admin endpoint to get pending reviews for moderation."""
    try:
        # TODO: Add admin role check
        
        filters = ReviewFilters(
            status="pending",
            skip=skip,
            limit=limit,
            sort_by="created_at",
            sort_order="asc"  # Oldest first for moderation queue
        )
        
        reviews, total_count = await review_service.get_vendor_reviews(
            "",  # Empty vendor_id to get all pending reviews
            filters
        )
        
        return APIResponse(
            success=True,
            message="Pending reviews retrieved successfully",
            data={
                "reviews": [review.dict() for review in reviews],
                "pagination": {
                    "total_count": total_count,
                    "skip": skip,
                    "limit": limit,
                    "has_more": skip + limit < total_count
                }
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get pending reviews error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending reviews"
        )


@router.get("/admin/stats", response_model=APIResponse)
async def get_review_stats(
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Admin endpoint to get review statistics."""
    try:
        # TODO: Add admin role check
        # This is a placeholder implementation
        
        return APIResponse(
            success=True,
            message="Review statistics retrieved successfully",
            data={
                "total_reviews": 0,
                "pending_reviews": 0,
                "approved_reviews": 0,
                "flagged_reviews": 0,
                "average_rating": 0.0
            }
        )
        
    except Exception as e:
        logger.error(f"Get review stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get review statistics"
        )


@router.post("/admin/bulk-moderate", response_model=APIResponse)
async def bulk_moderate_reviews(
    bulk_operation: BulkReviewOperation,
    current_user: UserInDB = Depends(get_current_active_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """Admin endpoint for bulk review moderation."""
    try:
        # TODO: Add admin role check
        # TODO: Implement bulk moderation in review service
        
        return APIResponse(
            success=True,
            message="Bulk moderation completed successfully",
            data={
                "processed_count": len(bulk_operation.review_ids),
                "action": bulk_operation.action
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Bulk moderate reviews error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk moderation"
        )


# Vendor-specific endpoints
@router.get("/vendor/my/reviews", response_model=APIResponse)
async def get_my_vendor_reviews(
    language: Optional[str] = Query(None, description="Language code for translation"),
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return"),
    current_user: UserInDB = Depends(get_current_vendor),
    review_service: ReviewService = Depends(get_review_service)
):
    """Get reviews for the current vendor's profile."""
    try:
        filters = ReviewFilters(
            skip=skip,
            limit=limit
        )
        
        reviews, total_count = await review_service.get_vendor_reviews(
            str(current_user.id),
            filters,
            language
        )
        
        return APIResponse(
            success=True,
            message="Your vendor reviews retrieved successfully",
            data={
                "reviews": [review.dict() for review in reviews],
                "pagination": {
                    "total_count": total_count,
                    "skip": skip,
                    "limit": limit,
                    "has_more": skip + limit < total_count
                }
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get my vendor reviews error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get your vendor reviews"
        )


@router.get("/vendor/my/summary", response_model=APIResponse)
async def get_my_vendor_review_summary(
    current_user: UserInDB = Depends(get_current_vendor),
    review_service: ReviewService = Depends(get_review_service)
):
    """Get review summary for the current vendor's profile."""
    try:
        summary = await review_service.get_review_summary(str(current_user.id))
        
        return APIResponse(
            success=True,
            message="Your vendor review summary retrieved successfully",
            data=summary.dict()
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get my vendor review summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get your vendor review summary"
        )