"""
Payment system models for the Multilingual Mandi platform.
Supports UPI, digital wallets, and card payments with multilingual invoicing.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from decimal import Decimal

from pydantic import BaseModel, Field, validator
from bson import ObjectId


class PaymentMethod(str, Enum):
    """Supported payment methods."""
    UPI = "upi"
    DIGITAL_WALLET = "digital_wallet"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    CASH_ON_DELIVERY = "cod"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class DigitalWalletProvider(str, Enum):
    """Supported digital wallet providers."""
    PAYTM = "paytm"
    PHONEPE = "phonepe"
    GOOGLE_PAY = "google_pay"
    AMAZON_PAY = "amazon_pay"
    MOBIKWIK = "mobikwik"
    FREECHARGE = "freecharge"


class CardType(str, Enum):
    """Supported card types."""
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionType(str, Enum):
    """Transaction types."""
    PURCHASE = "purchase"
    REFUND = "refund"
    ESCROW_DEPOSIT = "escrow_deposit"
    ESCROW_RELEASE = "escrow_release"


class DeliveryStatus(str, Enum):
    """Delivery status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"


class DeliveryMethod(str, Enum):
    """Delivery method enumeration."""
    SELF_PICKUP = "self_pickup"
    VENDOR_DELIVERY = "vendor_delivery"
    THIRD_PARTY_COURIER = "third_party_courier"
    LOCAL_TRANSPORT = "local_transport"


class UPIDetails(BaseModel):
    """UPI payment details."""
    upi_id: str = Field(..., description="UPI ID of the payer")
    transaction_ref: Optional[str] = Field(None, description="UPI transaction reference")
    
    @validator('upi_id')
    def validate_upi_id(cls, v):
        """Validate UPI ID format."""
        if '@' not in v:
            raise ValueError('Invalid UPI ID format')
        return v.lower()


class DigitalWalletDetails(BaseModel):
    """Digital wallet payment details."""
    provider: DigitalWalletProvider
    wallet_id: str = Field(..., description="Wallet account identifier")
    transaction_ref: Optional[str] = Field(None, description="Wallet transaction reference")


class CardDetails(BaseModel):
    """Card payment details (sensitive data handled securely)."""
    card_type: CardType
    last_four_digits: str = Field(..., min_length=4, max_length=4)
    card_network: str = Field(..., description="Visa, Mastercard, RuPay, etc.")
    bank_name: Optional[str] = Field(None, description="Issuing bank name")
    transaction_ref: Optional[str] = Field(None, description="Card transaction reference")


class BankTransferDetails(BaseModel):
    """Bank transfer payment details."""
    account_number: str = Field(..., description="Last 4 digits of account number")
    ifsc_code: str = Field(..., description="IFSC code of the bank")
    bank_name: str = Field(..., description="Name of the bank")
    transaction_ref: Optional[str] = Field(None, description="Bank transaction reference")


class PaymentDetails(BaseModel):
    """Payment method specific details."""
    method: PaymentMethod
    upi_details: Optional[UPIDetails] = None
    wallet_details: Optional[DigitalWalletDetails] = None
    card_details: Optional[CardDetails] = None
    bank_details: Optional[BankTransferDetails] = None
    
    @validator('upi_details')
    def validate_upi_details(cls, v, values):
        """Validate UPI details when method is UPI."""
        if values.get('method') == PaymentMethod.UPI and not v:
            raise ValueError('UPI details required for UPI payment')
        return v
    
    @validator('wallet_details')
    def validate_wallet_details(cls, v, values):
        """Validate wallet details when method is digital wallet."""
        if values.get('method') == PaymentMethod.DIGITAL_WALLET and not v:
            raise ValueError('Wallet details required for digital wallet payment')
        return v
    
    @validator('card_details')
    def validate_card_details(cls, v, values):
        """Validate card details when method is card."""
        if values.get('method') == PaymentMethod.CARD and not v:
            raise ValueError('Card details required for card payment')
        return v


class PaymentTransaction(BaseModel):
    """Payment transaction model."""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    order_id: str = Field(..., description="Associated order identifier")
    buyer_id: str = Field(..., description="Buyer user ID")
    vendor_id: str = Field(..., description="Vendor user ID")
    
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(default="INR", description="Currency code")
    
    payment_details: PaymentDetails
    transaction_type: TransactionType = Field(default=TransactionType.PURCHASE)
    
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    status_history: List[Dict[str, Union[str, datetime]]] = Field(default_factory=list)
    
    gateway_transaction_id: Optional[str] = Field(None, description="Payment gateway transaction ID")
    gateway_response: Optional[Dict] = Field(None, description="Gateway response data")
    
    fees: Optional[Decimal] = Field(None, description="Transaction fees")
    tax: Optional[Decimal] = Field(None, description="Tax amount")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="Transaction completion time")
    
    # Multilingual support
    description: Dict[str, str] = Field(default_factory=dict, description="Transaction description in multiple languages")
    
    # Escrow support
    is_escrow: bool = Field(default=False, description="Whether this is an escrow transaction")
    escrow_release_conditions: Optional[Dict] = Field(None, description="Conditions for escrow release")
    
    # Refund support
    refund_reason: Optional[str] = Field(None, description="Reason for refund if applicable")
    refunded_amount: Optional[Decimal] = Field(None, description="Amount refunded")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            ObjectId: str,
            Decimal: float
        }


class Invoice(BaseModel):
    """Multilingual invoice model."""
    invoice_id: str = Field(..., description="Unique invoice identifier")
    transaction_id: str = Field(..., description="Associated transaction ID")
    order_id: str = Field(..., description="Associated order ID")
    
    buyer_info: Dict[str, str] = Field(..., description="Buyer information")
    vendor_info: Dict[str, str] = Field(..., description="Vendor information")
    
    # Multilingual invoice content
    invoice_content: Dict[str, Dict] = Field(..., description="Invoice content in multiple languages")
    
    # Financial details
    subtotal: Decimal = Field(..., description="Subtotal amount")
    tax_amount: Decimal = Field(default=Decimal('0'), description="Tax amount")
    discount_amount: Decimal = Field(default=Decimal('0'), description="Discount amount")
    total_amount: Decimal = Field(..., description="Total invoice amount")
    
    currency: str = Field(default="INR", description="Currency code")
    
    # Invoice metadata
    invoice_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = Field(None, description="Payment due date")
    
    # Status
    is_paid: bool = Field(default=False, description="Payment status")
    paid_at: Optional[datetime] = Field(None, description="Payment completion time")
    
    # File references
    pdf_file_path: Optional[str] = Field(None, description="Generated PDF file path")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            ObjectId: str,
            Decimal: float
        }


class EscrowStatus(str, Enum):
    """Escrow status enumeration."""
    ACTIVE = "active"
    RELEASED = "released"
    PARTIALLY_RELEASED = "partially_released"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class EscrowReleaseCondition(str, Enum):
    """Escrow release condition types."""
    DELIVERY_CONFIRMATION = "delivery_confirmation"
    QUALITY_INSPECTION = "quality_inspection"
    TIME_BASED = "time_based"
    MILESTONE_COMPLETION = "milestone_completion"
    MANUAL_APPROVAL = "manual_approval"


class CreditTermsStatus(str, Enum):
    """Credit terms status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class PaymentReminderType(str, Enum):
    """Payment reminder types."""
    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"
    VOICE_CALL = "voice_call"


class RefundReason(str, Enum):
    """Refund reason enumeration."""
    PRODUCT_DEFECT = "product_defect"
    DELIVERY_FAILURE = "delivery_failure"
    QUALITY_ISSUE = "quality_issue"
    BUYER_CANCELLATION = "buyer_cancellation"
    VENDOR_CANCELLATION = "vendor_cancellation"
    DISPUTE_RESOLUTION = "dispute_resolution"
    POLICY_VIOLATION = "policy_violation"


class EscrowTransaction(BaseModel):
    """Escrow transaction model for high-value transactions."""
    escrow_id: str = Field(..., description="Unique escrow identifier")
    transaction_id: str = Field(..., description="Associated payment transaction ID")
    
    buyer_id: str = Field(..., description="Buyer user ID")
    vendor_id: str = Field(..., description="Vendor user ID")
    
    amount: Decimal = Field(..., description="Escrowed amount")
    currency: str = Field(default="INR", description="Currency code")
    
    # Escrow conditions
    release_conditions: Dict = Field(..., description="Conditions for fund release")
    milestone_conditions: Optional[List[Dict]] = Field(None, description="Milestone-based release conditions")
    
    # Status tracking
    status: EscrowStatus = Field(default=EscrowStatus.ACTIVE, description="Escrow status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Release tracking
    released_amount: Decimal = Field(default=Decimal('0'), description="Amount released so far")
    remaining_amount: Decimal = Field(..., description="Remaining escrowed amount")
    
    # Release history
    release_history: List[Dict] = Field(default_factory=list, description="History of fund releases")
    
    # Dispute handling
    dispute_raised: bool = Field(default=False, description="Whether a dispute has been raised")
    dispute_details: Optional[Dict] = Field(None, description="Dispute information")
    dispute_resolution_deadline: Optional[datetime] = Field(None, description="Deadline for dispute resolution")
    
    # Automatic release settings
    auto_release_enabled: bool = Field(default=True, description="Whether automatic release is enabled")
    auto_release_date: Optional[datetime] = Field(None, description="Date for automatic release")
    
    # Fees and charges
    escrow_fee: Optional[Decimal] = Field(None, description="Escrow service fee")
    fee_paid_by: Optional[str] = Field(None, description="Who pays the escrow fee (buyer/vendor/split)")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            ObjectId: str,
            Decimal: float
        }


class CreditTerms(BaseModel):
    """Credit terms and payment scheduling model."""
    credit_id: str = Field(..., description="Unique credit terms identifier")
    transaction_id: str = Field(..., description="Associated transaction ID")
    
    buyer_id: str = Field(..., description="Buyer user ID")
    vendor_id: str = Field(..., description="Vendor user ID")
    
    # Credit details
    total_amount: Decimal = Field(..., description="Total credit amount")
    currency: str = Field(default="INR", description="Currency code")
    
    # Payment schedule
    payment_schedule: List[Dict] = Field(..., description="List of scheduled payments")
    installment_count: int = Field(..., description="Number of installments")
    
    # Terms
    credit_period_days: int = Field(..., description="Credit period in days")
    interest_rate: Optional[Decimal] = Field(None, description="Interest rate percentage")
    late_fee_rate: Optional[Decimal] = Field(None, description="Late payment fee rate")
    
    # Status
    status: CreditTermsStatus = Field(default=CreditTermsStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Payment tracking
    paid_amount: Decimal = Field(default=Decimal('0'), description="Amount paid so far")
    remaining_amount: Decimal = Field(..., description="Remaining amount to be paid")
    next_payment_date: Optional[datetime] = Field(None, description="Next payment due date")
    
    # Payment history
    payment_history: List[Dict] = Field(default_factory=list, description="History of payments made")
    
    # Overdue tracking
    overdue_amount: Decimal = Field(default=Decimal('0'), description="Overdue amount")
    overdue_days: int = Field(default=0, description="Number of days overdue")
    
    # Relationship history
    trading_relationship_months: Optional[int] = Field(None, description="Length of trading relationship in months")
    previous_credit_score: Optional[float] = Field(None, description="Previous credit performance score")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            ObjectId: str,
            Decimal: float
        }


class PaymentReminder(BaseModel):
    """Payment reminder and notification model."""
    reminder_id: str = Field(..., description="Unique reminder identifier")
    credit_id: str = Field(..., description="Associated credit terms ID")
    transaction_id: str = Field(..., description="Associated transaction ID")
    
    recipient_id: str = Field(..., description="User ID to receive reminder")
    reminder_type: PaymentReminderType = Field(..., description="Type of reminder")
    
    # Reminder details
    due_amount: Decimal = Field(..., description="Amount due")
    due_date: datetime = Field(..., description="Payment due date")
    days_until_due: int = Field(..., description="Days until payment is due")
    
    # Reminder content
    message_content: Dict[str, str] = Field(..., description="Multilingual reminder message")
    
    # Scheduling
    scheduled_at: datetime = Field(..., description="When reminder is scheduled to be sent")
    sent_at: Optional[datetime] = Field(None, description="When reminder was actually sent")
    
    # Status
    is_sent: bool = Field(default=False, description="Whether reminder has been sent")
    delivery_status: Optional[str] = Field(None, description="Delivery status of reminder")
    
    # Response tracking
    acknowledged: bool = Field(default=False, description="Whether recipient acknowledged reminder")
    acknowledged_at: Optional[datetime] = Field(None, description="When reminder was acknowledged")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            ObjectId: str,
            Decimal: float
        }


class RefundRequest(BaseModel):
    """Refund and return policy enforcement model."""
    refund_id: str = Field(..., description="Unique refund request identifier")
    transaction_id: str = Field(..., description="Associated transaction ID")
    
    requester_id: str = Field(..., description="User ID who requested refund")
    requester_type: str = Field(..., description="Type of requester (buyer/vendor)")
    
    # Refund details
    refund_amount: Decimal = Field(..., description="Requested refund amount")
    currency: str = Field(default="INR", description="Currency code")
    refund_reason: RefundReason = Field(..., description="Reason for refund")
    
    # Request details
    description: Dict[str, str] = Field(..., description="Multilingual refund description")
    supporting_documents: List[str] = Field(default_factory=list, description="Supporting document URLs")
    
    # Status and processing
    status: str = Field(default="pending", description="Refund request status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Review process
    reviewed_by: Optional[str] = Field(None, description="Admin/system user who reviewed")
    reviewed_at: Optional[datetime] = Field(None, description="When request was reviewed")
    review_notes: Optional[Dict[str, str]] = Field(None, description="Multilingual review notes")
    
    # Approval/rejection
    approved: Optional[bool] = Field(None, description="Whether refund was approved")
    approval_reason: Optional[str] = Field(None, description="Reason for approval/rejection")
    
    # Processing
    processed_at: Optional[datetime] = Field(None, description="When refund was processed")
    refund_transaction_id: Optional[str] = Field(None, description="Refund transaction ID")
    
    # Return policy compliance
    return_policy_compliant: Optional[bool] = Field(None, description="Whether request complies with return policy")
    policy_violations: List[str] = Field(default_factory=list, description="List of policy violations if any")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            ObjectId: str,
            Decimal: float
        }


class PaymentMethodValidation(BaseModel):
    """Payment method validation result."""
    is_valid: bool = Field(..., description="Whether the payment method is valid")
    method: PaymentMethod = Field(..., description="Payment method being validated")
    validation_errors: List[str] = Field(default_factory=list, description="Validation error messages")
    supported_features: List[str] = Field(default_factory=list, description="Supported features for this method")


class PaymentGatewayConfig(BaseModel):
    """Payment gateway configuration."""
    gateway_name: str = Field(..., description="Name of the payment gateway")
    is_enabled: bool = Field(default=True, description="Whether the gateway is enabled")
    supported_methods: List[PaymentMethod] = Field(..., description="Supported payment methods")
    api_endpoint: str = Field(..., description="Gateway API endpoint")
    merchant_id: str = Field(..., description="Merchant identifier")
    api_key: str = Field(..., description="API key (encrypted)")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for status updates")
    
    # Gateway specific settings
    settings: Dict = Field(default_factory=dict, description="Gateway specific configuration")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            ObjectId: str
        }


class DeliveryAddress(BaseModel):
    """Delivery address information."""
    name: str = Field(..., description="Recipient name")
    phone: str = Field(..., description="Contact phone number")
    address_line1: str = Field(..., description="Address line 1")
    address_line2: Optional[str] = Field(None, description="Address line 2")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(default="India", description="Country")
    landmark: Optional[str] = Field(None, description="Landmark for easy location")
    coordinates: Optional[Dict[str, float]] = Field(None, description="GPS coordinates")


class DeliveryTracking(BaseModel):
    """Delivery tracking information."""
    tracking_id: str = Field(..., description="Unique tracking identifier")
    transaction_id: str = Field(..., description="Associated transaction ID")
    order_id: str = Field(..., description="Associated order ID")
    
    delivery_method: DeliveryMethod = Field(..., description="Method of delivery")
    delivery_status: DeliveryStatus = Field(default=DeliveryStatus.PENDING)
    
    pickup_address: DeliveryAddress = Field(..., description="Pickup address")
    delivery_address: DeliveryAddress = Field(..., description="Delivery address")
    
    # Delivery partner information
    delivery_partner: Optional[str] = Field(None, description="Delivery partner name")
    delivery_partner_contact: Optional[str] = Field(None, description="Delivery partner contact")
    vehicle_details: Optional[Dict] = Field(None, description="Vehicle information")
    
    # Timing information
    estimated_pickup_time: Optional[datetime] = Field(None, description="Estimated pickup time")
    actual_pickup_time: Optional[datetime] = Field(None, description="Actual pickup time")
    estimated_delivery_time: Optional[datetime] = Field(None, description="Estimated delivery time")
    actual_delivery_time: Optional[datetime] = Field(None, description="Actual delivery time")
    
    # Tracking updates
    tracking_updates: List[Dict] = Field(default_factory=list, description="Delivery status updates")
    
    # Special instructions
    delivery_instructions: Optional[Dict[str, str]] = Field(None, description="Multilingual delivery instructions")
    special_requirements: Optional[List[str]] = Field(None, description="Special delivery requirements")
    
    # Proof of delivery
    delivery_proof: Optional[Dict] = Field(None, description="Delivery proof (signature, photo, etc.)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            ObjectId: str
        }


class TransactionRecord(BaseModel):
    """Comprehensive transaction record for accounting and tax purposes."""
    record_id: str = Field(..., description="Unique record identifier")
    transaction_id: str = Field(..., description="Associated transaction ID")
    
    # Financial details
    gross_amount: Decimal = Field(..., description="Gross transaction amount")
    tax_breakdown: Dict[str, Decimal] = Field(default_factory=dict, description="Tax breakdown by type")
    discount_details: Dict[str, Decimal] = Field(default_factory=dict, description="Discount breakdown")
    net_amount: Decimal = Field(..., description="Net amount after taxes and discounts")
    
    # Accounting information
    accounting_period: str = Field(..., description="Accounting period (YYYY-MM)")
    financial_year: str = Field(..., description="Financial year")
    
    # Tax compliance
    gstin_buyer: Optional[str] = Field(None, description="Buyer's GSTIN")
    gstin_vendor: Optional[str] = Field(None, description="Vendor's GSTIN")
    tax_invoice_number: Optional[str] = Field(None, description="Tax invoice number")
    
    # Product/service details
    item_details: List[Dict] = Field(..., description="Detailed item information")
    hsn_sac_codes: List[str] = Field(default_factory=list, description="HSN/SAC codes")
    
    # Compliance flags
    tds_applicable: bool = Field(default=False, description="Whether TDS is applicable")
    tcs_applicable: bool = Field(default=False, description="Whether TCS is applicable")
    reverse_charge: bool = Field(default=False, description="Whether reverse charge applies")
    
    # Record keeping
    created_at: datetime = Field(default_factory=datetime.utcnow)
    archived_at: Optional[datetime] = Field(None, description="When record was archived")
    retention_period: int = Field(default=7, description="Retention period in years")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            ObjectId: str,
            Decimal: float
        }