"""
WebRTC models for voice and video communication.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from app.models.translation import LanguageCode


class CallType(str, Enum):
    """Types of WebRTC calls."""
    VOICE = "voice"
    VIDEO = "video"
    SCREEN_SHARE = "screen_share"


class CallStatus(str, Enum):
    """Call status states."""
    INITIATING = "initiating"
    RINGING = "ringing"
    CONNECTED = "connected"
    ENDED = "ended"
    FAILED = "failed"


class SignalType(str, Enum):
    """WebRTC signaling message types."""
    OFFER = "offer"
    ANSWER = "answer"
    ICE_CANDIDATE = "ice_candidate"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class CallInitiateRequest(BaseModel):
    """Request to initiate a call."""
    callee_id: str = Field(..., description="ID of the user to call")
    call_type: CallType = Field(default=CallType.VOICE, description="Type of call")
    conversation_id: Optional[str] = Field(None, description="Associated conversation ID")
    enable_translation: bool = Field(default=True, description="Enable live translation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "callee_id": "user456",
                "call_type": "video",
                "conversation_id": "conv123",
                "enable_translation": True
            }
        }


class CallAnswerRequest(BaseModel):
    """Request to answer a call."""
    call_id: str = Field(..., description="ID of the call to answer")
    accept: bool = Field(..., description="Whether to accept or reject the call")
    
    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call123",
                "accept": True
            }
        }


class WebRTCSignalRequest(BaseModel):
    """WebRTC signaling request."""
    call_id: str = Field(..., description="ID of the call")
    signal_type: SignalType = Field(..., description="Type of signaling message")
    signal_data: Dict[str, Any] = Field(..., description="Signaling data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call123",
                "signal_type": "offer",
                "signal_data": {
                    "sdp": "v=0\r\no=- 123456789 2 IN IP4 127.0.0.1\r\n...",
                    "type": "offer"
                }
            }
        }


class VoiceTranslationRequest(BaseModel):
    """Request for voice translation during a call."""
    call_id: str = Field(..., description="ID of the call")
    audio_data: str = Field(..., description="Base64 encoded audio data")
    source_language: LanguageCode = Field(..., description="Source language")
    target_language: LanguageCode = Field(..., description="Target language")
    
    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call123",
                "audio_data": "base64_encoded_audio_data",
                "source_language": "hi",
                "target_language": "en"
            }
        }


class CallRecordingRequest(BaseModel):
    """Request to control call recording."""
    call_id: str = Field(..., description="ID of the call")
    enable_recording: bool = Field(..., description="Enable or disable recording")
    
    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call123",
                "enable_recording": True
            }
        }


class CallParticipant(BaseModel):
    """Call participant information."""
    user_id: str = Field(..., description="User ID")
    user_name: str = Field(..., description="User display name")
    role: str = Field(..., description="Participant role (caller/callee)")
    preferred_language: LanguageCode = Field(..., description="User's preferred language")
    joined_at: Optional[datetime] = Field(None, description="When user joined the call")
    left_at: Optional[datetime] = Field(None, description="When user left the call")


class CallInfo(BaseModel):
    """Call information."""
    call_id: str = Field(..., description="Unique call identifier")
    call_type: CallType = Field(..., description="Type of call")
    status: CallStatus = Field(..., description="Current call status")
    participants: List[CallParticipant] = Field(..., description="Call participants")
    conversation_id: Optional[str] = Field(None, description="Associated conversation")
    enable_translation: bool = Field(default=False, description="Translation enabled")
    recording_enabled: bool = Field(default=False, description="Recording enabled")
    created_at: datetime = Field(..., description="Call creation time")
    answered_at: Optional[datetime] = Field(None, description="Call answer time")
    connected_at: Optional[datetime] = Field(None, description="Call connection time")
    ended_at: Optional[datetime] = Field(None, description="Call end time")
    duration_seconds: Optional[int] = Field(None, description="Call duration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call123",
                "call_type": "video",
                "status": "connected",
                "participants": [
                    {
                        "user_id": "user123",
                        "user_name": "John Doe",
                        "role": "caller",
                        "preferred_language": "en",
                        "joined_at": "2024-01-01T12:00:00Z"
                    }
                ],
                "conversation_id": "conv123",
                "enable_translation": True,
                "recording_enabled": False,
                "created_at": "2024-01-01T12:00:00Z",
                "connected_at": "2024-01-01T12:00:05Z"
            }
        }


class CallResponse(BaseModel):
    """Response for call operations."""
    call_id: str = Field(..., description="Call ID")
    status: CallStatus = Field(..., description="Call status")
    message: str = Field(..., description="Response message")
    call_info: Optional[CallInfo] = Field(None, description="Detailed call information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call123",
                "status": "connected",
                "message": "Call connected successfully",
                "call_info": {
                    "call_id": "call123",
                    "call_type": "video",
                    "status": "connected"
                }
            }
        }


class VoiceTranslationResponse(BaseModel):
    """Response for voice translation."""
    status: str = Field(..., description="Translation status")
    original_text: Optional[str] = Field(None, description="Original transcribed text")
    translated_text: Optional[str] = Field(None, description="Translated text")
    audio_url: Optional[str] = Field(None, description="URL to translated audio")
    source_language: Optional[LanguageCode] = Field(None, description="Source language")
    target_language: Optional[LanguageCode] = Field(None, description="Target language")
    error: Optional[str] = Field(None, description="Error message if translation failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "translation_sent",
                "original_text": "नमस्ते, आप कैसे हैं?",
                "translated_text": "Hello, how are you?",
                "audio_url": "/api/v1/voice/audio/translated_abc123.mp3",
                "source_language": "hi",
                "target_language": "en"
            }
        }


class CallStatsResponse(BaseModel):
    """Call statistics response."""
    active_calls: int = Field(default=0, description="Number of active calls")
    total_calls_today: int = Field(default=0, description="Total calls today")
    average_call_duration: float = Field(default=0.0, description="Average call duration in minutes")
    translation_usage: Dict[str, int] = Field(default_factory=dict, description="Translation usage by language pair")
    call_types: Dict[str, int] = Field(default_factory=dict, description="Call types distribution")
    
    class Config:
        json_schema_extra = {
            "example": {
                "active_calls": 5,
                "total_calls_today": 42,
                "average_call_duration": 8.5,
                "translation_usage": {
                    "hi-en": 15,
                    "en-hi": 12,
                    "ta-en": 8
                },
                "call_types": {
                    "voice": 25,
                    "video": 15,
                    "screen_share": 2
                }
            }
        }


class WebSocketCallMessage(BaseModel):
    """WebSocket message for call events."""
    type: str = Field(..., description="Message type")
    call_id: str = Field(..., description="Call ID")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "call_invitation",
                "call_id": "call123",
                "data": {
                    "caller_id": "user123",
                    "caller_name": "John Doe",
                    "call_type": "video"
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class CallDemonstrationRequest(BaseModel):
    """Request for video demonstration during a call."""
    call_id: str = Field(..., description="ID of the call")
    demonstration_type: str = Field(..., description="Type of demonstration (product, process, etc.)")
    description: Optional[str] = Field(None, description="Description of what will be demonstrated")
    enable_screen_share: bool = Field(default=False, description="Enable screen sharing")
    
    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call123",
                "demonstration_type": "product",
                "description": "Showing the quality of organic vegetables",
                "enable_screen_share": False
            }
        }


class CallTranscriptionRequest(BaseModel):
    """Request to enable call transcription."""
    call_id: str = Field(..., description="ID of the call")
    enable_transcription: bool = Field(..., description="Enable or disable transcription")
    languages: List[LanguageCode] = Field(default_factory=list, description="Languages to transcribe")
    
    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call123",
                "enable_transcription": True,
                "languages": ["hi", "en"]
            }
        }


class CallTranscriptionResponse(BaseModel):
    """Response for call transcription."""
    call_id: str = Field(..., description="Call ID")
    transcription_enabled: bool = Field(..., description="Whether transcription is enabled")
    supported_languages: List[LanguageCode] = Field(default_factory=list, description="Supported languages")
    message: str = Field(..., description="Response message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call123",
                "transcription_enabled": True,
                "supported_languages": ["hi", "en", "ta"],
                "message": "Transcription enabled for the call"
            }
        }