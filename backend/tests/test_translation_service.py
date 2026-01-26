"""
Unit tests for translation service.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.translation_service import TranslationService
from app.models.translation import (
    TranslationRequest,
    LanguageDetectionRequest,
    BatchTranslationRequest,
    LanguageCode
)


@pytest.fixture
def mock_db():
    """Mock database."""
    db = Mock()
    db.__getitem__ = Mock(return_value=AsyncMock())
    return db


@pytest.fixture
def mock_redis():
    """Mock Redis cache."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    return redis


@pytest.fixture
def translation_service(mock_db, mock_redis):
    """Translation service instance with mocked dependencies."""
    with patch('boto3.client') as mock_boto3:
        mock_boto3.return_value = None  # Simulate no AWS credentials
        service = TranslationService(mock_db, mock_redis)
        return service


class TestTranslationService:
    """Test cases for TranslationService."""
    
    @pytest.mark.asyncio
    async def test_same_language_translation(self, translation_service):
        """Test translation when source and target languages are the same."""
        request = TranslationRequest(
            text="Hello world",
            source_language=LanguageCode.ENGLISH,
            target_language=LanguageCode.ENGLISH
        )
        
        result = await translation_service.translate_text(request)
        
        assert result.original_text == "Hello world"
        assert result.translated_text == "Hello world"
        assert result.source_language == LanguageCode.ENGLISH
        assert result.target_language == LanguageCode.ENGLISH
        assert result.confidence_score == 1.0
        assert result.provider == "no_translation_needed"
        assert not result.cached
    
    @pytest.mark.asyncio
    async def test_language_detection_heuristic(self, translation_service):
        """Test heuristic language detection."""
        request = LanguageDetectionRequest(text="Hello world")
        
        result = await translation_service.detect_language(request)
        
        assert result.text == "Hello world"
        assert result.detected_language == LanguageCode.ENGLISH
        assert result.confidence_score == 0.7
        assert result.provider == "heuristic"
    
    @pytest.mark.asyncio
    async def test_hindi_language_detection_heuristic(self, translation_service):
        """Test heuristic detection for Hindi text."""
        request = LanguageDetectionRequest(text="नमस्ते दुनिया")
        
        result = await translation_service.detect_language(request)
        
        assert result.text == "नमस्ते दुनिया"
        assert result.detected_language == LanguageCode.HINDI
        assert result.confidence_score == 0.8
        assert result.provider == "heuristic"
    
    @pytest.mark.asyncio
    async def test_get_supported_languages(self, translation_service):
        """Test getting supported languages."""
        result = await translation_service.get_supported_languages()
        
        assert result.total_count == 22
        assert len(result.languages) == 22
        
        # Check if Hindi is in the list
        hindi_lang = next((lang for lang in result.languages if lang["code"] == "hi"), None)
        assert hindi_lang is not None
        assert hindi_lang["name"] == "Hindi"
        assert hindi_lang["native_name"] == "हिन्दी"
    
    @pytest.mark.asyncio
    async def test_batch_translation_same_language(self, translation_service):
        """Test batch translation with same source and target language."""
        request = BatchTranslationRequest(
            texts=["Hello", "World", "Test"],
            source_language=LanguageCode.ENGLISH,
            target_language=LanguageCode.ENGLISH
        )
        
        result = await translation_service.translate_batch(request)
        
        assert result.total_count == 3
        assert result.successful_count == 3
        assert result.failed_count == 0
        assert len(result.results) == 3
        
        for i, translation_result in enumerate(result.results):
            assert translation_result.original_text == request.texts[i]
            assert translation_result.translated_text == request.texts[i]
            assert translation_result.provider == "no_translation_needed"
    
    @pytest.mark.asyncio
    async def test_translation_stats_empty(self, translation_service):
        """Test getting translation stats when no data exists."""
        # Mock empty stats
        translation_service.stats_collection.find_one = AsyncMock(return_value=None)
        
        result = await translation_service.get_translation_stats()
        
        assert result.total_translations == 0
        assert result.cache_hit_rate == 0.0
        assert result.average_confidence == 0.0
        assert result.language_pairs == {}
        assert result.provider_usage == {}
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, translation_service):
        """Test cache key generation."""
        text = "Hello world"
        source_lang = "en"
        target_lang = "hi"
        
        key1 = translation_service._generate_cache_key(text, source_lang, target_lang)
        key2 = translation_service._generate_cache_key(text, source_lang, target_lang)
        
        # Same input should generate same key
        assert key1 == key2
        
        # Different input should generate different key
        key3 = translation_service._generate_cache_key("Different text", source_lang, target_lang)
        assert key1 != key3
        
        # Key should contain language codes
        assert source_lang in key1
        assert target_lang in key1
    
    @pytest.mark.asyncio
    async def test_translation_with_aws_unavailable(self, translation_service):
        """Test translation when AWS Translate is not available."""
        # Ensure AWS client is None
        translation_service.aws_translate = None
        
        # Mock Gemini API failure as well
        with patch.object(translation_service, '_translate_with_gemini', return_value=None):
            request = TranslationRequest(
                text="Hello world",
                source_language=LanguageCode.ENGLISH,
                target_language=LanguageCode.HINDI
            )
            
            with pytest.raises(Exception, match="Translation service unavailable"):
                await translation_service.translate_text(request)
    
    @pytest.mark.asyncio
    async def test_close_http_client(self, translation_service):
        """Test closing HTTP client connections."""
        # Mock the aclose method
        translation_service.http_client.aclose = AsyncMock()
        
        await translation_service.close()
        
        translation_service.http_client.aclose.assert_called_once()


class TestTranslationModels:
    """Test translation data models."""
    
    def test_translation_request_validation(self):
        """Test TranslationRequest validation."""
        # Valid request
        request = TranslationRequest(
            text="Hello",
            source_language=LanguageCode.ENGLISH,
            target_language=LanguageCode.HINDI
        )
        assert request.text == "Hello"
        assert request.source_language == LanguageCode.ENGLISH
        assert request.target_language == LanguageCode.HINDI
        
        # Test with context
        request_with_context = TranslationRequest(
            text="Hello",
            source_language=LanguageCode.ENGLISH,
            target_language=LanguageCode.HINDI,
            context="greeting"
        )
        assert request_with_context.context == "greeting"
    
    def test_language_detection_request_validation(self):
        """Test LanguageDetectionRequest validation."""
        request = LanguageDetectionRequest(text="Hello world")
        assert request.text == "Hello world"
    
    def test_batch_translation_request_validation(self):
        """Test BatchTranslationRequest validation."""
        request = BatchTranslationRequest(
            texts=["Hello", "World"],
            source_language=LanguageCode.ENGLISH,
            target_language=LanguageCode.HINDI
        )
        assert len(request.texts) == 2
        assert request.texts[0] == "Hello"
        assert request.texts[1] == "World"