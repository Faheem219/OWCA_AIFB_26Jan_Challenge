"""
WebRTC service for voice and video communication with live translation.
"""
import json
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from app.db.redis import RedisCache
from app.db.mongodb import Collections
from app.models.translation import LanguageCode, TranslationRequest
from app.services.translation_service import TranslationService
from app.services.voice_service import VoiceService

logger = logging.getLogger(__name__)


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


class WebRTCService:
    """Service for managing WebRTC voice and video calls."""
    
    def __init__(self, redis: RedisCache, translation_service: TranslationService, voice_service: VoiceService):
        """Initialize WebRTC service."""
        self.redis = redis
        self.translation_service = translation_service
        self.voice_service = voice_service
        
        # Redis keys for call management
        self.active_calls_key = "webrtc:active_calls"
        self.call_participants_prefix = "webrtc:call:"
        self.user_calls_prefix = "webrtc:user_calls:"
        self.signaling_prefix = "webrtc:signaling:"
        
        # Call settings
        self.max_call_duration = 3600  # 1 hour max
        self.call_timeout = 30  # 30 seconds to answer
        
    async def initiate_call(
        self,
        caller_id: str,
        caller_name: str,
        callee_id: str,
        call_type: CallType,
        conversation_id: Optional[str] = None,
        enable_translation: bool = True
    ) -> Dict[str, Any]:
        """Initiate a WebRTC call."""
        call_id = str(uuid.uuid4())
        
        # Check if callee is available
        is_online = await self.redis.sismember("online_users", callee_id)
        if not is_online:
            raise ValueError("Callee is not online")
        
        # Check if callee is already in a call
        existing_call = await self.redis.get(f"{self.user_calls_prefix}{callee_id}")
        if existing_call:
            raise ValueError("Callee is already in a call")
        
        # Create call record
        call_data = {
            "call_id": call_id,
            "caller_id": caller_id,
            "caller_name": caller_name,
            "callee_id": callee_id,
            "call_type": call_type.value,
            "status": CallStatus.INITIATING.value,
            "conversation_id": conversation_id,
            "enable_translation": enable_translation,
            "created_at": datetime.utcnow().isoformat(),
            "participants": [caller_id, callee_id]
        }
        
        # Store call data
        await self.redis.setex(
            f"{self.call_participants_prefix}{call_id}",
            self.max_call_duration,
            json.dumps(call_data)
        )
        
        # Mark users as in call
        await self.redis.setex(f"{self.user_calls_prefix}{caller_id}", self.max_call_duration, call_id)
        await self.redis.setex(f"{self.user_calls_prefix}{callee_id}", self.max_call_duration, call_id)
        
        # Add to active calls set
        await self.redis.sadd(self.active_calls_key, call_id)
        
        # Send call invitation via WebSocket
        invitation = {
            "type": "call_invitation",
            "call_id": call_id,
            "caller_id": caller_id,
            "caller_name": caller_name,
            "call_type": call_type.value,
            "conversation_id": conversation_id,
            "enable_translation": enable_translation
        }
        
        await self.redis.publish(f"user:{callee_id}", json.dumps(invitation))
        
        # Set timeout for call answer
        await self.redis.setex(f"call_timeout:{call_id}", self.call_timeout, "pending")
        
        logger.info(f"Call {call_id} initiated from {caller_id} to {callee_id}")
        
        return {
            "call_id": call_id,
            "status": CallStatus.INITIATING.value,
            "message": "Call invitation sent"
        }
    
    async def answer_call(self, call_id: str, user_id: str, accept: bool) -> Dict[str, Any]:
        """Answer or reject a call."""
        call_data = await self._get_call_data(call_id)
        if not call_data:
            raise ValueError("Call not found")
        
        if call_data["callee_id"] != user_id:
            raise ValueError("User not authorized to answer this call")
        
        if call_data["status"] != CallStatus.INITIATING.value:
            raise ValueError("Call is not in answerable state")
        
        if accept:
            # Accept the call
            call_data["status"] = CallStatus.RINGING.value
            call_data["answered_at"] = datetime.utcnow().isoformat()
            
            await self._update_call_data(call_id, call_data)
            
            # Notify caller that call was accepted
            response = {
                "type": "call_answered",
                "call_id": call_id,
                "accepted": True,
                "callee_id": user_id
            }
            
            await self.redis.publish(f"user:{call_data['caller_id']}", json.dumps(response))
            
            logger.info(f"Call {call_id} accepted by {user_id}")
            
            return {
                "call_id": call_id,
                "status": CallStatus.RINGING.value,
                "message": "Call accepted, establishing connection"
            }
        else:
            # Reject the call
            await self._end_call(call_id, "rejected")
            
            # Notify caller that call was rejected
            response = {
                "type": "call_answered",
                "call_id": call_id,
                "accepted": False,
                "callee_id": user_id
            }
            
            await self.redis.publish(f"user:{call_data['caller_id']}", json.dumps(response))
            
            logger.info(f"Call {call_id} rejected by {user_id}")
            
            return {
                "call_id": call_id,
                "status": CallStatus.ENDED.value,
                "message": "Call rejected"
            }
    
    async def handle_webrtc_signal(
        self,
        call_id: str,
        user_id: str,
        signal_type: str,
        signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle WebRTC signaling messages."""
        call_data = await self._get_call_data(call_id)
        if not call_data:
            raise ValueError("Call not found")
        
        if user_id not in call_data["participants"]:
            raise ValueError("User not authorized for this call")
        
        # Determine the target user (the other participant)
        target_user = call_data["caller_id"] if user_id == call_data["callee_id"] else call_data["callee_id"]
        
        # Forward the signaling message to the other participant
        signal_message = {
            "type": "webrtc_signal",
            "call_id": call_id,
            "signal_type": signal_type,
            "signal_data": signal_data,
            "from_user": user_id
        }
        
        await self.redis.publish(f"user:{target_user}", json.dumps(signal_message))
        
        # Update call status if this is a connection establishment
        if signal_type == "connected":
            call_data["status"] = CallStatus.CONNECTED.value
            call_data["connected_at"] = datetime.utcnow().isoformat()
            await self._update_call_data(call_id, call_data)
        
        return {"status": "signal_forwarded"}
    
    async def end_call(self, call_id: str, user_id: str) -> Dict[str, Any]:
        """End a call."""
        call_data = await self._get_call_data(call_id)
        if not call_data:
            raise ValueError("Call not found")
        
        if user_id not in call_data["participants"]:
            raise ValueError("User not authorized to end this call")
        
        await self._end_call(call_id, "ended_by_user")
        
        # Notify other participant
        other_user = call_data["caller_id"] if user_id == call_data["callee_id"] else call_data["callee_id"]
        end_message = {
            "type": "call_ended",
            "call_id": call_id,
            "ended_by": user_id
        }
        
        await self.redis.publish(f"user:{other_user}", json.dumps(end_message))
        
        logger.info(f"Call {call_id} ended by {user_id}")
        
        return {
            "call_id": call_id,
            "status": CallStatus.ENDED.value,
            "message": "Call ended"
        }
    
    async def process_voice_translation(
        self,
        call_id: str,
        user_id: str,
        audio_data: str,
        source_language: LanguageCode,
        target_language: LanguageCode
    ) -> Dict[str, Any]:
        """Process voice translation during a call."""
        call_data = await self._get_call_data(call_id)
        if not call_data:
            raise ValueError("Call not found")
        
        if not call_data.get("enable_translation", False):
            raise ValueError("Translation not enabled for this call")
        
        if user_id not in call_data["participants"]:
            raise ValueError("User not authorized for this call")
        
        try:
            # For now, we'll simulate the translation process
            # In a real implementation, this would:
            # 1. Convert speech to text using Web Speech API results from frontend
            # 2. Translate the text
            # 3. Convert translated text to speech
            # 4. Send the translated audio to the other participant
            
            # Simulate translation (in real implementation, text would come from frontend STT)
            original_text = "Sample speech text"  # This would come from frontend
            
            translation_request = TranslationRequest(
                text=original_text,
                source_language=source_language,
                target_language=target_language,
                context="voice_call"
            )
            
            translation_result = await self.translation_service.translate_text(translation_request)
            
            # Generate speech for translated text
            from app.models.voice import TextToSpeechRequest, VoiceType, AudioFormat
            
            tts_request = TextToSpeechRequest(
                text=translation_result.translated_text,
                language=target_language,
                voice_type=VoiceType.STANDARD,
                audio_format=AudioFormat.MP3
            )
            
            tts_result = await self.voice_service.text_to_speech(tts_request)
            
            # Send translated audio to other participant
            other_user = call_data["caller_id"] if user_id == call_data["callee_id"] else call_data["callee_id"]
            
            translation_message = {
                "type": "voice_translation",
                "call_id": call_id,
                "original_text": original_text,
                "translated_text": translation_result.translated_text,
                "translated_audio_url": tts_result.audio_url,
                "source_language": source_language.value,
                "target_language": target_language.value,
                "from_user": user_id
            }
            
            await self.redis.publish(f"user:{other_user}", json.dumps(translation_message))
            
            return {
                "status": "translation_sent",
                "translated_text": translation_result.translated_text,
                "audio_url": tts_result.audio_url
            }
            
        except Exception as e:
            logger.error(f"Voice translation error in call {call_id}: {e}")
            return {
                "status": "translation_failed",
                "error": str(e)
            }
    
    async def record_call(self, call_id: str, user_id: str, enable_recording: bool) -> Dict[str, Any]:
        """Enable or disable call recording."""
        call_data = await self._get_call_data(call_id)
        if not call_data:
            raise ValueError("Call not found")
        
        if user_id not in call_data["participants"]:
            raise ValueError("User not authorized for this call")
        
        call_data["recording_enabled"] = enable_recording
        if enable_recording:
            call_data["recording_started_at"] = datetime.utcnow().isoformat()
            call_data["recording_started_by"] = user_id
        else:
            call_data["recording_stopped_at"] = datetime.utcnow().isoformat()
        
        await self._update_call_data(call_id, call_data)
        
        # Notify other participant about recording status
        other_user = call_data["caller_id"] if user_id == call_data["callee_id"] else call_data["callee_id"]
        
        recording_message = {
            "type": "recording_status",
            "call_id": call_id,
            "recording_enabled": enable_recording,
            "changed_by": user_id
        }
        
        await self.redis.publish(f"user:{other_user}", json.dumps(recording_message))
        
        logger.info(f"Call {call_id} recording {'enabled' if enable_recording else 'disabled'} by {user_id}")
        
        return {
            "call_id": call_id,
            "recording_enabled": enable_recording,
            "message": f"Recording {'started' if enable_recording else 'stopped'}"
        }
    
    async def get_active_calls(self, user_id: str) -> List[Dict[str, Any]]:
        """Get active calls for a user."""
        user_call_id = await self.redis.get(f"{self.user_calls_prefix}{user_id}")
        if not user_call_id:
            return []
        
        call_data = await self._get_call_data(user_call_id)
        if not call_data:
            return []
        
        return [call_data]
    
    async def get_call_stats(self) -> Dict[str, Any]:
        """Get call statistics."""
        active_calls = await self.redis.scard(self.active_calls_key)
        
        # Get call history from the last 24 hours (this would typically be stored in MongoDB)
        stats = {
            "active_calls": active_calls,
            "total_calls_today": 0,  # Would be calculated from database
            "average_call_duration": 0.0,  # Would be calculated from database
            "translation_usage": {},  # Would be calculated from database
            "call_types": {
                "voice": 0,
                "video": 0,
                "screen_share": 0
            }
        }
        
        return stats
    
    async def cleanup_expired_calls(self):
        """Clean up expired calls."""
        try:
            active_call_ids = await self.redis.smembers(self.active_calls_key)
            
            for call_id in active_call_ids:
                call_data = await self._get_call_data(call_id)
                if not call_data:
                    # Call data expired, remove from active set
                    await self.redis.srem(self.active_calls_key, call_id)
                    continue
                
                # Check if call has been active too long
                created_at = datetime.fromisoformat(call_data["created_at"])
                if datetime.utcnow() - created_at > timedelta(seconds=self.max_call_duration):
                    await self._end_call(call_id, "timeout")
                    logger.info(f"Call {call_id} ended due to timeout")
                
        except Exception as e:
            logger.error(f"Error during call cleanup: {e}")
    
    async def _get_call_data(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call data from Redis."""
        try:
            data = await self.redis.get(f"{self.call_participants_prefix}{call_id}")
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error retrieving call data for {call_id}: {e}")
        return None
    
    async def _update_call_data(self, call_id: str, call_data: Dict[str, Any]):
        """Update call data in Redis."""
        try:
            await self.redis.setex(
                f"{self.call_participants_prefix}{call_id}",
                self.max_call_duration,
                json.dumps(call_data)
            )
        except Exception as e:
            logger.error(f"Error updating call data for {call_id}: {e}")
    
    async def _end_call(self, call_id: str, reason: str):
        """End a call and clean up resources."""
        call_data = await self._get_call_data(call_id)
        if not call_data:
            return
        
        # Update call status
        call_data["status"] = CallStatus.ENDED.value
        call_data["ended_at"] = datetime.utcnow().isoformat()
        call_data["end_reason"] = reason
        
        # Store final call data (in production, this would go to MongoDB for history)
        await self._update_call_data(call_id, call_data)
        
        # Clean up user call associations
        for participant_id in call_data["participants"]:
            await self.redis.delete(f"{self.user_calls_prefix}{participant_id}")
        
        # Remove from active calls
        await self.redis.srem(self.active_calls_key, call_id)
        
        # Clean up timeout
        await self.redis.delete(f"call_timeout:{call_id}")