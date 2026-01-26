#!/usr/bin/env python3
"""
Demo script for the Multilingual Mandi Payment System.
Shows UPI, digital wallet, and card payment integration.
"""

import asyncio
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


async def demo_payment_validation():
    """Demo payment method validation."""
    print("🔍 Payment Method Validation Demo")
    print("=" * 50)
    
    service = PaymentService()
    
    # Demo UPI validation
    print("\n1. UPI Payment Validation:")
    upi_details = UPIDetails(upi_id="farmer@paytm")
    payment_details = PaymentDetails(
        method=PaymentMethod.UPI,
        upi_details=upi_details
    )
    
    validation = await service.validate_payment_method(payment_details)
    print(f"   UPI ID: {upi_details.upi_id}")
    print(f"   Valid: {validation.is_valid}")
    print(f"   Features: {', '.join(validation.supported_features)}")
    
    # Demo Digital Wallet validation
    print("\n2. Digital Wallet Validation:")
    wallet_details = DigitalWalletDetails(
        provider=DigitalWalletProvider.PHONEPE,
        wallet_id="phonepe_buyer_123"
    )
    payment_details = PaymentDetails(
        method=PaymentMethod.DIGITAL_WALLET,
        wallet_details=wallet_details
    )
    
    validation = await service.validate_payment_method(payment_details)
    print(f"   Provider: {wallet_details.provider}")
    print(f"   Valid: {validation.is_valid}")
    print(f"   Features: {', '.join(validation.supported_features)}")
    
    # Demo Card validation
    print("\n3. Card Payment Validation:")
    card_details = CardDetails(
        card_type=CardType.DEBIT,
        last_four_digits="1234",
        card_network="rupay",
        bank_name="State Bank of India"
    )
    payment_details = PaymentDetails(
        method=PaymentMethod.CARD,
        card_details=card_details
    )
    
    validation = await service.validate_payment_method(payment_details)
    print(f"   Card: {card_details.card_network.upper()} {card_details.card_type} ****{card_details.last_four_digits}")
    print(f"   Bank: {card_details.bank_name}")
    print(f"   Valid: {validation.is_valid}")
    print(f"   Features: {', '.join(validation.supported_features)}")


async def demo_supported_methods():
    """Demo supported payment methods."""
    print("\n\n💳 Supported Payment Methods")
    print("=" * 50)
    
    service = PaymentService()
    methods = await service.get_supported_payment_methods()
    
    for i, method in enumerate(methods, 1):
        print(f"\n{i}. {method['name']} ({method['method']})")
        print(f"   Description: {method['description']}")
        print(f"   Features: {', '.join(method['features'])}")
        
        if 'supported_providers' in method:
            print(f"   Providers: {', '.join(method['supported_providers'])}")
        elif 'supported_networks' in method:
            print(f"   Networks: {', '.join(method['supported_networks'])}")
        elif 'supported_banks' in method:
            print(f"   Banks: {', '.join(method['supported_banks'])}")


async def demo_payment_scenarios():
    """Demo different payment scenarios."""
    print("\n\n🛒 Payment Scenarios Demo")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Small Vegetable Purchase",
            "amount": Decimal("250.00"),
            "method": "UPI",
            "details": "farmer@paytm → buyer@phonepe"
        },
        {
            "name": "Bulk Grain Order",
            "amount": Decimal("15000.00"),
            "method": "Digital Wallet",
            "details": "PhonePe Business Account"
        },
        {
            "name": "Premium Organic Products",
            "amount": Decimal("5500.00"),
            "method": "Card Payment",
            "details": "RuPay Debit Card ****1234"
        },
        {
            "name": "High-Value Commodity Trade",
            "amount": Decimal("75000.00"),
            "method": "Escrow + UPI",
            "details": "Escrow protection for quality assurance"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   Amount: ₹{scenario['amount']:,.2f}")
        print(f"   Method: {scenario['method']}")
        print(f"   Details: {scenario['details']}")
        
        # Show appropriate features for amount
        if scenario['amount'] > 50000:
            print("   🔒 Escrow protection recommended")
            print("   📋 Quality inspection required")
        elif scenario['amount'] > 10000:
            print("   📱 SMS notifications enabled")
            print("   📄 Digital invoice generated")
        else:
            print("   ⚡ Instant settlement")
            print("   📱 Mobile-friendly checkout")


async def demo_multilingual_support():
    """Demo multilingual payment support."""
    print("\n\n🌐 Multilingual Payment Support")
    print("=" * 50)
    
    languages = [
        ("en", "English", "Payment successful"),
        ("hi", "हिन्दी", "भुगतान सफल"),
        ("ta", "தமிழ்", "பணம் செலுத்துதல் வெற்றிகரமாக"),
        ("te", "తెలుగు", "చెల్లింపు విజయవంతం"),
        ("bn", "বাংলা", "পেমেন্ট সফল"),
        ("mr", "मराठी", "पेमेंट यशस्वी"),
        ("gu", "ગુજરાતી", "ચુકવણી સફળ"),
        ("kn", "ಕನ್ನಡ", "ಪಾವತಿ ಯಶಸ್ವಿ")
    ]
    
    print("\nPayment confirmations in Indian languages:")
    for code, name, message in languages:
        print(f"   {code.upper()}: {message} ({name})")
    
    print("\n📄 Invoice Generation:")
    print("   • Buyer language: Hindi (हिन्दी)")
    print("   • Vendor language: Tamil (தமிழ்)")
    print("   • System generates bilingual invoice automatically")
    
    print("\n🔔 SMS Notifications:")
    print("   • Sent in user's preferred language")
    print("   • Supports all 22 official Indian languages")
    print("   • Automatic translation for cross-language transactions")


async def demo_security_features():
    """Demo security and trust features."""
    print("\n\n🔐 Security & Trust Features")
    print("=" * 50)
    
    features = [
        {
            "feature": "Payment Method Validation",
            "description": "Real-time validation of UPI IDs, card details, and wallet accounts"
        },
        {
            "feature": "Escrow Protection",
            "description": "Funds held securely until delivery confirmation for high-value transactions"
        },
        {
            "feature": "Fraud Detection",
            "description": "AI-powered monitoring for suspicious transaction patterns"
        },
        {
            "feature": "Data Encryption",
            "description": "End-to-end encryption for all sensitive payment information"
        },
        {
            "feature": "Multi-Gateway Support",
            "description": "Redundancy with Razorpay, PayU, and Cashfree integrations"
        },
        {
            "feature": "Transaction Tracking",
            "description": "Complete audit trail with status history and gateway responses"
        }
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"\n{i}. {feature['feature']}")
        print(f"   {feature['description']}")


async def main():
    """Run the payment system demo."""
    print("🏪 Multilingual Mandi Payment System Demo")
    print("🇮🇳 Empowering Indian Farmers & Traders")
    print("=" * 60)
    
    try:
        await demo_payment_validation()
        await demo_supported_methods()
        await demo_payment_scenarios()
        await demo_multilingual_support()
        await demo_security_features()
        
        print("\n\n✅ Payment System Demo Complete!")
        print("🚀 Ready for production deployment")
        print("📞 Supporting farmers across India with secure, multilingual payments")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)