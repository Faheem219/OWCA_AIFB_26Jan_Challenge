"""
Tests for escrow and credit management functionality.
Tests escrow services, credit terms, payment scheduling, and refund processing.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
import pytest_asyncio
import uuid

from app.models.payment import (
    PaymentDetails,
    PaymentMethod,
    PaymentStatus,
    UPIDetails,
    EscrowStatus,
    EscrowTransaction,
    CreditTerms,
    CreditTermsStatus,
    PaymentReminder,
    PaymentReminderType,
    RefundRequest,
    RefundReason
)
from app.services.payment_service import PaymentService


@pytest_asyncio.fixture
async def payment_service():
    """Create payment service instance."""
    service = PaymentService()
    await service.initialize()
    return service


@pytest_asyncio.fixture
async def completed_transaction(payment_service):
    """Create a completed high-value transaction for escrow testing."""
    upi_details = UPIDetails(upi_id="buyer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_ESCROW_TEST",
        buyer_id="buyer_123",
        vendor_id="vendor_123",
        amount=Decimal("50000.00"),  # High value for escrow
        payment_details=payment_details,
        description={"en": "High-value agricultural equipment purchase"}
    )
    
    # Process payment to completion
    await payment_service.process_payment(transaction.transaction_id)
    
    return transaction


@pytest.mark.asyncio
async def test_create_escrow_transaction(payment_service, completed_transaction):
    """Test creating escrow transaction for high-value payments."""
    release_conditions = {
        "delivery_confirmation": True,
        "quality_inspection": True,
        "dispute_period_days": 7
    }
    
    milestone_conditions = [
        {
            "milestone": "delivery_confirmed",
            "release_percentage": 70,
            "description": "Release 70% on delivery confirmation"
        },
        {
            "milestone": "quality_approved",
            "release_percentage": 30,
            "description": "Release remaining 30% after quality approval"
        }
    ]
    
    escrow = await payment_service.create_escrow_transaction(
        transaction_id=completed_transaction.transaction_id,
        release_conditions=release_conditions,
        milestone_conditions=milestone_conditions,
        auto_release_days=14,
        escrow_fee_percentage=Decimal('1.5')
    )
    
    # Verify escrow transaction
    assert escrow.escrow_id.startswith("ESC_")
    assert escrow.transaction_id == completed_transaction.transaction_id
    assert escrow.buyer_id == completed_transaction.buyer_id
    assert escrow.vendor_id == completed_transaction.vendor_id
    assert escrow.amount == completed_transaction.amount
    assert escrow.remaining_amount == completed_transaction.amount
    assert escrow.status == EscrowStatus.ACTIVE
    assert escrow.release_conditions == release_conditions
    assert escrow.milestone_conditions == milestone_conditions
    assert escrow.auto_release_enabled is True
    assert escrow.auto_release_date is not None
    assert escrow.escrow_fee == (completed_transaction.amount * Decimal('1.5')) / Decimal('100')
    assert escrow.fee_paid_by == "buyer"


@pytest.mark.asyncio
async def test_escrow_minimum_amount_validation(payment_service):
    """Test that escrow requires minimum transaction amount."""
    # Create low-value transaction
    upi_details = UPIDetails(upi_id="buyer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_LOW_VALUE",
        buyer_id="buyer_123",
        vendor_id="vendor_123",
        amount=Decimal("500.00"),  # Below minimum for escrow
        payment_details=payment_details
    )
    
    await payment_service.process_payment(transaction.transaction_id)
    
    # Try to create escrow - should fail
    with pytest.raises(Exception) as exc_info:
        await payment_service.create_escrow_transaction(
            transaction_id=transaction.transaction_id,
            release_conditions={"delivery_confirmation": True}
        )
    
    assert "amount too low for escrow" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_release_escrow_funds(payment_service, completed_transaction):
    """Test releasing funds from escrow account."""
    # Create escrow first
    escrow = await payment_service.create_escrow_transaction(
        transaction_id=completed_transaction.transaction_id,
        release_conditions={"delivery_confirmation": True}
    )
    
    # Release partial amount
    release_amount = Decimal("30000.00")
    result = await payment_service.release_escrow_funds(
        escrow_id=escrow.escrow_id,
        release_amount=release_amount,
        release_reason="delivery_confirmed",
        released_by="buyer_123"
    )
    
    # Verify release result
    assert result["success"] is True
    assert result["amount_released"] == float(release_amount)
    assert result["remaining_amount"] == float(completed_transaction.amount - release_amount)
    assert result["status"] == EscrowStatus.PARTIALLY_RELEASED
    assert "release_id" in result
    assert "transfer_result" in result
    
    # Verify transfer result
    transfer_result = result["transfer_result"]
    assert transfer_result["vendor_id"] == completed_transaction.vendor_id
    assert transfer_result["amount"] == float(release_amount)
    assert transfer_result["status"] == "completed"


@pytest.mark.asyncio
async def test_release_full_escrow_amount(payment_service, completed_transaction):
    """Test releasing full escrow amount."""
    # Create escrow
    escrow = await payment_service.create_escrow_transaction(
        transaction_id=completed_transaction.transaction_id,
        release_conditions={"quality_approved": True}
    )
    
    # Release full amount (None means full amount)
    result = await payment_service.release_escrow_funds(
        escrow_id=escrow.escrow_id,
        release_amount=None,  # Full amount
        release_reason="all_conditions_met",
        released_by="system"
    )
    
    # Verify full release
    assert result["success"] is True
    assert result["amount_released"] == float(completed_transaction.amount)
    assert result["remaining_amount"] == 0.0
    assert result["status"] == EscrowStatus.RELEASED


@pytest.mark.asyncio
async def test_create_credit_terms(payment_service):
    """Test creating credit terms for established trading relationships."""
    # Create transaction for credit terms
    upi_details = UPIDetails(upi_id="buyer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_CREDIT_TEST",
        buyer_id="established_buyer_123",
        vendor_id="trusted_vendor_123",
        amount=Decimal("25000.00"),
        payment_details=payment_details
    )
    
    # Mock trading relationship duration and credit score
    # In real implementation, these would be calculated from database
    payment_service._get_trading_relationship_duration = lambda b, v: 6  # 6 months
    payment_service._calculate_credit_score = lambda b: 0.85  # Good credit score
    
    # Create credit terms
    credit_terms = await payment_service.create_credit_terms(
        transaction_id=transaction.transaction_id,
        credit_period_days=90,
        installment_count=3,
        interest_rate=Decimal('2.5'),  # 2.5% interest
        late_fee_rate=Decimal('1.0')   # 1% late fee
    )
    
    # Verify credit terms
    assert credit_terms.credit_id.startswith("CRD_")
    assert credit_terms.transaction_id == transaction.transaction_id
    assert credit_terms.buyer_id == transaction.buyer_id
    assert credit_terms.vendor_id == transaction.vendor_id
    assert credit_terms.total_amount == transaction.amount
    assert credit_terms.installment_count == 3
    assert credit_terms.credit_period_days == 90
    assert credit_terms.interest_rate == Decimal('2.5')
    assert credit_terms.late_fee_rate == Decimal('1.0')
    assert credit_terms.status == CreditTermsStatus.ACTIVE
    assert credit_terms.remaining_amount == transaction.amount
    assert credit_terms.trading_relationship_months == 6
    assert credit_terms.previous_credit_score == 0.85
    
    # Verify payment schedule
    assert len(credit_terms.payment_schedule) == 3
    for i, payment in enumerate(credit_terms.payment_schedule):
        assert payment["installment_number"] == i + 1
        assert "due_date" in payment
        assert "amount" in payment
        assert payment["status"] == "pending"


@pytest.mark.asyncio
async def test_credit_terms_insufficient_history(payment_service):
    """Test that credit terms require sufficient trading history."""
    # Create transaction
    upi_details = UPIDetails(upi_id="buyer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_NEW_BUYER",
        buyer_id="new_buyer_123",
        vendor_id="vendor_123",
        amount=Decimal("15000.00"),
        payment_details=payment_details
    )
    
    # Mock insufficient trading history
    payment_service._get_trading_relationship_duration = lambda b, v: 1  # Only 1 month
    payment_service._calculate_credit_score = lambda b: 0.8
    
    # Try to create credit terms - should fail
    with pytest.raises(Exception) as exc_info:
        await payment_service.create_credit_terms(
            transaction_id=transaction.transaction_id,
            credit_period_days=60,
            installment_count=2
        )
    
    assert "insufficient trading history" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_credit_terms_low_credit_score(payment_service):
    """Test that credit terms require good credit score."""
    # Create transaction
    upi_details = UPIDetails(upi_id="buyer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_LOW_CREDIT",
        buyer_id="risky_buyer_123",
        vendor_id="vendor_123",
        amount=Decimal("20000.00"),
        payment_details=payment_details
    )
    
    # Mock sufficient history but low credit score
    payment_service._get_trading_relationship_duration = lambda b, v: 6  # 6 months
    payment_service._calculate_credit_score = lambda b: 0.5  # Low credit score
    
    # Try to create credit terms - should fail
    with pytest.raises(Exception) as exc_info:
        await payment_service.create_credit_terms(
            transaction_id=transaction.transaction_id,
            credit_period_days=60,
            installment_count=2
        )
    
    assert "credit score too low" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_payment_reminder(payment_service):
    """Test creating payment reminders for credit terms."""
    # Create transaction and credit terms
    upi_details = UPIDetails(upi_id="buyer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_REMINDER_TEST",
        buyer_id="buyer_123",
        vendor_id="vendor_123",
        amount=Decimal("18000.00"),
        payment_details=payment_details
    )
    
    # Mock requirements for credit terms
    payment_service._get_trading_relationship_duration = lambda b, v: 8
    payment_service._calculate_credit_score = lambda b: 0.9
    
    credit_terms = await payment_service.create_credit_terms(
        transaction_id=transaction.transaction_id,
        credit_period_days=60,
        installment_count=2
    )
    
    # Create payment reminder
    reminder = await payment_service.create_payment_reminder(
        credit_id=credit_terms.credit_id,
        reminder_type=PaymentReminderType.SMS,
        days_before_due=5
    )
    
    # Verify reminder
    assert reminder.reminder_id.startswith("REM_")
    assert reminder.credit_id == credit_terms.credit_id
    assert reminder.transaction_id == transaction.transaction_id
    assert reminder.recipient_id == credit_terms.buyer_id
    assert reminder.reminder_type == PaymentReminderType.SMS
    assert reminder.days_until_due > 0
    assert reminder.due_amount > Decimal('0')
    assert reminder.is_sent is False
    assert "en" in reminder.message_content
    assert len(reminder.message_content["en"]) > 0


@pytest.mark.asyncio
async def test_create_refund_request(payment_service, completed_transaction):
    """Test creating refund request with return policy enforcement."""
    refund_amount = Decimal("25000.00")  # Partial refund
    description = {
        "en": "Product quality does not match description",
        "hi": "उत्पाद की गुणवत्ता विवरण से मेल नहीं खाती"
    }
    supporting_documents = [
        "https://example.com/quality_issue_photo1.jpg",
        "https://example.com/quality_issue_photo2.jpg"
    ]
    
    refund_request = await payment_service.create_refund_request(
        transaction_id=completed_transaction.transaction_id,
        requester_id=completed_transaction.buyer_id,
        refund_amount=refund_amount,
        refund_reason=RefundReason.QUALITY_ISSUE,
        description=description,
        supporting_documents=supporting_documents
    )
    
    # Verify refund request
    assert refund_request.refund_id.startswith("REF_")
    assert refund_request.transaction_id == completed_transaction.transaction_id
    assert refund_request.requester_id == completed_transaction.buyer_id
    assert refund_request.requester_type == "buyer"
    assert refund_request.refund_amount == refund_amount
    assert refund_request.refund_reason == RefundReason.QUALITY_ISSUE
    assert refund_request.description == description
    assert refund_request.supporting_documents == supporting_documents
    assert refund_request.status == "pending"
    assert refund_request.return_policy_compliant is True  # Should be compliant for quality issues
    assert len(refund_request.policy_violations) == 0


@pytest.mark.asyncio
async def test_refund_request_policy_violations(payment_service):
    """Test refund request with policy violations."""
    # Create old transaction (simulate expired return period)
    upi_details = UPIDetails(upi_id="buyer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_OLD_TRANSACTION",
        buyer_id="buyer_123",
        vendor_id="vendor_123",
        amount=Decimal("15000.00"),
        payment_details=payment_details
    )
    
    await payment_service.process_payment(transaction.transaction_id)
    
    # Mock old transaction date
    old_date = datetime.utcnow() - timedelta(days=20)  # 20 days ago
    await payment_service.db.payment_transactions.update_one(
        {"transaction_id": transaction.transaction_id},
        {"$set": {"created_at": old_date}}
    )
    
    # Try to create refund request for buyer cancellation (7-day limit)
    refund_request = await payment_service.create_refund_request(
        transaction_id=transaction.transaction_id,
        requester_id=transaction.buyer_id,
        refund_amount=Decimal("15000.00"),
        refund_reason=RefundReason.BUYER_CANCELLATION,
        description={"en": "Changed mind about purchase"}
    )
    
    # Should have policy violations
    assert refund_request.return_policy_compliant is False
    assert len(refund_request.policy_violations) > 0
    assert any("return period expired" in violation.lower() for violation in refund_request.policy_violations)


@pytest.mark.asyncio
async def test_refund_request_excessive_amount(payment_service, completed_transaction):
    """Test refund request with amount exceeding transaction amount."""
    excessive_amount = completed_transaction.amount + Decimal("10000.00")
    
    with pytest.raises(Exception) as exc_info:
        await payment_service.create_refund_request(
            transaction_id=completed_transaction.transaction_id,
            requester_id=completed_transaction.buyer_id,
            refund_amount=excessive_amount,
            refund_reason=RefundReason.PRODUCT_DEFECT,
            description={"en": "Product is defective"}
        )
    
    assert "refund amount cannot exceed transaction amount" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_unauthorized_refund_request(payment_service, completed_transaction):
    """Test that unauthorized users cannot create refund requests."""
    unauthorized_user_id = "unauthorized_user_456"
    
    with pytest.raises(Exception) as exc_info:
        await payment_service.create_refund_request(
            transaction_id=completed_transaction.transaction_id,
            requester_id=unauthorized_user_id,
            refund_amount=Decimal("10000.00"),
            refund_reason=RefundReason.QUALITY_ISSUE,
            description={"en": "Quality issue"}
        )
    
    assert "not authorized" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_payment_schedule_generation():
    """Test payment schedule generation for credit terms."""
    service = PaymentService()
    
    total_amount = Decimal("30000.00")
    installment_count = 3
    credit_period_days = 90
    interest_rate = Decimal("3.0")  # 3% interest
    
    schedule = service._generate_payment_schedule(
        total_amount=total_amount,
        installment_count=installment_count,
        credit_period_days=credit_period_days,
        interest_rate=interest_rate
    )
    
    # Verify schedule structure
    assert len(schedule) == installment_count
    
    total_scheduled = Decimal('0')
    for i, payment in enumerate(schedule):
        assert payment["installment_number"] == i + 1
        assert "due_date" in payment
        assert "amount" in payment
        assert payment["status"] == "pending"
        assert isinstance(payment["due_date"], datetime)
        
        total_scheduled += Decimal(str(payment["amount"]))
    
    # Verify total includes interest
    expected_interest = (total_amount * interest_rate * credit_period_days) / (Decimal('100') * Decimal('365'))
    expected_total = total_amount + expected_interest
    
    # Allow small rounding differences
    assert abs(total_scheduled - expected_total) < Decimal('0.01')


@pytest.mark.asyncio
async def test_credit_score_calculation():
    """Test credit score calculation based on payment history."""
    service = PaymentService()
    service.db = type('MockDB', (), {})()
    
    # Mock credit history data
    mock_credit_history = [
        {
            "credit_id": "CRD_1",
            "buyer_id": "buyer_123",
            "total_amount": Decimal("20000.00"),
            "status": "completed",
            "overdue_days": 0
        },
        {
            "credit_id": "CRD_2", 
            "buyer_id": "buyer_123",
            "total_amount": Decimal("15000.00"),
            "status": "completed",
            "overdue_days": 2  # Slightly late
        },
        {
            "credit_id": "CRD_3",
            "buyer_id": "buyer_123", 
            "total_amount": Decimal("10000.00"),
            "status": "overdue",
            "overdue_days": 10
        }
    ]
    
    # Mock database find method
    async def mock_find(query):
        class MockCursor:
            def __init__(self, data):
                self.data = data
                self.index = 0
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                if self.index >= len(self.data):
                    raise StopAsyncIteration
                item = self.data[self.index]
                self.index += 1
                return item
        
        return MockCursor(mock_credit_history)
    
    service.db.credit_terms = type('MockCollection', (), {'find': mock_find})()
    
    # Calculate credit score
    score = await service._calculate_credit_score("buyer_123")
    
    # Score should be between 0 and 1
    assert 0 <= score <= 1
    
    # Score should reflect mixed payment history
    # (2 completed, 1 overdue should give moderate score)
    assert 0.4 <= score <= 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])