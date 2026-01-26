"""
Payment API endpoints for the Multilingual Mandi platform.
Handles payment processing, method validation, and invoice generation.
"""

from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.payment import (
    CreditTerms,
    EscrowTransaction,
    Invoice,
    PaymentDetails,
    PaymentMethod,
    PaymentMethodValidation,
    PaymentReminder,
    PaymentReminderType,
    PaymentTransaction,
    RefundReason,
    RefundRequest
)
from app.models.user import User
from app.services.payment_service import PaymentService

router = APIRouter()


async def get_payment_service():
    """Get initialized payment service."""
    service = PaymentService()
    await service.initialize()
    return service


class CreatePaymentRequest(BaseModel):
    """Request model for creating a payment transaction."""
    order_id: str
    vendor_id: str
    amount: Decimal
    payment_details: PaymentDetails
    description: Optional[Dict[str, str]] = None
    is_escrow: bool = False


class ProcessPaymentRequest(BaseModel):
    """Request model for processing a payment."""
    transaction_id: str


class CreateEscrowRequest(BaseModel):
    """Request model for creating an escrow transaction."""
    transaction_id: str
    release_conditions: Dict
    milestone_conditions: Optional[List[Dict]] = None
    auto_release_days: int = 7
    escrow_fee_percentage: Decimal = Decimal('1.0')


class ReleaseEscrowRequest(BaseModel):
    """Request model for releasing escrow funds."""
    escrow_id: str
    release_amount: Optional[Decimal] = None
    release_reason: str = "conditions_met"


class CreateCreditTermsRequest(BaseModel):
    """Request model for creating credit terms."""
    transaction_id: str
    credit_period_days: int
    installment_count: int
    interest_rate: Optional[Decimal] = None
    late_fee_rate: Optional[Decimal] = None


class ProcessCreditPaymentRequest(BaseModel):
    """Request model for processing credit payment."""
    credit_id: str
    payment_amount: Decimal
    payment_method: PaymentDetails


class CreateReminderRequest(BaseModel):
    """Request model for creating payment reminder."""
    credit_id: str
    reminder_type: PaymentReminderType
    days_before_due: int = 3


class CreateRefundRequest(BaseModel):
    """Request model for creating refund request."""
    transaction_id: str
    refund_amount: Decimal
    refund_reason: RefundReason
    description: Dict[str, str]
    supporting_documents: Optional[List[str]] = None


class GenerateInvoiceRequest(BaseModel):
    """Request model for generating an invoice."""
    transaction_id: str
    buyer_language: str = "en"
    vendor_language: str = "en"
    include_delivery_info: bool = True


class PaymentResponse(BaseModel):
    """Response model for payment operations."""
    success: bool
    message: str
    data: Optional[Dict] = None


@router.get("/methods", response_model=List[Dict])
async def get_supported_payment_methods(
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Get list of supported payment methods.
    
    Returns:
        List of supported payment methods with their features
    """
    try:
        methods = await payment_service.get_supported_payment_methods()
        return methods
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment methods: {str(e)}"
        )


@router.post("/validate", response_model=PaymentMethodValidation)
async def validate_payment_method(
    payment_details: PaymentDetails,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Validate payment method details.
    
    Args:
        payment_details: Payment method details to validate
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        PaymentMethodValidation: Validation result
    """
    try:
        validation = await payment_service.validate_payment_method(payment_details)
        return validation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment method validation failed: {str(e)}"
        )


@router.post("/create", response_model=PaymentResponse)
async def create_payment_transaction(
    request: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Create a new payment transaction.
    
    Args:
        request: Payment creation request
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        PaymentResponse: Transaction creation result
    """
    try:
        # Ensure the current user is the buyer
        buyer_id = current_user.user_id
        
        transaction = await payment_service.create_payment_transaction(
            order_id=request.order_id,
            buyer_id=buyer_id,
            vendor_id=request.vendor_id,
            amount=request.amount,
            payment_details=request.payment_details,
            description=request.description,
            is_escrow=request.is_escrow
        )
        
        return PaymentResponse(
            success=True,
            message="Payment transaction created successfully",
            data={
                "transaction_id": transaction.transaction_id,
                "status": transaction.status,
                "amount": float(transaction.amount),
                "payment_method": transaction.payment_details.method
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment transaction: {str(e)}"
        )


@router.post("/process", response_model=PaymentResponse)
async def process_payment(
    request: ProcessPaymentRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Process a payment transaction.
    
    Args:
        request: Payment processing request
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        PaymentResponse: Payment processing result
    """
    try:
        success, gateway_response = await payment_service.process_payment(
            request.transaction_id
        )
        
        return PaymentResponse(
            success=success,
            message="Payment processed successfully" if success else "Payment processing failed",
            data=gateway_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process payment: {str(e)}"
        )


@router.get("/transaction/{transaction_id}", response_model=PaymentTransaction)
async def get_payment_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Get payment transaction details.
    
    Args:
        transaction_id: Transaction ID
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        PaymentTransaction: Transaction details
    """
    try:
        transaction_data = await payment_service.db.payment_transactions.find_one(
            {"transaction_id": transaction_id}
        )
        
        if not transaction_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        transaction = PaymentTransaction(**transaction_data)
        
        # Check if user has access to this transaction
        if (current_user.user_id != transaction.buyer_id and 
            current_user.user_id != transaction.vendor_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this transaction"
            )
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transaction: {str(e)}"
        )


@router.post("/invoice/generate", response_model=Invoice)
async def generate_invoice(
    request: GenerateInvoiceRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Generate multilingual invoice for a transaction.
    
    Args:
        request: Invoice generation request
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        Invoice: Generated multilingual invoice
    """
    try:
        invoice = await payment_service.generate_multilingual_invoice(
            transaction_id=request.transaction_id,
            buyer_language=request.buyer_language,
            vendor_language=request.vendor_language,
            include_delivery_info=request.include_delivery_info
        )
        
        return invoice
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate invoice: {str(e)}"
        )


@router.post("/escrow/create", response_model=EscrowTransaction)
async def create_escrow_transaction(
    request: CreateEscrowRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Create escrow transaction for high-value payments.
    
    Args:
        request: Escrow creation request
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        EscrowTransaction: Created escrow transaction
    """
    try:
        escrow = await payment_service.create_escrow_transaction(
            transaction_id=request.transaction_id,
            release_conditions=request.release_conditions,
            milestone_conditions=request.milestone_conditions,
            auto_release_days=request.auto_release_days,
            escrow_fee_percentage=request.escrow_fee_percentage
        )
        
        return escrow
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create escrow transaction: {str(e)}"
        )


@router.post("/escrow/release", response_model=PaymentResponse)
async def release_escrow_funds(
    request: ReleaseEscrowRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Release funds from escrow account.
    
    Args:
        request: Escrow release request
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        PaymentResponse: Release operation result
    """
    try:
        result = await payment_service.release_escrow_funds(
            escrow_id=request.escrow_id,
            release_amount=request.release_amount,
            release_reason=request.release_reason,
            released_by=current_user.user_id
        )
        
        return PaymentResponse(
            success=result["success"],
            message="Escrow funds released successfully" if result["success"] else "Failed to release escrow funds",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to release escrow funds: {str(e)}"
        )


@router.get("/escrow/{escrow_id}", response_model=EscrowTransaction)
async def get_escrow_transaction(
    escrow_id: str,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Get escrow transaction details.
    
    Args:
        escrow_id: Escrow transaction ID
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        EscrowTransaction: Escrow transaction details
    """
    try:
        escrow_data = await payment_service.db.escrow_transactions.find_one(
            {"escrow_id": escrow_id}
        )
        
        if not escrow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Escrow transaction not found"
            )
        
        escrow = EscrowTransaction(**escrow_data)
        
        # Check if user has access to this escrow
        if (current_user.user_id != escrow.buyer_id and 
            current_user.user_id != escrow.vendor_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this escrow transaction"
            )
        
        return escrow
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get escrow transaction: {str(e)}"
        )


@router.post("/credit/create", response_model=CreditTerms)
async def create_credit_terms(
    request: CreateCreditTermsRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Create credit terms and payment scheduling.
    
    Args:
        request: Credit terms creation request
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        CreditTerms: Created credit terms
    """
    try:
        credit_terms = await payment_service.create_credit_terms(
            transaction_id=request.transaction_id,
            credit_period_days=request.credit_period_days,
            installment_count=request.installment_count,
            interest_rate=request.interest_rate,
            late_fee_rate=request.late_fee_rate
        )
        
        return credit_terms
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create credit terms: {str(e)}"
        )


@router.post("/credit/payment", response_model=PaymentResponse)
async def process_credit_payment(
    request: ProcessCreditPaymentRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Process a credit payment installment.
    
    Args:
        request: Credit payment request
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        PaymentResponse: Payment processing result
    """
    try:
        result = await payment_service.process_credit_payment(
            credit_id=request.credit_id,
            payment_amount=request.payment_amount,
            payment_method=request.payment_method
        )
        
        return PaymentResponse(
            success=result["success"],
            message="Credit payment processed successfully" if result["success"] else "Credit payment failed",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process credit payment: {str(e)}"
        )


@router.get("/credit/{credit_id}", response_model=CreditTerms)
async def get_credit_terms(
    credit_id: str,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Get credit terms details.
    
    Args:
        credit_id: Credit terms ID
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        CreditTerms: Credit terms details
    """
    try:
        credit_data = await payment_service.db.credit_terms.find_one(
            {"credit_id": credit_id}
        )
        
        if not credit_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credit terms not found"
            )
        
        credit_terms = CreditTerms(**credit_data)
        
        # Check if user has access to this credit terms
        if (current_user.user_id != credit_terms.buyer_id and 
            current_user.user_id != credit_terms.vendor_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this credit terms"
            )
        
        return credit_terms
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credit terms: {str(e)}"
        )


@router.post("/reminder/create", response_model=PaymentReminder)
async def create_payment_reminder(
    request: CreateReminderRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Create payment reminder for credit terms.
    
    Args:
        request: Reminder creation request
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        PaymentReminder: Created reminder
    """
    try:
        reminder = await payment_service.create_payment_reminder(
            credit_id=request.credit_id,
            reminder_type=request.reminder_type,
            days_before_due=request.days_before_due
        )
        
        return reminder
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment reminder: {str(e)}"
        )


@router.post("/refund/create", response_model=RefundRequest)
async def create_refund_request(
    request: CreateRefundRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Create refund request with return policy enforcement.
    
    Args:
        request: Refund request creation
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        RefundRequest: Created refund request
    """
    try:
        refund_request = await payment_service.create_refund_request(
            transaction_id=request.transaction_id,
            requester_id=current_user.user_id,
            refund_amount=request.refund_amount,
            refund_reason=request.refund_reason,
            description=request.description,
            supporting_documents=request.supporting_documents
        )
        
        return refund_request
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create refund request: {str(e)}"
        )


@router.get("/refund/{refund_id}", response_model=RefundRequest)
async def get_refund_request(
    refund_id: str,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Get refund request details.
    
    Args:
        refund_id: Refund request ID
        current_user: Current authenticated user
        payment_service: Payment service instance
        
    Returns:
        RefundRequest: Refund request details
    """
    try:
        refund_data = await payment_service.db.refund_requests.find_one(
            {"refund_id": refund_id}
        )
        
        if not refund_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund request not found"
            )
        
        refund_request = RefundRequest(**refund_data)
        
        # Check if user has access to this refund request
        if current_user.user_id != refund_request.requester_id:
            # Also allow access to the other party in the transaction
            transaction_data = await payment_service.db.payment_transactions.find_one(
                {"transaction_id": refund_request.transaction_id}
            )
            if transaction_data:
                transaction = PaymentTransaction(**transaction_data)
                if (current_user.user_id != transaction.buyer_id and 
                    current_user.user_id != transaction.vendor_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied to this refund request"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this refund request"
                )
        
        return refund_request
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get refund request: {str(e)}"
        )


@router.get("/user/transactions", response_model=List[PaymentTransaction])
async def get_user_transactions(
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
    limit: int = 50,
    offset: int = 0
):
    """
    Get user's payment transactions.
    
    Args:
        current_user: Current authenticated user
        payment_service: Payment service instance
        limit: Maximum number of transactions to return
        offset: Number of transactions to skip
        
    Returns:
        List[PaymentTransaction]: User's transactions
    """
    try:
        # Get transactions where user is buyer or vendor
        cursor = payment_service.db.payment_transactions.find(
            {
                "$or": [
                    {"buyer_id": current_user.user_id},
                    {"vendor_id": current_user.user_id}
                ]
            }
        ).sort("created_at", -1).skip(offset).limit(limit)
        
        transactions = []
        async for transaction_data in cursor:
            transactions.append(PaymentTransaction(**transaction_data))
        
        return transactions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user transactions: {str(e)}"
        )


@router.get("/user/invoices", response_model=List[Invoice])
async def get_user_invoices(
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
    limit: int = 50,
    offset: int = 0
):
    """
    Get user's invoices.
    
    Args:
        current_user: Current authenticated user
        payment_service: Payment service instance
        limit: Maximum number of invoices to return
        offset: Number of invoices to skip
        
    Returns:
        List[Invoice]: User's invoices
    """
    try:
        # Get user's transaction IDs
        transaction_cursor = payment_service.db.payment_transactions.find(
            {
                "$or": [
                    {"buyer_id": current_user.user_id},
                    {"vendor_id": current_user.user_id}
                ]
            },
            {"transaction_id": 1}
        )
        
        transaction_ids = []
        async for transaction in transaction_cursor:
            transaction_ids.append(transaction["transaction_id"])
        
        if not transaction_ids:
            return []
        
        # Get invoices for these transactions
        cursor = payment_service.db.invoices.find(
            {"transaction_id": {"$in": transaction_ids}}
        ).sort("invoice_date", -1).skip(offset).limit(limit)
        
        invoices = []
        async for invoice_data in cursor:
            invoices.append(Invoice(**invoice_data))
        
        return invoices
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user invoices: {str(e)}"
        )