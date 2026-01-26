"""
Integration tests for payment system functionality.
Tests payment method validation, transaction creation, and processing.
"""

import pytest
from decimal import Decimal
from datetime import datetime
import pytest_asyncio

from app.models.payment import (
    PaymentDetails,
    PaymentMethod,
    UPIDetails,
    DigitalWalletDetails,
    DigitalWalletProvider,
    CardDetails,
    CardType
)
from app.services.payment_service import PaymentService


@pytest_asyncio.fixture
async def payment_service():
    """Create payment service instance."""
    service = PaymentService()
    await service.initialize()
    return service


@pytest.mark.asyncio
async def test_upi_payment_validation(payment_service):
    """Test UPI payment method validation."""
    # Valid UPI details
    upi_details = UPIDetails(upi_id="test@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    validation = await payment_service.validate_payment_method(payment_details)
    
    assert validation.is_valid is True
    assert validation.method == PaymentMethod.UPI
    assert len(validation.validation_errors) == 0
    assert "instant_transfer" in validation.supported_features


@pytest.mark.asyncio
async def test_invalid_upi_validation(payment_service):
    """Test invalid UPI ID validation."""
    # Invalid UPI ID (missing @)
    upi_details = UPIDetails(upi_id="testpaytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    validation = await payment_service.validate_payment_method(payment_details)
    
    assert validation.is_valid is False
    assert len(validation.validation_errors) > 0
    assert "Invalid UPI ID format" in validation.validation_errors


@pytest.mark.asyncio
async def test_digital_wallet_validation(payment_service):
    """Test digital wallet payment validation."""
    wallet_details = DigitalWalletDetails(
        provider=DigitalWalletProvider.PAYTM,
        wallet_id="test_wallet_123"
    )
    payment_details = PaymentDetails(
        method=PaymentMethod.DIGITAL_WALLET,
        wallet_details=wallet_details
    )
    
    validation = await payment_service.validate_payment_method(payment_details)
    
    assert validation.is_valid is True
    assert validation.method == PaymentMethod.DIGITAL_WALLET
    assert len(validation.validation_errors) == 0
    assert "instant_transfer" in validation.supported_features


@pytest.mark.asyncio
async def test_card_payment_validation(payment_service):
    """Test card payment validation."""
    card_details = CardDetails(
        card_type=CardType.DEBIT,
        last_four_digits="1234",
        card_network="visa",
        bank_name="Test Bank"
    )
    payment_details = PaymentDetails(
        method=PaymentMethod.CARD,
        card_details=card_details
    )
    
    validation = await payment_service.validate_payment_method(payment_details)
    
    assert validation.is_valid is True
    assert validation.method == PaymentMethod.CARD
    assert len(validation.validation_errors) == 0
    assert "emi" in validation.supported_features


@pytest.mark.asyncio
async def test_create_payment_transaction(payment_service):
    """Test creating a payment transaction."""
    upi_details = UPIDetails(upi_id="buyer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_123",
        buyer_id="buyer_123",
        vendor_id="vendor_123",
        amount=Decimal("1000.00"),
        payment_details=payment_details,
        description={"en": "Test payment for agricultural products"}
    )
    
    assert transaction.transaction_id.startswith("TXN_")
    assert transaction.order_id == "ORDER_123"
    assert transaction.buyer_id == "buyer_123"
    assert transaction.vendor_id == "vendor_123"
    assert transaction.amount == Decimal("1000.00")
    assert transaction.payment_details.method == PaymentMethod.UPI
    assert transaction.status == "pending"
    assert len(transaction.status_history) == 1


@pytest.mark.asyncio
async def test_process_upi_payment(payment_service):
    """Test processing UPI payment."""
    # Create transaction first
    upi_details = UPIDetails(upi_id="buyer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_UPI_123",
        buyer_id="buyer_123",
        vendor_id="vendor_123",
        amount=Decimal("500.00"),
        payment_details=payment_details
    )
    
    # Process the payment
    success, gateway_response = await payment_service.process_payment(
        transaction.transaction_id
    )
    
    assert success is True
    assert "gateway_transaction_id" in gateway_response
    assert gateway_response["status"] == "success"
    assert gateway_response["method"] == "upi"
    assert gateway_response["amount"] == 500.0


@pytest.mark.asyncio
async def test_process_wallet_payment(payment_service):
    """Test processing digital wallet payment."""
    wallet_details = DigitalWalletDetails(
        provider=DigitalWalletProvider.PHONEPE,
        wallet_id="phonepe_wallet_123"
    )
    payment_details = PaymentDetails(
        method=PaymentMethod.DIGITAL_WALLET,
        wallet_details=wallet_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_WALLET_123",
        buyer_id="buyer_123",
        vendor_id="vendor_123",
        amount=Decimal("750.00"),
        payment_details=payment_details
    )
    
    success, gateway_response = await payment_service.process_payment(
        transaction.transaction_id
    )
    
    assert success is True
    assert gateway_response["provider"] == "phonepe"
    assert gateway_response["status"] == "success"
    assert gateway_response["amount"] == 750.0


@pytest.mark.asyncio
async def test_generate_multilingual_invoice(payment_service):
    """Test generating multilingual invoice."""
    # Create and process a transaction first
    upi_details = UPIDetails(upi_id="buyer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_INVOICE_123",
        buyer_id="buyer_123",
        vendor_id="vendor_123",
        amount=Decimal("1200.00"),
        payment_details=payment_details
    )
    
    # Process payment to completion
    await payment_service.process_payment(transaction.transaction_id)
    
    # Generate invoice
    invoice = await payment_service.generate_multilingual_invoice(
        transaction_id=transaction.transaction_id,
        buyer_language="hi",
        vendor_language="en"
    )
    
    assert invoice.invoice_id.startswith("INV_")
    assert invoice.transaction_id == transaction.transaction_id
    assert invoice.order_id == "ORDER_INVOICE_123"
    assert invoice.total_amount == Decimal("1200.00")
    assert invoice.currency == "INR"
    
    # Check multilingual content
    assert "en" in invoice.invoice_content
    assert "hi" in invoice.invoice_content
    assert "title" in invoice.invoice_content["en"]
    assert "title" in invoice.invoice_content["hi"]


@pytest.mark.asyncio
async def test_get_supported_payment_methods(payment_service):
    """Test getting supported payment methods."""
    methods = await payment_service.get_supported_payment_methods()
    
    assert len(methods) > 0
    
    # Check UPI method
    upi_method = next((m for m in methods if m["method"] == PaymentMethod.UPI), None)
    assert upi_method is not None
    assert "instant_transfer" in upi_method["features"]
    assert "paytm" in upi_method["supported_providers"]
    
    # Check digital wallet method
    wallet_method = next((m for m in methods if m["method"] == PaymentMethod.DIGITAL_WALLET), None)
    assert wallet_method is not None
    assert "phonepe" in wallet_method["supported_providers"]
    
    # Check card method
    card_method = next((m for m in methods if m["method"] == PaymentMethod.CARD), None)
    assert card_method is not None
    assert "visa" in card_method["supported_networks"]


@pytest.mark.asyncio
async def test_create_escrow_transaction(payment_service):
    """Test creating escrow transaction for high-value payments."""
    # Create a high-value transaction
    upi_details = UPIDetails(upi_id="buyer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    transaction = await payment_service.create_payment_transaction(
        order_id="ORDER_ESCROW_123",
        buyer_id="buyer_123",
        vendor_id="vendor_123",
        amount=Decimal("50000.00"),  # High value
        payment_details=payment_details,
        is_escrow=True
    )
    
    # Create escrow transaction
    release_conditions = {
        "delivery_confirmation": True,
        "quality_inspection": True,
        "dispute_period_days": 7
    }
    
    escrow = await payment_service.create_escrow_transaction(
        transaction_id=transaction.transaction_id,
        release_conditions=release_conditions
    )
    
    assert escrow.escrow_id.startswith("ESC_")
    assert escrow.transaction_id == transaction.transaction_id
    assert escrow.buyer_id == "buyer_123"
    assert escrow.vendor_id == "vendor_123"
    assert escrow.amount == Decimal("50000.00")
    assert escrow.remaining_amount == Decimal("50000.00")
    assert escrow.release_conditions == release_conditions
    assert escrow.status == "active"


if __name__ == "__main__":
    pytest.main([__file__])