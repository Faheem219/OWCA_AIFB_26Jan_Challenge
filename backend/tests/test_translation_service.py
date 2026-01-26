"""
Basic tests for the translation service.

These tests focus on core functionality validation rather than comprehensive testing.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.translation_service import (
    TranslationService,
    TranslationRequest,
    BulkTranslationRequest,
    TranslationResult,
    LanguageDetectionResult,
    BulkTranslationResult
)


class TestTranslationService:
    """Test cases for TranslationService."""
    
    @pytest.fixture
    def translation_service(self):
        """Create a translation service instance for testing."""
        service = TranslationService()
        return service
    
    def test_supported_languages(self, translation_service):
        """Test getting supported languages."""
        languages = translation_service.get_supported_languages()
        
        assert isinstance(languages, dict)
        assert len(languages) == 10  # All supported languages
        assert "en" in languages
        assert "hi" in languages
        assert languages["en"] == "English"
        assert languages["hi"] == "Hindi"
    
    def test_supported_language_pairs(self, translation_service):
        """Test getting supported language pairs."""
        pairs = translation_service.get_supported_language_pairs()
        
        assert isinstance(pairs, dict)
        assert "en" in pairs
        assert "hi" in pairs
        assert "hi" in pairs["en"]  # English to Hindi
        assert "en" in pairs["hi"]  # Hindi to English
        assert "en" not in pairs["en"]  # Same language not supported
    
    def test_validate_language_codes_valid(self, translation_service):
        """Test language code validation with valid codes."""
        is_valid, error_msg = translation_service._validate_language_codes("en", "hi")
        
        assert is_valid is True
        assert error_msg == ""
    
    def test_validate_language_codes_invalid_source(self, translation_service):
        """Test language code validation with invalid source."""
        is_valid, error_msg = translation_service._validate_language_codes("xx", "hi")
        
        assert is_valid is False
        assert "not supported" in error_msg
    
    def test_validate_language_codes_same_language(self, translation_service):
        """Test language code validation with same source and target."""
        is_valid, error_msg = translation_service._validate_language_codes("en", "en")
        
        assert is_valid is False
        assert "cannot be the same" in error_msg
    
    def test_generate_cache_key(self, translation_service):
        """Test cache key generation."""
        key1 = translation_service._generate_cache_key("hello", "en", "hi")
        key2 = translation_service._generate_cache_key("hello", "en", "hi")
        key3 = translation_service._generate_cache_key("world", "en", "hi")
        
        assert key1 == key2  # Same text should generate same key
        assert key1 != key3  # Different text should generate different key
        assert key1.startswith("translation:en:hi:")
    
    @pytest.mark.asyncio
    async def test_translate_text_validation_empty_text(self, translation_service):
        """Test translation with empty text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await translation_service.translate_text("", "en", "hi")
    
    @pytest.mark.asyncio
    async def test_translate_text_validation_invalid_language(self, translation_service):
        """Test translation with invalid language codes."""
        with pytest.raises(ValueError, match="not supported"):
            await translation_service.translate_text("hello", "xx", "hi")
    
    @pytest.mark.asyncio
    async def test_detect_language_validation_empty_text(self, translation_service):
        """Test language detection with empty text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await translation_service.detect_language("")
    
    @pytest.mark.asyncio
    async def test_bulk_translate_validation_empty_list(self, translation_service):
        """Test bulk translation with empty text list."""
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            await translation_service.bulk_translate([], "en", "hi")
    
    @pytest.mark.asyncio
    async def test_bulk_translate_validation_too_many_texts(self, translation_service):
        """Test bulk translation with too many texts."""
        texts = ["text"] * 101  # More than 100 texts
        with pytest.raises(ValueError, match="Maximum 100 texts allowed"):
            await translation_service.bulk_translate(texts, "en", "hi")
    
    @pytest.mark.asyncio
    @patch('app.services.translation_service.get_cached_translation')
    async def test_translate_text_cached_result(self, mock_get_cached, translation_service):
        """Test translation with cached result."""
        # Mock cached translation
        mock_get_cached.return_value = "नमस्ते"
        
        result = await translation_service.translate_text("hello", "en", "hi")
        
        assert isinstance(result, TranslationResult)
        assert result.original_text == "hello"
        assert result.translated_text == "नमस्ते"
        assert result.source_language == "en"
        assert result.target_language == "hi"
        assert result.cached is True
    
    @pytest.mark.asyncio
    @patch('app.services.translation_service.cache')
    async def test_detect_language_cached_result(self, mock_cache, translation_service):
        """Test language detection with cached result."""
        # Mock cached detection result
        cached_result = {
            "text": "hello",
            "detected_language": "en",
            "confidence_score": 0.95,
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_cache.get = AsyncMock(return_value=cached_result)
        
        result = await translation_service.detect_language("hello")
        
        assert isinstance(result, LanguageDetectionResult)
        assert result.text == "hello"
        assert result.detected_language == "en"
        assert result.confidence_score == 0.95
    
    @pytest.mark.asyncio
    @patch('app.services.translation_service.translation_service.translate_text')
    async def test_bulk_translate_success(self, mock_translate, translation_service):
        """Test successful bulk translation."""
        # Mock individual translation results
        mock_translate.side_effect = [
            TranslationResult(
                original_text="hello",
                translated_text="नमस्ते",
                source_language="en",
                target_language="hi"
            ),
            TranslationResult(
                original_text="world",
                translated_text="दुनिया",
                source_language="en",
                target_language="hi"
            )
        ]
        
        result = await translation_service.bulk_translate(
            ["hello", "world"], "en", "hi"
        )
        
        assert isinstance(result, BulkTranslationResult)
        assert result.total_count == 2
        assert result.successful_count == 2
        assert result.failed_count == 0
        assert len(result.results) == 2
    
    @pytest.mark.asyncio
    async def test_health_check_no_aws_client(self, translation_service):
        """Test health check when AWS client is not available."""
        translation_service.translate_client = None
        
        health_status = await translation_service.health_check()
        
        assert health_status["service"] == "translation"
        assert health_status["status"] == "degraded"
        assert health_status["aws_translate"] == "unavailable"
    
    @pytest.mark.asyncio
    @patch('app.services.translation_service.cache')
    async def test_health_check_cache_error(self, mock_cache, translation_service):
        """Test health check when cache is not available."""
        mock_cache.set.side_effect = Exception("Cache error")
        
        health_status = await translation_service.health_check()
        
        assert health_status["service"] == "translation"
        assert health_status["cache"] == "error"
        # Status should be degraded if cache fails
        assert health_status["status"] in ["degraded", "healthy"]  # Depends on AWS client status


class TestTranslationModels:
    """Test cases for translation data models."""
    
    def test_translation_request_validation(self):
        """Test TranslationRequest validation."""
        # Valid request
        request = TranslationRequest(
            text="hello",
            source_language="en",
            target_language="hi"
        )
        assert request.text == "hello"
        assert request.source_language == "en"
        assert request.target_language == "hi"
        assert request.context is None
        
        # Test with context
        request_with_context = TranslationRequest(
            text="hello",
            source_language="en",
            target_language="hi",
            context="greeting"
        )
        assert request_with_context.context == "greeting"
    
    def test_translation_request_validation_errors(self):
        """Test TranslationRequest validation errors."""
        # Empty text
        with pytest.raises(ValueError):
            TranslationRequest(
                text="",
                source_language="en",
                target_language="hi"
            )
        
        # Text too long
        with pytest.raises(ValueError):
            TranslationRequest(
                text="x" * 10001,  # Exceeds max length
                source_language="en",
                target_language="hi"
            )
    
    def test_bulk_translation_request_validation(self):
        """Test BulkTranslationRequest validation."""
        # Valid request
        request = BulkTranslationRequest(
            texts=["hello", "world"],
            source_language="en",
            target_language="hi"
        )
        assert len(request.texts) == 2
        assert request.texts[0] == "hello"
        
        # Empty texts list
        with pytest.raises(ValueError):
            BulkTranslationRequest(
                texts=[],
                source_language="en",
                target_language="hi"
            )
        
        # Too many texts
        with pytest.raises(ValueError):
            BulkTranslationRequest(
                texts=["text"] * 101,
                source_language="en",
                target_language="hi"
            )
    
    def test_translation_result_model(self):
        """Test TranslationResult model."""
        result = TranslationResult(
            original_text="hello",
            translated_text="नमस्ते",
            source_language="en",
            target_language="hi"
        )
        
        assert result.original_text == "hello"
        assert result.translated_text == "नमस्ते"
        assert result.source_language == "en"
        assert result.target_language == "hi"
        assert result.cached is False
        assert isinstance(result.timestamp, datetime)
    
    def test_language_detection_result_model(self):
        """Test LanguageDetectionResult model."""
        result = LanguageDetectionResult(
            text="hello",
            detected_language="en",
            confidence_score=0.95
        )
        
        assert result.text == "hello"
        assert result.detected_language == "en"
        assert result.confidence_score == 0.95
        assert isinstance(result.timestamp, datetime)
    
    def test_bulk_translation_result_model(self):
        """Test BulkTranslationResult model."""
        individual_results = [
            TranslationResult(
                original_text="hello",
                translated_text="नमस्ते",
                source_language="en",
                target_language="hi"
            )
        ]
        
        result = BulkTranslationResult(
            results=individual_results,
            total_count=1,
            successful_count=1,
            failed_count=0
        )
        
        assert len(result.results) == 1
        assert result.total_count == 1
        assert result.successful_count == 1
        assert result.failed_count == 0
        assert isinstance(result.timestamp, datetime)