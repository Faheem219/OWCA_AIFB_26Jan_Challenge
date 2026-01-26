"""
Property-based test for credit terms and payment scheduling.
**Validates: Requirements 7.5**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
import uuid

from app.models.payment import (
    PaymentTransaction,
    PaymentDetails,
    PaymentMethod,
    PaymentStatus,
    UPIDetails,
    CreditTerms,
    CreditTermsStatus,
    PaymentReminder,
    PaymentReminderType,
    TransactionType
)
from app.services.payment_service import PaymentService


# Credit eligibility thresholds
MIN_TRADING_RELATIONSHIP_MONTHS = 3
MIN_CREDIT_SCORE = 0.7
MIN_CREDIT_AMOUNT = Decimal('5000.00')
MAX_CREDIT_AMOUNT = Decimal('500000.00')


@composite
def credit_eligible_amount_strategy(draw):
    """Generate transaction amounts eligible for credit terms."""
    return draw(st.decimals(
        min_value=MIN_CREDIT_AMOUNT,
        max_value=MAX_CREDIT_AMOUNT,
        places=2
    ))


@composite
def credit_parameters_strategy(draw):
    """Generate valid credit term parameters."""
    credit_period_days = draw(st.integers(min_value=30, max_value=365))
    installment_count = draw(st.integers(min_value=2, max_value=12))
    
    # Ensure installment period is reasonable
    assume(credit_period_days >= installment_count * 7)  # At least 7 days between installments
    
    interest_rate = draw(st.one_of(
        st.none(),
        st.decimals(min_value=Decimal('0.0'), max_value=Decimal('24.0'), places=2)
    ))
    
    late_fee_rate = draw(st.one_of(
        st.none(),
        st.decimals(min_value=Decimal('0.5'), max_value=Decimal('5.0'), places=2)
    ))
    
    return {
        "credit_period_days": credit_period_days,
        "installment_count": installment_count,
        "interest_rate": interest_rate,
        "late_fee_rate": late_fee_rate
    }


@composite
def trading_relationship_data_strategy(draw):
    """Generate trading relationship data for credit eligibility."""
    relationship_months = draw(st.integers(min_value=MIN_TRADING_RELATIONSHIP_MONTHS, max_value=60))
    credit_score = draw(st.decimals(min_value=MIN_CREDIT_SCORE, max_value=Decimal('1.0'), places=2))
    
    return {
        "relationship_months": relationship_months,
        "credit_score": float(credit_score)
    }


@composite
def credit_eligible_transaction_strategy(draw):
    """Generate transactions eligible for credit terms."""
    transaction_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
    order_id = f"ORDER_{uuid.uuid4().hex[:8].upper()}"
    buyer_id = str(ObjectId())
    vendor_id = str(ObjectId())
    amount = draw(credit_eligible_amount_strategy())
    
    # Generate payment method
    upi_details = UPIDetails(upi_id=f"buyer@{draw(st.sampled_from(['paytm', 'phonepe', 'googlepay']))}")
    payment_details = PaymentDetails(method=PaymentMethod.UPI, upi_details=upi_details)
    
    transaction = PaymentTransaction(
        transaction_id=transaction_id,
        order_id=order_id,
        buyer_id=buyer_id,
        vendor_id=vendor_id,
        amount=amount,
        payment_details=payment_details,
        status=PaymentStatus.PENDING,  # Credit terms can be created before payment completion
        created_at=datetime.utcnow()
    )
    
    return transaction


@pytest.fixture
def mock_db():
    """Mock database with payment transactions and credit terms collections."""
    db = MagicMock()
    db.payment_transactions = AsyncMock()
    db.credit_terms = AsyncMock()
    db.payment_reminders = AsyncMock()
    db.reminder_queue = AsyncMock()
    db.users = AsyncMock()
    return db


@pytest.fixture
def payment_service(mock_db):
    """Payment service instance with mocked dependencies."""
    service = PaymentService()
    service.db = mock_db
    return service


class TestCreditTermsSchedulingProperties:
    """Property-based tests for credit terms and payment scheduling."""
    
    @given(
        transaction=credit_eligible_transaction_strategy(),
        credit_params=credit_parameters_strategy(),
        relationship_data=trading_relationship_data_strategy()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_property_36_credit_terms_and_scheduling(
        self,
        transaction,
        credit_params,
        relationship_data,
        payment_service,
        mock_db
    ):
        """
        **Property 36: Credit Terms and Scheduling**
        **Validates: Requirements 7.5**
        
        For any established trading relationship, the system should support credit terms 
        and payment scheduling functionality.
        """
        # Setup mock database responses
        mock_db.payment_transactions.find_one.return_value = transaction.model_dump()
        mock_db.credit_terms.insert_one.return_value = MagicMock()
        mock_db.payment_transactions.update_one.return_value = MagicMock()
        mock_db.reminder_queue.insert_one.return_value = MagicMock()
        
        # Mock trading relationship and credit score
        payment_service._get_trading_relationship_duration = AsyncMock(
            return_value=relationship_data["relationship_months"]
        )
        payment_service._calculate_credit_score = AsyncMock(
            return_value=relationship_data["credit_score"]
        )
        
        # **Core Property Validations**
        
        # 1. Transaction must be eligible for credit terms
        assert transaction.amount >= MIN_CREDIT_AMOUNT, "Transaction must meet minimum amount for credit"
        assert relationship_data["relationship_months"] >= MIN_TRADING_RELATIONSHIP_MONTHS, "Must have sufficient trading history"
        assert relationship_data["credit_score"] >= MIN_CREDIT_SCORE, "Must have sufficient credit score"
        
        # Create credit terms
        credit_terms = await payment_service.create_credit_terms(
            transaction_id=transaction.transaction_id,
            credit_period_days=credit_params["credit_period_days"],
            installment_count=credit_params["installment_count"],
            interest_rate=credit_params["interest_rate"],
            late_fee_rate=credit_params["late_fee_rate"]
        )
        
        # 2. Credit terms must be created successfully
        assert credit_terms is not None
        assert isinstance(credit_terms, CreditTerms)
        
        # 3. Credit terms must have valid identifier and reference original transaction
        assert credit_terms.credit_id.startswith("CRD_")
        assert len(credit_terms.credit_id) == 16  # CRD_ + 12 character hex
        assert credit_terms.transaction_id == transaction.transaction_id
        
        # 4. Credit terms must preserve transaction parties and amount
        assert credit_terms.buyer_id == transaction.buyer_id
        assert credit_terms.vendor_id == transaction.vendor_id
        assert credit_terms.total_amount == transaction.amount
        assert credit_terms.currency == transaction.currency
        
        # 5. Credit parameters must be preserved correctly
        assert credit_terms.credit_period_days == credit_params["credit_period_days"]
        assert credit_terms.installment_count == credit_params["installment_count"]
        assert credit_terms.interest_rate == credit_params["interest_rate"]
        assert credit_terms.late_fee_rate == credit_params["late_fee_rate"]
        
        # 6. Credit terms must start with full amount remaining
        assert credit_terms.remaining_amount == transaction.amount
        assert credit_terms.paid_amount == Decimal('0')
        
        # 7. Credit terms must be in active status initially
        assert credit_terms.status == CreditTermsStatus.ACTIVE
        
        # 8. Payment schedule must be generated correctly
        assert len(credit_terms.payment_schedule) == credit_params["installment_count"]
        
        total_scheduled_amount = Decimal('0')
        for i, payment in enumerate(credit_terms.payment_schedule):
            # Each payment must have required fields
            assert payment["installment_number"] == i + 1
            assert "due_date" in payment
            assert "amount" in payment
            assert payment["status"] == "pending"
            
            # Due date must be in the future and within credit period
            due_date = payment["due_date"]
            assert isinstance(due_date, datetime)
            assert due_date > datetime.utcnow()
            assert due_date <= datetime.utcnow() + timedelta(days=credit_params["credit_period_days"])
            
            # Amount must be positive
            payment_amount = Decimal(str(payment["amount"]))
            assert payment_amount > Decimal('0')
            total_scheduled_amount += payment_amount
        
        # 9. Total scheduled amount must account for interest if applicable
        if credit_params["interest_rate"]:
            expected_interest = (
                transaction.amount * 
                credit_params["interest_rate"] * 
                credit_params["credit_period_days"]
            ) / (Decimal('100') * Decimal('365'))
            expected_total = transaction.amount + expected_interest
            # Allow small rounding differences
            assert abs(total_scheduled_amount - expected_total) < Decimal('1.00')
        else:
            # Without interest, total should equal original amount
            assert abs(total_scheduled_amount - transaction.amount) < Decimal('1.00')
        
        # 10. Payment schedule must be chronologically ordered
        for i in range(1, len(credit_terms.payment_schedule)):
            prev_date = credit_terms.payment_schedule[i-1]["due_date"]
            curr_date = credit_terms.payment_schedule[i]["due_date"]
            assert curr_date > prev_date, "Payment schedule must be chronologically ordered"
        
        # 11. Next payment date must be set correctly
        assert credit_terms.next_payment_date is not None
        assert credit_terms.next_payment_date == credit_terms.payment_schedule[0]["due_date"]
        
        # 12. Trading relationship data must be preserved
        assert credit_terms.trading_relationship_months == relationship_data["relationship_months"]
        assert credit_terms.previous_credit_score == relationship_data["credit_score"]
        
        # 13. Payment history must be empty initially
        assert credit_terms.payment_history == []
        
        # 14. Overdue tracking must be initialized
        assert credit_terms.overdue_amount == Decimal('0')
        assert credit_terms.overdue_days == 0
        
        # 15. Timestamps must be set correctly
        assert isinstance(credit_terms.created_at, datetime)
        assert isinstance(credit_terms.updated_at, datetime)
        assert credit_terms.created_at <= credit_terms.updated_at
        
        # 16. Database operations must be called correctly
        mock_db.credit_terms.insert_one.assert_called_once()
        mock_db.payment_transactions.update_one.assert_called_once()
        
        # Verify the transaction update
        update_call = mock_db.payment_transactions.update_one.call_args
        assert update_call[0][0] == {"transaction_id": transaction.transaction_id}
        update_data = update_call[0][1]["$set"]
        assert update_data["credit_terms_id"] == credit_terms.credit_id
    
    @given(
        transaction=credit_eligible_transaction_strategy(),
        credit_params=credit_parameters_strategy(),
        relationship_data=trading_relationship_data_strategy()
    )
    @settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_payment_reminder_creation(
        self,
        transaction,
        credit_params,
        relationship_data,
        payment_service,
        mock_db
    ):
        """
        Test that payment reminders are created correctly for credit terms.
        """
        # Setup mocks
        mock_db.payment_transactions.find_one.return_value = transaction.model_dump()
        mock_db.credit_terms.insert_one.return_value = MagicMock()
        mock_db.payment_transactions.update_one.return_value = MagicMock()
        mock_db.reminder_queue.insert_one.return_value = MagicMock()
        mock_db.users.find_one.return_value = {"user_id": transaction.buyer_id, "preferred_language": "en"}
        
        # Mock eligibility
        payment_service._get_trading_relationship_duration = AsyncMock(
            return_value=relationship_data["relationship_months"]
        )
        payment_service._calculate_credit_score = AsyncMock(
            return_value=relationship_data["credit_score"]
        )
        
        # Create credit terms
        credit_terms = await payment_service.create_credit_terms(
            transaction_id=transaction.transaction_id,
            credit_period_days=credit_params["credit_period_days"],
            installment_count=credit_params["installment_count"],
            interest_rate=credit_params["interest_rate"],
            late_fee_rate=credit_params["late_fee_rate"]
        )
        
        # Mock credit terms data for reminder creation
        mock_db.credit_terms.find_one.return_value = credit_terms.model_dump()
        mock_db.payment_reminders.insert_one.return_value = MagicMock()
        
        # Create payment reminder
        reminder = await payment_service.create_payment_reminder(
            credit_id=credit_terms.credit_id,
            reminder_type=PaymentReminderType.SMS,
            days_before_due=3
        )
        
        # Verify reminder creation
        assert reminder.reminder_id.startswith("REM_")
        assert reminder.credit_id == credit_terms.credit_id
        assert reminder.transaction_id == transaction.transaction_id
        assert reminder.recipient_id == transaction.buyer_id
        assert reminder.reminder_type == PaymentReminderType.SMS
        assert reminder.due_amount > Decimal('0')
        assert reminder.due_date == credit_terms.next_payment_date
        assert reminder.days_until_due > 0
        assert reminder.is_sent is False
        assert "en" in reminder.message_content
        assert len(reminder.message_content["en"]) > 0
    
    @given(
        insufficient_months=st.integers(min_value=0, max_value=MIN_TRADING_RELATIONSHIP_MONTHS - 1),
        transaction=credit_eligible_transaction_strategy()
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_insufficient_trading_history_rejection(
        self,
        insufficient_months,
        transaction,
        payment_service,
        mock_db
    ):
        """
        Test that credit terms are rejected for insufficient trading history.
        """
        # Setup mocks
        mock_db.payment_transactions.find_one.return_value = transaction.model_dump()
        
        # Mock insufficient trading relationship
        payment_service._get_trading_relationship_duration = AsyncMock(
            return_value=insufficient_months
        )
        payment_service._calculate_credit_score = AsyncMock(
            return_value=0.9  # Good credit score, but insufficient history
        )
        
        # Attempt to create credit terms - should fail
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_credit_terms(
                transaction_id=transaction.transaction_id,
                credit_period_days=60,
                installment_count=2
            )
        
        # Verify appropriate error message
        error_message = str(exc_info.value).lower()
        assert any(phrase in error_message for phrase in [
            "insufficient trading history", "trading history", "relationship"
        ]), f"Expected trading history error, got: {exc_info.value}"
    
    @given(
        low_credit_score=st.decimals(
            min_value=Decimal('0.0'),
            max_value=MIN_CREDIT_SCORE - Decimal('0.01'),
            places=2
        ),
        transaction=credit_eligible_transaction_strategy()
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_low_credit_score_rejection(
        self,
        low_credit_score,
        transaction,
        payment_service,
        mock_db
    ):
        """
        Test that credit terms are rejected for low credit scores.
        """
        # Setup mocks
        mock_db.payment_transactions.find_one.return_value = transaction.model_dump()
        
        # Mock sufficient history but low credit score
        payment_service._get_trading_relationship_duration = AsyncMock(
            return_value=6  # Sufficient months
        )
        payment_service._calculate_credit_score = AsyncMock(
            return_value=float(low_credit_score)
        )
        
        # Attempt to create credit terms - should fail
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_credit_terms(
                transaction_id=transaction.transaction_id,
                credit_period_days=60,
                installment_count=2
            )
        
        # Verify appropriate error message
        error_message = str(exc_info.value).lower()
        assert any(phrase in error_message for phrase in [
            "credit score too low", "credit score", "insufficient credit"
        ]), f"Expected credit score error, got: {exc_info.value}"
    
    @given(
        credit_params=credit_parameters_strategy()
    )
    @settings(max_examples=20, deadline=1000)
    def test_payment_schedule_generation_properties(self, credit_params):
        """
        Test properties of payment schedule generation algorithm.
        """
        service = PaymentService()
        
        total_amount = Decimal("30000.00")
        
        schedule = service._generate_payment_schedule(
            total_amount=total_amount,
            installment_count=credit_params["installment_count"],
            credit_period_days=credit_params["credit_period_days"],
            interest_rate=credit_params["interest_rate"]
        )
        
        # Verify schedule structure
        assert len(schedule) == credit_params["installment_count"]
        
        # Verify installment numbering
        for i, payment in enumerate(schedule):
            assert payment["installment_number"] == i + 1
            assert payment["status"] == "pending"
            assert isinstance(payment["due_date"], datetime)
            assert payment["due_date"] > datetime.utcnow()
        
        # Verify chronological ordering
        for i in range(1, len(schedule)):
            assert schedule[i]["due_date"] > schedule[i-1]["due_date"]
        
        # Verify total amount calculation
        total_scheduled = sum(Decimal(str(payment["amount"])) for payment in schedule)
        
        if credit_params["interest_rate"]:
            # With interest, total should be higher than original amount
            assert total_scheduled > total_amount
            
            # Calculate expected interest
            expected_interest = (
                total_amount * 
                credit_params["interest_rate"] * 
                credit_params["credit_period_days"]
            ) / (Decimal('100') * Decimal('365'))
            expected_total = total_amount + expected_interest
            
            # Allow small rounding differences
            assert abs(total_scheduled - expected_total) < Decimal('1.00')
        else:
            # Without interest, total should equal original amount
            assert abs(total_scheduled - total_amount) < Decimal('1.00')
        
        # Verify all amounts are positive
        for payment in schedule:
            assert Decimal(str(payment["amount"])) > Decimal('0')
        
        # Verify payment distribution is reasonable
        min_payment = min(Decimal(str(payment["amount"])) for payment in schedule)
        max_payment = max(Decimal(str(payment["amount"])) for payment in schedule)
        
        # No payment should be more than 3x another payment (reasonable distribution)
        if min_payment > Decimal('0'):
            assert max_payment / min_payment <= 3
    
    @given(
        amounts=st.lists(
            credit_eligible_amount_strategy(),
            min_size=1,
            max_size=5
        ),
        installment_counts=st.lists(
            st.integers(min_value=2, max_value=12),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=10, deadline=1000)
    def test_credit_amount_distribution_properties(self, amounts, installment_counts):
        """
        Test properties of credit amount distribution across installments.
        """
        service = PaymentService()
        
        for amount in amounts:
            for installment_count in installment_counts:
                # Generate schedule without interest for simplicity
                schedule = service._generate_payment_schedule(
                    total_amount=amount,
                    installment_count=installment_count,
                    credit_period_days=90,
                    interest_rate=None
                )
                
                # Verify total amount conservation
                total_scheduled = sum(Decimal(str(payment["amount"])) for payment in schedule)
                assert abs(total_scheduled - amount) < Decimal('0.01')
                
                # Verify reasonable distribution
                avg_payment = amount / installment_count
                for payment in schedule:
                    payment_amount = Decimal(str(payment["amount"]))
                    # Each payment should be within reasonable range of average
                    assert payment_amount >= avg_payment * Decimal('0.5')
                    assert payment_amount <= avg_payment * Decimal('1.5')
                
                # Verify precision
                for payment in schedule:
                    payment_amount = Decimal(str(payment["amount"]))
                    assert payment_amount.as_tuple().exponent >= -2  # At most 2 decimal places


if __name__ == "__main__":
    pytest.main([__file__, "-v"])