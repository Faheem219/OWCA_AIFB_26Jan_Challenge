#!/usr/bin/env python3
"""
Demo script to showcase the translation service functionality.
"""
import asyncio
import sys
import os
from unittest.mock import AsyncMock

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.translation_service import TranslationService
from app.models.translation import (
    TranslationRequest,
    LanguageDetectionRequest,
    BatchTranslationRequest,
    LanguageCode
)


async def demo_translation_service():
    """Demonstrate translation service functionality."""
    print("🌍 Multilingual Mandi Translation Service Demo")
    print("=" * 50)
    
    # Mock database and Redis for demo
    from unittest.mock import MagicMock
    
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_collection.update_one = AsyncMock()
    
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock()
    
    # Initialize translation service (without AWS credentials for demo)
    service = TranslationService(mock_db, mock_redis)
    # Ensure AWS client is None for demo
    service.aws_translate = None
    
    print("\n1. 📋 Supported Languages:")
    languages = await service.get_supported_languages()
    print(f"   Total supported languages: {languages.total_count}")
    for lang in languages.languages[:5]:  # Show first 5
        print(f"   • {lang['code']}: {lang['name']} ({lang['native_name']})")
    print("   ... and 17 more languages")
    
    print("\n2. 🔄 Same Language Translation (No Translation Needed):")
    request = TranslationRequest(
        text="Hello, welcome to Multilingual Mandi!",
        source_language=LanguageCode.ENGLISH,
        target_language=LanguageCode.ENGLISH
    )
    result = await service.translate_text(request)
    print(f"   Original: {result.original_text}")
    print(f"   Translated: {result.translated_text}")
    print(f"   Provider: {result.provider}")
    print(f"   Confidence: {result.confidence_score}")
    
    print("\n3. 🔍 Language Detection:")
    detection_tests = [
        "Hello world",
        "नमस्ते दुनिया",
        "வணக்கம் உலகம்",
        "হ্যালো বিশ্ব"
    ]
    
    for text in detection_tests:
        request = LanguageDetectionRequest(text=text)
        result = await service.detect_language(request)
        lang_name = service.LANGUAGE_NAMES.get(result.detected_language.value, {}).get("name", "Unknown")
        print(f"   Text: '{text}' → Detected: {lang_name} ({result.detected_language.value}) [{result.confidence_score:.2f}]")
    
    print("\n4. 📦 Batch Translation (Same Language):")
    batch_request = BatchTranslationRequest(
        texts=["Hello", "Thank you", "Goodbye", "Welcome"],
        source_language=LanguageCode.ENGLISH,
        target_language=LanguageCode.ENGLISH
    )
    batch_result = await service.translate_batch(batch_request)
    print(f"   Total texts: {batch_result.total_count}")
    print(f"   Successful: {batch_result.successful_count}")
    print(f"   Failed: {batch_result.failed_count}")
    for i, result in enumerate(batch_result.results):
        print(f"   {i+1}. '{result.original_text}' → '{result.translated_text}'")
    
    print("\n5. 📊 Translation Statistics:")
    stats = await service.get_translation_stats()
    print(f"   Total translations: {stats.total_translations}")
    print(f"   Cache hit rate: {stats.cache_hit_rate:.2%}")
    print(f"   Average confidence: {stats.average_confidence:.2f}")
    
    print("\n6. 🔧 Service Configuration:")
    print(f"   AWS Translate configured: {service.aws_translate is not None}")
    print(f"   HTTP client available: {service.http_client is not None}")
    print(f"   Cache TTL: {service.cache_ttl} seconds")
    print(f"   Cache prefix: {service.cache_prefix}")
    
    print("\n7. 🌐 Language Support Matrix:")
    print("   The service supports translation between any of these language pairs:")
    major_languages = ["hi", "en", "ta", "te", "bn", "mr", "gu"]
    for source in major_languages[:3]:
        source_name = service.LANGUAGE_NAMES[source]["name"]
        targets = [service.LANGUAGE_NAMES[target]["name"] for target in major_languages if target != source]
        print(f"   {source_name} → {', '.join(targets[:4])}...")
    
    print("\n✅ Translation Service Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("• ✅ Support for 22 Indian languages")
    print("• ✅ Language detection with heuristic fallback")
    print("• ✅ Batch translation capabilities")
    print("• ✅ Caching layer for performance")
    print("• ✅ AWS Translate integration (with fallback)")
    print("• ✅ Comprehensive error handling")
    print("• ✅ Statistics and monitoring")
    
    # Clean up
    await service.close()


if __name__ == "__main__":
    asyncio.run(demo_translation_service())