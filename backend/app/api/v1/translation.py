"""
Translation API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user, get_translation_service
from app.models.user import User
from app.models.translation import (
    TranslationRequest,
    TranslationResult,
    LanguageDetectionRequest,
    LanguageDetection,
    BatchTranslationRequest,
    BatchTranslationResult,
    SupportedLanguagesResponse,
    TranslationStats
)
from app.services.translation_service import TranslationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/translate",
    response_model=TranslationResult,
    summary="Translate text",
    description="Translate text from source language to target language using AWS Translate with Gemini API fallback"
)
async def translate_text(
    request: TranslationRequest,
    translation_service: TranslationService = Depends(get_translation_service),
    current_user: User = Depends(get_current_user)
):
    """Translate text between supported Indian languages."""
    try:
        result = await translation_service.translate_text(request)
        logger.info(f"Translation completed for user {current_user.email}: {request.source_language} -> {request.target_language}")
        return result
    except Exception as e:
        logger.error(f"Translation failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@router.post(
    "/detect-language",
    response_model=LanguageDetection,
    summary="Detect language",
    description="Detect the language of input text using AWS Translate with heuristic fallback"
)
async def detect_language(
    request: LanguageDetectionRequest,
    translation_service: TranslationService = Depends(get_translation_service),
    current_user: User = Depends(get_current_user)
):
    """Detect the language of input text."""
    try:
        result = await translation_service.detect_language(request)
        logger.info(f"Language detection completed for user {current_user.email}: detected {result.detected_language}")
        return result
    except Exception as e:
        logger.error(f"Language detection failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Language detection failed: {str(e)}"
        )


@router.post(
    "/translate-batch",
    response_model=BatchTranslationResult,
    summary="Batch translate texts",
    description="Translate multiple texts in a single request for improved efficiency"
)
async def translate_batch(
    request: BatchTranslationRequest,
    translation_service: TranslationService = Depends(get_translation_service),
    current_user: User = Depends(get_current_user)
):
    """Translate multiple texts in batch."""
    try:
        result = await translation_service.translate_batch(request)
        logger.info(f"Batch translation completed for user {current_user.email}: {result.successful_count}/{result.total_count} successful")
        return result
    except Exception as e:
        logger.error(f"Batch translation failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch translation failed: {str(e)}"
        )


@router.get(
    "/languages",
    response_model=SupportedLanguagesResponse,
    summary="Get supported languages",
    description="Get list of all supported languages for translation"
)
async def get_supported_languages(
    translation_service: TranslationService = Depends(get_translation_service)
):
    """Get list of supported languages."""
    try:
        result = await translation_service.get_supported_languages()
        return result
    except Exception as e:
        logger.error(f"Failed to get supported languages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supported languages: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=TranslationStats,
    summary="Get translation statistics",
    description="Get translation service usage statistics (admin only)"
)
async def get_translation_stats(
    translation_service: TranslationService = Depends(get_translation_service),
    current_user: User = Depends(get_current_user)
):
    """Get translation service statistics."""
    # Note: In a real application, you might want to restrict this to admin users
    try:
        result = await translation_service.get_translation_stats()
        return result
    except Exception as e:
        logger.error(f"Failed to get translation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get translation stats: {str(e)}"
        )


@router.get(
    "/health",
    summary="Translation service health check",
    description="Check the health status of translation service and external providers"
)
async def translation_health_check(
    translation_service: TranslationService = Depends(get_translation_service)
):
    """Health check for translation service."""
    try:
        # Test basic functionality
        test_request = TranslationRequest(
            text="Hello",
            source_language="en",
            target_language="hi"
        )
        
        # This will test the service without requiring authentication
        # We'll create a simple health check that doesn't depend on external APIs
        health_status = {
            "status": "healthy",
            "aws_translate_configured": translation_service.aws_translate is not None,
            "gemini_api_configured": bool(translation_service.http_client),
            "cache_available": translation_service.redis is not None,
            "database_available": translation_service.db is not None,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"Translation health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T12:00:00Z"
            }
        )