"""
Tests for the rating and review system.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId

from app.models.review import (
    ReviewCreate, ReviewUpdate, ReviewStatus, ReviewCategory, Rating
)
from app.services.review_service import ReviewService
from app.services.translation_service import TranslationService


@pytest.fixture
def mock_db():
    """Mock database."""
    db = MagicMock()
    db.reviews = AsyncMock()
    db.users = AsyncMock()
    db.transactions = AsyncMock()
    db.notifications = AsyncMock()
    return db


@pytest.fixture
def mock_translation_service():
    """Mock translation service."""
    service = MagicMock(spec=TranslationService)
    service.translate_text = AsyncMock()
    return service


@pytest.fixture
def review_service(mock_db, mock_translation_service):
    """Review service instance."""
    return ReviewService(mock_db, mock_translation_service)


@pytest.fixture
def sample_review_data():
    """Sample review data."""
    return ReviewCreate(
        vendor_id=str(ObjectId()),
        overall_rating=4.5,
        detailed_ratings=[
            Rating(category=ReviewCategory.PRODUCT_QUALITY, score=5.0),
            Rating(category=ReviewCategory.DELIVERY_TIME, score=4.0)
        ],
        title="Great product!",
        content="Very satisfied with the quality and delivery time.",
        original_language="en",
        is_verified_purchase=True
    )


class TestReviewModels:
    """Test review models."""
    
    def test_rating_validation(self):
        """Test rating score validation."""
        # Valid rating
        rating = Rating(category=ReviewCategory.PRODUCT_QUALITY, score=4.5)
        assert rating.score == 4.5
        
        # Invalid rating - too low
        with pytest.raises(ValueError):
            Rating(category=ReviewCategory.PRODUCT_QUALITY, score=0.5)
        
        # Invalid rating - too high
        with pytest.raises(ValueError):
            Rating(category=ReviewCategory.PRODUCT_QUALITY, score=5.5)
    
    def test_review_create_model(self, sample_review_data):
        """Test review creation model."""
        assert sample_review_data.overall_rating == 4.5
        assert len(sample_review_data.detailed_ratings) == 2
        assert sample_review_data.title == "Great product!"
        assert sample_review_data.is_verified_purchase is True


class TestReviewService:
    """Test review service functionality."""
    
    @pytest.mark.asyncio
    async def test_create_review_success(self, review_service, sample_review_data, mock_db):
        """Test successful review creation."""
        # Mock database responses
        buyer_id = str(ObjectId())
        vendor_id = sample_review_data.vendor_id
        
        # Mock buyer exists
        mock_db.users.find_one.return_value = {
            "_id": ObjectId(buyer_id),
            "full_name": "Test Buyer"
        }
        
        # Mock vendor exists
        mock_db.users.find_one.return_value = {
            "_id": ObjectId(vendor_id),
            "vendor_profile": {"business_name": "Test Vendor"}
        }
        
        # Mock no existing review
        mock_db.reviews.find_one.return_value = None
        
        # Mock successful insert
        mock_db.reviews.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        
        # Mock translation service
        review_service.translation_service.translate_text.return_value = MagicMock(
            translated_text="Translated content",
            provider="aws_translate",
            confidence_score=0.9
        )
        
        # Create review
        result = await review_service.create_review(buyer_id, sample_review_data)
        
        # Verify result
        assert result is not None
        assert result.overall_rating == 4.5
        assert result.content == sample_review_data.content
        
        # Verify database calls
        mock_db.reviews.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_review_buyer_not_found(self, review_service, sample_review_data, mock_db):
        """Test review creation with non-existent buyer."""
        buyer_id = str(ObjectId())
        
        # Mock buyer not found
        mock_db.users.find_one.return_value = None
        
        # Attempt to create review
        with pytest.raises(Exception):  # Should raise HTTPException
            await review_service.create_review(buyer_id, sample_review_data)
    
    @pytest.mark.asyncio
    async def test_content_moderation(self, review_service):
        """Test content moderation functionality."""
        from app.models.review import Review
        
        # Test clean content
        clean_review = Review(
            vendor_id=str(ObjectId()),
            buyer_id=str(ObjectId()),
            overall_rating=4.0,
            content="Great product, very satisfied!",
            original_language="en"
        )
        
        result = await review_service._moderate_content(clean_review)
        assert result["requires_review"] is False
        
        # Test content with excessive repetition (should trigger spam detection)
        spam_review = Review(
            vendor_id=str(ObjectId()),
            buyer_id=str(ObjectId()),
            overall_rating=1.0,
            content="good " * 20,  # 20 repetitions of "good" (not in profanity list)
            original_language="en"
        )
        
        result = await review_service._moderate_content(spam_review)
        assert result["requires_review"] is True
        assert "repetition" in result["reason"].lower()


class TestReviewAPI:
    """Test review API endpoints."""
    
    def test_review_endpoints_exist(self):
        """Test that review endpoints are properly defined."""
        from app.api.v1.reviews import router
        
        # Check that router has routes
        assert len(router.routes) > 0
        
        # Check for key endpoints
        route_paths = [route.path for route in router.routes]
        assert "/" in route_paths  # Create review
        assert "/{review_id}" in route_paths  # Get/update review
        assert "/vendor/{vendor_id}" in route_paths  # Get vendor reviews
        assert "/vendor/{vendor_id}/summary" in route_paths  # Get vendor summary


class TestMultilingualSupport:
    """Test multilingual review support."""
    
    @pytest.mark.asyncio
    async def test_review_translation_generation(self, review_service, mock_translation_service):
        """Test automatic translation generation for reviews."""
        from app.models.review import Review
        from app.models.translation import TranslationResult
        
        # Create a review
        review = Review(
            vendor_id=str(ObjectId()),
            buyer_id=str(ObjectId()),
            overall_rating=4.0,
            content="Great product!",
            title="Excellent",
            original_language="en"
        )
        
        # Mock translation service response
        mock_translation_service.translate_text.return_value = TranslationResult(
            original_text="Great product!",
            translated_text="उत्कृष्ट उत्पाद!",
            source_language="en",
            target_language="hi",
            confidence_score=0.9,
            provider="aws_translate",
            cached=False
        )
        
        # Generate translations
        await review_service._generate_review_translations(review)
        
        # Verify translation service was called
        assert mock_translation_service.translate_text.called
    
    def test_review_language_filtering(self):
        """Test filtering reviews by language."""
        from app.models.review import ReviewFilters
        
        filters = ReviewFilters(
            language="hi",
            min_rating=4.0,
            skip=0,
            limit=10
        )
        
        assert filters.language == "hi"
        assert filters.min_rating == 4.0


if __name__ == "__main__":
    pytest.main([__file__])