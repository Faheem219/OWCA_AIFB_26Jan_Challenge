"""
Unit tests for user profile models and validation.

This module tests the user profile creation, validation, and CRUD operations
to ensure proper role-based validation and data integrity.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserRole,
    BusinessType,
    ProductCategory,
    SupportedLanguage,
    LocationData,
    BudgetRange,
    VerificationStatus,
    UserPreferences,
    Address,
    DocumentReference
)
from app.services.user_service import UserService
from app.core.exceptions import (
    ValidationException,
    AuthenticationException,
    NotFoundException,
    AuthorizationException
)


class TestUserProfileValidation:
    """Unit tests for user profile validation."""
    
    @pytest.fixture
    def user_service(self):
        """Create user service instance."""
        return UserService()
    
    @pytest.fixture
    def valid_location(self):
        """Create valid location data."""
        return LocationData(
            address="123 Market Street",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001",
            country="India"
        )
    
    @pytest.fixture
    def valid_vendor_request(self, valid_location):
        """Create valid vendor creation request."""
        return UserCreateRequest(
            email="vendor@example.com",
            password="SecurePass123!",
            phone="+919876543210",
            role=UserRole.VENDOR,
            preferred_languages=[SupportedLanguage.ENGLISH, SupportedLanguage.HINDI],
            location=valid_location,
            business_name="Fresh Vegetables Store",
            business_type=BusinessType.SMALL_BUSINESS,
            product_categories=[ProductCategory.VEGETABLES, ProductCategory.FRUITS],
            market_location="Crawford Market, Mumbai"
        )
    
    @pytest.fixture
    def valid_buyer_request(self, valid_location):
        """Create valid buyer creation request."""
        return UserCreateRequest(
            email="buyer@example.com",
            password="SecurePass123!",
            phone="+919876543211",
            role=UserRole.BUYER,
            preferred_languages=[SupportedLanguage.ENGLISH],
            location=valid_location,
            preferred_categories=[ProductCategory.VEGETABLES],
            budget_range=BudgetRange(
                min_amount=Decimal("100"),
                max_amount=Decimal("5000"),
                currency="INR"
            )
        )
    
    @pytest.mark.asyncio
    async def test_valid_vendor_profile_creation(self, user_service, valid_vendor_request):
        """Test successful vendor profile creation with all required fields."""
        with patch('app.services.user_service.get_database') as mock_db:
            # Mock database operations
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = None  # No existing user
            mock_collection.insert_one.return_value = MagicMock(inserted_id="mock_id")
            mock_collection.find_one.return_value = {
                "user_id": "test_user_id",
                "email": "vendor@example.com",
                "role": "vendor",
                "business_name": "Fresh Vegetables Store",
                "business_type": "small_business",
                "product_categories": ["vegetables", "fruits"],
                "market_location": "Crawford Market, Mumbai",
                "verification_status": "unverified",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "location": valid_vendor_request.location.dict(),
                "preferred_languages": ["en", "hi"],
                "preferences": UserPreferences().dict(),
                "verification_documents": [],
                "rating": 0.0,
                "total_transactions": 0,
                "total_revenue": "0"
            }
            
            result = await user_service.create_user_profile(valid_vendor_request)
            
            assert result is not None
            assert result.email == "vendor@example.com"
            assert result.role == UserRole.VENDOR
            assert result.business_name == "Fresh Vegetables Store"
            assert result.business_type == BusinessType.SMALL_BUSINESS
            assert ProductCategory.VEGETABLES in result.product_categories
            assert ProductCategory.FRUITS in result.product_categories
    
    @pytest.mark.asyncio
    async def test_valid_buyer_profile_creation(self, user_service, valid_buyer_request):
        """Test successful buyer profile creation with all required fields."""
        with patch('app.services.user_service.get_database') as mock_db:
            # Mock database operations
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = None  # No existing user
            mock_collection.insert_one.return_value = MagicMock(inserted_id="mock_id")
            mock_collection.find_one.return_value = {
                "user_id": "test_user_id",
                "email": "buyer@example.com",
                "role": "buyer",
                "preferred_categories": ["vegetables"],
                "budget_range": {
                    "min_amount": "100",
                    "max_amount": "5000",
                    "currency": "INR"
                },
                "verification_status": "unverified",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "location": valid_buyer_request.location.dict(),
                "preferred_languages": ["en"],
                "preferences": UserPreferences().dict(),
                "purchase_history": [],
                "delivery_addresses": [],
                "total_purchases": 0,
                "total_spent": "0"
            }
            
            result = await user_service.create_user_profile(valid_buyer_request)
            
            assert result is not None
            assert result.email == "buyer@example.com"
            assert result.role == UserRole.BUYER
            assert ProductCategory.VEGETABLES in result.preferred_categories
    
    @pytest.mark.asyncio
    async def test_vendor_missing_business_name(self, user_service, valid_vendor_request):
        """Test vendor profile creation fails when business name is missing."""
        valid_vendor_request.business_name = None
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "Business name is required for vendors" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_vendor_empty_business_name(self, user_service, valid_vendor_request):
        """Test vendor profile creation fails when business name is empty."""
        valid_vendor_request.business_name = "   "
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "Business name is required for vendors" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_vendor_missing_business_type(self, user_service, valid_vendor_request):
        """Test vendor profile creation fails when business type is missing."""
        valid_vendor_request.business_type = None
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "Business type is required for vendors" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_vendor_missing_product_categories(self, user_service, valid_vendor_request):
        """Test vendor profile creation fails when product categories are missing."""
        valid_vendor_request.product_categories = None
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "At least one product category is required for vendors" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_vendor_empty_product_categories(self, user_service, valid_vendor_request):
        """Test vendor profile creation fails when product categories list is empty."""
        valid_vendor_request.product_categories = []
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "At least one product category is required for vendors" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_vendor_missing_market_location(self, user_service, valid_vendor_request):
        """Test vendor profile creation fails when market location is missing."""
        valid_vendor_request.market_location = None
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "Market location is required for vendors" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_vendor_business_name_too_short(self, user_service, valid_vendor_request):
        """Test vendor profile creation fails when business name is too short."""
        valid_vendor_request.business_name = "A"
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "Business name must be at least 2 characters long" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_vendor_business_name_too_long(self, user_service, valid_vendor_request):
        """Test vendor profile creation fails when business name is too long."""
        valid_vendor_request.business_name = "A" * 101
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "Business name cannot exceed 100 characters" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_vendor_too_many_product_categories(self, user_service, valid_vendor_request):
        """Test vendor profile creation fails when too many product categories are selected."""
        valid_vendor_request.product_categories = [
            ProductCategory.VEGETABLES,
            ProductCategory.FRUITS,
            ProductCategory.GRAINS,
            ProductCategory.SPICES,
            ProductCategory.DAIRY,
            ProductCategory.VEGETABLES  # This would be 6 if it weren't a duplicate
        ]
        # Create 6 unique categories by using all available ones
        all_categories = list(ProductCategory)
        valid_vendor_request.product_categories = all_categories[:6] if len(all_categories) >= 6 else all_categories
        
        if len(valid_vendor_request.product_categories) > 5:
            with pytest.raises(ValidationException) as exc_info:
                await user_service.create_user_profile(valid_vendor_request)
            
            assert "Cannot select more than 5 product categories" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_buyer_invalid_budget_range(self, user_service, valid_buyer_request):
        """Test buyer profile creation fails when budget range is invalid."""
        valid_buyer_request.budget_range = BudgetRange(
            min_amount=Decimal("5000"),
            max_amount=Decimal("1000"),  # Max less than min
            currency="INR"
        )
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_buyer_request)
        
        assert "Budget minimum amount cannot exceed maximum amount" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_buyer_negative_budget_amounts(self, user_service, valid_buyer_request):
        """Test buyer profile creation fails when budget amounts are negative."""
        valid_buyer_request.budget_range = BudgetRange(
            min_amount=Decimal("-100"),
            max_amount=Decimal("1000"),
            currency="INR"
        )
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_buyer_request)
        
        assert "Budget minimum amount cannot be negative" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_missing_location(self, user_service, valid_vendor_request):
        """Test profile creation fails when location is missing."""
        valid_vendor_request.location = None
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "Location is required for all users" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_missing_city_in_location(self, user_service, valid_vendor_request):
        """Test profile creation fails when city is missing in location."""
        valid_vendor_request.location.city = ""
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "City is required in location" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_missing_state_in_location(self, user_service, valid_vendor_request):
        """Test profile creation fails when state is missing in location."""
        valid_vendor_request.location.state = ""
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "State is required in location" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_pincode(self, user_service, valid_vendor_request):
        """Test profile creation fails when pincode is invalid."""
        valid_vendor_request.location.pincode = "12345"  # Only 5 digits
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "Valid 6-digit pincode is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_missing_preferred_languages(self, user_service, valid_vendor_request):
        """Test profile creation fails when preferred languages are missing."""
        valid_vendor_request.preferred_languages = []
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "At least one preferred language is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_too_many_preferred_languages(self, user_service, valid_vendor_request):
        """Test profile creation fails when too many preferred languages are selected."""
        valid_vendor_request.preferred_languages = [
            SupportedLanguage.ENGLISH,
            SupportedLanguage.HINDI,
            SupportedLanguage.TAMIL,
            SupportedLanguage.TELUGU  # 4 languages, max is 3
        ]
        
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user_profile(valid_vendor_request)
        
        assert "Cannot select more than 3 preferred languages" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_duplicate_email(self, user_service, valid_vendor_request):
        """Test profile creation fails when email already exists."""
        with patch('app.services.user_service.get_database') as mock_db:
            # Mock existing user with same email
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = {
                "email": "vendor@example.com",
                "user_id": "existing_user"
            }
            
            with pytest.raises(ValidationException) as exc_info:
                await user_service.create_user_profile(valid_vendor_request)
            
            assert "User with this email already exists" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_duplicate_phone(self, user_service, valid_vendor_request):
        """Test profile creation fails when phone number already exists."""
        with patch('app.services.user_service.get_database') as mock_db:
            # Mock existing user with same phone
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = {
                "phone": "+919876543210",
                "user_id": "existing_user"
            }
            
            with pytest.raises(ValidationException) as exc_info:
                await user_service.create_user_profile(valid_vendor_request)
            
            assert "User with this phone number already exists" in str(exc_info.value)


class TestProfileCompletenessValidation:
    """Unit tests for profile completeness validation."""
    
    @pytest.fixture
    def user_service(self):
        """Create user service instance."""
        return UserService()
    
    @pytest.mark.asyncio
    async def test_complete_vendor_profile(self, user_service):
        """Test completeness validation for a complete vendor profile."""
        with patch('app.services.user_service.get_database') as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = {
                "user_id": "test_vendor",
                "email": "vendor@example.com",
                "role": "vendor",
                "business_name": "Fresh Vegetables Store",
                "business_type": "small_business",
                "product_categories": ["vegetables", "fruits"],
                "market_location": "Crawford Market, Mumbai",
                "location": {
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "pincode": "400001"
                },
                "preferred_languages": ["en", "hi"]
            }
            
            result = await user_service.validate_profile_completeness("test_vendor")
            
            assert result["is_complete"] is True
            assert result["completeness_percentage"] == 100.0
            assert len(result["missing_fields"]) == 0
    
    @pytest.mark.asyncio
    async def test_incomplete_vendor_profile(self, user_service):
        """Test completeness validation for an incomplete vendor profile."""
        with patch('app.services.user_service.get_database') as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = {
                "user_id": "test_vendor",
                "email": "vendor@example.com",
                "role": "vendor",
                "business_name": "Fresh Vegetables Store",
                # Missing business_type, product_categories, market_location
                "location": {
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "pincode": "400001"
                },
                "preferred_languages": ["en"]
            }
            
            result = await user_service.validate_profile_completeness("test_vendor")
            
            assert result["is_complete"] is False
            assert result["completeness_percentage"] < 100.0
            assert "business_type" in result["missing_fields"]
            assert "product_categories" in result["missing_fields"]
            assert "market_location" in result["missing_fields"]
    
    @pytest.mark.asyncio
    async def test_complete_buyer_profile(self, user_service):
        """Test completeness validation for a complete buyer profile."""
        with patch('app.services.user_service.get_database') as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = {
                "user_id": "test_buyer",
                "email": "buyer@example.com",
                "role": "buyer",
                "location": {
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "pincode": "400001"
                },
                "preferred_languages": ["en"]
            }
            
            result = await user_service.validate_profile_completeness("test_buyer")
            
            assert result["is_complete"] is True
            assert result["completeness_percentage"] == 100.0
            assert len(result["missing_fields"]) == 0
    
    @pytest.mark.asyncio
    async def test_profile_completeness_user_not_found(self, user_service):
        """Test completeness validation when user is not found."""
        with patch('app.services.user_service.get_database') as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = None
            
            with pytest.raises(NotFoundException) as exc_info:
                await user_service.validate_profile_completeness("nonexistent_user")
            
            assert "User not found" in str(exc_info.value)


class TestVerificationDocuments:
    """Unit tests for verification document management."""
    
    @pytest.fixture
    def user_service(self):
        """Create user service instance."""
        return UserService()
    
    @pytest.mark.asyncio
    async def test_add_verification_document_success(self, user_service):
        """Test successful addition of verification document."""
        with patch('app.services.user_service.get_database') as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = {
                "user_id": "test_vendor",
                "role": "vendor",
                "verification_documents": []
            }
            mock_collection.update_one.return_value = MagicMock()
            
            result = await user_service.add_verification_document(
                "test_vendor",
                "aadhaar",
                "https://example.com/aadhaar.pdf",
                "test_vendor"
            )
            
            assert len(result) == 1
            assert result[0].document_type == "aadhaar"
            assert result[0].document_url == "https://example.com/aadhaar.pdf"
            assert result[0].verification_status == VerificationStatus.UNVERIFIED
    
    @pytest.mark.asyncio
    async def test_add_verification_document_unauthorized(self, user_service):
        """Test adding verification document fails when unauthorized."""
        with pytest.raises(AuthorizationException) as exc_info:
            await user_service.add_verification_document(
                "test_vendor",
                "aadhaar",
                "https://example.com/aadhaar.pdf",
                "different_user"  # Different user trying to add document
            )
        
        assert "You can only add documents to your own profile" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_add_verification_document_buyer_fails(self, user_service):
        """Test adding verification document fails for buyers."""
        with patch('app.services.user_service.get_database') as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = {
                "user_id": "test_buyer",
                "role": "buyer"
            }
            
            with pytest.raises(ValidationException) as exc_info:
                await user_service.add_verification_document(
                    "test_buyer",
                    "aadhaar",
                    "https://example.com/aadhaar.pdf",
                    "test_buyer"
                )
            
            assert "Only vendors can add verification documents" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_add_verification_document_invalid_type(self, user_service):
        """Test adding verification document fails with invalid document type."""
        with patch('app.services.user_service.get_database') as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = {
                "user_id": "test_vendor",
                "role": "vendor",
                "verification_documents": []
            }
            
            with pytest.raises(ValidationException) as exc_info:
                await user_service.add_verification_document(
                    "test_vendor",
                    "invalid_document_type",
                    "https://example.com/doc.pdf",
                    "test_vendor"
                )
            
            assert "Invalid document type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_replace_existing_verification_document(self, user_service):
        """Test replacing an existing verification document."""
        with patch('app.services.user_service.get_database') as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.users = mock_collection
            mock_collection.find_one.return_value = {
                "user_id": "test_vendor",
                "role": "vendor",
                "verification_documents": [
                    {
                        "document_type": "aadhaar",
                        "document_url": "https://example.com/old_aadhaar.pdf",
                        "verification_status": "unverified",
                        "uploaded_at": datetime.utcnow()
                    }
                ]
            }
            mock_collection.update_one.return_value = MagicMock()
            
            result = await user_service.add_verification_document(
                "test_vendor",
                "aadhaar",
                "https://example.com/new_aadhaar.pdf",
                "test_vendor"
            )
            
            assert len(result) == 1
            assert result[0].document_type == "aadhaar"
            assert result[0].document_url == "https://example.com/new_aadhaar.pdf"