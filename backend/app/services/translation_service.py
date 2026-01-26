"""
Translation service with AWS Translate integration and caching.
"""
import hashlib
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from motor.motor_asyncio import AsyncIOMotorDatabase
import httpx

from app.core.config import settings
from app.db.redis import RedisCache
from app.db.mongodb import Collections
from app.models.translation import (
    TranslationRequest,
    TranslationResult,
    LanguageDetectionRequest,
    LanguageDetection,
    BatchTranslationRequest,
    BatchTranslationResult,
    TranslationCache,
    SupportedLanguagesResponse,
    TranslationStats,
    LanguageCode
)

logger = logging.getLogger(__name__)


class TranslationService:
    """Translation service with AWS Translate integration and caching."""
    
    # Language mapping for AWS Translate
    AWS_LANGUAGE_MAP = {
        "hi": "hi",      # Hindi
        "en": "en",      # English
        "ta": "ta",      # Tamil
        "te": "te",      # Telugu
        "bn": "bn",      # Bengali
        "mr": "mr",      # Marathi
        "gu": "gu",      # Gujarati
        "kn": "kn",      # Kannada
        "ml": "ml",      # Malayalam
        "pa": "pa",      # Punjabi
        "or": "or",      # Odia
        "as": "as",      # Assamese
        "ur": "ur",      # Urdu
        # Note: Some languages may not be supported by AWS Translate
        # These will fallback to Gemini API
    }
    
    # Language names for display
    LANGUAGE_NAMES = {
        "hi": {"name": "Hindi", "native_name": "हिन्दी"},
        "en": {"name": "English", "native_name": "English"},
        "ta": {"name": "Tamil", "native_name": "தமிழ்"},
        "te": {"name": "Telugu", "native_name": "తెలుగు"},
        "bn": {"name": "Bengali", "native_name": "বাংলা"},
        "mr": {"name": "Marathi", "native_name": "मराठी"},
        "gu": {"name": "Gujarati", "native_name": "ગુજરાતી"},
        "kn": {"name": "Kannada", "native_name": "ಕನ್ನಡ"},
        "ml": {"name": "Malayalam", "native_name": "മലയാളം"},
        "pa": {"name": "Punjabi", "native_name": "ਪੰਜਾਬੀ"},
        "or": {"name": "Odia", "native_name": "ଓଡ଼ିଆ"},
        "as": {"name": "Assamese", "native_name": "অসমীয়া"},
        "ur": {"name": "Urdu", "native_name": "اردو"},
        "sa": {"name": "Sanskrit", "native_name": "संस्कृतम्"},
        "sd": {"name": "Sindhi", "native_name": "سنڌي"},
        "ne": {"name": "Nepali", "native_name": "नेपाली"},
        "ks": {"name": "Kashmiri", "native_name": "कॉशुर"},
        "doi": {"name": "Dogri", "native_name": "डोगरी"},
        "mni": {"name": "Manipuri", "native_name": "মৈতৈলোন্"},
        "kok": {"name": "Konkani", "native_name": "कोंकणी"},
        "mai": {"name": "Maithili", "native_name": "मैथिली"},
        "bo": {"name": "Bodo", "native_name": "बर'"},
    }
    
    def __init__(self, db: AsyncIOMotorDatabase, redis: RedisCache):
        """Initialize translation service."""
        self.db = db
        self.redis = redis
        self.cache_collection = db[Collections.TRANSLATIONS_CACHE]
        self.stats_collection = db[Collections.TRANSLATION_STATS]
        
        # Initialize AWS Translate client
        self.aws_translate = None
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                self.aws_translate = boto3.client(
                    'translate',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                logger.info("AWS Translate client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AWS Translate client: {e}")
        
        # Initialize HTTP client for Gemini API fallback
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Cache settings
        self.cache_ttl = 86400 * 7  # 7 days
        self.cache_prefix = "translation:"
    
    async def translate_text(
        self, 
        request: TranslationRequest
    ) -> TranslationResult:
        """Translate text from source to target language."""
        # Check if source and target languages are the same
        if request.source_language == request.target_language:
            return TranslationResult(
                original_text=request.text,
                translated_text=request.text,
                source_language=request.source_language,
                target_language=request.target_language,
                confidence_score=1.0,
                provider="no_translation_needed",
                cached=False
            )
        
        # Check cache first
        cached_result = await self._get_cached_translation(
            request.text, 
            request.source_language, 
            request.target_language
        )
        
        if cached_result:
            logger.info(f"Cache hit for translation: {request.source_language} -> {request.target_language}")
            await self._update_cache_access(cached_result)
            return TranslationResult(
                original_text=request.text,
                translated_text=cached_result.translated_text,
                source_language=request.source_language,
                target_language=request.target_language,
                confidence_score=cached_result.confidence_score,
                provider=cached_result.provider,
                cached=True
            )
        
        # Try AWS Translate first
        result = await self._translate_with_aws(request)
        
        # Fallback to Gemini API if AWS fails
        if not result:
            result = await self._translate_with_gemini(request)
        
        # If both fail, return error
        if not result:
            logger.error(f"All translation providers failed for: {request.source_language} -> {request.target_language}")
            raise Exception("Translation service unavailable")
        
        # Cache the result
        await self._cache_translation(request, result)
        
        # Update statistics
        await self._update_translation_stats(request.source_language, request.target_language, result.provider)
        
        return result
    
    async def detect_language(self, request: LanguageDetectionRequest) -> LanguageDetection:
        """Detect the language of input text."""
        # Try AWS Translate first
        if self.aws_translate:
            try:
                # AWS Translate uses detect_dominant_language method
                response = self.aws_translate.detect_dominant_language(Text=request.text)
                
                if response.get('Languages'):
                    dominant_lang = response['Languages'][0]
                    language_code = dominant_lang['LanguageCode']
                    confidence = dominant_lang['Score']
                    
                    # Map AWS language code to our supported languages
                    if language_code in [lang.value for lang in LanguageCode]:
                        alternatives = [
                            {"language": lang['LanguageCode'], "score": lang['Score']}
                            for lang in response['Languages'][1:3]  # Top 2 alternatives
                            if lang['LanguageCode'] in [l.value for l in LanguageCode]
                        ]
                        
                        return LanguageDetection(
                            text=request.text,
                            detected_language=LanguageCode(language_code),
                            confidence_score=confidence,
                            alternative_languages=alternatives,
                            provider="aws_translate"
                        )
                        
            except Exception as e:
                logger.warning(f"AWS language detection failed: {e}")
        
        # Fallback to simple heuristic detection
        return await self._detect_language_heuristic(request)
    
    async def translate_batch(self, request: BatchTranslationRequest) -> BatchTranslationResult:
        """Translate multiple texts in batch."""
        results = []
        successful_count = 0
        failed_count = 0
        
        for text in request.texts:
            try:
                translation_request = TranslationRequest(
                    text=text,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    context=request.context
                )
                
                result = await self.translate_text(translation_request)
                results.append(result)
                successful_count += 1
                
            except Exception as e:
                logger.error(f"Batch translation failed for text '{text}': {e}")
                failed_count += 1
                # Add failed result
                results.append(TranslationResult(
                    original_text=text,
                    translated_text=text,  # Return original text on failure
                    source_language=request.source_language,
                    target_language=request.target_language,
                    confidence_score=0.0,
                    provider="failed",
                    cached=False
                ))
        
        return BatchTranslationResult(
            results=results,
            total_count=len(request.texts),
            successful_count=successful_count,
            failed_count=failed_count,
            provider="mixed" if failed_count > 0 else results[0].provider if results else "none"
        )
    
    async def get_supported_languages(self) -> SupportedLanguagesResponse:
        """Get list of supported languages."""
        languages = [
            {
                "code": code,
                "name": info["name"],
                "native_name": info["native_name"]
            }
            for code, info in self.LANGUAGE_NAMES.items()
        ]
        
        return SupportedLanguagesResponse(
            languages=languages,
            total_count=len(languages)
        )
    
    async def get_translation_stats(self) -> TranslationStats:
        """Get translation service statistics."""
        # Get stats from database
        stats_doc = await self.stats_collection.find_one({"_id": "global_stats"})
        
        if not stats_doc:
            return TranslationStats()
        
        return TranslationStats(
            total_translations=stats_doc.get("total_translations", 0),
            cache_hit_rate=stats_doc.get("cache_hit_rate", 0.0),
            average_confidence=stats_doc.get("average_confidence", 0.0),
            language_pairs=stats_doc.get("language_pairs", {}),
            provider_usage=stats_doc.get("provider_usage", {}),
            timestamp=stats_doc.get("timestamp", datetime.utcnow())
        )
    
    async def _translate_with_aws(self, request: TranslationRequest) -> Optional[TranslationResult]:
        """Translate using AWS Translate."""
        if not self.aws_translate:
            return None
        
        # Check if languages are supported by AWS
        if (request.source_language not in self.AWS_LANGUAGE_MAP or 
            request.target_language not in self.AWS_LANGUAGE_MAP):
            return None
        
        try:
            response = self.aws_translate.translate_text(
                Text=request.text,
                SourceLanguageCode=self.AWS_LANGUAGE_MAP[request.source_language],
                TargetLanguageCode=self.AWS_LANGUAGE_MAP[request.target_language]
            )
            
            return TranslationResult(
                original_text=request.text,
                translated_text=response['TranslatedText'],
                source_language=request.source_language,
                target_language=request.target_language,
                confidence_score=0.9,  # AWS doesn't provide confidence scores
                provider="aws_translate",
                cached=False
            )
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS Translate error: {e}")
            return None
    
    async def _translate_with_gemini(self, request: TranslationRequest) -> Optional[TranslationResult]:
        """Translate using Google Gemini API as fallback."""
        if not settings.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured")
            return None
        
        try:
            # Construct prompt for Gemini
            source_lang_name = self.LANGUAGE_NAMES.get(request.source_language, {}).get("name", request.source_language)
            target_lang_name = self.LANGUAGE_NAMES.get(request.target_language, {}).get("name", request.target_language)
            
            prompt = f"""Translate the following text from {source_lang_name} to {target_lang_name}. 
            Provide only the translation without any additional text or explanation.
            
            Text to translate: {request.text}
            
            Translation:"""
            
            # Make API call to Gemini
            headers = {
                "Content-Type": "application/json",
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={settings.GEMINI_API_KEY}"
            
            response = await self.http_client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("candidates") and data["candidates"][0].get("content"):
                    translated_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
                    return TranslationResult(
                        original_text=request.text,
                        translated_text=translated_text,
                        source_language=request.source_language,
                        target_language=request.target_language,
                        confidence_score=0.8,  # Estimated confidence for Gemini
                        provider="gemini_api",
                        cached=False
                    )
            
            logger.error(f"Gemini API error: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Gemini translation error: {e}")
            return None
    
    async def _detect_language_heuristic(self, request: LanguageDetectionRequest) -> LanguageDetection:
        """Simple heuristic language detection as fallback."""
        text = request.text.lower()
        
        # Simple character-based detection for major Indian languages
        if any(char in text for char in "हिंदी"):
            detected_lang = LanguageCode.HINDI
            confidence = 0.8
        elif any(char in text for char in "தமிழ்"):
            detected_lang = LanguageCode.TAMIL
            confidence = 0.8
        elif any(char in text for char in "తెలుగు"):
            detected_lang = LanguageCode.TELUGU
            confidence = 0.8
        elif any(char in text for char in "বাংলা"):
            detected_lang = LanguageCode.BENGALI
            confidence = 0.8
        elif any(char in text for char in "ગુજરાતી"):
            detected_lang = LanguageCode.GUJARATI
            confidence = 0.8
        elif text.isascii():
            detected_lang = LanguageCode.ENGLISH
            confidence = 0.7
        else:
            # Default to Hindi for unknown scripts
            detected_lang = LanguageCode.HINDI
            confidence = 0.5
        
        return LanguageDetection(
            text=request.text,
            detected_language=detected_lang,
            confidence_score=confidence,
            alternative_languages=[],
            provider="heuristic"
        )
    
    def _generate_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key for translation."""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"{self.cache_prefix}{source_lang}:{target_lang}:{text_hash}"
    
    async def _get_cached_translation(
        self, 
        text: str, 
        source_lang: LanguageCode, 
        target_lang: LanguageCode
    ) -> Optional[TranslationCache]:
        """Get cached translation from Redis."""
        cache_key = self._generate_cache_key(text, source_lang.value, target_lang.value)
        
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return TranslationCache(**json.loads(cached_data))
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        
        return None
    
    async def _cache_translation(self, request: TranslationRequest, result: TranslationResult):
        """Cache translation result."""
        cache_key = self._generate_cache_key(
            request.text, 
            request.source_language.value, 
            request.target_language.value
        )
        
        cache_data = TranslationCache(
            text_hash=hashlib.md5(request.text.encode('utf-8')).hexdigest(),
            source_language=request.source_language,
            target_language=request.target_language,
            translated_text=result.translated_text,
            confidence_score=result.confidence_score,
            provider=result.provider
        )
        
        try:
            await self.redis.setex(
                cache_key, 
                self.cache_ttl, 
                cache_data.json()
            )
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
    
    async def _update_cache_access(self, cached_result: TranslationCache):
        """Update cache access statistics."""
        # This could be implemented to track cache usage patterns
        pass
    
    async def _update_translation_stats(self, source_lang: LanguageCode, target_lang: LanguageCode, provider: str):
        """Update translation statistics."""
        try:
            language_pair = f"{source_lang.value}-{target_lang.value}"
            
            await self.stats_collection.update_one(
                {"_id": "global_stats"},
                {
                    "$inc": {
                        "total_translations": 1,
                        f"language_pairs.{language_pair}": 1,
                        f"provider_usage.{provider}": 1
                    },
                    "$set": {
                        "timestamp": datetime.utcnow()
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Stats update error: {e}")
    
    async def close(self):
        """Close HTTP client connections."""
        await self.http_client.aclose()