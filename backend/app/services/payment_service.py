"""
Payment service for the Multilingual Mandi platform.
Handles UPI, digital wallet, and card payment processing with multilingual support.
"""

import asyncio
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.db.mongodb import get_database
from app.models.payment import (
    CardDetails,
    CreditTerms,
    CreditTermsStatus,
    DigitalWalletDetails,
    EscrowReleaseCondition,
    EscrowStatus,
    EscrowTransaction,
    Invoice,
    PaymentDetails,
    PaymentGatewayConfig,
    PaymentMethod,
    PaymentMethodValidation,
    PaymentReminder,
    PaymentReminderType,
    PaymentStatus,
    PaymentTransaction,
    RefundReason,
    RefundRequest,
    TransactionType,
    UPIDetails
)
from app.services.translation_service import TranslationService


class PaymentService:
    """Service for handling payment processing and management."""
    
    def __init__(self):
        self.db = None
        self.translation_service = None
        self.supported_gateways = {
            "razorpay": {
                "upi": True,
                "cards": True,
                "wallets": ["paytm", "phonepe", "google_pay"],
                "api_endpoint": "https://api.razorpay.com/v1"
            },
            "payu": {
                "upi": True,
                "cards": True,
                "wallets": ["paytm", "mobikwik", "freecharge"],
                "api_endpoint": "https://secure.payu.in/_payment"
            },
            "cashfree": {
                "upi": True,
                "cards": True,
                "wallets": ["phonepe", "amazon_pay"],
                "api_endpoint": "https://api.cashfree.com/pg"
            }
        }
    
    async def initialize(self):
        """Initialize the payment service with database connection."""
        self.db = await get_database()
        # Only initialize translation service if needed for invoice generation
        # For basic payment operations, we don't need it
    
    async def validate_payment_method(
        self, 
        payment_details: PaymentDetails
    ) -> PaymentMethodValidation:
        """
        Validate payment method details and check availability.
        
        Args:
            payment_details: Payment method details to validate
            
        Returns:
            PaymentMethodValidation: Validation result with errors if any
        """
        validation_errors = []
        supported_features = []
        
        try:
            if payment_details.method == PaymentMethod.UPI:
                if not payment_details.upi_details:
                    validation_errors.append("UPI details are required")
                else:
                    # Validate UPI ID format
                    upi_id = payment_details.upi_details.upi_id
                    if '@' not in upi_id or len(upi_id.split('@')) != 2:
                        validation_errors.append("Invalid UPI ID format")
                    
                    # Check if UPI ID domain is supported
                    domain = upi_id.split('@')[1]
                    supported_domains = ['paytm', 'phonepe', 'googlepay', 'amazonpay', 'ybl', 'okhdfcbank', 'okicici', 'okaxis']
                    if domain not in supported_domains:
                        validation_errors.append(f"UPI domain {domain} may not be supported")
                    
                    supported_features = ["instant_transfer", "qr_code", "collect_request"]
            
            elif payment_details.method == PaymentMethod.DIGITAL_WALLET:
                if not payment_details.wallet_details:
                    validation_errors.append("Digital wallet details are required")
                else:
                    provider = payment_details.wallet_details.provider
                    if provider not in ["paytm", "phonepe", "google_pay", "amazon_pay", "mobikwik", "freecharge"]:
                        validation_errors.append(f"Unsupported wallet provider: {provider}")
                    
                    supported_features = ["instant_transfer", "cashback", "loyalty_points"]
            
            elif payment_details.method == PaymentMethod.CARD:
                if not payment_details.card_details:
                    validation_errors.append("Card details are required")
                else:
                    # Validate card network
                    network = payment_details.card_details.card_network.lower()
                    supported_networks = ['visa', 'mastercard', 'rupay', 'amex', 'diners']
                    if network not in supported_networks:
                        validation_errors.append(f"Unsupported card network: {network}")
                    
                    supported_features = ["emi", "international", "contactless"]
            
            elif payment_details.method == PaymentMethod.BANK_TRANSFER:
                if not payment_details.bank_details:
                    validation_errors.append("Bank transfer details are required")
                else:
                    # Validate IFSC code format
                    ifsc = payment_details.bank_details.ifsc_code
                    if len(ifsc) != 11 or not ifsc[:4].isalpha() or not ifsc[4].isdigit():
                        validation_errors.append("Invalid IFSC code format")
                    
                    supported_features = ["neft", "rtgs", "imps"]
            
            is_valid = len(validation_errors) == 0
            
            return PaymentMethodValidation(
                is_valid=is_valid,
                method=payment_details.method,
                validation_errors=validation_errors,
                supported_features=supported_features
            )
            
        except Exception as e:
            return PaymentMethodValidation(
                is_valid=False,
                method=payment_details.method,
                validation_errors=[f"Validation error: {str(e)}"],
                supported_features=[]
            )
    
    async def create_payment_transaction(
        self,
        order_id: str,
        buyer_id: str,
        vendor_id: str,
        amount: Decimal,
        payment_details: PaymentDetails,
        description: Optional[Dict[str, str]] = None,
        is_escrow: bool = False
    ) -> PaymentTransaction:
        """
        Create a new payment transaction.
        
        Args:
            order_id: Order identifier
            buyer_id: Buyer user ID
            vendor_id: Vendor user ID
            amount: Transaction amount
            payment_details: Payment method details
            description: Multilingual transaction description
            is_escrow: Whether this is an escrow transaction
            
        Returns:
            PaymentTransaction: Created transaction
        """
        if not self.db:
            await self.initialize()
        
        # Validate payment method
        validation = await self.validate_payment_method(payment_details)
        if not validation.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid payment method: {', '.join(validation.validation_errors)}"
            )
        
        # Generate transaction ID
        transaction_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        
        # Create transaction
        transaction = PaymentTransaction(
            transaction_id=transaction_id,
            order_id=order_id,
            buyer_id=buyer_id,
            vendor_id=vendor_id,
            amount=amount,
            payment_details=payment_details,
            description=description or {},
            is_escrow=is_escrow,
            status_history=[{
                "status": PaymentStatus.PENDING,
                "timestamp": datetime.utcnow(),
                "note": "Transaction created"
            }]
        )
        
        # Store in database
        await self.db.payment_transactions.insert_one(transaction.dict())
        
        return transaction
    
    async def process_upi_payment(
        self,
        transaction: PaymentTransaction
    ) -> Tuple[bool, Dict]:
        """
        Process UPI payment through payment gateway.
        
        Args:
            transaction: Payment transaction to process
            
        Returns:
            Tuple[bool, Dict]: Success status and gateway response
        """
        try:
            upi_details = transaction.payment_details.upi_details
            if not upi_details:
                raise ValueError("UPI details not found")
            
            # Simulate UPI payment processing
            # In production, this would integrate with actual payment gateways
            gateway_response = {
                "gateway": "razorpay",
                "method": "upi",
                "upi_id": upi_details.upi_id,
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "status": "success",
                "gateway_transaction_id": f"pay_{uuid.uuid4().hex[:16]}",
                "transaction_ref": f"upi_{uuid.uuid4().hex[:12]}",
                "processed_at": datetime.utcnow().isoformat()
            }
            
            # Update transaction with gateway response
            await self._update_transaction_status(
                transaction.transaction_id,
                PaymentStatus.COMPLETED,
                gateway_response,
                "UPI payment completed successfully"
            )
            
            return True, gateway_response
            
        except Exception as e:
            # Handle payment failure
            error_response = {
                "error": str(e),
                "status": "failed",
                "processed_at": datetime.utcnow().isoformat()
            }
            
            await self._update_transaction_status(
                transaction.transaction_id,
                PaymentStatus.FAILED,
                error_response,
                f"UPI payment failed: {str(e)}"
            )
            
            return False, error_response
    
    async def process_wallet_payment(
        self,
        transaction: PaymentTransaction
    ) -> Tuple[bool, Dict]:
        """
        Process digital wallet payment.
        
        Args:
            transaction: Payment transaction to process
            
        Returns:
            Tuple[bool, Dict]: Success status and gateway response
        """
        try:
            wallet_details = transaction.payment_details.wallet_details
            if not wallet_details:
                raise ValueError("Wallet details not found")
            
            # Simulate wallet payment processing
            gateway_response = {
                "gateway": "payu",
                "method": "wallet",
                "provider": wallet_details.provider,
                "wallet_id": wallet_details.wallet_id,
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "status": "success",
                "gateway_transaction_id": f"wallet_{uuid.uuid4().hex[:16]}",
                "transaction_ref": f"{wallet_details.provider}_{uuid.uuid4().hex[:12]}",
                "processed_at": datetime.utcnow().isoformat()
            }
            
            await self._update_transaction_status(
                transaction.transaction_id,
                PaymentStatus.COMPLETED,
                gateway_response,
                f"{wallet_details.provider.title()} payment completed successfully"
            )
            
            return True, gateway_response
            
        except Exception as e:
            error_response = {
                "error": str(e),
                "status": "failed",
                "processed_at": datetime.utcnow().isoformat()
            }
            
            await self._update_transaction_status(
                transaction.transaction_id,
                PaymentStatus.FAILED,
                error_response,
                f"Wallet payment failed: {str(e)}"
            )
            
            return False, error_response
    
    async def process_card_payment(
        self,
        transaction: PaymentTransaction
    ) -> Tuple[bool, Dict]:
        """
        Process card payment.
        
        Args:
            transaction: Payment transaction to process
            
        Returns:
            Tuple[bool, Dict]: Success status and gateway response
        """
        try:
            card_details = transaction.payment_details.card_details
            if not card_details:
                raise ValueError("Card details not found")
            
            # Simulate card payment processing
            gateway_response = {
                "gateway": "cashfree",
                "method": "card",
                "card_type": card_details.card_type,
                "card_network": card_details.card_network,
                "last_four": card_details.last_four_digits,
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "status": "success",
                "gateway_transaction_id": f"card_{uuid.uuid4().hex[:16]}",
                "transaction_ref": f"card_{uuid.uuid4().hex[:12]}",
                "processed_at": datetime.utcnow().isoformat()
            }
            
            await self._update_transaction_status(
                transaction.transaction_id,
                PaymentStatus.COMPLETED,
                gateway_response,
                f"{card_details.card_network} {card_details.card_type} payment completed successfully"
            )
            
            return True, gateway_response
            
        except Exception as e:
            error_response = {
                "error": str(e),
                "status": "failed",
                "processed_at": datetime.utcnow().isoformat()
            }
            
            await self._update_transaction_status(
                transaction.transaction_id,
                PaymentStatus.FAILED,
                error_response,
                f"Card payment failed: {str(e)}"
            )
            
            return False, error_response
    
    async def process_payment(
        self,
        transaction_id: str
    ) -> Tuple[bool, Dict]:
        """
        Process payment based on the payment method.
        
        Args:
            transaction_id: Transaction ID to process
            
        Returns:
            Tuple[bool, Dict]: Success status and processing result
        """
        if not self.db:
            await self.initialize()
        
        # Get transaction
        transaction_data = await self.db.payment_transactions.find_one(
            {"transaction_id": transaction_id}
        )
        
        if not transaction_data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        transaction = PaymentTransaction(**transaction_data)
        
        # Check if already processed
        if transaction.status in [PaymentStatus.COMPLETED, PaymentStatus.FAILED]:
            return transaction.status == PaymentStatus.COMPLETED, transaction.gateway_response or {}
        
        # Update status to processing
        await self._update_transaction_status(
            transaction_id,
            PaymentStatus.PROCESSING,
            {},
            "Payment processing started"
        )
        
        # Process based on payment method
        method = transaction.payment_details.method
        
        if method == PaymentMethod.UPI:
            return await self.process_upi_payment(transaction)
        elif method == PaymentMethod.DIGITAL_WALLET:
            return await self.process_wallet_payment(transaction)
        elif method == PaymentMethod.CARD:
            return await self.process_card_payment(transaction)
        else:
            # For other methods like bank transfer, COD
            await self._update_transaction_status(
                transaction_id,
                PaymentStatus.PENDING,
                {"method": method},
                f"Payment method {method} requires manual processing"
            )
            return True, {"status": "pending", "method": method}
    
    async def generate_multilingual_invoice(
        self,
        transaction_id: str,
        buyer_language: str = "en",
        vendor_language: str = "en",
        include_delivery_info: bool = True
    ) -> Invoice:
        """
        Generate multilingual invoice for a completed transaction.
        
        Args:
            transaction_id: Transaction ID
            buyer_language: Buyer's preferred language
            vendor_language: Vendor's preferred language
            include_delivery_info: Whether to include delivery information
            
        Returns:
            Invoice: Generated multilingual invoice
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
        
        # Get buyer and vendor information
        buyer_info = await self._get_user_info(transaction.buyer_id)
        vendor_info = await self._get_user_info(transaction.vendor_id)
        
        # Get delivery information if requested
        delivery_info = None
        if include_delivery_info:
            delivery_data = await self.db.delivery_tracking.find_one(
                {"transaction_id": transaction_id}
            )
            if delivery_data:
                from app.models.payment import DeliveryTracking
                delivery_info = DeliveryTracking(**delivery_data)
        
        # Generate invoice ID
        invoice_id = f"INV_{uuid.uuid4().hex[:12].upper()}"
        
        # Create base invoice content in English
        base_content = {
            "title": "Invoice",
            "invoice_number": invoice_id,
            "transaction_details": {
                "transaction_id": transaction.transaction_id,
                "order_id": transaction.order_id,
                "payment_method": transaction.payment_details.method,
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "status": transaction.status,
                "payment_date": transaction.completed_at.isoformat() if transaction.completed_at else None
            },
            "buyer_section": "Buyer Information",
            "vendor_section": "Vendor Information", 
            "payment_section": "Payment Details",
            "delivery_section": "Delivery Information" if delivery_info else None,
            "footer": "Thank you for your business!",
            "terms_conditions": "Terms and conditions apply as per the platform agreement."
        }
        
        # Add delivery information to content if available
        if delivery_info:
            base_content["delivery_details"] = {
                "tracking_id": delivery_info.tracking_id,
                "delivery_method": delivery_info.delivery_method,
                "delivery_status": delivery_info.delivery_status,
                "pickup_address": delivery_info.pickup_address.dict(),
                "delivery_address": delivery_info.delivery_address.dict(),
                "estimated_delivery": delivery_info.estimated_delivery_time.isoformat() if delivery_info.estimated_delivery_time else None,
                "actual_delivery": delivery_info.actual_delivery_time.isoformat() if delivery_info.actual_delivery_time else None
            }
        
        # Translate content to required languages
        languages = list(set([buyer_language, vendor_language, "en"]))
        invoice_content = {}
        
        translation_service = await self._get_translation_service()
        
        for lang in languages:
            if lang == "en":
                invoice_content[lang] = base_content
            else:
                # Translate each section
                translated_content = {}
                for key, value in base_content.items():
                    if isinstance(value, str):
                        translated_value = await translation_service.translate_text(
                            value, "en", lang
                        )
                        translated_content[key] = translated_value.translated_text
                    else:
                        translated_content[key] = value
                
                invoice_content[lang] = translated_content
        
        # Calculate amounts
        subtotal = transaction.amount
        tax_amount = Decimal('0')  # Can be calculated based on business rules
        total_amount = subtotal + tax_amount
        
        # Create invoice
        invoice = Invoice(
            invoice_id=invoice_id,
            transaction_id=transaction_id,
            order_id=transaction.order_id,
            buyer_info=buyer_info,
            vendor_info=vendor_info,
            invoice_content=invoice_content,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            currency=transaction.currency,
            is_paid=transaction.status == PaymentStatus.COMPLETED,
            paid_at=transaction.completed_at
        )
        
        # Store invoice in database
        await self.db.invoices.insert_one(invoice.dict())
        
        return invoice
    
    async def create_escrow_transaction(
        self,
        transaction_id: str,
        release_conditions: Dict,
        milestone_conditions: Optional[List[Dict]] = None,
        auto_release_days: int = 7,
        escrow_fee_percentage: Decimal = Decimal('1.0')
    ) -> EscrowTransaction:
        """
        Create escrow transaction for high-value payments.
        
        Args:
            transaction_id: Associated payment transaction ID
            release_conditions: Conditions for fund release
            milestone_conditions: Optional milestone-based release conditions
            auto_release_days: Days after which funds are automatically released
            escrow_fee_percentage: Escrow service fee as percentage of amount
            
        Returns:
            EscrowTransaction: Created escrow transaction
        """
        if not self.db:
            await self.initialize()
        
        # Get payment transaction
        transaction_data = await self.db.payment_transactions.find_one(
            {"transaction_id": transaction_id}
        )
        
        if not transaction_data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        transaction = PaymentTransaction(**transaction_data)
        
        # Validate transaction is eligible for escrow
        if transaction.amount < Decimal('10000'):  # Minimum amount for escrow
            raise HTTPException(
                status_code=400, 
                detail="Transaction amount too low for escrow service"
            )
        
        if transaction.status != PaymentStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Transaction must be completed before creating escrow"
            )
        
        # Calculate escrow fee
        escrow_fee = (transaction.amount * escrow_fee_percentage) / Decimal('100')
        
        # Create escrow transaction
        escrow_id = f"ESC_{uuid.uuid4().hex[:12].upper()}"
        auto_release_date = datetime.utcnow() + timedelta(days=auto_release_days)
        
        escrow = EscrowTransaction(
            escrow_id=escrow_id,
            transaction_id=transaction_id,
            buyer_id=transaction.buyer_id,
            vendor_id=transaction.vendor_id,
            amount=transaction.amount,
            currency=transaction.currency,
            release_conditions=release_conditions,
            milestone_conditions=milestone_conditions,
            remaining_amount=transaction.amount,
            auto_release_date=auto_release_date,
            escrow_fee=escrow_fee,
            fee_paid_by="buyer"  # Default: buyer pays escrow fee
        )
        
        # Store escrow transaction
        await self.db.escrow_transactions.insert_one(escrow.dict())
        
        # Update payment transaction to mark as escrow
        await self.db.payment_transactions.update_one(
            {"transaction_id": transaction_id},
            {
                "$set": {
                    "is_escrow": True,
                    "escrow_release_conditions": release_conditions,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return escrow
    
    async def release_escrow_funds(
        self,
        escrow_id: str,
        release_amount: Optional[Decimal] = None,
        release_reason: str = "conditions_met",
        released_by: str = "system"
    ) -> Dict:
        """
        Release funds from escrow account.
        
        Args:
            escrow_id: Escrow transaction ID
            release_amount: Amount to release (None for full amount)
            release_reason: Reason for fund release
            released_by: Who authorized the release
            
        Returns:
            Dict: Release operation result
        """
        if not self.db:
            await self.initialize()
        
        # Get escrow transaction
        escrow_data = await self.db.escrow_transactions.find_one(
            {"escrow_id": escrow_id}
        )
        
        if not escrow_data:
            raise HTTPException(status_code=404, detail="Escrow transaction not found")
        
        escrow = EscrowTransaction(**escrow_data)
        
        # Validate escrow status
        if escrow.status not in [EscrowStatus.ACTIVE, EscrowStatus.PARTIALLY_RELEASED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot release funds from escrow with status: {escrow.status}"
            )
        
        # Determine release amount
        if release_amount is None:
            release_amount = escrow.remaining_amount
        elif release_amount > escrow.remaining_amount:
            raise HTTPException(
                status_code=400,
                detail="Release amount exceeds remaining escrow balance"
            )
        
        # Create release record
        release_record = {
            "release_id": f"REL_{uuid.uuid4().hex[:8].upper()}",
            "amount": release_amount,
            "reason": release_reason,
            "released_by": released_by,
            "released_at": datetime.utcnow(),
            "transaction_ref": f"escrow_release_{uuid.uuid4().hex[:12]}"
        }
        
        # Update escrow transaction
        new_released_amount = escrow.released_amount + release_amount
        new_remaining_amount = escrow.remaining_amount - release_amount
        
        # Determine new status
        if new_remaining_amount == Decimal('0'):
            new_status = EscrowStatus.RELEASED
        else:
            new_status = EscrowStatus.PARTIALLY_RELEASED
        
        # Update database
        await self.db.escrow_transactions.update_one(
            {"escrow_id": escrow_id},
            {
                "$set": {
                    "released_amount": new_released_amount,
                    "remaining_amount": new_remaining_amount,
                    "status": new_status,
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "release_history": release_record
                }
            }
        )
        
        # Process actual fund transfer (simulate)
        transfer_result = await self._process_escrow_release_transfer(
            escrow.vendor_id,
            release_amount,
            escrow.currency,
            release_record["transaction_ref"]
        )
        
        return {
            "success": True,
            "release_id": release_record["release_id"],
            "amount_released": float(release_amount),
            "remaining_amount": float(new_remaining_amount),
            "status": new_status,
            "transfer_result": transfer_result
        }
    
    async def create_credit_terms(
        self,
        transaction_id: str,
        credit_period_days: int,
        installment_count: int,
        interest_rate: Optional[Decimal] = None,
        late_fee_rate: Optional[Decimal] = None
    ) -> CreditTerms:
        """
        Create credit terms and payment scheduling for established trading relationships.
        
        Args:
            transaction_id: Associated transaction ID
            credit_period_days: Credit period in days
            installment_count: Number of installments
            interest_rate: Interest rate percentage (optional)
            late_fee_rate: Late payment fee rate percentage (optional)
            
        Returns:
            CreditTerms: Created credit terms
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
        
        # Validate trading relationship eligibility
        relationship_months = await self._get_trading_relationship_duration(
            transaction.buyer_id, 
            transaction.vendor_id
        )
        
        if relationship_months < 3:  # Minimum 3 months trading history
            raise HTTPException(
                status_code=400,
                detail="Insufficient trading history for credit terms"
            )
        
        # Get previous credit score
        credit_score = await self._calculate_credit_score(transaction.buyer_id)
        
        if credit_score < 0.7:  # Minimum credit score of 70%
            raise HTTPException(
                status_code=400,
                detail="Credit score too low for credit terms"
            )
        
        # Generate payment schedule
        payment_schedule = self._generate_payment_schedule(
            transaction.amount,
            installment_count,
            credit_period_days,
            interest_rate
        )
        
        # Create credit terms
        credit_id = f"CRD_{uuid.uuid4().hex[:12].upper()}"
        
        credit_terms = CreditTerms(
            credit_id=credit_id,
            transaction_id=transaction_id,
            buyer_id=transaction.buyer_id,
            vendor_id=transaction.vendor_id,
            total_amount=transaction.amount,
            currency=transaction.currency,
            payment_schedule=payment_schedule,
            installment_count=installment_count,
            credit_period_days=credit_period_days,
            interest_rate=interest_rate,
            late_fee_rate=late_fee_rate,
            remaining_amount=transaction.amount,
            next_payment_date=payment_schedule[0]["due_date"] if payment_schedule else None,
            trading_relationship_months=relationship_months,
            previous_credit_score=credit_score
        )
        
        # Store credit terms
        await self.db.credit_terms.insert_one(credit_terms.dict())
        
        # Update transaction to mark as credit
        await self.db.payment_transactions.update_one(
            {"transaction_id": transaction_id},
            {
                "$set": {
                    "transaction_type": TransactionType.PURCHASE,
                    "credit_terms_id": credit_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Schedule payment reminders
        await self._schedule_payment_reminders(credit_terms)
        
        return credit_terms
    
    async def process_credit_payment(
        self,
        credit_id: str,
        payment_amount: Decimal,
        payment_method: PaymentDetails
    ) -> Dict:
        """
        Process a credit payment installment.
        
        Args:
            credit_id: Credit terms ID
            payment_amount: Amount being paid
            payment_method: Payment method details
            
        Returns:
            Dict: Payment processing result
        """
        if not self.db:
            await self.initialize()
        
        # Get credit terms
        credit_data = await self.db.credit_terms.find_one(
            {"credit_id": credit_id}
        )
        
        if not credit_data:
            raise HTTPException(status_code=404, detail="Credit terms not found")
        
        credit_terms = CreditTerms(**credit_data)
        
        # Validate payment amount
        if payment_amount > credit_terms.remaining_amount:
            raise HTTPException(
                status_code=400,
                detail="Payment amount exceeds remaining balance"
            )
        
        # Create payment transaction for this installment
        installment_transaction = await self.create_payment_transaction(
            order_id=f"{credit_terms.transaction_id}_installment_{len(credit_terms.payment_history) + 1}",
            buyer_id=credit_terms.buyer_id,
            vendor_id=credit_terms.vendor_id,
            amount=payment_amount,
            payment_details=payment_method,
            description={"en": f"Credit payment installment for {credit_terms.transaction_id}"}
        )
        
        # Process the payment
        success, gateway_response = await self.process_payment(
            installment_transaction.transaction_id
        )
        
        if success:
            # Update credit terms
            payment_record = {
                "payment_id": f"PAY_{uuid.uuid4().hex[:8].upper()}",
                "amount": payment_amount,
                "payment_date": datetime.utcnow(),
                "transaction_id": installment_transaction.transaction_id,
                "gateway_response": gateway_response
            }
            
            new_paid_amount = credit_terms.paid_amount + payment_amount
            new_remaining_amount = credit_terms.remaining_amount - payment_amount
            
            # Determine new status
            if new_remaining_amount == Decimal('0'):
                new_status = CreditTermsStatus.COMPLETED
                next_payment_date = None
            else:
                new_status = CreditTermsStatus.ACTIVE
                next_payment_date = self._calculate_next_payment_date(
                    credit_terms.payment_schedule,
                    len(credit_terms.payment_history) + 1
                )
            
            # Update database
            await self.db.credit_terms.update_one(
                {"credit_id": credit_id},
                {
                    "$set": {
                        "paid_amount": new_paid_amount,
                        "remaining_amount": new_remaining_amount,
                        "status": new_status,
                        "next_payment_date": next_payment_date,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "payment_history": payment_record
                    }
                }
            )
            
            return {
                "success": True,
                "payment_id": payment_record["payment_id"],
                "amount_paid": float(payment_amount),
                "remaining_amount": float(new_remaining_amount),
                "status": new_status,
                "next_payment_date": next_payment_date.isoformat() if next_payment_date else None
            }
        else:
            return {
                "success": False,
                "error": "Payment processing failed",
                "gateway_response": gateway_response
            }
    
    async def create_payment_reminder(
        self,
        credit_id: str,
        reminder_type: PaymentReminderType,
        days_before_due: int = 3
    ) -> PaymentReminder:
        """
        Create payment reminder for credit terms.
        
        Args:
            credit_id: Credit terms ID
            reminder_type: Type of reminder to send
            days_before_due: Days before due date to send reminder
            
        Returns:
            PaymentReminder: Created reminder
        """
        if not self.db:
            await self.initialize()
        
        # Get credit terms
        credit_data = await self.db.credit_terms.find_one(
            {"credit_id": credit_id}
        )
        
        if not credit_data:
            raise HTTPException(status_code=404, detail="Credit terms not found")
        
        credit_terms = CreditTerms(**credit_data)
        
        if not credit_terms.next_payment_date:
            raise HTTPException(
                status_code=400,
                detail="No upcoming payment date for reminder"
            )
        
        # Calculate reminder schedule
        scheduled_at = credit_terms.next_payment_date - timedelta(days=days_before_due)
        days_until_due = (credit_terms.next_payment_date - datetime.utcnow()).days
        
        # Get next payment amount
        next_payment_amount = self._get_next_payment_amount(
            credit_terms.payment_schedule,
            len(credit_terms.payment_history)
        )
        
        # Generate multilingual reminder message
        message_content = await self._generate_reminder_message(
            credit_terms.buyer_id,
            next_payment_amount,
            credit_terms.next_payment_date,
            reminder_type
        )
        
        # Create reminder
        reminder_id = f"REM_{uuid.uuid4().hex[:12].upper()}"
        
        reminder = PaymentReminder(
            reminder_id=reminder_id,
            credit_id=credit_id,
            transaction_id=credit_terms.transaction_id,
            recipient_id=credit_terms.buyer_id,
            reminder_type=reminder_type,
            due_amount=next_payment_amount,
            due_date=credit_terms.next_payment_date,
            days_until_due=days_until_due,
            message_content=message_content,
            scheduled_at=scheduled_at
        )
        
        # Store reminder
        await self.db.payment_reminders.insert_one(reminder.dict())
        
        return reminder
    
    async def create_refund_request(
        self,
        transaction_id: str,
        requester_id: str,
        refund_amount: Decimal,
        refund_reason: RefundReason,
        description: Dict[str, str],
        supporting_documents: Optional[List[str]] = None
    ) -> RefundRequest:
        """
        Create refund request with return policy enforcement.
        
        Args:
            transaction_id: Associated transaction ID
            requester_id: User requesting refund
            refund_amount: Requested refund amount
            refund_reason: Reason for refund
            description: Multilingual description
            supporting_documents: Supporting document URLs
            
        Returns:
            RefundRequest: Created refund request
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
        
        # Validate requester authorization
        if requester_id not in [transaction.buyer_id, transaction.vendor_id]:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to request refund for this transaction"
            )
        
        requester_type = "buyer" if requester_id == transaction.buyer_id else "vendor"
        
        # Validate refund amount
        if refund_amount > transaction.amount:
            raise HTTPException(
                status_code=400,
                detail="Refund amount cannot exceed transaction amount"
            )
        
        # Check return policy compliance
        policy_compliance = await self._check_return_policy_compliance(
            transaction,
            refund_reason,
            refund_amount
        )
        
        # Create refund request
        refund_id = f"REF_{uuid.uuid4().hex[:12].upper()}"
        
        refund_request = RefundRequest(
            refund_id=refund_id,
            transaction_id=transaction_id,
            requester_id=requester_id,
            requester_type=requester_type,
            refund_amount=refund_amount,
            currency=transaction.currency,
            refund_reason=refund_reason,
            description=description,
            supporting_documents=supporting_documents or [],
            return_policy_compliant=policy_compliance["compliant"],
            policy_violations=policy_compliance["violations"]
        )
        
        # Store refund request
        await self.db.refund_requests.insert_one(refund_request.dict())
        
        # Auto-approve if policy compliant and meets criteria
        if policy_compliance["compliant"] and await self._should_auto_approve_refund(refund_request):
            await self._process_refund_approval(refund_id, True, "Auto-approved based on policy compliance")
        
        return refund_request
    
    async def get_supported_payment_methods(self) -> List[Dict]:
        """
        Get list of supported payment methods with their features.
        
        Returns:
            List[Dict]: Supported payment methods and features
        """
        return [
            {
                "method": PaymentMethod.UPI,
                "name": "UPI",
                "description": "Unified Payments Interface",
                "features": ["instant_transfer", "qr_code", "collect_request"],
                "supported_providers": ["paytm", "phonepe", "googlepay", "amazonpay", "ybl"]
            },
            {
                "method": PaymentMethod.DIGITAL_WALLET,
                "name": "Digital Wallet",
                "description": "Digital wallet payments",
                "features": ["instant_transfer", "cashback", "loyalty_points"],
                "supported_providers": ["paytm", "phonepe", "google_pay", "amazon_pay", "mobikwik", "freecharge"]
            },
            {
                "method": PaymentMethod.CARD,
                "name": "Card Payment",
                "description": "Credit/Debit card payments",
                "features": ["emi", "international", "contactless"],
                "supported_networks": ["visa", "mastercard", "rupay", "amex"]
            },
            {
                "method": PaymentMethod.BANK_TRANSFER,
                "name": "Bank Transfer",
                "description": "Direct bank transfer",
                "features": ["neft", "rtgs", "imps"],
                "supported_banks": ["all_major_banks"]
            },
            {
                "method": PaymentMethod.CASH_ON_DELIVERY,
                "name": "Cash on Delivery",
                "description": "Pay when you receive",
                "features": ["no_advance_payment", "inspection_allowed"],
                "supported_areas": ["urban", "semi_urban"]
            }
        ]
    
    async def _update_transaction_status(
        self,
        transaction_id: str,
        status: PaymentStatus,
        gateway_response: Dict,
        note: str
    ):
        """Update transaction status and add to history."""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow(),
            "$push": {
                "status_history": {
                    "status": status,
                    "timestamp": datetime.utcnow(),
                    "note": note
                }
            }
        }
        
        if gateway_response:
            update_data["gateway_response"] = gateway_response
            if "gateway_transaction_id" in gateway_response:
                update_data["gateway_transaction_id"] = gateway_response["gateway_transaction_id"]
        
        if status == PaymentStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow()
        
        await self.db.payment_transactions.update_one(
            {"transaction_id": transaction_id},
            update_data
        )
    
    async def _get_translation_service(self):
        """Get translation service, initializing if needed."""
        if self.translation_service is None:
            from app.db.redis import get_redis
            redis = await get_redis()
            from app.services.translation_service import TranslationService
            self.translation_service = TranslationService(self.db, redis)
        return self.translation_service
    
    async def _process_escrow_release_transfer(
        self,
        vendor_id: str,
        amount: Decimal,
        currency: str,
        transaction_ref: str
    ) -> Dict:
        """Process actual fund transfer for escrow release."""
        # Simulate fund transfer to vendor
        return {
            "transfer_id": f"TRF_{uuid.uuid4().hex[:12].upper()}",
            "vendor_id": vendor_id,
            "amount": float(amount),
            "currency": currency,
            "status": "completed",
            "processed_at": datetime.utcnow().isoformat(),
            "reference": transaction_ref
        }
    
    async def _get_trading_relationship_duration(
        self,
        buyer_id: str,
        vendor_id: str
    ) -> int:
        """Get trading relationship duration in months."""
        # Get first transaction between buyer and vendor
        first_transaction = await self.db.payment_transactions.find_one(
            {
                "$or": [
                    {"buyer_id": buyer_id, "vendor_id": vendor_id},
                    {"buyer_id": vendor_id, "vendor_id": buyer_id}
                ]
            },
            sort=[("created_at", 1)]
        )
        
        if not first_transaction:
            return 0
        
        first_date = first_transaction["created_at"]
        months_diff = (datetime.utcnow() - first_date).days // 30
        return max(months_diff, 0)
    
    async def _calculate_credit_score(self, buyer_id: str) -> float:
        """Calculate credit score based on payment history."""
        # Get all credit terms for this buyer
        credit_history = []
        async for credit_data in self.db.credit_terms.find({"buyer_id": buyer_id}):
            credit_history.append(CreditTerms(**credit_data))
        
        if not credit_history:
            return 0.5  # Default score for new users
        
        total_score = 0
        total_weight = 0
        
        for credit in credit_history:
            # Calculate score based on payment timeliness and completion
            if credit.status == CreditTermsStatus.COMPLETED:
                score = 1.0
            elif credit.status == CreditTermsStatus.ACTIVE:
                score = 0.8
            elif credit.status == CreditTermsStatus.OVERDUE:
                score = 0.4
            else:  # DEFAULTED
                score = 0.1
            
            # Weight by amount and recency
            weight = float(credit.total_amount) * (1.0 / max(1, credit.overdue_days + 1))
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.5
    
    def _generate_payment_schedule(
        self,
        total_amount: Decimal,
        installment_count: int,
        credit_period_days: int,
        interest_rate: Optional[Decimal] = None
    ) -> List[Dict]:
        """Generate payment schedule for credit terms."""
        schedule = []
        
        # Calculate installment amount
        if interest_rate:
            # Simple interest calculation
            interest_amount = (total_amount * interest_rate * credit_period_days) / (Decimal('100') * Decimal('365'))
            total_with_interest = total_amount + interest_amount
        else:
            total_with_interest = total_amount
        
        installment_amount = total_with_interest / installment_count
        
        # Generate schedule
        current_date = datetime.utcnow()
        days_between_payments = credit_period_days // installment_count
        
        for i in range(installment_count):
            due_date = current_date + timedelta(days=(i + 1) * days_between_payments)
            
            # Last installment gets any remainder
            if i == installment_count - 1:
                amount = total_with_interest - (installment_amount * (installment_count - 1))
            else:
                amount = installment_amount
            
            schedule.append({
                "installment_number": i + 1,
                "due_date": due_date,
                "amount": amount,
                "status": "pending"
            })
        
        return schedule
    
    def _calculate_next_payment_date(
        self,
        payment_schedule: List[Dict],
        payments_made: int
    ) -> Optional[datetime]:
        """Calculate next payment due date."""
        if payments_made >= len(payment_schedule):
            return None
        
        next_payment = payment_schedule[payments_made]
        return next_payment["due_date"]
    
    def _get_next_payment_amount(
        self,
        payment_schedule: List[Dict],
        payments_made: int
    ) -> Decimal:
        """Get next payment amount from schedule."""
        if payments_made >= len(payment_schedule):
            return Decimal('0')
        
        next_payment = payment_schedule[payments_made]
        return Decimal(str(next_payment["amount"]))
    
    async def _generate_reminder_message(
        self,
        buyer_id: str,
        amount: Decimal,
        due_date: datetime,
        reminder_type: PaymentReminderType
    ) -> Dict[str, str]:
        """Generate multilingual reminder message."""
        # Get user's preferred language
        user_data = await self.db.users.find_one({"user_id": buyer_id})
        user_language = user_data.get("preferred_language", "en") if user_data else "en"
        
        # Base message in English
        base_message = f"Payment reminder: ₹{amount} due on {due_date.strftime('%Y-%m-%d')}. Please make your payment to avoid late fees."
        
        # For now, return English message
        # In production, this would use the translation service
        return {
            "en": base_message,
            user_language: base_message  # Would be translated in production
        }
    
    async def _schedule_payment_reminders(self, credit_terms: CreditTerms):
        """Schedule automatic payment reminders."""
        # Schedule reminders for each payment in the schedule
        for i, payment in enumerate(credit_terms.payment_schedule):
            due_date = payment["due_date"]
            
            # Schedule reminder 3 days before due date
            reminder_date = due_date - timedelta(days=3)
            
            if reminder_date > datetime.utcnow():
                # Create reminder (would be processed by background job)
                reminder_data = {
                    "credit_id": credit_terms.credit_id,
                    "installment_number": i + 1,
                    "due_date": due_date,
                    "amount": payment["amount"],
                    "scheduled_for": reminder_date,
                    "reminder_type": "sms"  # Default to SMS
                }
                
                # Store in reminders queue (simplified)
                await self.db.reminder_queue.insert_one(reminder_data)
    
    async def _check_return_policy_compliance(
        self,
        transaction: PaymentTransaction,
        refund_reason: RefundReason,
        refund_amount: Decimal
    ) -> Dict:
        """Check if refund request complies with return policy."""
        violations = []
        
        # Check time limits
        days_since_transaction = (datetime.utcnow() - transaction.created_at).days
        
        if refund_reason == RefundReason.BUYER_CANCELLATION:
            if days_since_transaction > 7:  # 7-day return policy
                violations.append("Return period expired (7 days)")
        elif refund_reason == RefundReason.QUALITY_ISSUE:
            if days_since_transaction > 14:  # 14-day quality issue policy
                violations.append("Quality issue reporting period expired (14 days)")
        elif refund_reason == RefundReason.DELIVERY_FAILURE:
            if days_since_transaction > 30:  # 30-day delivery issue policy
                violations.append("Delivery issue reporting period expired (30 days)")
        
        # Check refund amount limits
        if refund_amount > transaction.amount:
            violations.append("Refund amount exceeds transaction amount")
        
        # Check transaction status
        if transaction.status != PaymentStatus.COMPLETED:
            violations.append("Transaction not completed")
        
        # Check if already refunded
        existing_refund = await self.db.refund_requests.find_one({
            "transaction_id": transaction.transaction_id,
            "status": {"$in": ["approved", "processed"]}
        })
        
        if existing_refund:
            violations.append("Transaction already refunded")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }
    
    async def _should_auto_approve_refund(self, refund_request: RefundRequest) -> bool:
        """Determine if refund should be auto-approved."""
        # Auto-approve small amounts with valid reasons
        if (refund_request.refund_amount <= Decimal('1000') and 
            refund_request.refund_reason in [RefundReason.DELIVERY_FAILURE, RefundReason.PRODUCT_DEFECT]):
            return True
        
        # Auto-approve vendor cancellations
        if (refund_request.requester_type == "vendor" and 
            refund_request.refund_reason == RefundReason.VENDOR_CANCELLATION):
            return True
        
        return False
    
    async def _process_refund_approval(
        self,
        refund_id: str,
        approved: bool,
        reason: str
    ):
        """Process refund approval/rejection."""
        update_data = {
            "approved": approved,
            "approval_reason": reason,
            "reviewed_at": datetime.utcnow(),
            "reviewed_by": "system",
            "updated_at": datetime.utcnow()
        }
        
        if approved:
            update_data["status"] = "approved"
            # In production, would trigger actual refund processing
        else:
            update_data["status"] = "rejected"
        
    async def _get_user_info(self, user_id: str) -> Dict[str, str]:
        """Get user information for invoice generation."""
        # This would typically fetch from user database
        # For now, return mock data
        return {
            "user_id": user_id,
            "name": f"User {user_id[:8]}",
            "email": f"user{user_id[:8]}@example.com",
            "phone": "+91-9876543210"
        }