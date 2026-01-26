"""
WebRTC API endpoints for voice and video communication.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.core.config import settings
from app.db.mongodb import get_database
from app.db.redis import get_redis
from app.services.webrtc_service import WebRTCService, CallType
from app.services.translation_service import TranslationService
from app.services.voice_service import VoiceService
from app.models.webrtc import (
    CallInitiateRequest, CallAnswerRequest, WebRTCSignalRequest,
    VoiceTranslationRequest, CallRecordingRequest, CallDemonstrationRequest,
    CallTranscriptionRequest, CallResponse, VoiceTranslationResponse,
    CallStatsResponse, CallTranscriptionResponse, CallInfo
)
from app.models.translation import LanguageCode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webrtc", tags=["WebRTC"])
security = HTTPBearer()


async def get_webrtc_service():
    """Get WebRTC service instance."""
    db = await get_database()
    redis = await get_redis()
    translation_service = TranslationService(db, redis)
    voice_service = VoiceService(db, redis, translation_service)
    return WebRTCService(redis, translation_service, voice_service)


async def get_current_user(token: str = Depends(security)):
    """Get current user from JWT token."""
    # Mock implementation - in production, decode JWT and get user info
    return {
        "user_id": "user123",
        "user_name": "John Doe",
        "preferred_language": "en"
    }


@router.post("/calls/initiate", response_model=CallResponse)
async def initiate_call(
    request: CallInitiateRequest,
    webrtc_service: WebRTCService = Depends(get_webrtc_service),
    current_user: dict = Depends(get_current_user)
):
    """Initiate a WebRTC call."""
    try:
        result = await webrtc_service.initiate_call(
            caller_id=current_user["user_id"],
            caller_name=current_user["user_name"],
            callee_id=request.callee_id,
            call_type=request.call_type,
            conversation_id=request.conversation_id,
            enable_translation=request.enable_translation
        )
        
        return CallResponse(
            call_id=result["call_id"],
            status=result["status"],
            message=result["message"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error initiating call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate call"
        )


@router.post("/calls/answer", response_model=CallResponse)
async def answer_call(
    request: CallAnswerRequest,
    webrtc_service: WebRTCService = Depends(get_webrtc_service),
    current_user: dict = Depends(get_current_user)
):
    """Answer or reject a call."""
    try:
        result = await webrtc_service.answer_call(
            call_id=request.call_id,
            user_id=current_user["user_id"],
            accept=request.accept
        )
        
        return CallResponse(
            call_id=result["call_id"],
            status=result["status"],
            message=result["message"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error answering call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to answer call"
        )


@router.post("/calls/{call_id}/signal")
async def handle_webrtc_signal(
    call_id: str,
    request: WebRTCSignalRequest,
    webrtc_service: WebRTCService = Depends(get_webrtc_service),
    current_user: dict = Depends(get_current_user)
):
    """Handle WebRTC signaling messages."""
    try:
        result = await webrtc_service.handle_webrtc_signal(
            call_id=call_id,
            user_id=current_user["user_id"],
            signal_type=request.signal_type.value,
            signal_data=request.signal_data
        )
        
        return {"status": "success", "message": "Signal processed"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error handling WebRTC signal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process signal"
        )


@router.post("/calls/{call_id}/end", response_model=CallResponse)
async def end_call(
    call_id: str,
    webrtc_service: WebRTCService = Depends(get_webrtc_service),
    current_user: dict = Depends(get_current_user)
):
    """End a call."""
    try:
        result = await webrtc_service.end_call(
            call_id=call_id,
            user_id=current_user["user_id"]
        )
        
        return CallResponse(
            call_id=result["call_id"],
            status=result["status"],
            message=result["message"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error ending call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end call"
        )


@router.post("/calls/translate", response_model=VoiceTranslationResponse)
async def translate_voice(
    request: VoiceTranslationRequest,
    webrtc_service: WebRTCService = Depends(get_webrtc_service),
    current_user: dict = Depends(get_current_user)
):
    """Process voice translation during a call."""
    try:
        result = await webrtc_service.process_voice_translation(
            call_id=request.call_id,
            user_id=current_user["user_id"],
            audio_data=request.audio_data,
            source_language=request.source_language,
            target_language=request.target_language
        )
        
        return VoiceTranslationResponse(
            status=result["status"],
            original_text=result.get("original_text"),
            translated_text=result.get("translated_text"),
            audio_url=result.get("audio_url"),
            source_language=request.source_language,
            target_language=request.target_language,
            error=result.get("error")
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing voice translation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process voice translation"
        )


@router.post("/calls/record", response_model=CallResponse)
async def control_recording(
    request: CallRecordingRequest,
    webrtc_service: WebRTCService = Depends(get_webrtc_service),
    current_user: dict = Depends(get_current_user)
):
    """Control call recording."""
    try:
        result = await webrtc_service.record_call(
            call_id=request.call_id,
            user_id=current_user["user_id"],
            enable_recording=request.enable_recording
        )
        
        return CallResponse(
            call_id=result["call_id"],
            status="recording_controlled",
            message=result["message"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error controlling recording: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to control recording"
        )


@router.post("/calls/demonstrate")
async def start_demonstration(
    request: CallDemonstrationRequest,
    webrtc_service: WebRTCService = Depends(get_webrtc_service),
    current_user: dict = Depends(get_current_user)
):
    """Start a video demonstration during a call."""
    try:
        # This is a placeholder for demonstration functionality
        # In a real implementation, this would:
        # 1. Enable screen sharing or camera focus
        # 2. Notify other participants about the demonstration
        # 3. Possibly start recording the demonstration
        
        return {
            "status": "demonstration_started",
            "call_id": request.call_id,
            "message": f"Started {request.demonstration_type} demonstration"
        }
        
    except Exception as e:
        logger.error(f"Error starting demonstration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start demonstration"
        )


@router.post("/calls/transcribe", response_model=CallTranscriptionResponse)
async def control_transcription(
    request: CallTranscriptionRequest,
    webrtc_service: WebRTCService = Depends(get_webrtc_service),
    current_user: dict = Depends(get_current_user)
):
    """Control call transcription."""
    try:
        # This is a placeholder for transcription functionality
        # In a real implementation, this would:
        # 1. Enable/disable real-time transcription
        # 2. Set up language-specific transcription
        # 3. Store transcription results
        
        supported_languages = [
            LanguageCode.HINDI, LanguageCode.ENGLISH, LanguageCode.TAMIL,
            LanguageCode.TELUGU, LanguageCode.BENGALI, LanguageCode.MARATHI
        ]
        
        return CallTranscriptionResponse(
            call_id=request.call_id,
            transcription_enabled=request.enable_transcription,
            supported_languages=supported_languages,
            message=f"Transcription {'enabled' if request.enable_transcription else 'disabled'}"
        )
        
    except Exception as e:
        logger.error(f"Error controlling transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to control transcription"
        )


@router.get("/calls/active", response_model=List[CallInfo])
async def get_active_calls(
    webrtc_service: WebRTCService = Depends(get_webrtc_service),
    current_user: dict = Depends(get_current_user)
):
    """Get active calls for the current user."""
    try:
        calls = await webrtc_service.get_active_calls(current_user["user_id"])
        
        # Convert to CallInfo objects (simplified for demo)
        call_infos = []
        for call_data in calls:
            call_info = CallInfo(
                call_id=call_data["call_id"],
                call_type=CallType(call_data["call_type"]),
                status=call_data["status"],
                participants=[],  # Would be populated from call_data
                conversation_id=call_data.get("conversation_id"),
                enable_translation=call_data.get("enable_translation", False),
                recording_enabled=call_data.get("recording_enabled", False),
                created_at=call_data["created_at"]
            )
            call_infos.append(call_info)
        
        return call_infos
        
    except Exception as e:
        logger.error(f"Error getting active calls: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active calls"
        )


@router.get("/stats", response_model=CallStatsResponse)
async def get_call_stats(
    webrtc_service: WebRTCService = Depends(get_webrtc_service),
    current_user: dict = Depends(get_current_user)
):
    """Get call statistics."""
    try:
        stats = await webrtc_service.get_call_stats()
        
        return CallStatsResponse(
            active_calls=stats["active_calls"],
            total_calls_today=stats["total_calls_today"],
            average_call_duration=stats["average_call_duration"],
            translation_usage=stats["translation_usage"],
            call_types=stats["call_types"]
        )
        
    except Exception as e:
        logger.error(f"Error getting call stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get call statistics"
        )


@router.post("/cleanup")
async def cleanup_expired_calls(
    webrtc_service: WebRTCService = Depends(get_webrtc_service),
    current_user: dict = Depends(get_current_user)
):
    """Clean up expired calls (admin endpoint)."""
    try:
        await webrtc_service.cleanup_expired_calls()
        return {"status": "success", "message": "Expired calls cleaned up"}
        
    except Exception as e:
        logger.error(f"Error cleaning up calls: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up expired calls"
        )