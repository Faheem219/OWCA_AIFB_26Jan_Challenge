"""
Translation service data models.
"""
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class LanguageCode(str, Enum):
    """Supported language codes for translation."""
    HINDI = "hi"
    ENGLISH = "en"
    TAMIL = "ta"
    TELUGU = "te"
    BENGALI = "bn"
    MARATHI = "mr"
    GUJARATI = "gu"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"
    ODIA = "or"
    ASSAMESE = "as"
    URDU = "ur"
    SANSKRIT = "sa"
    SINDHI = "sd"
    NEPALI = "ne"
    KASHMIRI = "ks"
    DOGRI = "doi"
    MANIPURI = "mni"
    KONKANI = "kok"
    MAITHILI = "mai"
    BODO = "bo"


class TranslationRequest(BaseModel):
    """Request model for text translation."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to translate")
    source_language: LanguageCode = Field(..., description="Source language code")
    target_language: LanguageCode = Field(..., description="Target language code")
    context: Optional[str] = Field(None, max_length=500, description="Context for better translation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "नमस्ते, आप कैसे हैं?",
                "source_language": "hi",
                "target_language": "en",
                "context": "greeting"
            }
        }


class TranslationResult(BaseModel):
    """Result model for text translation."""
    original_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    source_language: LanguageCode = Field(..., description="Detected/provided source language")
    target_language: LanguageCode = Field(..., description="Target language")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Translation confidence score")
    provider: str = Field(..., description="Translation service provider used")
    cached: bool = Field(False, description="Whether result was retrieved from cache")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_text": "नमस्ते, आप कैसे हैं?",
                "translated_text": "Hello, how are you?",
                "source_language": "hi",
                "target_language": "en",
                "confidence_score": 0.95,
                "provider": "aws_translate",
                "cached": False,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class LanguageDetectionRequest(BaseModel):
    """Request model for language detection."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to detect language for")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "नमस्ते, आप कैसे हैं?"
            }
        }


class LanguageDetection(BaseModel):
    """Result model for language detection."""
    text: str = Field(..., description="Input text")
    detected_language: LanguageCode = Field(..., description="Detected language code")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    alternative_languages: List[Dict[str, float]] = Field(
        default_factory=list, 
        description="Alternative language possibilities with scores"
    )
    provider: str = Field(..., description="Detection service provider used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "नमस्ते, आप कैसे हैं?",
                "detected_language": "hi",
                "confidence_score": 0.98,
                "alternative_languages": [
                    {"language": "ur", "score": 0.15},
                    {"language": "ne", "score": 0.05}
                ],
                "provider": "aws_translate",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class BatchTranslationRequest(BaseModel):
    """Request model for batch translation."""
    texts: List[str] = Field(..., min_items=1, max_items=100, description="List of texts to translate")
    source_language: LanguageCode = Field(..., description="Source language code")
    target_language: LanguageCode = Field(..., description="Target language code")
    context: Optional[str] = Field(None, max_length=500, description="Context for better translation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "texts": ["नमस्ते", "धन्यवाद", "अलविदा"],
                "source_language": "hi",
                "target_language": "en",
                "context": "common_phrases"
            }
        }


class BatchTranslationResult(BaseModel):
    """Result model for batch translation."""
    results: List[TranslationResult] = Field(..., description="List of translation results")
    total_count: int = Field(..., description="Total number of translations")
    successful_count: int = Field(..., description="Number of successful translations")
    failed_count: int = Field(..., description="Number of failed translations")
    provider: str = Field(..., description="Translation service provider used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TranslationCache(BaseModel):
    """Model for cached translations."""
    text_hash: str = Field(..., description="Hash of the original text")
    source_language: LanguageCode = Field(..., description="Source language")
    target_language: LanguageCode = Field(..., description="Target language")
    translated_text: str = Field(..., description="Cached translated text")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    provider: str = Field(..., description="Original translation provider")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(default=1, description="Number of times accessed")
    last_accessed: datetime = Field(default_factory=datetime.utcnow)


class SupportedLanguagesResponse(BaseModel):
    """Response model for supported languages."""
    languages: List[Dict[str, str]] = Field(..., description="List of supported languages")
    total_count: int = Field(..., description="Total number of supported languages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "languages": [
                    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
                    {"code": "en", "name": "English", "native_name": "English"},
                    {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"}
                ],
                "total_count": 22
            }
        }


class TranslationStats(BaseModel):
    """Translation service statistics."""
    total_translations: int = Field(default=0)
    cache_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    average_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    language_pairs: Dict[str, int] = Field(default_factory=dict)
    provider_usage: Dict[str, int] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)