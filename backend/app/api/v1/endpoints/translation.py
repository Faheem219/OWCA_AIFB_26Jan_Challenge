"""
Translation service endpoints for multilingual support.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List

from app.services.translation_service import (
    translation_service,
    TranslationRequest,
    BulkTranslationRequest,
    TranslationResult,
    LanguageDetectionResult,
    BulkTranslationResult
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/translate", response_model=TranslationResult)
async def translate_text(translation_request: TranslationRequest) -> TranslationResult:
    """
    Translate text between supported languages.
    
    Args:
        translation_request: Translation request with text and language codes
        
    Returns:
        Translation result
        
    Raises:
        HTTPException: If translation fails or validation errors occur
    """
    try:
        result = await translation_service.translate_text(
            text=translation_request.text,
            source_language=translation_request.source_language,
            target_language=translation_request.target_language,
            context=translation_request.context
        )
        
        logger.info(f"Translation completed: {translation_request.source_language} -> {translation_request.target_language}")
        return result
        
    except ValueError as e:
        logger.error(f"Translation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Translation service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Translation service temporarily unavailable"
        )


@router.post("/detect-language", response_model=LanguageDetectionResult)
async def detect_language(request: Dict[str, str]) -> LanguageDetectionResult:
    """
    Detect the language of given text.
    
    Args:
        request: Dictionary containing 'text' field
        
    Returns:
        Detected language information
        
    Raises:
        HTTPException: If language detection fails
    """
    try:
        text = request.get("text")
        if not text:
            raise ValueError("Text field is required")
        
        result = await translation_service.detect_language(text)
        
        logger.info(f"Language detected: {result.detected_language} (confidence: {result.confidence_score:.2f})")
        return result
        
    except ValueError as e:
        logger.error(f"Language detection validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Language detection service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected language detection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Language detection service temporarily unavailable"
        )


@router.get("/supported-languages")
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get list of supported languages.
    
    Returns:
        Dictionary containing supported languages and language pairs
    """
    try:
        languages = translation_service.get_supported_languages()
        language_pairs = translation_service.get_supported_language_pairs()
        
        return {
            "languages": languages,
            "language_pairs": language_pairs,
            "total_languages": len(languages),
            "total_pairs": sum(len(targets) for targets in language_pairs.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve supported languages"
        )


@router.post("/bulk-translate", response_model=BulkTranslationResult)
async def bulk_translate(bulk_request: BulkTranslationRequest) -> BulkTranslationResult:
    """
    Translate multiple texts in a single request.
    
    Args:
        bulk_request: Bulk translation request
        
    Returns:
        Bulk translation results
        
    Raises:
        HTTPException: If bulk translation fails
    """
    try:
        result = await translation_service.bulk_translate(
            texts=bulk_request.texts,
            source_language=bulk_request.source_language,
            target_language=bulk_request.target_language,
            context=bulk_request.context
        )
        
        logger.info(f"Bulk translation completed: {result.successful_count}/{result.total_count} successful")
        return result
        
    except ValueError as e:
        logger.error(f"Bulk translation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected bulk translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk translation service temporarily unavailable"
        )


@router.get("/health")
async def translation_health_check() -> Dict[str, Any]:
    """
    Check the health of the translation service.
    
    Returns:
        Health status information
    """
    try:
        health_status = await translation_service.health_check()
        
        # Set appropriate HTTP status based on health
        if health_status["status"] == "degraded":
            # Service is partially working
            return health_status
        elif health_status["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_status
            )
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to perform health check"
        )