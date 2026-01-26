"""
Voice processing service with AWS Polly integration and audio file handling.
"""
import os
import uuid
import base64
import hashlib
import logging
import asyncio
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from motor.motor_asyncio import AsyncIOMotorDatabase
import aiofiles
from pydub import AudioSegment
from pydub.utils import which

from app.core.config import settings
from app.db.redis import RedisCache
from app.db.mongodb import Collections
from app.models.voice import (
    TextToSpeechRequest,
    TextToSpeechResult,
    SpeechToTextRequest,
    SpeechToTextResult,
    VoiceTranslationRequest,
    VoiceTranslationResult,
    VoiceCapabilities,
    VoiceCapabilitiesResponse,
    AudioFileInfo,
    VoiceProcessingStats,
    VoiceType,
    AudioFormat,
    Gender,
    LanguageCode
)
from app.models.translation import TranslationRequest
from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)


class VoiceService:
    """Voice processing service with AWS Polly integration."""
    
    # AWS Polly voice mapping for Indian languages
    POLLY_VOICES = {
        LanguageCode.HINDI: [
            {"id": "Aditi", "gender": "Female", "type": "standard"},
            {"id": "Kajal", "gender": "Female", "type": "neural"}
        ],
        LanguageCode.ENGLISH: [
            {"id": "Raveena", "gender": "Female", "type": "standard"},
            {"id": "Aria", "gender": "Female", "type": "neural"},
            {"id": "Matthew", "gender": "Male", "type": "neural"}
        ],
        LanguageCode.TAMIL: [
            {"id": "Aditi", "gender": "Female", "type": "standard"}  # Fallback to Hindi voice
        ],
        LanguageCode.TELUGU: [
            {"id": "Aditi", "gender": "Female", "type": "standard"}  # Fallback to Hindi voice
        ],
        LanguageCode.BENGALI: [
            {"id": "Aditi", "gender": "Female", "type": "standard"}  # Fallback to Hindi voice
        ],
        LanguageCode.MARATHI: [
            {"id": "Aditi", "gender": "Female", "type": "standard"}  # Fallback to Hindi voice
        ],
        LanguageCode.GUJARATI: [
            {"id": "Aditi", "gender": "Female", "type": "standard"}  # Fallback to Hindi voice
        ]
    }
    
    # Audio format configurations
    AUDIO_FORMATS = {
        AudioFormat.MP3: {"content_type": "audio/mpeg", "extension": ".mp3"},
        AudioFormat.WAV: {"content_type": "audio/wav", "extension": ".wav"},
        AudioFormat.OGG: {"content_type": "audio/ogg", "extension": ".ogg"},
        AudioFormat.PCM: {"content_type": "audio/pcm", "extension": ".pcm"}
    }
    
    def __init__(self, db: AsyncIOMotorDatabase, redis: RedisCache, translation_service: TranslationService):
        """Initialize voice service."""
        self.db = db
        self.redis = redis
        self.translation_service = translation_service
        self.audio_files_collection = db[Collections.AUDIO_FILES]
        self.voice_stats_collection = db[Collections.VOICE_STATS]
        
        # Initialize AWS Polly client
        self.polly_client = None
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                self.polly_client = boto3.client(
                    'polly',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                logger.info("AWS Polly client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AWS Polly client: {e}")
        
        # Set up audio storage directory
        self.audio_storage_dir = Path(settings.UPLOAD_DIR) / "voice"
        self.audio_storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache settings
        self.cache_ttl = 86400 * 7  # 7 days
        self.audio_cache_prefix = "voice_audio:"
        
        # Check for ffmpeg (required for pydub)
        if not which("ffmpeg"):
            logger.warning("ffmpeg not found. Audio format conversion may be limited.")
    
    async def text_to_speech(self, request: TextToSpeechRequest) -> TextToSpeechResult:
        """Convert text to speech using AWS Polly."""
        # Check cache first
        cache_key = self._generate_tts_cache_key(request)
        cached_result = await self._get_cached_audio(cache_key)
        
        if cached_result:
            logger.info(f"TTS cache hit for language {request.language}")
            return cached_result
        
        # Generate speech using AWS Polly
        if not self.polly_client:
            raise Exception("AWS Polly not configured")
        
        # Select appropriate voice
        voice_id = self._select_voice(request.language, request.gender, request.voice_type)
        
        try:
            # Prepare Polly request
            polly_params = {
                'Text': request.text,
                'OutputFormat': self._get_polly_format(request.audio_format),
                'VoiceId': voice_id,
                'SampleRate': '22050'
            }
            
            # Add speed control if supported
            if request.speed != 1.0:
                # Use SSML for speed control
                ssml_text = f'<speak><prosody rate="{int(request.speed * 100)}%">{request.text}</prosody></speak>'
                polly_params['Text'] = ssml_text
                polly_params['TextType'] = 'ssml'
            
            # Call AWS Polly
            response = self.polly_client.synthesize_speech(**polly_params)
            
            # Save audio file
            file_id = str(uuid.uuid4())
            file_path = await self._save_audio_file(
                response['AudioStream'].read(),
                file_id,
                request.audio_format
            )
            
            # Get audio duration and file size
            duration = await self._get_audio_duration(file_path)
            file_size = os.path.getsize(file_path)
            
            # Create result
            result = TextToSpeechResult(
                original_text=request.text,
                language=request.language,
                audio_url=f"/api/v1/voice/audio/{file_id}{self.AUDIO_FORMATS[request.audio_format]['extension']}",
                audio_format=request.audio_format,
                duration_seconds=duration,
                voice_id=voice_id,
                provider="aws_polly",
                file_size_bytes=file_size
            )
            
            # Cache the result
            await self._cache_audio_result(cache_key, result)
            
            # Store file info in database
            await self._store_audio_file_info(file_id, request.text, file_path, file_size, duration, request.audio_format)
            
            # Update statistics
            await self._update_tts_stats(request.language, voice_id, duration)
            
            return result
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS Polly error: {e}")
            raise Exception(f"Text-to-speech conversion failed: {str(e)}")
    
    async def speech_to_text(self, request: SpeechToTextRequest) -> SpeechToTextResult:
        """Convert speech to text. Note: This is a placeholder for Web Speech API integration."""
        # This method serves as a backend endpoint for receiving STT results from frontend
        # The actual speech recognition happens on the frontend using Web Speech API
        
        if not request.audio_data and not request.audio_url:
            raise ValueError("Either audio_data or audio_url must be provided")
        
        # For now, return a placeholder result
        # In a real implementation, you might use AWS Transcribe or another STT service
        logger.warning("Speech-to-text processing is handled by Web Speech API on frontend")
        
        return SpeechToTextResult(
            transcribed_text="[Speech recognition handled by Web Speech API]",
            detected_language=request.language,
            confidence_score=0.0,
            alternatives=[],
            provider="web_speech_api_placeholder"
        )
    
    async def voice_to_voice_translation(self, request: VoiceTranslationRequest) -> VoiceTranslationResult:
        """Complete voice-to-voice translation pipeline."""
        # Step 1: Speech to Text (placeholder - handled by frontend)
        stt_request = SpeechToTextRequest(
            audio_data=request.audio_data,
            audio_url=request.audio_url,
            language=request.source_language,
            audio_format=request.audio_format
        )
        
        # For demo purposes, we'll simulate STT result
        # In production, this would come from the frontend or a backend STT service
        original_text = "नमस्ते, आप कैसे हैं?"  # Placeholder
        detected_language = request.source_language or LanguageCode.HINDI
        stt_confidence = 0.95
        
        # Step 2: Text Translation
        translation_request = TranslationRequest(
            text=original_text,
            source_language=detected_language,
            target_language=request.target_language
        )
        
        translation_result = await self.translation_service.translate_text(translation_request)
        
        # Step 3: Text to Speech
        tts_request = TextToSpeechRequest(
            text=translation_result.translated_text,
            language=request.target_language,
            voice_type=request.voice_type,
            audio_format=request.output_format
        )
        
        tts_result = await self.text_to_speech(tts_request)
        
        # Combine results
        result = VoiceTranslationResult(
            original_text=original_text,
            translated_text=translation_result.translated_text,
            source_language=detected_language,
            target_language=request.target_language,
            input_audio_duration=2.5,  # Placeholder
            output_audio_url=tts_result.audio_url,
            output_audio_duration=tts_result.duration_seconds,
            transcription_confidence=stt_confidence,
            translation_confidence=translation_result.confidence_score,
            providers={
                "stt": "web_speech_api",
                "translation": translation_result.provider,
                "tts": tts_result.provider
            }
        )
        
        # Update statistics
        await self._update_voice_translation_stats(detected_language, request.target_language)
        
        return result
    
    async def get_voice_capabilities(self) -> VoiceCapabilitiesResponse:
        """Get available voice capabilities for each language."""
        capabilities = []
        total_voices = 0
        
        for language, voices in self.POLLY_VOICES.items():
            language_name = self.translation_service.LANGUAGE_NAMES.get(
                language.value, {"name": language.value}
            )["name"]
            
            voice_list = [
                {
                    "id": voice["id"],
                    "name": voice["id"],
                    "gender": voice["gender"],
                    "voice_type": voice["type"]
                }
                for voice in voices
            ]
            
            capabilities.append(VoiceCapabilities(
                language=language,
                language_name=language_name,
                available_voices=voice_list,
                supports_neural=any(v["type"] == "neural" for v in voices),
                supports_ssml=True
            ))
            
            total_voices += len(voices)
        
        return VoiceCapabilitiesResponse(
            capabilities=capabilities,
            total_languages=len(capabilities),
            total_voices=total_voices
        )
    
    async def get_audio_file(self, file_id: str) -> Optional[bytes]:
        """Retrieve audio file by ID."""
        try:
            # Find file info in database
            file_info = await self.audio_files_collection.find_one({"file_id": file_id})
            if not file_info:
                return None
            
            file_path = Path(file_info["file_path"])
            if not file_path.exists():
                logger.error(f"Audio file not found: {file_path}")
                return None
            
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Error retrieving audio file {file_id}: {e}")
            return None
    
    async def get_voice_stats(self) -> VoiceProcessingStats:
        """Get voice processing statistics."""
        stats_doc = await self.voice_stats_collection.find_one({"_id": "global_voice_stats"})
        
        if not stats_doc:
            return VoiceProcessingStats()
        
        return VoiceProcessingStats(
            total_tts_requests=stats_doc.get("total_tts_requests", 0),
            total_stt_requests=stats_doc.get("total_stt_requests", 0),
            total_voice_translations=stats_doc.get("total_voice_translations", 0),
            average_tts_duration=stats_doc.get("average_tts_duration", 0.0),
            average_stt_accuracy=stats_doc.get("average_stt_accuracy", 0.0),
            language_usage=stats_doc.get("language_usage", {}),
            provider_usage=stats_doc.get("provider_usage", {}),
            total_audio_files=stats_doc.get("total_audio_files", 0),
            total_storage_bytes=stats_doc.get("total_storage_bytes", 0),
            timestamp=stats_doc.get("timestamp", datetime.utcnow())
        )
    
    def _select_voice(self, language: LanguageCode, gender: Optional[Gender], voice_type: VoiceType) -> str:
        """Select appropriate voice for the given parameters."""
        voices = self.POLLY_VOICES.get(language, self.POLLY_VOICES[LanguageCode.ENGLISH])
        
        # Filter by gender if specified
        if gender:
            gender_voices = [v for v in voices if v["gender"] == gender.value]
            if gender_voices:
                voices = gender_voices
        
        # Filter by voice type if specified
        if voice_type != VoiceType.STANDARD:
            type_voices = [v for v in voices if v["type"] == voice_type.value]
            if type_voices:
                voices = type_voices
        
        # Return the first matching voice
        return voices[0]["id"]
    
    def _get_polly_format(self, audio_format: AudioFormat) -> str:
        """Convert our audio format to Polly format."""
        format_map = {
            AudioFormat.MP3: "mp3",
            AudioFormat.WAV: "pcm",
            AudioFormat.OGG: "ogg_vorbis",
            AudioFormat.PCM: "pcm"
        }
        return format_map.get(audio_format, "mp3")
    
    async def _save_audio_file(self, audio_data: bytes, file_id: str, audio_format: AudioFormat) -> Path:
        """Save audio data to file."""
        extension = self.AUDIO_FORMATS[audio_format]["extension"]
        file_path = self.audio_storage_dir / f"{file_id}{extension}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(audio_data)
        
        return file_path
    
    async def _get_audio_duration(self, file_path: Path) -> Optional[float]:
        """Get audio file duration using pydub."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            audio = await loop.run_in_executor(None, AudioSegment.from_file, str(file_path))
            return len(audio) / 1000.0  # Convert milliseconds to seconds
        except Exception as e:
            logger.warning(f"Could not determine audio duration: {e}")
            return None
    
    async def _store_audio_file_info(
        self, 
        file_id: str, 
        original_text: str, 
        file_path: Path, 
        file_size: int, 
        duration: Optional[float],
        audio_format: AudioFormat
    ):
        """Store audio file information in database."""
        file_info = AudioFileInfo(
            file_id=file_id,
            filename=f"{file_id}{self.AUDIO_FORMATS[audio_format]['extension']}",
            file_path=str(file_path),
            file_size_bytes=file_size,
            audio_format=audio_format,
            duration_seconds=duration,
            expires_at=datetime.utcnow() + timedelta(days=7)  # Files expire after 7 days
        )
        
        await self.audio_files_collection.insert_one({
            **file_info.dict(),
            "original_text": original_text,
            "_id": file_id
        })
    
    def _generate_tts_cache_key(self, request: TextToSpeechRequest) -> str:
        """Generate cache key for TTS request."""
        key_data = f"{request.text}:{request.language.value}:{request.voice_type.value}:{request.audio_format.value}:{request.speed}"
        return f"{self.audio_cache_prefix}{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def _get_cached_audio(self, cache_key: str) -> Optional[TextToSpeechResult]:
        """Get cached TTS result."""
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                import json
                return TextToSpeechResult(**json.loads(cached_data))
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        return None
    
    async def _cache_audio_result(self, cache_key: str, result: TextToSpeechResult):
        """Cache TTS result."""
        try:
            await self.redis.setex(cache_key, self.cache_ttl, result.json())
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
    
    async def _update_tts_stats(self, language: LanguageCode, voice_id: str, duration: Optional[float]):
        """Update TTS statistics."""
        try:
            update_data = {
                "$inc": {
                    "total_tts_requests": 1,
                    f"language_usage.{language.value}": 1,
                    f"provider_usage.aws_polly": 1,
                    "total_audio_files": 1
                },
                "$set": {"timestamp": datetime.utcnow()}
            }
            
            if duration:
                update_data["$inc"]["total_tts_duration"] = duration
            
            await self.voice_stats_collection.update_one(
                {"_id": "global_voice_stats"},
                update_data,
                upsert=True
            )
        except Exception as e:
            logger.error(f"Stats update error: {e}")
    
    async def _update_voice_translation_stats(self, source_lang: LanguageCode, target_lang: LanguageCode):
        """Update voice translation statistics."""
        try:
            await self.voice_stats_collection.update_one(
                {"_id": "global_voice_stats"},
                {
                    "$inc": {
                        "total_voice_translations": 1,
                        f"language_usage.{source_lang.value}": 1,
                        f"language_usage.{target_lang.value}": 1
                    },
                    "$set": {"timestamp": datetime.utcnow()}
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Voice translation stats update error: {e}")
    
    async def cleanup_expired_files(self):
        """Clean up expired audio files."""
        try:
            # Find expired files
            expired_files = await self.audio_files_collection.find({
                "expires_at": {"$lt": datetime.utcnow()}
            }).to_list(None)
            
            for file_doc in expired_files:
                try:
                    # Delete physical file
                    file_path = Path(file_doc["file_path"])
                    if file_path.exists():
                        file_path.unlink()
                    
                    # Remove from database
                    await self.audio_files_collection.delete_one({"_id": file_doc["_id"]})
                    
                    logger.info(f"Cleaned up expired audio file: {file_doc['file_id']}")
                    
                except Exception as e:
                    logger.error(f"Error cleaning up file {file_doc['file_id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error during file cleanup: {e}")