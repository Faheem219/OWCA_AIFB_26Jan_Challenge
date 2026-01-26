"""
Basic payment system tests that don't require database setup.
Tests payment method validation and core functionality.
"""

import pytest
from decimal import Decimal

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


@pytest.mark.asyncio
async def test_upi_payment_validation():
    """Test UPI payment method validation."""
    service = PaymentService()
    
    # Valid UPI details
    upi_details = UPIDetails(upi_id="test@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    validation = await service.validate_payment_method(payment_details)
    
    assert validation.is_valid is True
    assert validation.method == PaymentMethod.UPI
    assert len(validation.validation_errors) == 0
    assert "instant_transfer" in validation.supported_features


@pytest.mark.asyncio
async def test_invalid_upi_validation():
    """Test invalid UPI ID validation."""
    service = PaymentService()
    
    # Test with a UPI ID that passes Pydantic validation but fails business logic
    # Use a valid format but unsupported domain
    upi_details = UPIDetails(upi_id="test@unsupporteddomain")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    validation = await service.validate_payment_method(payment_details)
    
    assert validation.is_valid is False
    assert len(validation.validation_errors) > 0
    assert "may not be supported" in validation.validation_errors[0]


@pytest.mark.asyncio
async def test_digital_wallet_validation():
    """Test digital wallet payment validation."""
    service = PaymentService()
    
    wallet_details = DigitalWalletDetails(
        provider=DigitalWalletProvider.PAYTM,
        wallet_id="test_wallet_123"
    )
    payment_details = PaymentDetails(
        method=PaymentMethod.DIGITAL_WALLET,
        wallet_details=wallet_details
    )
    
    validation = await service.validate_payment_method(payment_details)
    
    assert validation.is_valid is True
    assert validation.method == PaymentMethod.DIGITAL_WALLET
    assert len(validation.validation_errors) == 0
    assert "instant_transfer" in validation.supported_features


@pytest.mark.asyncio
async def test_card_payment_validation():
    """Test card payment validation."""
    service = PaymentService()
    
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
    
    validation = await service.validate_payment_method(payment_details)
    
    assert validation.is_valid is True
    assert validation.method == PaymentMethod.CARD
    assert len(validation.validation_errors) == 0
    assert "emi" in validation.supported_features


@pytest.mark.asyncio
async def test_unsupported_card_network():
    """Test validation with unsupported card network."""
    service = PaymentService()
    
    card_details = CardDetails(
        card_type=CardType.CREDIT,
        last_four_digits="5678",
        card_network="unknown_network",
        bank_name="Test Bank"
    )
    payment_details = PaymentDetails(
        method=PaymentMethod.CARD,
        card_details=card_details
    )
    
    validation = await service.validate_payment_method(payment_details)
    
    assert validation.is_valid is False
    assert len(validation.validation_errors) > 0
    assert "Unsupported card network" in validation.validation_errors[0]


@pytest.mark.asyncio
async def test_get_supported_payment_methods():
    """Test getting supported payment methods."""
    service = PaymentService()
    
    methods = await service.get_supported_payment_methods()
    
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
async def test_missing_payment_details():
    """Test validation when payment method details are missing."""
    service = PaymentService()
    
    # Create a valid payment details object but test service-level validation
    # Test bank transfer method with missing bank details
    payment_details = PaymentDetails(
        method=PaymentMethod.BANK_TRANSFER,
        bank_details=None
    )
    
    validation = await service.validate_payment_method(payment_details)
    
    assert validation.is_valid is False
    assert "Bank transfer details are required" in validation.validation_errors


@pytest.mark.asyncio
async def test_pydantic_validation_errors():
    """Test that Pydantic validation catches invalid data at model level."""
    from pydantic_core import ValidationError
    
    # Test invalid UPI ID format (should be caught by Pydantic)
    with pytest.raises(ValidationError):
        UPIDetails(upi_id="invalid_format_no_at_symbol")
    
    # Test that valid UPI format works
    valid_upi = UPIDetails(upi_id="test@paytm")
    assert valid_upi.upi_id == "test@paytm"


@pytest.mark.asyncio
async def test_wallet_provider_validation():
    """Test digital wallet provider validation."""
    service = PaymentService()
    
    # Valid providers
    valid_providers = [
        DigitalWalletProvider.PAYTM,
        DigitalWalletProvider.PHONEPE,
        DigitalWalletProvider.GOOGLE_PAY,
        DigitalWalletProvider.AMAZON_PAY,
        DigitalWalletProvider.MOBIKWIK,
        DigitalWalletProvider.FREECHARGE
    ]
    
    for provider in valid_providers:
        wallet_details = DigitalWalletDetails(
            provider=provider,
            wallet_id=f"test_{provider}_123"
        )
        payment_details = PaymentDetails(
            method=PaymentMethod.DIGITAL_WALLET,
            wallet_details=wallet_details
        )
        
        validation = await service.validate_payment_method(payment_details)
        assert validation.is_valid is True, f"Provider {provider} should be valid"


@pytest.mark.asyncio
async def test_supported_card_networks():
    """Test supported card networks validation."""
    service = PaymentService()
    
    supported_networks = ['visa', 'mastercard', 'rupay', 'amex']
    
    for network in supported_networks:
        card_details = CardDetails(
            card_type=CardType.DEBIT,
            last_four_digits="1234",
            card_network=network,
            bank_name="Test Bank"
        )
        payment_details = PaymentDetails(
            method=PaymentMethod.CARD,
            card_details=card_details
        )
        
        validation = await service.validate_payment_method(payment_details)
        assert validation.is_valid is True, f"Card network {network} should be supported"


if __name__ == "__main__":
    pytest.main([__file__])