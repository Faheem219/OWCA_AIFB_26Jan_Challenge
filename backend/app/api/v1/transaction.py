"""
Transaction management API endpoints for the Multilingual Mandi platform.
Handles transaction tracking, delivery coordination, and record maintenance.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.payment import (
    DeliveryAddress,
    DeliveryMethod,
    DeliveryStatus,
    DeliveryTracking,
    TransactionRecord
)
from app.models.user import User
from app.services.transaction_service import TransactionService

router = APIRouter()


async def get_transaction_service():
    """Get initialized transaction service."""
    service = TransactionService()
    await service.initialize()
    return service


class CreateDeliveryTrackingRequest(BaseModel):
    """Request model for creating delivery tracking."""
    transaction_id: str
    delivery_method: DeliveryMethod
    pickup_address: DeliveryAddress
    delivery_address: DeliveryAddress
    delivery_instructions: Optional[Dict[str, str]] = None
    special_requirements: Optional[List[str]] = None


class UpdateDeliveryStatusRequest(BaseModel):
    """Request model for updating delivery status."""
    tracking_id: str
    new_status: DeliveryStatus
    location: Optional[str] = None
    message: Optional[str] = None
    proof_data: Optional[Dict] = None


class CreateTransactionRecordRequest(BaseModel):
    """Request model for creating transaction record."""
    transaction_id: str
    item_details: List[Dict]
    tax_breakdown: Optional[Dict[str, float]] = None
    discount_details: Optional[Dict[str, float]] = None
    gstin_buyer: Optional[str] = None
    gstin_vendor: Optional[str] = None


class TransactionResponse(BaseModel):
    """Response model for transaction operations."""
    success: bool
    message: str
    data: Optional[Dict] = None


@router.post("/delivery/create", response_model=DeliveryTracking)
async def create_delivery_tracking(
    request: CreateDeliveryTrackingRequest,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """
    Create delivery tracking for a transaction.
    
    Args:
        request: Delivery tracking creation request
        current_user: Current authenticated user
        transaction_service: Transaction service instance
        
    Returns:
        DeliveryTracking: Created delivery tracking record
    """
    try:
        delivery_tracking = await transaction_service.create_delivery_tracking(
            transaction_id=request.transaction_id,
            delivery_method=request.delivery_method,
            pickup_address=request.pickup_address,
            delivery_address=request.delivery_address,
            delivery_instructions=request.delivery_instructions,
            special_requirements=request.special_requirements
        )
        
        return delivery_tracking
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create delivery tracking: {str(e)}"
        )


@router.put("/delivery/status", response_model=DeliveryTracking)
async def update_delivery_status(
    request: UpdateDeliveryStatusRequest,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """
    Update delivery status with tracking information.
    
    Args:
        request: Delivery status update request
        current_user: Current authenticated user
        transaction_service: Transaction service instance
        
    Returns:
        DeliveryTracking: Updated delivery tracking record
    """
    try:
        delivery_tracking = await transaction_service.update_delivery_status(
            tracking_id=request.tracking_id,
            new_status=request.new_status,
            location=request.location,
            message=request.message,
            updated_by=current_user.user_id,
            proof_data=request.proof_data
        )
        
        return delivery_tracking
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update delivery status: {str(e)}"
        )


@router.get("/delivery/track/{tracking_id}", response_model=DeliveryTracking)
async def get_delivery_tracking(
    tracking_id: str,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """
    Get delivery tracking information.
    
    Args:
        tracking_id: Delivery tracking ID
        current_user: Current authenticated user
        transaction_service: Transaction service instance
        
    Returns:
        DeliveryTracking: Delivery tracking information
    """
    try:
        delivery_tracking = await transaction_service.get_delivery_tracking(tracking_id)
        return delivery_tracking
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get delivery tracking: {str(e)}"
        )


@router.get("/delivery/transaction/{transaction_id}", response_model=Optional[DeliveryTracking])
async def get_transaction_delivery_status(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """
    Get delivery status for a transaction.
    
    Args:
        transaction_id: Transaction ID
        current_user: Current authenticated user
        transaction_service: Transaction service instance
        
    Returns:
        Optional[DeliveryTracking]: Delivery tracking if exists
    """
    try:
        delivery_tracking = await transaction_service.get_transaction_delivery_status(
            transaction_id
        )
        return delivery_tracking
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transaction delivery status: {str(e)}"
        )


@router.post("/record/create", response_model=TransactionRecord)
async def create_transaction_record(
    request: CreateTransactionRecordRequest,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """
    Create comprehensive transaction record for accounting purposes.
    
    Args:
        request: Transaction record creation request
        current_user: Current authenticated user
        transaction_service: Transaction service instance
        
    Returns:
        TransactionRecord: Created transaction record
    """
    try:
        # Convert float values to Decimal for tax and discount breakdowns
        from decimal import Decimal
        
        tax_breakdown = None
        if request.tax_breakdown:
            tax_breakdown = {k: Decimal(str(v)) for k, v in request.tax_breakdown.items()}
        
        discount_details = None
        if request.discount_details:
            discount_details = {k: Decimal(str(v)) for k, v in request.discount_details.items()}
        
        transaction_record = await transaction_service.create_transaction_record(
            transaction_id=request.transaction_id,
            item_details=request.item_details,
            tax_breakdown=tax_breakdown,
            discount_details=discount_details,
            gstin_buyer=request.gstin_buyer,
            gstin_vendor=request.gstin_vendor
        )
        
        return transaction_record
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction record: {str(e)}"
        )


@router.get("/records", response_model=List[TransactionRecord])
async def get_transaction_records(
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    accounting_period: Optional[str] = Query(None, description="Accounting period (YYYY-MM)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get transaction records for the current user with filtering options.
    
    Args:
        current_user: Current authenticated user
        transaction_service: Transaction service instance
        start_date: Start date filter
        end_date: End date filter
        accounting_period: Accounting period filter
        limit: Maximum records to return
        offset: Number of records to skip
        
    Returns:
        List[TransactionRecord]: Filtered transaction records
    """
    try:
        records = await transaction_service.get_transaction_records(
            user_id=current_user.user_id,
            start_date=start_date,
            end_date=end_date,
            accounting_period=accounting_period,
            limit=limit,
            offset=offset
        )
        
        return records
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transaction records: {str(e)}"
        )


@router.get("/delivery/summary", response_model=Dict)
async def get_delivery_coordination_summary(
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
    language: str = Query("en", description="Language for the summary")
):
    """
    Generate delivery coordination summary for the current user.
    
    Args:
        current_user: Current authenticated user
        transaction_service: Transaction service instance
        language: Language for the summary
        
    Returns:
        Dict: Delivery coordination summary
    """
    try:
        summary = await transaction_service.generate_delivery_coordination_summary(
            user_id=current_user.user_id,
            language=language
        )
        
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate delivery summary: {str(e)}"
        )


@router.get("/delivery/methods", response_model=List[Dict])
async def get_supported_delivery_methods():
    """
    Get list of supported delivery methods.
    
    Returns:
        List[Dict]: Supported delivery methods with descriptions
    """
    try:
        methods = [
            {
                "method": DeliveryMethod.SELF_PICKUP,
                "name": "Self Pickup",
                "description": "Buyer picks up from vendor location",
                "estimated_time": "Same day",
                "cost": "Free",
                "features": ["immediate_availability", "no_delivery_charges"]
            },
            {
                "method": DeliveryMethod.VENDOR_DELIVERY,
                "name": "Vendor Delivery",
                "description": "Vendor delivers to buyer location",
                "estimated_time": "1-2 days",
                "cost": "Variable",
                "features": ["direct_delivery", "vendor_coordination"]
            },
            {
                "method": DeliveryMethod.THIRD_PARTY_COURIER,
                "name": "Third Party Courier",
                "description": "Professional courier service delivery",
                "estimated_time": "2-5 days",
                "cost": "Standard rates",
                "features": ["tracking", "insurance", "professional_handling"]
            },
            {
                "method": DeliveryMethod.LOCAL_TRANSPORT,
                "name": "Local Transport",
                "description": "Local transport service delivery",
                "estimated_time": "Same day or next day",
                "cost": "Local rates",
                "features": ["local_knowledge", "flexible_timing"]
            }
        ]
        
        return methods
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get delivery methods: {str(e)}"
        )


@router.get("/status/options", response_model=List[Dict])
async def get_delivery_status_options():
    """
    Get list of delivery status options.
    
    Returns:
        List[Dict]: Delivery status options with descriptions
    """
    try:
        statuses = [
            {
                "status": DeliveryStatus.PENDING,
                "name": "Pending",
                "description": "Delivery tracking created, awaiting pickup"
            },
            {
                "status": DeliveryStatus.CONFIRMED,
                "name": "Confirmed",
                "description": "Delivery confirmed by vendor/courier"
            },
            {
                "status": DeliveryStatus.PICKED_UP,
                "name": "Picked Up",
                "description": "Package picked up from vendor location"
            },
            {
                "status": DeliveryStatus.IN_TRANSIT,
                "name": "In Transit",
                "description": "Package is on the way to destination"
            },
            {
                "status": DeliveryStatus.OUT_FOR_DELIVERY,
                "name": "Out for Delivery",
                "description": "Package is out for final delivery"
            },
            {
                "status": DeliveryStatus.DELIVERED,
                "name": "Delivered",
                "description": "Package successfully delivered"
            },
            {
                "status": DeliveryStatus.FAILED,
                "name": "Failed",
                "description": "Delivery attempt failed"
            },
            {
                "status": DeliveryStatus.RETURNED,
                "name": "Returned",
                "description": "Package returned to vendor"
            }
        ]
        
        return statuses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get delivery status options: {str(e)}"
        )