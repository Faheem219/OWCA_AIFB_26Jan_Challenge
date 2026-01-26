"""
Unit tests for the authentication service.

Tests cover user registration, login, token management, and various authentication methods.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.auth_service import AuthService
from app.models.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    OAuthCredentials,
    AadhaarCredentials,
    VerificationData,
    AuthMethod
)
from app.models.user import UserRole, SupportedLanguage, BusinessType
from app.core.exceptions import (
    AuthenticationException,
    ValidationException,
    ExternalServiceException
)


class TestAuthService:
    """Test cases for AuthService."""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance for testing."""
        return AuthService()
    
    @pytest.fixture
    def mock_db(self):
        """Mock database for testing."""
        db = AsyncMock(spec=AsyncIOMotorDatabase)
        db.users = AsyncMock()
        db.security_events = AsyncMock()
        return db
    
    @pytest.fixture
    def sample_register_request(self):
        """Sample registration request for vendor."""
        return RegisterRequest(
            method=AuthMethod.EMAIL,
            email="vendor@example.com",
            password="SecurePass123!",
            phone="+919876543210",
            role=UserRole.VENDOR,
            preferred_language=SupportedLanguage.ENGLISH,
            full_name="Test Vendor",
            location_city="Mumbai",
            location_state="Maharashtra",
            location_pincode="400001",
            business_name="Test Business",
            business_type="small_business",
            accept_terms=True,
            accept_privacy=True
        )
    
    @pytest.fixture
    def sample_buyer_register_request(self):
        """Sample registration request for buyer."""
        return RegisterRequest(
            method=AuthMethod.EMAIL,
            email="buyer@example.com",
            password="SecurePass123!",
            phone="+919876543211",
            role=UserRole.BUYER,
            preferred_language=SupportedLanguage.HINDI,
            full_name="Test Buyer",
            location_city="Delhi",
            location_state="Delhi",
            location_pincode="110001",
            accept_terms=True,
            accept_privacy=True
        )
    
    @pytest.fixture
    def sample_login_request(self):
        """Sample login request."""
        return LoginRequest(
            method=AuthMethod.EMAIL,
            identifier="vendor@example.com",
            password="SecurePass123!",
            remember_me=False
        )
    
    @pytest.fixture
    def sample_user_doc(self):
        """Sample user document from database."""
        return {
            "_id": "507f1f77bcf86cd799439011",
            "user_id": "user123",
            "email": "vendor@example.com",
            "password_hash": "$2b$12$hashed_password",
            "phone": "+919876543210",
            "role": "vendor",
            "preferred_languages": ["en"],
            "location": {
                "address": "Mumbai, Maharashtra",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001",
                "country": "India"
            },
            "verification_status": "unverified",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "full_name": "Test Vendor",
            "business_name": "Test Business",
            "business_type": "small_business",
            "product_categories": [],
            "market_location": "Mumbai, Maharashtra",
            "verification_documents": [],
            "rating": 0.0,
            "total_transactions": 0,
            "total_revenue": "0"
        }
    
    @pytest.mark.asyncio
    async def test_register_vendor_success(self, auth_service, sample_register_request, mock_db):
        """Test successful vendor registration."""
        # Mock database operations
        mock_db.users.find_one.return_value = None  # No existing user
        mock_db.users.insert_one.return_value = MagicMock(inserted_id="507f1f77bcf86cd799439011")
        mock_db.users.update_one.return_value = MagicMock(modified_count=1)
        
        with patch('app.services.auth_service.get_database', return_value=mock_db):
            with patch.object(auth_service, '_send_verification') as mock_send_verification:
                with patch.object(auth_service, '_log_security_event') as mock_log_event:
                    result = await auth_service.register_user(sample_register_request)
        
        # Assertions
        assert result.success is True
        assert result.user_id is not None
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.requires_verification is True
        assert result.verification_method == "email"
        
        # Verify database calls
        mock_db.users.find_one.assert_called_once()
        mock_db.users.insert_one.assert_called_once()
        mock_db.users.update_one.assert_called_once()
        
        # Verify verification email sent
        mock_send_verification.assert_called_once()
        mock_log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_buyer_success(self, auth_service, sample_buyer_register_request, mock_db):
        """Test successful buyer registration."""
        # Mock database operations
        mock_db.users.find_one.return_value = None  # No existing user
        mock_db.users.insert_one.return_value = MagicMock(inserted_id="507f1f77bcf86cd799439012")
        mock_db.users.update_one.return_value = MagicMock(modified_count=1)