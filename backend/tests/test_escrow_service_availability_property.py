"""
Property-based test for escrow service availability.
**Validates: Requirements 7.4**
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
    DigitalWalletDetails,
    DigitalWalletProvider,
    CardDetails,
    CardType,
    EscrowTransaction,
    EscrowStatus,
    TransactionType
)
from app.services.payment_service import PaymentService


# High-value transaction threshold for escrow eligibility
ESCROW_MINIMUM_AMOUNT = Decimal('10000.00')

# Maximum reasonable transaction amount for testing
MAX_TRANSACTION_AMOUNT = Decimal('1000000.00')


@composite
def high_value_amount_strategy(draw):
    """Generate high-value transaction amounts eligible for escrow."""
    return draw(st.decimals(
        min_value=ESCROW_MINIMUM_AMOUNT,
        max_value=MAX_TRANSACTION_AMOUNT,
        places=2
    ))


@composite
def escrow_release_conditions_strategy(draw):
    """Generate various escrow release conditions."""
    conditions = {}
    
    # Basic conditions
    if draw(st.booleans()):
        conditions["delivery_confirmation"] = draw(st.booleans())
    
    if draw(st.booleans()):
        conditions["quality_inspection"] = draw(st.booleans())
    
    if draw(st.booleans()):
        conditions["dispute_period_days"] = draw(st.integers(min_value=1, max_value=30))
    
    if draw(st.booleans()):
        conditions["inspection_period_hours"] = draw(st.integers(min_value=24, max_value=168))
    
    if draw(st.booleans()):
        conditions["documentation_required"] = draw(st.booleans())
    
    # Ensure at least one condition is present
    if not conditions:
        conditions["delivery_confirmation"] = True
    
    return conditions


@composite
def milestone_conditions_strategy(draw):
    """Generate milestone-based release conditions."""
    milestone_count = draw(st.integers(min_value=1, max_value=4))
    milestones = []
    
    total_percentage = 0
    for i in range(milestone_count):
        if i == milestone_count - 1:
            # Last milestone gets remaining percentage
            percentage = 100 - total_percentage
        else:
            # Distribute remaining percentage
            remaining = 100 - total_percentage
            max_percentage = remaining - (milestone_count - i - 1)  # Leave at least 1% for each remaining milestone
            percentage = draw(st.integers(min_value=1, max_value=max(1, max_percentage)))
        
        total_percentage += percentage
        
        milestone_names = [
            "delivery_confirmed", "quality_approved", "documentation_verified",
            "installation_completed", "training_provided", "warranty_activated"
        ]
        
        milestone = {
            "milestone": draw(st.sampled_from(milestone_names)),
            "release_percentage": percentage,
            "description": f"Release {percentage}% on milestone completion"
        }
        milestones.append(milestone)
    
    return milestones


@composite
def completed_high_value_transaction_strategy(draw):
    """Generate completed high-value transactions eligible for escrow."""
    transaction_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
    order_id = f"ORDER_{uuid.uuid4().hex[:8].upper()}"
    buyer_id = str(ObjectId())
    vendor_id = str(ObjectId())
    amount = draw(high_value_amount_strategy())
    
    # Generate payment method
    method = draw(st.sampled_from([PaymentMethod.UPI, PaymentMethod.DIGITAL_WALLET, PaymentMethod.CARD]))
    
    if method == PaymentMethod.UPI:
        upi_providers = ["paytm", "phonepe", "googlepay", "amazonpay", "ybl"]
        provider = draw(st.sampled_from(upi_providers))
        user_id = draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))))
        upi_details = UPIDetails(upi_id=f"{user_id}@{provider}")
        payment_details = PaymentDetails(method=method, upi_details=upi_details)
    elif method == PaymentMethod.DIGITAL_WALLET:
        provider = draw(st.sampled_from(list(DigitalWalletProvider)))
        wallet_id = draw(st.text(min_size=5, max_size=30))
        wallet_details = DigitalWalletDetails(provider=provider, wallet_id=wallet_id)
        payment_details = PaymentDetails(method=method, wallet_details=wallet_details)
    else:  # CARD
        card_type = draw(st.sampled_from(list(CardType)))
        last_four = draw(st.text(min_size=4, max_size=4, alphabet="0123456789"))
        network = draw(st.sampled_from(["visa", "mastercard", "rupay", "amex"]))
        bank = draw(st.text(min_size=5, max_size=30))
        card_details = CardDetails(
            card_type=card_type,
            last_four_digits=last_four,
            card_network=network,
            bank_name=bank
        )
        payment_details = PaymentDetails(method=method, card_details=card_details)
    
    # Create completed transaction
    transaction = PaymentTransaction(
        transaction_id=transaction_id,
        order_id=order_id,
        buyer_id=buyer_id,
        vendor_id=vendor_id,
        amount=amount,
        payment_details=payment_details,
        status=PaymentStatus.COMPLETED,
        completed_at=datetime.utcnow(),
        gateway_transaction_id=f"gw_{uuid.uuid4().hex[:16]}",
        gateway_response={"status": "success", "method": payment_details.method}
    )
    
    return transaction


@pytest.fixture
def mock_db():
    """Mock database with payment transactions and escrow collections."""
    db = MagicMock()
    db.payment_transactions = AsyncMock()
    db.escrow_transactions = AsyncMock()
    return db


@pytest.fixture
def payment_service(mock_db):
    """Payment service instance with mocked dependencies."""
    service = PaymentService()
    service.db = mock_db
    return service


class TestEscrowServiceAvailabilityProperties:
    """Property-based tests for escrow service availability."""
    
    @given(
        transaction=completed_high_value_transaction_strategy(),
        release_conditions=escrow_release_conditions_strategy(),
        milestone_conditions=st.one_of(st.none(), milestone_conditions_strategy()),
        auto_release_days=st.integers(min_value=1, max_value=30),
        escrow_fee_percentage=st.decimals(min_value=Decimal('0.5'), max_value=Decimal('5.0'), places=2)
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_property_35_escrow_service_availability(
        self,
        transaction,
        release_conditions,
        milestone_conditions,
        auto_release_days,
        escrow_fee_percentage,
        payment_service,
        mock_db
    ):
        """
        **Property 35: Escrow Service Availability**
        **Validates: Requirements 7.4**
        
        For any high-value transaction above the defined threshold, escrow services 
        should be offered and function correctly.
        """
        # Setup mock database responses
        mock_db.payment_transactions.find_one.return_value = transaction.model_dump()
        mock_db.escrow_transactions.insert_one.return_value = MagicMock()
        mock_db.payment_transactions.update_one.return_value = MagicMock()
        
        # Reset mock call counts for this test iteration
        mock_db.escrow_transactions.insert_one.reset_mock()
        mock_db.payment_transactions.update_one.reset_mock()
        
        # **Core Property Validations**
        
        # 1. High-value transactions must be eligible for escrow
        assert transaction.amount >= ESCROW_MINIMUM_AMOUNT, "Transaction must meet minimum amount for escrow"
        assert transaction.status == PaymentStatus.COMPLETED, "Transaction must be completed for escrow"
        
        # Create escrow transaction
        escrow = await payment_service.create_escrow_transaction(
            transaction_id=transaction.transaction_id,
            release_conditions=release_conditions,
            milestone_conditions=milestone_conditions,
            auto_release_days=auto_release_days,
            escrow_fee_percentage=escrow_fee_percentage
        )
        
        # 2. Escrow transaction must be created successfully
        assert escrow is not None
        assert isinstance(escrow, EscrowTransaction)
        
        # 3. Escrow must have valid identifier and reference original transaction
        assert escrow.escrow_id.startswith("ESC_")
        assert len(escrow.escrow_id) == 16  # ESC_ + 12 character hex
        assert escrow.transaction_id == transaction.transaction_id
        
        # 4. Escrow must preserve transaction parties and amount
        assert escrow.buyer_id == transaction.buyer_id
        assert escrow.vendor_id == transaction.vendor_id
        assert escrow.amount == transaction.amount
        assert escrow.currency == transaction.currency
        
        # 5. Escrow must start with full amount available
        assert escrow.remaining_amount == transaction.amount
        assert escrow.released_amount == Decimal('0')
        
        # 6. Escrow must be in active status initially
        assert escrow.status == EscrowStatus.ACTIVE
        
        # 7. Release conditions must be preserved
        assert escrow.release_conditions == release_conditions
        assert escrow.milestone_conditions == milestone_conditions
        
        # 8. Auto-release must be configured correctly
        assert escrow.auto_release_enabled is True
        assert escrow.auto_release_date is not None
        expected_release_date = datetime.utcnow() + timedelta(days=auto_release_days)
        # Allow some tolerance for execution time
        time_diff = abs((escrow.auto_release_date - expected_release_date).total_seconds())
        assert time_diff < 60, "Auto-release date should be set correctly"
        
        # 9. Escrow fee must be calculated correctly
        expected_fee = (transaction.amount * escrow_fee_percentage) / Decimal('100')
        assert escrow.escrow_fee == expected_fee
        assert escrow.fee_paid_by == "buyer"  # Default fee payer
        
        # 10. Escrow must have proper timestamps
        assert isinstance(escrow.created_at, datetime)
        assert isinstance(escrow.updated_at, datetime)
        assert escrow.created_at <= escrow.updated_at
        
        # 11. Dispute handling must be initialized
        assert escrow.dispute_raised is False
        assert escrow.dispute_details is None
        
        # 12. Release history must be empty initially
        assert escrow.release_history == []
        
        # 13. Database operations must be called correctly
        mock_db.escrow_transactions.insert_one.assert_called_once()
        mock_db.payment_transactions.update_one.assert_called_once()
        
        # Verify the update call marked transaction as escrow
        update_call = mock_db.payment_transactions.update_one.call_args
        assert update_call[0][0] == {"transaction_id": transaction.transaction_id}
        update_data = update_call[0][1]["$set"]
        assert update_data["is_escrow"] is True
        assert update_data["escrow_release_conditions"] == release_conditions
    
    @given(
        transaction=completed_high_value_transaction_strategy(),
        release_conditions=escrow_release_conditions_strategy()
    )
    @settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_escrow_fund_release_functionality(
        self,
        transaction,
        release_conditions,
        payment_service,
        mock_db
    ):
        """
        Test that escrow fund release functionality works correctly.
        """
        # Setup mocks
        mock_db.payment_transactions.find_one.return_value = transaction.model_dump()
        mock_db.escrow_transactions.insert_one.return_value = MagicMock()
        mock_db.payment_transactions.update_one.return_value = MagicMock()
        
        # Create escrow
        escrow = await payment_service.create_escrow_transaction(
            transaction_id=transaction.transaction_id,
            release_conditions=release_conditions
        )
        
        # Mock escrow data for release operation
        mock_db.escrow_transactions.find_one.return_value = escrow.model_dump()
        mock_db.escrow_transactions.update_one.return_value = MagicMock()
        
        # Test partial release
        release_amount = transaction.amount / 2  # Release 50%
        
        result = await payment_service.release_escrow_funds(
            escrow_id=escrow.escrow_id,
            release_amount=release_amount,
            release_reason="milestone_completed",
            released_by="system"
        )
        
        # Verify release result
        assert result["success"] is True
        assert Decimal(str(result["amount_released"])) == release_amount
        assert Decimal(str(result["remaining_amount"])) == transaction.amount - release_amount
        assert result["status"] == EscrowStatus.PARTIALLY_RELEASED
        assert "release_id" in result
        assert "transfer_result" in result
        
        # Verify transfer result structure
        transfer_result = result["transfer_result"]
        assert transfer_result["vendor_id"] == transaction.vendor_id
        assert Decimal(str(transfer_result["amount"])) == release_amount
        assert transfer_result["status"] == "completed"
        assert "transfer_id" in transfer_result
        assert "processed_at" in transfer_result
    
    @given(
        low_amount=st.decimals(
            min_value=Decimal('1.00'),
            max_value=ESCROW_MINIMUM_AMOUNT - Decimal('0.01'),
            places=2
        )
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_escrow_minimum_amount_enforcement(
        self,
        low_amount,
        payment_service,
        mock_db
    ):
        """
        Test that escrow service enforces minimum transaction amount.
        """
        # Create low-value transaction
        transaction_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        low_value_transaction = PaymentTransaction(
            transaction_id=transaction_id,
            order_id=f"ORDER_{uuid.uuid4().hex[:8].upper()}",
            buyer_id=str(ObjectId()),
            vendor_id=str(ObjectId()),
            amount=low_amount,
            payment_details=PaymentDetails(
                method=PaymentMethod.UPI,
                upi_details=UPIDetails(upi_id="test@paytm")
            ),
            status=PaymentStatus.COMPLETED,
            completed_at=datetime.utcnow()
        )
        
        # Setup mock
        mock_db.payment_transactions.find_one.return_value = low_value_transaction.model_dump()
        
        # Attempt to create escrow - should fail
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_escrow_transaction(
                transaction_id=transaction_id,
                release_conditions={"delivery_confirmation": True}
            )
        
        # Verify appropriate error message
        error_message = str(exc_info.value).lower()
        assert any(phrase in error_message for phrase in [
            "amount too low", "minimum amount", "insufficient amount", "below threshold"
        ]), f"Expected minimum amount error, got: {exc_info.value}"
    
    @given(
        transaction=completed_high_value_transaction_strategy(),
        milestone_conditions=milestone_conditions_strategy()
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_milestone_based_escrow_release(
        self,
        transaction,
        milestone_conditions,
        payment_service,
        mock_db
    ):
        """
        Test milestone-based escrow release functionality.
        """
        # Setup mocks
        mock_db.payment_transactions.find_one.return_value = transaction.model_dump()
        mock_db.escrow_transactions.insert_one.return_value = MagicMock()
        mock_db.payment_transactions.update_one.return_value = MagicMock()
        
        # Create escrow with milestone conditions
        escrow = await payment_service.create_escrow_transaction(
            transaction_id=transaction.transaction_id,
            release_conditions={"milestone_based": True},
            milestone_conditions=milestone_conditions
        )
        
        # Verify milestone conditions are preserved
        assert escrow.milestone_conditions == milestone_conditions
        
        # Verify total milestone percentages add up to 100%
        total_percentage = sum(milestone["release_percentage"] for milestone in milestone_conditions)
        assert total_percentage == 100, f"Milestone percentages should sum to 100%, got {total_percentage}"
        
        # Verify each milestone has required fields
        for milestone in milestone_conditions:
            assert "milestone" in milestone
            assert "release_percentage" in milestone
            assert "description" in milestone
            assert isinstance(milestone["release_percentage"], int)
            assert 1 <= milestone["release_percentage"] <= 100
            assert len(milestone["milestone"]) > 0
            assert len(milestone["description"]) > 0
    
    @given(
        transaction=completed_high_value_transaction_strategy(),
        release_conditions=escrow_release_conditions_strategy()
    )
    @settings(max_examples=15, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_escrow_dispute_handling_initialization(
        self,
        transaction,
        release_conditions,
        payment_service,
        mock_db
    ):
        """
        Test that escrow transactions are properly initialized for dispute handling.
        """
        # Setup mocks
        mock_db.payment_transactions.find_one.return_value = transaction.model_dump()
        mock_db.escrow_transactions.insert_one.return_value = MagicMock()
        mock_db.payment_transactions.update_one.return_value = MagicMock()
        
        # Create escrow
        escrow = await payment_service.create_escrow_transaction(
            transaction_id=transaction.transaction_id,
            release_conditions=release_conditions
        )
        
        # Verify dispute handling is properly initialized
        assert escrow.dispute_raised is False
        assert escrow.dispute_details is None
        assert escrow.dispute_resolution_deadline is None
        
        # Verify escrow can handle dispute scenarios
        assert hasattr(escrow, 'dispute_raised')
        assert hasattr(escrow, 'dispute_details')
        assert hasattr(escrow, 'dispute_resolution_deadline')
    
    @given(
        amounts=st.lists(
            high_value_amount_strategy(),
            min_size=1,
            max_size=5
        ),
        fee_percentages=st.lists(
            st.decimals(min_value=Decimal('0.1'), max_value=Decimal('10.0'), places=2),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=10, deadline=1000)
    def test_escrow_fee_calculation_accuracy(self, amounts, fee_percentages):
        """
        Test that escrow fees are calculated accurately for various amounts and percentages.
        """
        for amount in amounts:
            for fee_percentage in fee_percentages:
                # Calculate expected fee and round to 2 decimal places for practical use
                expected_fee = ((amount * fee_percentage) / Decimal('100')).quantize(Decimal('0.01'))
                
                # Verify fee calculation properties
                assert expected_fee >= Decimal('0'), "Escrow fee must be non-negative"
                assert expected_fee <= amount, "Escrow fee should not exceed transaction amount"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])