"""
Transaction management service for the Multilingual Mandi platform.
Handles transaction tracking, delivery coordination, and record maintenance.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException

from app.core.config import settings
from app.db.mongodb import get_database
from app.models.payment import (
    DeliveryAddress,
    DeliveryMethod,
    DeliveryStatus,
    DeliveryTracking,
    PaymentTransaction,
    TransactionRecord
)
from app.services.translation_service import TranslationService


class TransactionService:
    """Service for transaction tracking and delivery coordination."""
    
    def __init__(self):
        self.db = None
        self.translation_service = None
    
    async def initialize(self):
        """Initialize the transaction service with database connection."""
        self.db = await get_database()
    
    async def create_delivery_tracking(
        self,
        transaction_id: str,
        delivery_method: DeliveryMethod,
        pickup_address: DeliveryAddress,
        delivery_address: DeliveryAddress,
        delivery_instructions: Optional[Dict[str, str]] = None,
        special_requirements: Optional[List[str]] = None
    ) -> DeliveryTracking:
        """
        Create delivery tracking for a transaction.
        
        Args:
            transaction_id: Associated transaction ID
            delivery_method: Method of delivery
            pickup_address: Pickup address information
            delivery_address: Delivery address information
            delivery_instructions: Multilingual delivery instructions
            special_requirements: Special delivery requirements
            
        Returns:
            DeliveryTracking: Created delivery tracking record
        """
        if not self.db:
            await self.initialize()
        
        # Verify transaction exists
        transaction_data = await self.db.payment_transactions.find_one(
            {"transaction_id": transaction_id}
        )
        
        if not transaction_data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        transaction = PaymentTransaction(**transaction_data)
        
        # Generate tracking ID
        tracking_id = f"TRK_{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate estimated delivery time based on delivery method
        estimated_delivery_time = self._calculate_estimated_delivery_time(
            delivery_method, pickup_address, delivery_address
        )
        
        # Create delivery tracking
        delivery_tracking = DeliveryTracking(
            tracking_id=tracking_id,
            transaction_id=transaction_id,
            order_id=transaction.order_id,
            delivery_method=delivery_method,
            pickup_address=pickup_address,
            delivery_address=delivery_address,
            estimated_delivery_time=estimated_delivery_time,
            delivery_instructions=delivery_instructions or {},
            special_requirements=special_requirements or [],
            tracking_updates=[{
                "status": DeliveryStatus.PENDING,
                "timestamp": datetime.utcnow(),
                "location": pickup_address.city,
                "message": "Delivery tracking created",
                "updated_by": "system"
            }]
        )
        
        # Store in database
        await self.db.delivery_tracking.insert_one(delivery_tracking.dict())
        
        return delivery_tracking
    
    async def update_delivery_status(
        self,
        tracking_id: str,
        new_status: DeliveryStatus,
        location: Optional[str] = None,
        message: Optional[str] = None,
        updated_by: str = "system",
        proof_data: Optional[Dict] = None
    ) -> DeliveryTracking:
        """
        Update delivery status with tracking information.
        
        Args:
            tracking_id: Delivery tracking ID
            new_status: New delivery status
            location: Current location
            message: Status update message
            updated_by: Who updated the status
            proof_data: Proof of delivery data
            
        Returns:
            DeliveryTracking: Updated delivery tracking record
        """
        if not self.db:
            await self.initialize()
        
        # Get current tracking record
        tracking_data = await self.db.delivery_tracking.find_one(
            {"tracking_id": tracking_id}
        )
        
        if not tracking_data:
            raise HTTPException(status_code=404, detail="Delivery tracking not found")
        
        # Create status update
        status_update = {
            "status": new_status,
            "timestamp": datetime.utcnow(),
            "location": location or tracking_data.get("pickup_address", {}).get("city", "Unknown"),
            "message": message or f"Status updated to {new_status}",
            "updated_by": updated_by
        }
        
        # Update fields based on status
        update_data = {
            "delivery_status": new_status,
            "updated_at": datetime.utcnow(),
            "$push": {"tracking_updates": status_update}
        }
        
        # Set specific timestamps based on status
        if new_status == DeliveryStatus.PICKED_UP:
            update_data["actual_pickup_time"] = datetime.utcnow()
        elif new_status == DeliveryStatus.DELIVERED:
            update_data["actual_delivery_time"] = datetime.utcnow()
            if proof_data:
                update_data["delivery_proof"] = proof_data
        
        # Update database
        await self.db.delivery_tracking.update_one(
            {"tracking_id": tracking_id},
            update_data
        )
        
        # Get updated record
        updated_data = await self.db.delivery_tracking.find_one(
            {"tracking_id": tracking_id}
        )
        
        return DeliveryTracking(**updated_data)
    
    async def get_delivery_tracking(
        self,
        tracking_id: str
    ) -> DeliveryTracking:
        """
        Get delivery tracking information.
        
        Args:
            tracking_id: Delivery tracking ID
            
        Returns:
            DeliveryTracking: Delivery tracking information
        """
        if not self.db:
            await self.initialize()
        
        tracking_data = await self.db.delivery_tracking.find_one(
            {"tracking_id": tracking_id}
        )
        
        if not tracking_data:
            raise HTTPException(status_code=404, detail="Delivery tracking not found")
        
        return DeliveryTracking(**tracking_data)
    
    async def get_transaction_delivery_status(
        self,
        transaction_id: str
    ) -> Optional[DeliveryTracking]:
        """
        Get delivery status for a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Optional[DeliveryTracking]: Delivery tracking if exists
        """
        if not self.db:
            await self.initialize()
        
        tracking_data = await self.db.delivery_tracking.find_one(
            {"transaction_id": transaction_id}
        )
        
        if not tracking_data:
            return None
        
        return DeliveryTracking(**tracking_data)
    
    async def create_transaction_record(
        self,
        transaction_id: str,
        item_details: List[Dict],
        tax_breakdown: Optional[Dict[str, Decimal]] = None,
        discount_details: Optional[Dict[str, Decimal]] = None,
        gstin_buyer: Optional[str] = None,
        gstin_vendor: Optional[str] = None
    ) -> TransactionRecord:
        """
        Create comprehensive transaction record for accounting purposes.
        
        Args:
            transaction_id: Associated transaction ID
            item_details: Detailed item information
            tax_breakdown: Tax breakdown by type
            discount_details: Discount breakdown
            gstin_buyer: Buyer's GSTIN
            gstin_vendor: Vendor's GSTIN
            
        Returns:
            TransactionRecord: Created transaction record
        """
        if not self.db:
            await self.initialize()
        
        # Get transaction details
        transaction_data = await self.db.payment_transactions.find_one(
            {"transaction_id": transaction_id}
        )
        
        if not transaction_data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        transaction = PaymentTransaction(**transaction_data)
        
        # Generate record ID
        record_id = f"REC_{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate amounts
        gross_amount = transaction.amount
        total_tax = sum(tax_breakdown.values()) if tax_breakdown else Decimal('0')
        total_discount = sum(discount_details.values()) if discount_details else Decimal('0')
        net_amount = gross_amount + total_tax - total_discount
        
        # Determine accounting period
        now = datetime.utcnow()
        accounting_period = now.strftime("%Y-%m")
        
        # Determine financial year (April to March in India)
        if now.month >= 4:
            financial_year = f"{now.year}-{now.year + 1}"
        else:
            financial_year = f"{now.year - 1}-{now.year}"
        
        # Extract HSN/SAC codes from item details
        hsn_sac_codes = []
        for item in item_details:
            if "hsn_code" in item:
                hsn_sac_codes.append(item["hsn_code"])
            elif "sac_code" in item:
                hsn_sac_codes.append(item["sac_code"])
        
        # Create transaction record
        record = TransactionRecord(
            record_id=record_id,
            transaction_id=transaction_id,
            gross_amount=gross_amount,
            tax_breakdown=tax_breakdown or {},
            discount_details=discount_details or {},
            net_amount=net_amount,
            accounting_period=accounting_period,
            financial_year=financial_year,
            gstin_buyer=gstin_buyer,
            gstin_vendor=gstin_vendor,
            item_details=item_details,
            hsn_sac_codes=hsn_sac_codes,
            tds_applicable=self._is_tds_applicable(gross_amount, gstin_buyer, gstin_vendor),
            tcs_applicable=self._is_tcs_applicable(item_details),
            reverse_charge=self._is_reverse_charge_applicable(gstin_buyer, gstin_vendor)
        )
        
        # Store in database
        await self.db.transaction_records.insert_one(record.dict())
        
        return record
    
    async def get_transaction_records(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        accounting_period: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TransactionRecord]:
        """
        Get transaction records for a user with filtering options.
        
        Args:
            user_id: User ID
            start_date: Start date filter
            end_date: End date filter
            accounting_period: Accounting period filter (YYYY-MM)
            limit: Maximum records to return
            offset: Number of records to skip
            
        Returns:
            List[TransactionRecord]: Filtered transaction records
        """
        if not self.db:
            await self.initialize()
        
        # Get user's transaction IDs
        transaction_cursor = self.db.payment_transactions.find(
            {
                "$or": [
                    {"buyer_id": user_id},
                    {"vendor_id": user_id}
                ]
            },
            {"transaction_id": 1}
        )
        
        transaction_ids = []
        async for transaction in transaction_cursor:
            transaction_ids.append(transaction["transaction_id"])
        
        if not transaction_ids:
            return []
        
        # Build filter query
        filter_query = {"transaction_id": {"$in": transaction_ids}}
        
        if accounting_period:
            filter_query["accounting_period"] = accounting_period
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            filter_query["created_at"] = date_filter
        
        # Get records
        cursor = self.db.transaction_records.find(filter_query).sort(
            "created_at", -1
        ).skip(offset).limit(limit)
        
        records = []
        async for record_data in cursor:
            records.append(TransactionRecord(**record_data))
        
        return records
    
    async def generate_delivery_coordination_summary(
        self,
        user_id: str,
        language: str = "en"
    ) -> Dict:
        """
        Generate delivery coordination summary for a user.
        
        Args:
            user_id: User ID
            language: Language for the summary
            
        Returns:
            Dict: Delivery coordination summary
        """
        if not self.db:
            await self.initialize()
        
        # Get user's transactions
        transaction_cursor = self.db.payment_transactions.find(
            {
                "$or": [
                    {"buyer_id": user_id},
                    {"vendor_id": user_id}
                ]
            },
            {"transaction_id": 1, "order_id": 1}
        )
        
        transaction_ids = []
        async for transaction in transaction_cursor:
            transaction_ids.append(transaction["transaction_id"])
        
        if not transaction_ids:
            return {
                "total_deliveries": 0,
                "pending_deliveries": 0,
                "completed_deliveries": 0,
                "failed_deliveries": 0,
                "delivery_methods": {},
                "recent_deliveries": []
            }
        
        # Get delivery tracking records
        delivery_cursor = self.db.delivery_tracking.find(
            {"transaction_id": {"$in": transaction_ids}}
        )
        
        # Analyze delivery data
        total_deliveries = 0
        status_counts = {}
        method_counts = {}
        recent_deliveries = []
        
        async for delivery_data in delivery_cursor:
            delivery = DeliveryTracking(**delivery_data)
            total_deliveries += 1
            
            # Count by status
            status = delivery.delivery_status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by method
            method = delivery.delivery_method
            method_counts[method] = method_counts.get(method, 0) + 1
            
            # Add to recent deliveries
            recent_deliveries.append({
                "tracking_id": delivery.tracking_id,
                "transaction_id": delivery.transaction_id,
                "status": delivery.delivery_status,
                "method": delivery.delivery_method,
                "created_at": delivery.created_at,
                "estimated_delivery": delivery.estimated_delivery_time
            })
        
        # Sort recent deliveries by creation date
        recent_deliveries.sort(key=lambda x: x["created_at"], reverse=True)
        recent_deliveries = recent_deliveries[:10]  # Keep only 10 most recent
        
        # Translate status labels if needed
        if language != "en" and self.translation_service:
            # This would translate status labels to the requested language
            pass
        
        return {
            "total_deliveries": total_deliveries,
            "pending_deliveries": status_counts.get(DeliveryStatus.PENDING, 0),
            "completed_deliveries": status_counts.get(DeliveryStatus.DELIVERED, 0),
            "failed_deliveries": status_counts.get(DeliveryStatus.FAILED, 0),
            "delivery_methods": method_counts,
            "status_breakdown": status_counts,
            "recent_deliveries": recent_deliveries
        }
    
    def _calculate_estimated_delivery_time(
        self,
        delivery_method: DeliveryMethod,
        pickup_address: DeliveryAddress,
        delivery_address: DeliveryAddress
    ) -> datetime:
        """Calculate estimated delivery time based on method and addresses."""
        base_time = datetime.utcnow()
        
        # Simple estimation logic - in production this would be more sophisticated
        if delivery_method == DeliveryMethod.SELF_PICKUP:
            # Same day pickup
            return base_time + timedelta(hours=4)
        elif delivery_method == DeliveryMethod.VENDOR_DELIVERY:
            # Next day delivery for local, 2-3 days for distant
            if pickup_address.city.lower() == delivery_address.city.lower():
                return base_time + timedelta(days=1)
            else:
                return base_time + timedelta(days=2)
        elif delivery_method == DeliveryMethod.THIRD_PARTY_COURIER:
            # 2-5 days depending on distance
            if pickup_address.state.lower() == delivery_address.state.lower():
                return base_time + timedelta(days=2)
            else:
                return base_time + timedelta(days=4)
        else:  # LOCAL_TRANSPORT
            # Same day or next day
            return base_time + timedelta(hours=8)
    
    def _is_tds_applicable(
        self,
        amount: Decimal,
        gstin_buyer: Optional[str],
        gstin_vendor: Optional[str]
    ) -> bool:
        """Determine if TDS is applicable based on amount and GSTIN."""
        # Simplified logic - in production this would follow actual TDS rules
        return amount > Decimal('50000') and gstin_buyer is not None
    
    def _is_tcs_applicable(self, item_details: List[Dict]) -> bool:
        """Determine if TCS is applicable based on item details."""
        # Simplified logic - in production this would check specific item categories
        for item in item_details:
            if item.get("category") in ["scrap", "minerals", "forest_produce"]:
                return True
        return False
    
    def _is_reverse_charge_applicable(
        self,
        gstin_buyer: Optional[str],
        gstin_vendor: Optional[str]
    ) -> bool:
        """Determine if reverse charge mechanism applies."""
        # Simplified logic - in production this would follow GST rules
        return gstin_buyer is not None and gstin_vendor is None
    
    async def _get_translation_service(self):
        """Get translation service, initializing if needed."""
        if self.translation_service is None:
            from app.db.redis import get_redis
            redis = await get_redis()
            from app.services.translation_service import TranslationService
            self.translation_service = TranslationService(self.db, redis)
        return self.translation_service