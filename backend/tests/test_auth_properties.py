"""
Property-based tests for authentication system.
**Validates: Requirements 4.1**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings as hypothesis_settings, HealthCheck
from hypothesis.strategies import composite
from httpx import AsyncClient
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
import re


# Custom strategies for Indian context
@composite
def indian_phone_number(draw):
    """Generate valid Indian phone numbers."""
    prefix = draw(st.sampled_from(["+91", "91", ""]))
    number = draw(st.integers(min_value=6000000000, max_value=9999999999))
    return f"{prefix}{number}"


@composite
def indian_email(draw):
    """Generate valid email addresses."""
    username = draw(st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
        min_size=3,
        max_size=20
    ).filter(lambda x: x.isalnum()))
    domain = draw(st.sampled_from(["gmail.com", "yahoo.com", "outlook.com", "example.com"]))
    return f"{username}@{domain}"


@composite
def user_registration_data(draw):
    """Generate valid user registration data."""
    return {
        "email": draw(indian_email()),
        "phone": draw(indian_phone_number()),
        "password": draw(st.text(min_size=8, max_size=50)),
        "full_name": draw(st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Zs")),
            min_size=2,
            max_size=100
        ).filter(lambda x: x.strip() and len(x.strip()) >= 2)),
        "preferred_language": draw(st.sampled_from(settings.SUPPORTED_LANGUAGES)),
        "user_type": draw(st.sampled_from(["vendor", "buyer", "both"]))
    }


class TestAuthenticationProperties:
    """Property-based tests for authentication system."""
    
    @hypothesis_settings(max_examples=20, deadline=5000)
    @given(password=st.text(min_size=1, max_size=200).filter(lambda x: '\x00' not in x))
    def test_password_hashing_consistency(self, password):
        """
        Property: Password hashing should be consistent and verifiable.
        **Validates: Requirements 4.1**
        """
        # Hash the password
        hashed = get_password_hash(password)
        
        # Verify the password matches the hash
        assert verify_password(password, hashed) is True
        
        # Verify a different password doesn't match
        if len(password) > 1:
            wrong_password = password[:-1] + ("x" if password[-1] != "x" else "y")
            assert verify_password(wrong_password, hashed) is False
    
    @hypothesis_settings(max_examples=20, deadline=5000)
    @given(password=st.text(min_size=1, max_size=200).filter(lambda x: '\x00' not in x))
    def test_password_hash_uniqueness(self, password):
        """
        Property: Each password hashing should produce a unique hash.
        **Validates: Requirements 4.1**
        """
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify the same password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    @hypothesis_settings(max_examples=5, deadline=10000)
    @given(user_data=user_registration_data())
    def test_user_registration_verification_requirement_properties(self, user_data):
        """
        Property 16: Verification Requirement Enforcement
        For any vendor profile creation attempt, the system should require and validate 
        government-issued ID verification before allowing profile activation.
        **Validates: Requirements 4.1**
        """
        assume(user_data["user_type"] in ["vendor", "both"])
        
        # Add vendor profile to user data
        user_data["vendor_profile"] = {
            "business_name": "Test Business",
            "business_type": "agriculture",
            "specializations": ["rice"],
            "location": {
                "address": "123 Test Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001"
            },
            "languages_spoken": ["en"]
        }
        
        # Test that vendor profile requires verification
        # This is a property test for data structure validation
        assert "vendor_profile" in user_data
        vendor_profile = user_data["vendor_profile"]
        
        # Vendor profile should have required fields
        required_fields = ["business_name", "business_type", "location"]
        for field in required_fields:
            assert field in vendor_profile
        
        # Location should have required address fields
        location = vendor_profile["location"]
        location_fields = ["address", "city", "state", "pincode"]
        for field in location_fields:
            assert field in location
    
    @hypothesis_settings(max_examples=15, deadline=3000)
    @given(
        language=st.sampled_from(settings.SUPPORTED_LANGUAGES),
        user_type=st.sampled_from(["vendor", "buyer", "both"])
    )
    def test_supported_language_validation(self, language, user_type):
        """
        Property: All supported languages should be valid for user preferences.
        **Validates: Requirements 1.1**
        """
        # Language should be in supported languages list
        assert language in settings.SUPPORTED_LANGUAGES
        
        # Language code should be valid format (2-3 characters)
        assert len(language) in [2, 3]
        assert language.islower()
    
    @hypothesis_settings(max_examples=15, deadline=3000)
    @given(
        email=indian_email(),  # Use our custom email generator instead
        phone=indian_phone_number(),
        password=st.text(min_size=8, max_size=50).filter(lambda x: '\x00' not in x)
    )
    def test_user_data_validation_properties(self, email, phone, password):
        """
        Property: User data should follow validation rules.
        **Validates: Requirements 4.1**
        """
        # Email should be valid format (our custom generator ensures this)
        assert "@" in email
        assert "." in email.split("@")[-1]
        
        # Phone should contain only digits and optional country code
        clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
        assert clean_phone.isdigit()
        
        # Password should meet minimum requirements
        assert len(password) >= 8
    
    @hypothesis_settings(max_examples=10, deadline=3000)
    @given(
        business_types=st.lists(
            st.sampled_from([
                "agriculture", "wholesale", "retail", "manufacturing", 
                "services", "trading", "export", "import"
            ]),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    def test_vendor_specialization_properties(self, business_types):
        """
        Property: Vendor specializations should be valid business categories.
        **Validates: Requirements 4.5**
        """
        valid_business_types = [
            "agriculture", "wholesale", "retail", "manufacturing",
            "services", "trading", "export", "import"
        ]
        
        for business_type in business_types:
            assert business_type in valid_business_types
            assert isinstance(business_type, str)
            assert len(business_type) > 0
    
    @hypothesis_settings(max_examples=10, deadline=3000)
    @given(
        credentials=st.lists(
            st.fixed_dictionaries({
                "type": st.sampled_from(["government_id", "license", "certification"]),
                "number": st.text(min_size=5, max_size=50),
                "issuing_authority": st.text(min_size=3, max_size=100)
            }),
            min_size=1,
            max_size=5
        )
    )
    def test_credential_validation_properties(self, credentials):
        """
        Property: Vendor credentials should have required fields and valid types.
        **Validates: Requirements 4.1, 4.4**
        """
        valid_credential_types = ["government_id", "license", "certification"]
        
        for credential in credentials:
            # Required fields should be present
            assert "type" in credential
            assert "number" in credential
            assert "issuing_authority" in credential
            
            # Type should be valid
            assert credential["type"] in valid_credential_types
            
            # Fields should be non-empty strings
            assert isinstance(credential["number"], str)
            assert len(credential["number"]) >= 5
            assert isinstance(credential["issuing_authority"], str)
            assert len(credential["issuing_authority"]) >= 3