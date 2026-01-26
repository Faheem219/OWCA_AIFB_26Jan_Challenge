"""
Voice processing service data models.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from app.models.translation import LanguageCode


class VoiceType(str, Enum):
    """Supported voice types for text-to-speech."""
    STANDARD = "standard"
    NEURAL = "neural"
    WAVENET = "wavenet"


class AudioFormat(str, Enum):
    """Supported audio formats."""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    PCM = "pcm"


class Gender(str, Enum):
    """Voice gender options."""
    MALE = "Male"
    FEMALE = "Female"


class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech conversion."""
    text: str = Field(..., min_length=1, max_length=3000, description="Text to convert to speech")
    language: LanguageCode = Field(..., description="Language code for speech synthesis")
    voice_type: VoiceType = Field(default=VoiceType.STANDARD, description="Voice type to use")
    gender: Optional[Gender] = Field(default=Gender.FEMALE, description="Preferred voice gender")
    audio_format: AudioFormat = Field(default=AudioFormat.MP3, description="Output audio format")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Speech speed multiplier")
    pitch: Optional[str] = Field(default=None, description="Voice pitch adjustment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "नमस्ते, आप कैसे हैं?",
                "language": "hi",
                "voice_type": "standard",
                "gender": "Female",
                "audio_format": "mp3",
                "speed": 1.0
            }
        }


class TextToSpeechResult(BaseModel):
    """Result model for text-to-speech conversion."""
    original_text: str = Field(..., description="Original text")
    language: LanguageCode = Field(..., description="Language used for synthesis")
    audio_url: str = Field(..., description="URL to access the generated audio file")
    audio_format: AudioFormat = Field(..., description="Audio format")
    duration_seconds: Optional[float] = Field(None, description="Audio duration in seconds")
    voice_id: str = Field(..., description="Voice ID used for synthesis")
    provider: str = Field(..., description="TTS service provider used")
    file_size_bytes: int = Field(..., description="Audio file size in bytes")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_text": "नमस्ते, आप कैसे हैं?",
                "language": "hi",
                "audio_url": "/api/v1/voice/audio/abc123.mp3",
                "audio_format": "mp3",
                "duration_seconds": 2.5,
                "voice_id": "Aditi",
                "provider": "aws_polly",
                "file_size_bytes": 45678,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class SpeechToTextRequest(BaseModel):
    """Request model for speech-to-text conversion."""
    audio_data: Optional[str] = Field(None, description="Base64 encoded audio data")
    audio_url: Optional[str] = Field(None, description="URL to audio file")
    language: Optional[LanguageCode] = Field(None, description="Expected language (for better accuracy)")
    audio_format: AudioFormat = Field(default=AudioFormat.WAV, description="Audio format")
    sample_rate: Optional[int] = Field(default=16000, description="Audio sample rate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_data": "base64_encoded_audio_data_here",
                "language": "hi",
                "audio_format": "wav",
                "sample_rate": 16000
            }
        }


class SpeechToTextResult(BaseModel):
    """Result model for speech-to-text conversion."""
    transcribed_text: str = Field(..., description="Transcribed text from audio")
    detected_language: Optional[LanguageCode] = Field(None, description="Detected language")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence score")
    alternatives: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative transcriptions")
    duration_seconds: Optional[float] = Field(None, description="Audio duration processed")
    provider: str = Field(..., description="STT service provider used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "transcribed_text": "नमस्ते, आप कैसे हैं?",
                "detected_language": "hi",
                "confidence_score": 0.95,
                "alternatives": [
                    {"text": "नमस्ते आप कैसे हैं", "confidence": 0.87}
                ],
                "duration_seconds": 2.5,
                "provider": "web_speech_api",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class VoiceTranslationRequest(BaseModel):
    """Request model for voice-to-voice translation."""
    audio_data: Optional[str] = Field(None, description="Base64 encoded audio data")
    audio_url: Optional[str] = Field(None, description="URL to audio file")
    source_language: Optional[LanguageCode] = Field(None, description="Source language (auto-detect if None)")
    target_language: LanguageCode = Field(..., description="Target language for translation")
    audio_format: AudioFormat = Field(default=AudioFormat.WAV, description="Input audio format")
    output_format: AudioFormat = Field(default=AudioFormat.MP3, description="Output audio format")
    voice_type: VoiceType = Field(default=VoiceType.STANDARD, description="Output voice type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_data": "base64_encoded_audio_data_here",
                "source_language": "hi",
                "target_language": "en",
                "audio_format": "wav",
                "output_format": "mp3",
                "voice_type": "standard"
            }
        }


class VoiceTranslationResult(BaseModel):
    """Result model for voice-to-voice translation."""
    original_text: str = Field(..., description="Transcribed original text")
    translated_text: str = Field(..., description="Translated text")
    source_language: LanguageCode = Field(..., description="Detected/provided source language")
    target_language: LanguageCode = Field(..., description="Target language")
    input_audio_duration: Optional[float] = Field(None, description="Input audio duration in seconds")
    output_audio_url: str = Field(..., description="URL to translated audio file")
    output_audio_duration: Optional[float] = Field(None, description="Output audio duration in seconds")
    transcription_confidence: float = Field(..., ge=0.0, le=1.0, description="STT confidence score")
    translation_confidence: float = Field(..., ge=0.0, le=1.0, description="Translation confidence score")
    providers: Dict[str, str] = Field(..., description="Service providers used for each step")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_text": "नमस्ते, आप कैसे हैं?",
                "translated_text": "Hello, how are you?",
                "source_language": "hi",
                "target_language": "en",
                "input_audio_duration": 2.5,
                "output_audio_url": "/api/v1/voice/audio/translated_abc123.mp3",
                "output_audio_duration": 2.8,
                "transcription_confidence": 0.95,
                "translation_confidence": 0.92,
                "providers": {
                    "stt": "web_speech_api",
                    "translation": "aws_translate",
                    "tts": "aws_polly"
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class VoiceCapabilities(BaseModel):
    """Available voice capabilities for each language."""
    language: LanguageCode = Field(..., description="Language code")
    language_name: str = Field(..., description="Language display name")
    available_voices: List[Dict[str, Any]] = Field(..., description="Available voice options")
    supports_neural: bool = Field(default=False, description="Whether neural voices are available")
    supports_ssml: bool = Field(default=False, description="Whether SSML is supported")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "hi",
                "language_name": "Hindi",
                "available_voices": [
                    {
                        "id": "Aditi",
                        "name": "Aditi",
                        "gender": "Female",
                        "voice_type": "standard"
                    }
                ],
                "supports_neural": True,
                "supports_ssml": True
            }
        }


class VoiceCapabilitiesResponse(BaseModel):
    """Response model for voice capabilities."""
    capabilities: List[VoiceCapabilities] = Field(..., description="Voice capabilities by language")
    total_languages: int = Field(..., description="Total number of supported languages")
    total_voices: int = Field(..., description="Total number of available voices")
    
    class Config:
        json_schema_extra = {
            "example": {
                "capabilities": [
                    {
                        "language": "hi",
                        "language_name": "Hindi",
                        "available_voices": [
                            {
                                "id": "Aditi",
                                "name": "Aditi",
                                "gender": "Female",
                                "voice_type": "standard"
                            }
                        ],
                        "supports_neural": True,
                        "supports_ssml": True
                    }
                ],
                "total_languages": 22,
                "total_voices": 45
            }
        }


class AudioFileInfo(BaseModel):
    """Information about an audio file."""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="File storage path")
    file_size_bytes: int = Field(..., description="File size in bytes")
    audio_format: AudioFormat = Field(..., description="Audio format")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")
    sample_rate: Optional[int] = Field(None, description="Audio sample rate")
    channels: Optional[int] = Field(None, description="Number of audio channels")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="File expiration time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "abc123",
                "filename": "speech.mp3",
                "file_path": "/uploads/voice/abc123.mp3",
                "file_size_bytes": 45678,
                "audio_format": "mp3",
                "duration_seconds": 2.5,
                "sample_rate": 22050,
                "channels": 1,
                "created_at": "2024-01-01T12:00:00Z",
                "expires_at": "2024-01-08T12:00:00Z"
            }
        }


class VoiceProcessingStats(BaseModel):
    """Voice processing service statistics."""
    total_tts_requests: int = Field(default=0)
    total_stt_requests: int = Field(default=0)
    total_voice_translations: int = Field(default=0)
    average_tts_duration: float = Field(default=0.0)
    average_stt_accuracy: float = Field(default=0.0)
    language_usage: Dict[str, int] = Field(default_factory=dict)
    provider_usage: Dict[str, int] = Field(default_factory=dict)
    total_audio_files: int = Field(default=0)
    total_storage_bytes: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)