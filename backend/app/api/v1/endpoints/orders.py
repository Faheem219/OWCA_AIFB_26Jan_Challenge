"""
Orders management endpoints for buyer and vendor order handling.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Annotated, Optional
from datetime import datetime
from enum import Enum
import uuid
import logging

from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@router.post("/")
async def create_order(
    order_data: Dict[str, Any],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_database)]
) -> Dict[str, Any]:
    """
    Create a new order (buyer makes an offer/order to a vendor).
    """
    try:
        buyer_id = current_user.user_id
        
        # Validate required fields
        product_id = order_data.get("product_id")
        vendor_id = order_data.get("vendor_id")
        quantity = order_data.get("quantity", 1)
        offered_price = order_data.get("offered_price")
        message = order_data.get("message", "")
        
        logger.info(f"Creating order: buyer_id={buyer_id}, product_id={product_id}, vendor_id={vendor_id}")
        
        if not product_id:
            raise HTTPException(status_code=400, detail="Product ID is required")
        if not vendor_id:
            raise HTTPException(status_code=400, detail="Vendor ID is required")
        if not offered_price:
            raise HTTPException(status_code=400, detail="Offered price is required")
        
        # Get product details - products use 'product_id' field
        product = await db.products.find_one({"product_id": product_id})
        logger.info(f"Product lookup result: {product is not None}")
        if not product:
            logger.error(f"Product not found with product_id: {product_id}")
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Verify vendor owns the product
        if product.get("vendor_id") != vendor_id:
            logger.error(f"Vendor mismatch: product.vendor_id={product.get('vendor_id')}, provided vendor_id={vendor_id}")
            raise HTTPException(status_code=400, detail="Product does not belong to specified vendor")
        
        # Get buyer profile - users use 'user_id' field
        buyer = await db.users.find_one({"user_id": buyer_id})
        buyer_name = buyer.get("profile", {}).get("full_name", "Unknown Buyer") if buyer else "Unknown Buyer"
        buyer_email = buyer.get("email", "") if buyer else ""
        
        # Get vendor profile
        vendor = await db.users.find_one({"user_id": vendor_id})
        vendor_name = vendor.get("profile", {}).get("business_name") or vendor.get("profile", {}).get("full_name", "Unknown Vendor") if vendor else "Unknown Vendor"
        
        # Get product name
        product_name = product.get("name", {})
        if isinstance(product_name, dict):
            product_name = product_name.get("original_text", "Unknown Product")
        
        # Create order
        order_id = str(uuid.uuid4())
        order = {
            "_id": order_id,
            "buyer_id": buyer_id,
            "buyer_name": buyer_name,
            "buyer_email": buyer_email,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "product_id": product_id,
            "product_name": product_name,
            "product_image": product.get("images", [{}])[0].get("image_url") if product.get("images") else None,
            "quantity": quantity,
            "unit": product.get("availability", {}).get("unit", "kg"),
            "original_price": float(product.get("price_info", {}).get("base_price", 0)),
            "offered_price": float(offered_price),
            "total_amount": float(offered_price) * quantity,
            "message": message,
            "status": OrderStatus.PENDING.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "tracking_number": None,
            "estimated_delivery": None,
        }
        
        await db.orders.insert_one(order)
        
        return {
            "id": order_id,
            "message": "Order created successfully",
            "order": {
                **order,
                "_id": order_id,
                "created_at": order["created_at"].isoformat(),
                "updated_at": order["updated_at"].isoformat(),
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.get("/buyer")
async def get_buyer_orders(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_database)],
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Get all orders for the current buyer.
    """
    try:
        buyer_id = current_user.user_id
        
        query = {"buyer_id": buyer_id}
        if status:
            query["status"] = status
        
        orders = await db.orders.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        total = await db.orders.count_documents(query)
        
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                "id": str(order["_id"]),
                "product_id": order.get("product_id"),
                "product_name": order.get("product_name"),
                "product_image": order.get("product_image"),
                "vendor_id": order.get("vendor_id"),
                "vendor_name": order.get("vendor_name"),
                "quantity": order.get("quantity"),
                "unit": order.get("unit"),
                "original_price": order.get("original_price"),
                "offered_price": order.get("offered_price"),
                "total_amount": order.get("total_amount"),
                "message": order.get("message"),
                "status": order.get("status"),
                "tracking_number": order.get("tracking_number"),
                "estimated_delivery": order.get("estimated_delivery"),
                "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
                "updated_at": order.get("updated_at").isoformat() if order.get("updated_at") else None,
            })
        
        return {
            "orders": formatted_orders,
            "total": total,
            "has_more": skip + limit < total
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")


@router.get("/vendor")
async def get_vendor_orders(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_database)],
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Get all orders for the current vendor.
    """
    try:
        vendor_id = current_user.user_id
        
        query = {"vendor_id": vendor_id}
        if status:
            query["status"] = status
        
        orders = await db.orders.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        total = await db.orders.count_documents(query)
        
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                "id": str(order["_id"]),
                "product_id": order.get("product_id"),
                "product_name": order.get("product_name"),
                "product_image": order.get("product_image"),
                "buyer_id": order.get("buyer_id"),
                "buyer_name": order.get("buyer_name"),
                "buyer_email": order.get("buyer_email"),
                "quantity": order.get("quantity"),
                "unit": order.get("unit"),
                "original_price": order.get("original_price"),
                "offered_price": order.get("offered_price"),
                "total_amount": order.get("total_amount"),
                "message": order.get("message"),
                "status": order.get("status"),
                "tracking_number": order.get("tracking_number"),
                "estimated_delivery": order.get("estimated_delivery"),
                "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
                "updated_at": order.get("updated_at").isoformat() if order.get("updated_at") else None,
            })
        
        return {
            "orders": formatted_orders,
            "total": total,
            "has_more": skip + limit < total
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_database)]
) -> Dict[str, Any]:
    """
    Get a specific order by ID.
    """
    try:
        user_id = current_user.user_id
        
        order = await db.orders.find_one({"_id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Ensure user is buyer or vendor of the order
        if user_id not in [order.get("buyer_id"), order.get("vendor_id")]:
            raise HTTPException(status_code=403, detail="Not authorized to view this order")
        
        return {
            "id": str(order["_id"]),
            "product_id": order.get("product_id"),
            "product_name": order.get("product_name"),
            "product_image": order.get("product_image"),
            "buyer_id": order.get("buyer_id"),
            "buyer_name": order.get("buyer_name"),
            "buyer_email": order.get("buyer_email"),
            "vendor_id": order.get("vendor_id"),
            "vendor_name": order.get("vendor_name"),
            "quantity": order.get("quantity"),
            "unit": order.get("unit"),
            "original_price": order.get("original_price"),
            "offered_price": order.get("offered_price"),
            "total_amount": order.get("total_amount"),
            "message": order.get("message"),
            "status": order.get("status"),
            "tracking_number": order.get("tracking_number"),
            "estimated_delivery": order.get("estimated_delivery"),
            "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
            "updated_at": order.get("updated_at").isoformat() if order.get("updated_at") else None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch order: {str(e)}")


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_data: Dict[str, Any],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_database)]
) -> Dict[str, Any]:
    """
    Update order status (vendor only for most status changes, buyer can cancel pending orders).
    """
    try:
        user_id = current_user.user_id
        new_status = status_data.get("status")
        
        if not new_status or new_status not in [s.value for s in OrderStatus]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        order = await db.orders.find_one({"_id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        is_vendor = user_id == order.get("vendor_id")
        is_buyer = user_id == order.get("buyer_id")
        
        if not is_vendor and not is_buyer:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Buyers can only cancel pending orders
        if is_buyer and not is_vendor:
            if new_status != OrderStatus.CANCELLED.value:
                raise HTTPException(status_code=403, detail="Buyers can only cancel orders")
            if order.get("status") != OrderStatus.PENDING.value:
                raise HTTPException(status_code=400, detail="Can only cancel pending orders")
        
        # Update order
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        
        # Add tracking info if provided
        if status_data.get("tracking_number"):
            update_data["tracking_number"] = status_data.get("tracking_number")
        if status_data.get("estimated_delivery"):
            update_data["estimated_delivery"] = status_data.get("estimated_delivery")
        
        await db.orders.update_one(
            {"_id": order_id},
            {"$set": update_data}
        )
        
        return {
            "id": order_id,
            "status": new_status,
            "message": f"Order status updated to {new_status}",
            "updated_at": update_data["updated_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update order: {str(e)}")
