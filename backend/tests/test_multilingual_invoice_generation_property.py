"""
Property-based test for multilingual invoice generation.
**Validates: Requirements 7.2**
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
    Invoice,
    TransactionType
)
from app.models.translation import TranslationRequest, TranslationResult
from app.services.payment_service import PaymentService
from app.services.translation_service import TranslationService


# Supported languages for the platform
SUPPORTED_LANGUAGES = [
    "hi", "en", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "or", "as", "ur"
]

# Sample invoice content in different languages for validation
INVOICE_TERMS = {
    "en": {
        "title": "Invoice",
        "buyer_section": "Buyer Information",
        "vendor_section": "Vendor Information",
        "payment_section": "Payment Details",
        "delivery_section": "Delivery Information",
        "footer": "Thank you for your business!",
        "terms_conditions": "Terms and conditions apply as per the platform agreement."
    },
    "hi": {
        "title": "चालान",
        "buyer_section": "खरीदार की जानकारी",
        "vendor_section": "विक्रेता की जानकारी",
        "payment_section": "भुगतान विवरण",
        "delivery_section": "डिलीवरी की जानकारी",
        "footer": "आपके व्यापार के लिए धन्यवाद!",
        "terms_conditions": "प्लेटफॉर्म समझौते के अनुसार नियम और शर्तें लागू होती हैं।"
    },
    "ta": {
        "title": "விலைப்பட்டியல்",
        "buyer_section": "வாங்குபவர் தகவல்",
        "vendor_section": "விற்பனையாளர் தகவல்",
        "payment_section": "பணம் செலுத்தும் விவரங்கள்",
        "delivery_section": "டெலிவரி தகவல்",
        "footer": "உங்கள் வணிகத்திற்கு நன்றி!",
        "terms_conditions": "தளத்தின் ஒப்பந்தத்தின்படி விதிமுறைகள் மற்றும் நிபந்தனைகள் பொருந்தும்."
    }
}

# Sample product descriptions in different languages
PRODUCT_DESCRIPTIONS = {
    "en": [
        "Premium quality rice",
        "Fresh organic vegetables",
        "Traditional spices",
        "Handmade crafts",
        "Agricultural equipment"
    ],
    "hi": [
        "प्रीमियम गुणवत्ता चावल",
        "ताजी जैविक सब्जियां",
        "पारंपरिक मसाले",
        "हस्तनिर्मित शिल्प",
        "कृषि उपकरण"
    ],
    "ta": [
        "உயர்தர அரிசி",
        "புதிய இயற்கை காய்கறிகள்",
        "பாரம்பரிய மசாலாப் பொருட்கள்",
        "கைவினைப் பொருட்கள்",
        "விவசாய உபकரணங்கள்"
    ]
}


@composite
def payment_method_strategy(draw):
    """Generate various payment method details."""
    method = draw(st.sampled_from(list(PaymentMethod)))
    
    if method == PaymentMethod.UPI:
        upi_providers = ["paytm", "phonepe", "googlepay", "amazonpay", "ybl"]
        provider = draw(st.sampled_from(upi_providers))
        user_id = draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))))
        upi_details = UPIDetails(upi_id=f"{user_id}@{provider}")
        return PaymentDetails(method=method, upi_details=upi_details)
    
    elif method == PaymentMethod.DIGITAL_WALLET:
        provider = draw(st.sampled_from(list(DigitalWalletProvider)))
        wallet_id = draw(st.text(min_size=5, max_size=30))
        wallet_details = DigitalWalletDetails(provider=provider, wallet_id=wallet_id)
        return PaymentDetails(method=method, wallet_details=wallet_details)
    
    elif method == PaymentMethod.CARD:
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
        return PaymentDetails(method=method, card_details=card_details)
    
    else:
        # For other methods, return basic payment details
        return PaymentDetails(method=method)


@composite
def transaction_amount_strategy(draw):
    """Generate realistic transaction amounts."""
    # Generate amounts from ₹10 to ₹100,000
    return draw(st.decimals(
        min_value=Decimal('10.00'),
        max_value=Decimal('100000.00'),
        places=2
    ))


@composite
def language_pair_strategy(draw):
    """Generate buyer and vendor language combinations."""
    buyer_lang = draw(st.sampled_from(SUPPORTED_LANGUAGES))
    vendor_lang = draw(st.sampled_from(SUPPORTED_LANGUAGES))
    return buyer_lang, vendor_lang


@composite
def completed_transaction_strategy(draw):
    """Generate completed payment transactions for invoice generation."""
    transaction_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
    order_id = f"ORDER_{uuid.uuid4().hex[:8].upper()}"
    buyer_id = str(ObjectId())
    vendor_id = str(ObjectId())
    amount = draw(transaction_amount_strategy())
    payment_details = draw(payment_method_strategy())
    
    # Generate multilingual description
    lang = draw(st.sampled_from(SUPPORTED_LANGUAGES))
    if lang in PRODUCT_DESCRIPTIONS:
        desc_text = draw(st.sampled_from(PRODUCT_DESCRIPTIONS[lang]))
    else:
        desc_text = draw(st.sampled_from(PRODUCT_DESCRIPTIONS["en"]))
    
    description = {lang: desc_text}
    
    # Create completed transaction
    transaction = PaymentTransaction(
        transaction_id=transaction_id,
        order_id=order_id,
        buyer_id=buyer_id,
        vendor_id=vendor_id,
        amount=amount,
        payment_details=payment_details,
        description=description,
        status=PaymentStatus.COMPLETED,
        completed_at=datetime.utcnow(),
        gateway_transaction_id=f"gw_{uuid.uuid4().hex[:16]}",
        gateway_response={"status": "success", "method": payment_details.method}
    )
    
    return transaction


@pytest.fixture
def mock_db():
    """Mock database with payment transactions and invoices collections."""
    db = MagicMock()
    db.payment_transactions = AsyncMock()
    db.invoices = AsyncMock()
    db.delivery_tracking = AsyncMock()
    return db


@pytest.fixture
def mock_translation_service():
    """Mock translation service for multilingual content."""
    service = MagicMock(spec=TranslationService)
    service.translate_text = AsyncMock()
    return service


@pytest.fixture
def payment_service(mock_db, mock_translation_service):
    """Payment service instance with mocked dependencies."""
    service = PaymentService()
    service.db = mock_db
    service.translation_service = mock_translation_service
    return service


class TestMultilingualInvoiceGenerationProperties:
    """Property-based tests for multilingual invoice generation."""
    
    @given(
        transaction=completed_transaction_strategy(),
        buyer_lang=st.sampled_from(SUPPORTED_LANGUAGES),
        vendor_lang=st.sampled_from(SUPPORTED_LANGUAGES)
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_property_33_multilingual_invoice_generation(
        self,
        transaction,
        buyer_lang,
        vendor_lang,
        payment_service,
        mock_db,
        mock_translation_service
    ):
        """
        **Property 33: Multilingual Invoice Generation**
        **Validates: Requirements 7.2**
        
        For any completed transaction, invoices should be generated in the user's 
        preferred language with accurate translation of all terms.
        """
        # Setup mock database responses
        mock_db.payment_transactions.find_one.return_value = transaction.model_dump()
        mock_db.invoices.insert_one.return_value = MagicMock()
        mock_db.delivery_tracking.find_one.return_value = None  # No delivery info by default
        
        # Setup mock translation responses
        def mock_translate(text, source_lang, target_lang):
            # Return appropriate translations based on language
            if target_lang in INVOICE_TERMS and text in INVOICE_TERMS["en"].values():
                # Find the key for this text in English terms
                for key, value in INVOICE_TERMS["en"].items():
                    if value == text:
                        translated_text = INVOICE_TERMS[target_lang].get(key, text)
                        break
                else:
                    translated_text = f"[{target_lang}] {text}"
            else:
                translated_text = f"[{target_lang}] {text}"
            
            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_lang,
                target_language=target_lang,
                confidence_score=0.85,
                provider="mock_translate",
                cached=False
            )
        
        mock_translation_service.translate_text.side_effect = mock_translate
        
        # Generate multilingual invoice
        invoice = await payment_service.generate_multilingual_invoice(
            transaction_id=transaction.transaction_id,
            buyer_language=buyer_lang,
            vendor_language=vendor_lang,
            include_delivery_info=True
        )
        
        # **Core Property Validations**
        
        # 1. Invoice must be generated successfully
        assert invoice is not None
        assert isinstance(invoice, Invoice)
        
        # 2. Invoice must contain correct transaction information
        assert invoice.transaction_id == transaction.transaction_id
        assert invoice.order_id == transaction.order_id
        assert invoice.total_amount == transaction.amount
        assert invoice.currency == transaction.currency
        
        # 3. Invoice must contain multilingual content
        assert isinstance(invoice.invoice_content, dict)
        assert len(invoice.invoice_content) > 0
        
        # 4. Invoice must include both buyer and vendor languages
        required_languages = set([buyer_lang, vendor_lang, "en"])  # Always include English
        for lang in required_languages:
            assert lang in invoice.invoice_content, f"Language {lang} missing from invoice content"
        
        # 5. Each language version must contain all required sections
        for lang, content in invoice.invoice_content.items():
            assert isinstance(content, dict), f"Content for {lang} must be a dictionary"
            
            # Required sections in every language version
            required_sections = [
                "title", "buyer_section", "vendor_section", 
                "payment_section", "footer", "terms_conditions"
            ]
            
            for section in required_sections:
                assert section in content, f"Section '{section}' missing in {lang} content"
                assert isinstance(content[section], str), f"Section '{section}' must be string in {lang}"
                assert len(content[section].strip()) > 0, f"Section '{section}' cannot be empty in {lang}"
        
        # 6. Transaction details must be consistent across all languages
        for lang, content in invoice.invoice_content.items():
            tx_details = content.get("transaction_details", {})
            assert tx_details.get("transaction_id") == transaction.transaction_id
            assert tx_details.get("order_id") == transaction.order_id
            assert tx_details.get("payment_method") == transaction.payment_details.method
            assert tx_details.get("amount") == float(transaction.amount)
            assert tx_details.get("currency") == transaction.currency
            assert tx_details.get("status") == transaction.status
        
        # 7. Invoice metadata must be correct
        assert invoice.invoice_id.startswith("INV_")
        assert len(invoice.invoice_id) == 16  # INV_ + 12 character hex
        assert invoice.subtotal == transaction.amount
        assert invoice.total_amount >= invoice.subtotal  # Total >= subtotal (taxes may be added)
        assert isinstance(invoice.invoice_date, datetime)
        
        # 8. Payment status must reflect transaction completion
        if transaction.status == PaymentStatus.COMPLETED:
            assert invoice.is_paid is True
            assert invoice.paid_at is not None
        
        # 9. Buyer and vendor information must be present
        assert isinstance(invoice.buyer_info, dict)
        assert isinstance(invoice.vendor_info, dict)
        assert "user_id" in invoice.buyer_info
        assert "user_id" in invoice.vendor_info
        assert invoice.buyer_info["user_id"] == transaction.buyer_id
        assert invoice.vendor_info["user_id"] == transaction.vendor_id
    
    @given(
        transaction=completed_transaction_strategy(),
        target_language=st.sampled_from(SUPPORTED_LANGUAGES)
    )
    @settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_invoice_content_translation_accuracy(
        self,
        transaction,
        target_language,
        payment_service,
        mock_db,
        mock_translation_service
    ):
        """
        Test that invoice content is accurately translated to target language.
        """
        # Setup mocks
        mock_db.payment_transactions.find_one.return_value = transaction.model_dump()
        mock_db.invoices.insert_one.return_value = MagicMock()
        mock_db.delivery_tracking.find_one.return_value = None  # No delivery info by default
        
        # Track translation calls
        translation_calls = []
        
        def mock_translate(text, source_lang, target_lang):
            translation_calls.append((text, source_lang, target_lang))
            return TranslationResult(
                original_text=text,
                translated_text=f"[{target_lang}] {text}",
                source_language=source_lang,
                target_language=target_lang,
                confidence_score=0.85,
                provider="mock_translate",
                cached=False
            )
        
        mock_translation_service.translate_text.side_effect = mock_translate
        
        # Generate invoice
        invoice = await payment_service.generate_multilingual_invoice(
            transaction_id=transaction.transaction_id,
            buyer_language=target_language,
            vendor_language="en"
        )
        
        # Verify translation service was called for non-English languages
        if target_language != "en":
            assert len(translation_calls) > 0, "Translation service should be called for non-English languages"
            
            # Verify all translation calls used correct target language
            for text, source, target in translation_calls:
                assert target == target_language, f"Translation target should be {target_language}, got {target}"
                assert source == "en", f"Translation source should be 'en', got {source}"
        
        # Verify target language content exists and is properly formatted
        assert target_language in invoice.invoice_content
        target_content = invoice.invoice_content[target_language]
        
        # Check that translated content has the expected format
        if target_language != "en":
            for key, value in target_content.items():
                if isinstance(value, str) and value.startswith(f"[{target_language}]"):
                    # This indicates our mock translation was applied
                    assert len(value) > len(f"[{target_language}] "), "Translated content should not be empty"
    
    @given(
        transaction=completed_transaction_strategy(),
        include_delivery=st.booleans()
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_invoice_delivery_information_handling(
        self,
        transaction,
        include_delivery,
        payment_service,
        mock_db,
        mock_translation_service
    ):
        """
        Test that delivery information is correctly included/excluded in invoices.
        """
        # Setup mocks
        mock_db.payment_transactions.find_one.return_value = transaction.model_dump()
        mock_db.invoices.insert_one.return_value = MagicMock()
        
        # Mock delivery tracking data
        if include_delivery:
            from app.models.payment import DeliveryTracking, DeliveryAddress, DeliveryMethod, DeliveryStatus
            
            delivery_data = {
                "tracking_id": f"TRK_{uuid.uuid4().hex[:8].upper()}",
                "transaction_id": transaction.transaction_id,
                "order_id": transaction.order_id,
                "delivery_method": DeliveryMethod.VENDOR_DELIVERY,
                "delivery_status": DeliveryStatus.DELIVERED,
                "pickup_address": {
                    "name": "Test Vendor",
                    "phone": "+91-9876543210",
                    "address_line1": "123 Vendor Street",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "postal_code": "400001"
                },
                "delivery_address": {
                    "name": "Test Buyer",
                    "phone": "+91-9876543211",
                    "address_line1": "456 Buyer Avenue",
                    "city": "Delhi",
                    "state": "Delhi",
                    "postal_code": "110001"
                },
                "estimated_delivery_time": datetime.utcnow() + timedelta(days=2),
                "actual_delivery_time": datetime.utcnow() + timedelta(days=1)
            }
            mock_db.delivery_tracking.find_one.return_value = delivery_data
        else:
            mock_db.delivery_tracking.find_one.return_value = None
        
        # Mock translation
        mock_translation_service.translate_text.return_value = TranslationResult(
            original_text="test",
            translated_text="test_translated",
            source_language="en",
            target_language="hi",
            confidence_score=0.85,
            provider="mock",
            cached=False
        )
        
        # Generate invoice
        invoice = await payment_service.generate_multilingual_invoice(
            transaction_id=transaction.transaction_id,
            buyer_language="hi",
            vendor_language="en",
            include_delivery_info=include_delivery
        )
        
        # Verify delivery information handling
        for lang, content in invoice.invoice_content.items():
            if include_delivery:
                # Delivery section should be present
                assert "delivery_section" in content
                assert content["delivery_section"] is not None
                
                # Delivery details should be present
                if "delivery_details" in content:
                    delivery_details = content["delivery_details"]
                    assert "tracking_id" in delivery_details
                    assert "delivery_method" in delivery_details
                    assert "delivery_status" in delivery_details
            else:
                # Delivery section should be None or not present
                delivery_section = content.get("delivery_section")
                if delivery_section is not None:
                    # If present, it should indicate no delivery info
                    assert delivery_section is None or "delivery_details" not in content
    
    @given(
        amounts=st.lists(
            transaction_amount_strategy(),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=15, deadline=2000)
    def test_invoice_amount_calculations(self, amounts):
        """
        Test that invoice amount calculations are consistent and accurate.
        """
        for amount in amounts:
            # Test basic amount validation
            assert amount > Decimal('0'), "Transaction amount must be positive"
            assert amount <= Decimal('100000.00'), "Transaction amount within reasonable limits"
            
            # Test decimal precision
            assert amount.as_tuple().exponent >= -2, "Amount should have at most 2 decimal places"
            
            # Test that amount can be converted to float for JSON serialization
            float_amount = float(amount)
            assert float_amount > 0, "Amount should convert to positive float"
            
            # Test that conversion back to Decimal maintains precision
            converted_back = Decimal(str(float_amount))
            assert abs(converted_back - amount) < Decimal('0.01'), "Amount precision should be maintained"
    
    @given(
        buyer_lang=st.sampled_from(SUPPORTED_LANGUAGES),
        vendor_lang=st.sampled_from(SUPPORTED_LANGUAGES)
    )
    @settings(max_examples=20, deadline=1000)
    def test_language_support_completeness(self, buyer_lang, vendor_lang):
        """
        Test that all supported languages are properly handled.
        """
        # Verify languages are in supported list
        assert buyer_lang in SUPPORTED_LANGUAGES
        assert vendor_lang in SUPPORTED_LANGUAGES
        
        # Verify language codes are valid (2-3 character codes)
        assert 2 <= len(buyer_lang) <= 3
        assert 2 <= len(vendor_lang) <= 3
        
        # Verify language codes are lowercase
        assert buyer_lang.islower()
        assert vendor_lang.islower()
        
        # Test that language combination is valid for invoice generation
        languages_set = {buyer_lang, vendor_lang, "en"}  # Always include English
        assert len(languages_set) >= 1  # At least one language
        assert len(languages_set) <= 3  # At most three languages (buyer, vendor, English)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])