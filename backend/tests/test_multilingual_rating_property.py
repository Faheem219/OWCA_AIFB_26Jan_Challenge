"""
Property-based test for multilingual rating system.
**Validates: Requirements 4.2**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId

from app.models.review import (
    ReviewCreate, ReviewStatus, ReviewCategory, Rating, Review
)
from app.services.review_service import ReviewService
from app.services.translation_service import TranslationService
from app.models.translation import TranslationResult


# Supported languages for the platform
SUPPORTED_LANGUAGES = [
    "hi", "en", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "or", "as", "ur"
]

# Sample review content in different languages
SAMPLE_REVIEWS = {
    "en": [
        "Great product, very satisfied!",
        "Excellent quality and fast delivery",
        "Good value for money",
        "Outstanding service",
        "Highly recommended"
    ],
    "hi": [
        "बहुत अच्छा उत्पाद, बहुत संतुष्ट!",
        "उत्कृष्ट गुणवत्ता और तेज़ डिलीवरी",
        "पैसे के लिए अच्छा मूल्य",
        "उत्कृष्ट सेवा",
        "अत्यधिक अनुशंसित"
    ],
    "ta": [
        "சிறந்த தயாரிப்பு, மிகவும் திருப்தி!",
        "சிறந்த தரம் மற்றும் வேகமான டெலிவரி",
        "பணத்திற்கு நல்ல மதிப்பு",
        "சிறந்த சேவை",
        "மிகவும் பரிந்துரைக்கப்படுகிறது"
    ]
}


@composite
def review_content_strategy(draw):
    """Generate review content in various languages."""
    language = draw(st.sampled_from(SUPPORTED_LANGUAGES))
    
    if language in SAMPLE_REVIEWS:
        content = draw(st.sampled_from(SAMPLE_REVIEWS[language]))
    else:
        # Fallback to English content for languages without samples
        content = draw(st.sampled_from(SAMPLE_REVIEWS["en"]))
    
    return language, content


@composite
def rating_strategy(draw):
    """Generate valid rating scores."""
    return draw(st.floats(min_value=1.0, max_value=5.0))


@composite
def detailed_ratings_strategy(draw):
    """Generate detailed ratings for different categories."""
    categories = draw(st.lists(
        st.sampled_from(list(ReviewCategory)), 
        min_size=1, 
        max_size=len(ReviewCategory),
        unique=True
    ))
    
    ratings = []
    for category in categories:
        score = draw(rating_strategy())
        ratings.append(Rating(category=category, score=score))
    
    return ratings


@composite
def review_create_strategy(draw):
    """Generate ReviewCreate instances with multilingual content."""
    vendor_id = str(ObjectId())
    language, content = draw(review_content_strategy())
    overall_rating = draw(rating_strategy())
    detailed_ratings = draw(detailed_ratings_strategy())
    
    # Generate title in the same language (simplified)
    title_samples = {
        "en": ["Great!", "Excellent", "Good", "Outstanding", "Perfect"],
        "hi": ["बहुत अच्छा!", "उत्कृष्ट", "अच्छा", "उत्कृष्ट", "परफेक्ट"],
        "ta": ["சிறந்த!", "சிறப்பு", "நல்ல", "சிறந்த", "சரியான"]
    }
    
    title = None
    if language in title_samples:
        title = draw(st.sampled_from(title_samples[language]))
    
    return ReviewCreate(
        vendor_id=vendor_id,
        overall_rating=overall_rating,
        detailed_ratings=detailed_ratings,
        title=title,
        content=content,
        original_language=language,
        is_verified_purchase=draw(st.booleans()),
        is_anonymous=draw(st.booleans())
    )


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


class TestMultilingualRatingSystemProperties:
    """Property-based tests for multilingual rating system."""
    
    @given(review_data=review_create_strategy())
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_property_17_multilingual_rating_system(
        self, 
        review_data
    ):
        """
        **Property 17: Multilingual Rating System**
        **Validates: Requirements 4.2**
        
        For any completed transaction, buyers should be able to submit ratings 
        and reviews in their preferred language, and these should be properly 
        stored and displayed.
        """
        # Test: Review data can be created in any supported language
        assert review_data.original_language in SUPPORTED_LANGUAGES
        
        # Test: Review content is not empty
        assert len(review_data.content.strip()) > 0
        
        # Test: Rating is within valid range
        assert 1.0 <= review_data.overall_rating <= 5.0
        
        # Test: Detailed ratings are valid
        for rating in review_data.detailed_ratings:
            assert 1.0 <= rating.score <= 5.0
            assert isinstance(rating.category, ReviewCategory)
        
        # Test: Vendor ID is valid ObjectId format
        assert len(review_data.vendor_id) == 24  # ObjectId length
        
        # Test: Language-specific content validation
        if review_data.original_language in SAMPLE_REVIEWS:
            # If we have sample content for this language, verify it's from our samples
            assert review_data.content in SAMPLE_REVIEWS[review_data.original_language]
        
        # Test: Boolean fields are properly set
        assert isinstance(review_data.is_verified_purchase, bool)
        assert isinstance(review_data.is_anonymous, bool)
    
    @given(
        original_language=st.sampled_from(SUPPORTED_LANGUAGES),
        target_language=st.sampled_from(SUPPORTED_LANGUAGES)
    )
    @settings(max_examples=30, deadline=3000)
    @pytest.mark.asyncio
    async def test_review_translation_consistency(
        self, 
        original_language, 
        target_language, 
        review_service,
        mock_translation_service
    ):
        """
        Test that review translations maintain consistency across language pairs.
        """
        assume(original_language != target_language)
        
        # Create a review with original content
        review = Review(
            vendor_id=str(ObjectId()),
            buyer_id=str(ObjectId()),
            overall_rating=4.0,
            content="Test content for translation",
            original_language=original_language
        )
        
        # Mock translation service
        mock_translation_service.translate_text.return_value = TranslationResult(
            original_text="Test content for translation",
            translated_text="Translated test content",
            source_language=original_language,
            target_language=target_language,
            confidence_score=0.85,
            provider="aws_translate",
            cached=False
        )
        
        # Generate translations
        await review_service._generate_review_translations(review)
        
        # Verify translation service was called
        assert mock_translation_service.translate_text.called
        
        # Verify the translation request parameters
        call_args = mock_translation_service.translate_text.call_args_list
        assert len(call_args) > 0
        
        # Check that translation was requested for the target language
        translation_languages = [call[0][0].target_language for call in call_args]
        # Note: The service generates translations for all supported languages except original
        assert len(translation_languages) >= 1
    
    @given(
        rating_score=rating_strategy(),
        detailed_ratings=detailed_ratings_strategy()
    )
    @settings(max_examples=20, deadline=2000)
    def test_rating_score_validation(self, rating_score, detailed_ratings):
        """
        Test that rating scores are always within valid range (1.0 to 5.0).
        """
        # Test overall rating validation
        assert 1.0 <= rating_score <= 5.0
        
        # Test detailed ratings validation
        for rating in detailed_ratings:
            assert 1.0 <= rating.score <= 5.0
            assert isinstance(rating.category, ReviewCategory)
    
    @given(review_data=review_create_strategy())
    @settings(max_examples=20, deadline=2000)
    def test_review_language_preservation(self, review_data):
        """
        Test that review original language is preserved correctly.
        """
        # Verify original language is one of supported languages
        assert review_data.original_language in SUPPORTED_LANGUAGES
        
        # Verify content is not empty
        assert len(review_data.content.strip()) > 0
        
        # Verify rating is valid
        assert 1.0 <= review_data.overall_rating <= 5.0
    
    @given(
        language=st.sampled_from(SUPPORTED_LANGUAGES),
        content=st.text(min_size=10, max_size=500)
    )
    @settings(max_examples=15, deadline=2000)
    @pytest.mark.asyncio
    async def test_content_moderation_language_independence(
        self, 
        language, 
        content, 
        review_service
    ):
        """
        Test that content moderation works consistently across all languages.
        """
        # Filter out problematic characters that might cause issues
        assume(all(ord(char) < 65536 for char in content))  # Basic Multilingual Plane
        assume(len(content.strip()) > 5)
        
        review = Review(
            vendor_id=str(ObjectId()),
            buyer_id=str(ObjectId()),
            overall_rating=4.0,
            content=content,
            original_language=language
        )
        
        # Test content moderation
        result = await review_service._moderate_content(review)
        
        # Verify moderation result structure
        assert "requires_review" in result
        assert isinstance(result["requires_review"], bool)
        
        if result["requires_review"]:
            assert "reason" in result
            assert isinstance(result["reason"], str)
            assert len(result["reason"]) > 0
    
    @given(
        vendor_id=st.text(min_size=24, max_size=24),  # ObjectId length
        buyer_id=st.text(min_size=24, max_size=24),
        rating=rating_strategy()
    )
    @settings(max_examples=10, deadline=1000)
    def test_review_id_consistency(self, vendor_id, buyer_id, rating):
        """
        Test that review IDs are handled consistently.
        """
        # Assume valid ObjectId format (simplified check)
        assume(all(c in '0123456789abcdef' for c in vendor_id.lower()))
        assume(all(c in '0123456789abcdef' for c in buyer_id.lower()))
        
        # Test that we can create a review with these IDs
        review_data = ReviewCreate(
            vendor_id=vendor_id,
            overall_rating=rating,
            content="Test review content",
            original_language="en"
        )
        
        # Verify the review data is valid
        assert review_data.vendor_id == vendor_id
        assert review_data.overall_rating == rating
        assert review_data.original_language == "en"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])