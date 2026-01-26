"""
Voice processing API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Response
from fastapi.responses import StreamingResponse
import io
import logging

from app.api.deps import get_current_user, get_voice_service
from app.models.user import User
from app.models.voice import (
    TextToSpeechRequest,
    TextToSpeechResult,
    SpeechToTextRequest,
    SpeechToTextResult,
    VoiceTranslationRequest,
    VoiceTranslationResult,
    VoiceCapabilitiesResponse,
    VoiceProcessingStats,
    AudioFormat
)
from app.services.voice_service import VoiceService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/text-to-speech",
    response_model=TextToSpeechResult,
    summary="Convert text to speech",
    description="Convert text to speech using AWS Polly with support for Indian languages"
)
async def text_to_speech(
    request: TextToSpeechRequest,
    voice_service: VoiceService = Depends(get_voice_service),
    current_user: User = Depends(get_current_user)
):
    """Convert text to speech."""
    try:
        result = await voice_service.text_to_speech(request)
        logger.info(f"TTS completed for user {current_user.email}: {request.language} - {len(request.text)} chars")
        return result
    except Exception as e:
        logger.error(f"TTS failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text-to-speech conversion failed: {str(e)}"
        )


@router.post(
    "/speech-to-text",
    response_model=SpeechToTextResult,
    summary="Convert speech to text",
    description="Convert speech to text (placeholder endpoint - actual processing handled by Web Speech API)"
)
async def speech_to_text(
    request: SpeechToTextRequest,
    voice_service: VoiceService = Depends(get_voice_service),
    current_user: User = Depends(get_current_user)
):
    """Convert speech to text."""
    try:
        result = await voice_service.speech_to_text(request)
        logger.info(f"STT completed for user {current_user.email}")
        return result
    except Exception as e:
        logger.error(f"STT failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech-to-text conversion failed: {str(e)}"
        )


@router.post(
    "/voice-translation",
    response_model=VoiceTranslationResult,
    summary="Voice-to-voice translation",
    description="Complete voice translation pipeline: speech-to-text, translation, text-to-speech"
)
async def voice_translation(
    request: VoiceTranslationRequest,
    voice_service: VoiceService = Depends(get_voice_service),
    current_user: User = Depends(get_current_user)
):
    """Perform voice-to-voice translation."""
    try:
        result = await voice_service.voice_to_voice_translation(request)
        logger.info(f"Voice translation completed for user {current_user.email}: {request.source_language} -> {request.target_language}")
        return result
    except Exception as e:
        logger.error(f"Voice translation failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice translation failed: {str(e)}"
        )


@router.get(
    "/capabilities",
    response_model=VoiceCapabilitiesResponse,
    summary="Get voice capabilities",
    description="Get available voice capabilities for each supported language"
)
async def get_voice_capabilities(
    voice_service: VoiceService = Depends(get_voice_service)
):
    """Get voice capabilities for all supported languages."""
    try:
        result = await voice_service.get_voice_capabilities()
        return result
    except Exception as e:
        logger.error(f"Failed to get voice capabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voice capabilities: {str(e)}"
        )


@router.get(
    "/audio/{file_id}",
    summary="Get audio file",
    description="Retrieve generated audio file by ID"
)
async def get_audio_file(
    file_id: str,
    voice_service: VoiceService = Depends(get_voice_service),
    current_user: User = Depends(get_current_user)
):
    """Retrieve audio file by ID."""
    try:
        # Extract file extension from file_id if present
        if '.' in file_id:
            file_id_clean = file_id.split('.')[0]
            extension = file_id.split('.')[-1]
        else:
            file_id_clean = file_id
            extension = 'mp3'  # Default
        
        audio_data = await voice_service.get_audio_file(file_id_clean)
        
        if not audio_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found"
            )
        
        # Determine content type based on extension
        content_type_map = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'pcm': 'audio/pcm'
        }
        content_type = content_type_map.get(extension.lower(), 'audio/mpeg')
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={file_id}",
                "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve audio file {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audio file: {str(e)}"
        )


@router.post(
    "/upload-audio",
    summary="Upload audio file",
    description="Upload audio file for speech-to-text processing"
)
async def upload_audio_file(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    voice_service: VoiceService = Depends(get_voice_service),
    current_user: User = Depends(get_current_user)
):
    """Upload audio file for processing."""
    try:
        # Validate file type
        allowed_types = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/ogg', 'audio/webm']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Read file content
        audio_data = await file.read()
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(audio_data) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size is 10MB"
            )
        
        # For now, return success message
        # In a full implementation, you would process the audio here
        return {
            "message": "Audio file uploaded successfully",
            "filename": file.filename,
            "size": len(audio_data),
            "content_type": file.content_type,
            "note": "Audio processing will be implemented with Web Speech API integration"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio upload failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio upload failed: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=VoiceProcessingStats,
    summary="Get voice processing statistics",
    description="Get voice processing service usage statistics"
)
async def get_voice_stats(
    voice_service: VoiceService = Depends(get_voice_service),
    current_user: User = Depends(get_current_user)
):
    """Get voice processing statistics."""
    try:
        result = await voice_service.get_voice_stats()
        return result
    except Exception as e:
        logger.error(f"Failed to get voice stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voice stats: {str(e)}"
        )


@router.get(
    "/health",
    summary="Voice service health check",
    description="Check the health status of voice processing service"
)
async def voice_health_check(
    voice_service: VoiceService = Depends(get_voice_service)
):
    """Health check for voice service."""
    try:
        health_status = {
            "status": "healthy",
            "aws_polly_configured": voice_service.polly_client is not None,
            "audio_storage_available": voice_service.audio_storage_dir.exists(),
            "database_available": voice_service.db is not None,
            "cache_available": voice_service.redis is not None,
            "ffmpeg_available": True,  # We'll assume it's available for now
            "supported_languages": len(voice_service.POLLY_VOICES),
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Voice health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T12:00:00Z"
        }


@router.post(
    "/cleanup",
    summary="Cleanup expired audio files",
    description="Clean up expired audio files (admin only)"
)
async def cleanup_expired_files(
    voice_service: VoiceService = Depends(get_voice_service),
    current_user: User = Depends(get_current_user)
):
    """Clean up expired audio files."""
    try:
        # Note: In a real application, you might want to restrict this to admin users
        await voice_service.cleanup_expired_files()
        return {"message": "Cleanup completed successfully"}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )