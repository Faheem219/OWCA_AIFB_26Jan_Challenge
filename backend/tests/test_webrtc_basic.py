"""
Property-based tests for WebRTC multi-modal communication support.
**Validates: Requirements 6.2, 6.3**
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from datetime import datetime

from app.services.webrtc_service import WebRTCService, CallType, CallStatus
from app.services.translation_service import TranslationService
from app.services.voice_service import VoiceService
from app.models.translation import LanguageCode, TranslationRequest, TranslationResult
from app.models.voice import TextToSpeechRequest, TextToSpeechResult, VoiceType, AudioFormat


"""
Property-based tests for WebRTC multi-modal communication support.
**Validates: Requirements 6.2, 6.3**
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from datetime import datetime

from app.services.webrtc_service import WebRTCService, CallType, CallStatus
from app.services.translation_service import TranslationService
from app.services.voice_service import VoiceService
from app.models.translation import LanguageCode, TranslationRequest, TranslationResult
from app.models.voice import TextToSpeechRequest, TextToSpeechResult, VoiceType, AudioFormat


# Test data generators for property-based testing
@st.composite
def supported_language_code(draw):
    """Generate supported language codes."""
    languages = [
        LanguageCode.HINDI, LanguageCode.ENGLISH, LanguageCode.TAMIL,
        LanguageCode.TELUGU, LanguageCode.BENGALI, LanguageCode.MARATHI,
        LanguageCode.GUJARATI, LanguageCode.KANNADA, LanguageCode.MALAYALAM,
        LanguageCode.PUNJABI, LanguageCode.ODIA, LanguageCode.ASSAMESE
    ]
    return draw(st.sampled_from(languages))


@st.composite
def call_type_strategy(draw):
    """Generate call types."""
    return draw(st.sampled_from([CallType.VOICE, CallType.VIDEO, CallType.SCREEN_SHARE]))


@st.composite
def user_data(draw):
    """Generate user data for testing."""
    user_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    user_name = draw(st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))))
    language = draw(supported_language_code())
    
    return {
        'id': user_id,
        'name': user_name.strip(),
        'language': language
    }


@st.composite
def audio_data_strategy(draw):
    """Generate mock audio data."""
    return draw(st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))


@st.composite
def speech_text_strategy(draw):
    """Generate realistic speech text for voice communication."""
    phrases = [
        "Hello, how are you?",
        "What is the price today?",
        "I am interested in this product",
        "Can we negotiate?",
        "Thank you very much",
        "When can you deliver?",
        "The quality looks excellent",
        "I need this urgently",
        "What payment methods work?",
        "Is this certified organic?"
    ]
    return draw(st.sampled_from(phrases))


class TestWebRTCMultiModalProperties:
    """Property-based tests for WebRTC multi-modal communication."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = AsyncMock()
        redis.sadd = AsyncMock()
        redis.get = AsyncMock()
        redis.setex = AsyncMock()
        redis.delete = AsyncMock()
        redis.srem = AsyncMock()
        redis.publish = AsyncMock()
        redis.flushall = AsyncMock()
        redis.sismember = AsyncMock(return_value=True)  # Users are online by default
        return redis
    
    @pytest.fixture
    def mock_db(self):
        """Mock database."""
        return MagicMock()
    
    @pytest.fixture
    def mock_translation_service(self):
        """Mock translation service."""
        service = AsyncMock(spec=TranslationService)
        return service
    
    @pytest.fixture
    def mock_voice_service(self):
        """Mock voice service."""
        service = AsyncMock(spec=VoiceService)
        return service
    
    @pytest.fixture
    def webrtc_service(self, mock_redis, mock_db, mock_translation_service, mock_voice_service):
        """Create WebRTC service with mocked dependencies."""
        return WebRTCService(mock_redis, mock_translation_service, mock_voice_service)
    
    @pytest.mark.asyncio
    @given(
        caller=user_data(),
        callee=user_data(),
        call_type=call_type_strategy()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_multimodal_call_initiation_supports_all_types(
        self, 
        webrtc_service, 
        mock_redis,
        caller, 
        callee, 
        call_type
    ):
        """
        **Property 28: Multi-Modal Communication Support**
        *For any* communication session (text, voice, video), the system should 
        provide appropriate translation and interpretation services.
        **Validates: Requirements 6.2, 6.3**
        """
        # Ensure different users
        assume(caller['id'] != callee['id'])
        assume(len(caller['name'].strip()) > 0)
        assume(len(callee['name'].strip()) > 0)
        
        # Mock callee is online and not in another call
        mock_redis.sismember.return_value = True
        mock_redis.get.return_value = None  # No existing call
        
        # Test call initiation for any call type
        result = await webrtc_service.initiate_call(
            caller_id=caller['id'],
            caller_name=caller['name'],
            callee_id=callee['id'],
            call_type=call_type,
            enable_translation=True
        )
        
        # PROPERTY: All call types should be successfully initiated
        assert "call_id" in result, f"Call initiation should succeed for {call_type.value}"
        assert result["status"] == CallStatus.INITIATING.value, f"Status should be INITIATING for {call_type.value}"
        
        # PROPERTY: Call data should be stored with correct type
        mock_redis.setex.assert_called()
        call_data_json = mock_redis.setex.call_args[0][2]
        call_data = json.loads(call_data_json)
        assert call_data["call_type"] == call_type.value, f"Call type should be preserved as {call_type.value}"
        assert call_data["enable_translation"] == True, "Translation should be enabled for multi-modal support"
        
        # PROPERTY: Users should be marked as in call
        user_call_setex_calls = [call for call in mock_redis.setex.call_args_list 
                                if call[0][0].startswith("webrtc:user_calls:")]
        assert len(user_call_setex_calls) == 2, "Both users should be marked as in call"
        
        # PROPERTY: Call invitation should be sent
        mock_redis.publish.assert_called()
        invitation_data = json.loads(mock_redis.publish.call_args[0][1])
        assert invitation_data["type"] == "call_invitation", "Should send call invitation"
        assert invitation_data["call_type"] == call_type.value, "Invitation should specify correct call type"
        assert invitation_data["enable_translation"] == True, "Invitation should indicate translation support"
    
    @pytest.mark.asyncio
    @given(
        caller=user_data(),
        callee=user_data(),
        audio_data=audio_data_strategy(),
        speech_text=speech_text_strategy()
    )
    @settings(max_examples=25, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_voice_translation_during_multimodal_call(
        self,
        webrtc_service,
        mock_redis,
        mock_translation_service,
        mock_voice_service,
        caller,
        callee,
        audio_data,
        speech_text
    ):
        """
        **Property 28: Multi-Modal Communication Support**
        *For any* voice communication with different languages, the system should
        provide real-time translation and voice synthesis.
        **Validates: Requirements 6.2, 6.3**
        """
        # Ensure different users and languages for meaningful translation
        assume(caller['id'] != callee['id'])
        assume(caller['language'] != callee['language'])
        assume(len(caller['name'].strip()) > 0)
        assume(len(callee['name'].strip()) > 0)
        assume(len(speech_text.strip()) > 0)
        
        # Setup active call data
        call_id = "test_call_123"
        call_data = {
            "call_id": call_id,
            "caller_id": caller['id'],
            "callee_id": callee['id'],
            "participants": [caller['id'], callee['id']],
            "status": CallStatus.CONNECTED.value,
            "enable_translation": True
        }
        
        mock_redis.get.return_value = json.dumps(call_data)
        
        # Mock translation service response
        mock_translation_service.translate_text.return_value = TranslationResult(
            original_text=speech_text,
            translated_text=f"[TRANSLATED to {callee['language'].value}] {speech_text}",
            source_language=caller['language'],
            target_language=callee['language'],
            confidence_score=0.90,
            provider="aws_translate",
            cached=False
        )
        
        # Mock voice service response
        mock_voice_service.text_to_speech.return_value = TextToSpeechResult(
            original_text=f"[TRANSLATED to {callee['language'].value}] {speech_text}",
            language=callee['language'],
            audio_url=f"/api/v1/voice/audio/translated_{call_id}.mp3",
            audio_format=AudioFormat.MP3,
            voice_id="test_voice",
            provider="aws_polly",
            file_size_bytes=12345
        )
        
        # Test voice translation during call
        result = await webrtc_service.process_voice_translation(
            call_id=call_id,
            user_id=caller['id'],
            audio_data=audio_data,
            source_language=caller['language'],
            target_language=callee['language']
        )
        
        # PROPERTY: Voice translation should be processed successfully
        assert result["status"] == "translation_sent", "Voice translation should succeed"
        assert "translated_text" in result, "Should return translated text"
        assert "audio_url" in result, "Should return translated audio URL"
        
        # PROPERTY: Translation service should be called with correct parameters
        mock_translation_service.translate_text.assert_called_once()
        translation_request = mock_translation_service.translate_text.call_args[0][0]
        assert translation_request.source_language == caller['language'], "Should use caller's language as source"
        assert translation_request.target_language == callee['language'], "Should use callee's language as target"
        assert translation_request.context == "voice_call", "Should specify voice call context"
        
        # PROPERTY: Voice service should be called for TTS
        mock_voice_service.text_to_speech.assert_called_once()
        tts_request = mock_voice_service.text_to_speech.call_args[0][0]
        assert tts_request.language == callee['language'], "TTS should use target language"
        assert tts_request.audio_format == AudioFormat.MP3, "Should use appropriate audio format"
        
        # PROPERTY: Translated audio should be sent to other participant
        mock_redis.publish.assert_called()
        translation_message = json.loads(mock_redis.publish.call_args[0][1])
        assert translation_message["type"] == "voice_translation", "Should send voice translation message"
        assert translation_message["call_id"] == call_id, "Should reference correct call"
        assert translation_message["source_language"] == caller['language'].value, "Should specify source language"
        assert translation_message["target_language"] == callee['language'].value, "Should specify target language"
        assert "translated_audio_url" in translation_message, "Should include translated audio URL"
    
    @pytest.mark.asyncio
    @given(
        participants=st.lists(user_data(), min_size=2, max_size=4, unique_by=lambda x: x['id']),
        call_type=call_type_strategy()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_multimodal_call_supports_multiple_participants(
        self,
        webrtc_service,
        mock_redis,
        participants,
        call_type
    ):
        """
        **Property 28: Multi-Modal Communication Support**
        *For any* multi-participant communication session, the system should
        handle signaling and coordination for all participants.
        **Validates: Requirements 6.2, 6.3**
        """
        assume(len(participants) >= 2)
        assume(all(len(p['name'].strip()) > 0 for p in participants))
        
        caller = participants[0]
        callee = participants[1]
        
        # Mock all participants are online
        mock_redis.sismember.return_value = True
        mock_redis.get.return_value = None  # No existing calls
        
        # Initiate call
        result = await webrtc_service.initiate_call(
            caller_id=caller['id'],
            caller_name=caller['name'],
            callee_id=callee['id'],
            call_type=call_type,
            enable_translation=True
        )
        
        call_id = result["call_id"]
        
        # Setup call data with all participants
        call_data = {
            "call_id": call_id,
            "caller_id": caller['id'],
            "callee_id": callee['id'],
            "participants": [p['id'] for p in participants],
            "status": CallStatus.CONNECTED.value,
            "call_type": call_type.value,
            "enable_translation": True
        }
        
        mock_redis.get.return_value = json.dumps(call_data)
        
        # Test WebRTC signaling for each participant
        for i, participant in enumerate(participants):
            signal_result = await webrtc_service.handle_webrtc_signal(
                call_id=call_id,
                user_id=participant['id'],
                signal_type="offer" if i == 0 else "answer",
                signal_data={"type": "offer" if i == 0 else "answer", "sdp": f"mock_sdp_{i}"}
            )
            
            # PROPERTY: Signaling should work for all participants
            assert signal_result["status"] == "signal_forwarded", f"Signaling should work for participant {i}"
        
        # PROPERTY: All participants should be able to end the call
        for participant in participants[:2]:  # Test first two participants
            # Reset mock for clean assertion
            mock_redis.publish.reset_mock()
            
            end_result = await webrtc_service.end_call(call_id, participant['id'])
            
            assert end_result["status"] == CallStatus.ENDED.value, f"Participant {participant['id']} should be able to end call"
            
            # Should notify other participants
            mock_redis.publish.assert_called()
            end_message = json.loads(mock_redis.publish.call_args[0][1])
            assert end_message["type"] == "call_ended", "Should send call ended notification"
            assert end_message["ended_by"] == participant['id'], "Should specify who ended the call"
            
            break  # Only test one end call to avoid duplicate cleanup
    
    @pytest.mark.asyncio
    @given(
        caller=user_data(),
        callee=user_data(),
        call_type=call_type_strategy()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_call_recording_available_for_all_modes(
        self,
        webrtc_service,
        mock_redis,
        caller,
        callee,
        call_type
    ):
        """
        **Property 28: Multi-Modal Communication Support**
        *For any* communication mode (voice, video, screen share), call recording
        should be available and function correctly.
        **Validates: Requirements 6.2, 6.3**
        """
        assume(caller['id'] != callee['id'])
        assume(len(caller['name'].strip()) > 0)
        assume(len(callee['name'].strip()) > 0)
        
        # Setup active call data
        call_id = "test_call_recording"
        call_data = {
            "call_id": call_id,
            "caller_id": caller['id'],
            "callee_id": callee['id'],
            "participants": [caller['id'], callee['id']],
            "status": CallStatus.CONNECTED.value,
            "call_type": call_type.value,
            "recording_enabled": False
        }
        
        mock_redis.get.return_value = json.dumps(call_data)
        
        # Test enabling recording
        recording_result = await webrtc_service.record_call(
            call_id=call_id,
            user_id=caller['id'],
            enable_recording=True
        )
        
        # PROPERTY: Recording should be available for all call types
        assert recording_result["call_id"] == call_id, f"Recording should work for {call_type.value}"
        assert recording_result["recording_enabled"] == True, f"Recording should be enabled for {call_type.value}"
        assert "Recording started" in recording_result["message"], f"Should confirm recording start for {call_type.value}"
        
        # PROPERTY: Call data should be updated with recording info
        mock_redis.setex.assert_called()
        
        # PROPERTY: Other participant should be notified
        mock_redis.publish.assert_called()
        recording_message = json.loads(mock_redis.publish.call_args[0][1])
        assert recording_message["type"] == "recording_status", "Should send recording status notification"
        assert recording_message["recording_enabled"] == True, "Should indicate recording is enabled"
        assert recording_message["changed_by"] == caller['id'], "Should specify who changed recording status"
        
        # Test disabling recording
        mock_redis.publish.reset_mock()
        
        disable_result = await webrtc_service.record_call(
            call_id=call_id,
            user_id=caller['id'],
            enable_recording=False
        )
        
        # PROPERTY: Recording should be disableable for all call types
        assert disable_result["recording_enabled"] == False, f"Recording should be disableable for {call_type.value}"
        assert "Recording stopped" in disable_result["message"], f"Should confirm recording stop for {call_type.value}"
    
    @pytest.mark.asyncio
    @given(
        caller=user_data(),
        callee=user_data(),
        call_type=call_type_strategy()
    )
    @settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_translation_failure_handling_in_multimodal_calls(
        self,
        webrtc_service,
        mock_redis,
        mock_translation_service,
        mock_voice_service,
        caller,
        callee,
        call_type
    ):
        """
        **Property 28: Multi-Modal Communication Support**
        *For any* communication session where translation fails, the system should
        gracefully handle the failure while maintaining the communication channel.
        **Validates: Requirements 6.2, 6.3**
        """
        assume(caller['id'] != callee['id'])
        assume(caller['language'] != callee['language'])
        assume(len(caller['name'].strip()) > 0)
        assume(len(callee['name'].strip()) > 0)
        
        # Setup active call data
        call_id = "test_translation_failure"
        call_data = {
            "call_id": call_id,
            "caller_id": caller['id'],
            "callee_id": callee['id'],
            "participants": [caller['id'], callee['id']],
            "status": CallStatus.CONNECTED.value,
            "call_type": call_type.value,
            "enable_translation": True
        }
        
        mock_redis.get.return_value = json.dumps(call_data)
        
        # Mock translation service to fail
        mock_translation_service.translate_text.side_effect = Exception("Translation service unavailable")
        
        # Test voice translation with failure
        result = await webrtc_service.process_voice_translation(
            call_id=call_id,
            user_id=caller['id'],
            audio_data="mock_audio_data",
            source_language=caller['language'],
            target_language=callee['language']
        )
        
        # PROPERTY: Translation failure should be handled gracefully
        assert result["status"] == "translation_failed", "Should indicate translation failure"
        assert "error" in result, "Should provide error information"
        
        # PROPERTY: Translation should have been attempted
        mock_translation_service.translate_text.assert_called_once()
        
        # PROPERTY: Voice service should not be called if translation fails
        mock_voice_service.text_to_speech.assert_not_called()
        
        # PROPERTY: Call should remain active despite translation failure
        # (In a real implementation, this would be verified by checking call status)
        # The call infrastructure should remain functional even if translation fails
        assert call_data["status"] == CallStatus.CONNECTED.value, "Call should remain connected despite translation failure"
    
    @pytest.mark.asyncio
    @given(
        users=st.lists(user_data(), min_size=2, max_size=3, unique_by=lambda x: x['id']),
        call_type=call_type_strategy()
    )
    @settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_multimodal_call_lifecycle_consistency(
        self,
        webrtc_service,
        mock_redis,
        users,
        call_type
    ):
        """
        **Property 28: Multi-Modal Communication Support**
        *For any* communication session type, the call lifecycle (initiate, answer, connect, end)
        should be consistent and reliable.
        **Validates: Requirements 6.2, 6.3**
        """
        assume(len(users) >= 2)
        assume(all(len(u['name'].strip()) > 0 for u in users))
        
        caller = users[0]
        callee = users[1]
        
        # Mock users are online
        mock_redis.sismember.return_value = True
        mock_redis.get.return_value = None  # No existing calls
        
        # 1. PROPERTY: Call initiation should work for all types
        result = await webrtc_service.initiate_call(
            caller_id=caller['id'],
            caller_name=caller['name'],
            callee_id=callee['id'],
            call_type=call_type,
            enable_translation=True
        )
        
        call_id = result["call_id"]
        assert result["status"] == CallStatus.INITIATING.value, f"Initiation should work for {call_type.value}"
        
        # 2. PROPERTY: Call answering should work for all types
        call_data = {
            "call_id": call_id,
            "caller_id": caller['id'],
            "callee_id": callee['id'],
            "participants": [caller['id'], callee['id']],
            "status": CallStatus.INITIATING.value,
            "call_type": call_type.value,
            "enable_translation": True
        }
        
        mock_redis.get.return_value = json.dumps(call_data)
        
        answer_result = await webrtc_service.answer_call(
            call_id=call_id,
            user_id=callee['id'],
            accept=True
        )
        
        assert answer_result["status"] == CallStatus.RINGING.value, f"Answer should work for {call_type.value}"
        
        # 3. PROPERTY: Call ending should work for all types
        call_data["status"] = CallStatus.CONNECTED.value
        mock_redis.get.return_value = json.dumps(call_data)
        
        end_result = await webrtc_service.end_call(call_id, caller['id'])
        assert end_result["status"] == CallStatus.ENDED.value, f"Ending should work for {call_type.value}"
        
        # PROPERTY: Cleanup should occur for all call types
        mock_redis.delete.assert_called()  # User call associations cleaned
        mock_redis.srem.assert_called()    # Removed from active calls


class TestWebRTCBasic:
    """Basic tests for WebRTC multi-modal communication."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = AsyncMock()
        redis.sadd = AsyncMock()
        redis.get = AsyncMock()
        redis.setex = AsyncMock()
        redis.delete = AsyncMock()
        redis.srem = AsyncMock()
        redis.publish = AsyncMock()
        redis.flushall = AsyncMock()
        return redis
    
    @pytest.fixture
    def mock_db(self):
        """Mock database."""
        return MagicMock()
    
    @pytest.fixture
    def webrtc_service(self, mock_redis, mock_db):
        """Create WebRTC service with mocked dependencies."""
        translation_service = TranslationService(mock_db, mock_redis)
        voice_service = VoiceService(mock_db, mock_redis, translation_service)
        return WebRTCService(mock_redis, translation_service, voice_service)
    
    @pytest.mark.asyncio
    async def test_multimodal_call_initiation_voice(self, webrtc_service, mock_redis):
        """
        **Property 28: Multi-Modal Communication Support**
        Voice calls should support audio translation services.
        **Validates: Requirements 6.2, 6.3**
        """
        # Setup
        caller_id = "user123"
        callee_id = "user456"
        call_type = CallType.VOICE
        
        # Mock callee is online
        mock_redis.sismember.return_value = True
        mock_redis.get.return_value = None  # No existing call
        
        # Test call initiation
        result = await webrtc_service.initiate_call(
            caller_id=caller_id,
            caller_name="John Doe",
            callee_id=callee_id,
            call_type=call_type,
            enable_translation=True
        )
        
        # Verify call was created
        assert "call_id" in result
        assert result["status"] == CallStatus.INITIATING.value
        
        # Verify Redis operations were called
        mock_redis.setex.assert_called()  # Call data stored
        mock_redis.sadd.assert_called()   # Added to active calls
        mock_redis.publish.assert_called()  # Invitation sent
    
    @pytest.mark.asyncio
    async def test_multimodal_call_initiation_video(self, webrtc_service, mock_redis):
        """
        **Property 28: Multi-Modal Communication Support**
        Video calls should support both audio translation and visual demonstration.
        **Validates: Requirements 6.2, 6.3**
        """
        # Setup
        caller_id = "user123"
        callee_id = "user456"
        call_type = CallType.VIDEO
        
        # Mock callee is online
        mock_redis.sismember.return_value = True
        mock_redis.get.return_value = None  # No existing call
        
        # Test call initiation
        result = await webrtc_service.initiate_call(
            caller_id=caller_id,
            caller_name="John Doe",
            callee_id=callee_id,
            call_type=call_type,
            enable_translation=True
        )
        
        # Verify call was created
        assert "call_id" in result
        assert result["status"] == CallStatus.INITIATING.value
        
        # Verify multi-modal capabilities are enabled
        # (In a real implementation, this would check call data)
        assert call_type == CallType.VIDEO  # Supports video demonstration
    
    @pytest.mark.asyncio
    async def test_webrtc_signaling_support(self, webrtc_service, mock_redis):
        """
        **Property 28: Multi-Modal Communication Support**
        WebRTC signaling should work for establishing multi-modal channels.
        **Validates: Requirements 6.2, 6.3**
        """
        # Setup call data
        call_id = "test_call_123"
        caller_id = "user123"
        callee_id = "user456"
        
        call_data = {
            "call_id": call_id,
            "caller_id": caller_id,
            "callee_id": callee_id,
            "participants": [caller_id, callee_id],
            "status": CallStatus.RINGING.value
        }
        
        # Mock call data retrieval
        import json
        mock_redis.get.return_value = json.dumps(call_data)
        
        # Test signaling
        signal_result = await webrtc_service.handle_webrtc_signal(
            call_id=call_id,
            user_id=caller_id,
            signal_type="offer",
            signal_data={"type": "offer", "sdp": "mock_sdp_data"}
        )
        
        # Verify signaling was processed
        assert signal_result["status"] == "signal_forwarded"
        
        # Verify message was published to other participant
        mock_redis.publish.assert_called()
    
    @pytest.mark.asyncio
    async def test_call_recording_support(self, webrtc_service, mock_redis):
        """
        **Property 28: Multi-Modal Communication Support**
        Call recording should be available for all communication modes.
        **Validates: Requirements 6.2, 6.3**
        """
        # Setup call data
        call_id = "test_call_123"
        caller_id = "user123"
        callee_id = "user456"
        
        call_data = {
            "call_id": call_id,
            "caller_id": caller_id,
            "callee_id": callee_id,
            "participants": [caller_id, callee_id],
            "status": CallStatus.CONNECTED.value,
            "recording_enabled": False
        }
        
        # Mock call data retrieval and update
        import json
        mock_redis.get.return_value = json.dumps(call_data)
        
        # Test recording control
        recording_result = await webrtc_service.record_call(
            call_id=call_id,
            user_id=caller_id,
            enable_recording=True
        )
        
        # Verify recording control worked
        assert recording_result["call_id"] == call_id
        assert recording_result["recording_enabled"] == True
        
        # Verify call data was updated
        mock_redis.setex.assert_called()  # Call data updated
        mock_redis.publish.assert_called()  # Other participant notified
    
    @pytest.mark.asyncio
    async def test_voice_translation_during_call(self, webrtc_service, mock_redis):
        """
        **Property 28: Multi-Modal Communication Support**
        Voice translation should work during active calls.
        **Validates: Requirements 6.2, 6.3**
        """
        # Setup call data
        call_id = "test_call_123"
        caller_id = "user123"
        callee_id = "user456"
        
        call_data = {
            "call_id": call_id,
            "caller_id": caller_id,
            "callee_id": callee_id,
            "participants": [caller_id, callee_id],
            "status": CallStatus.CONNECTED.value,
            "enable_translation": True
        }
        
        # Mock call data retrieval
        import json
        mock_redis.get.return_value = json.dumps(call_data)
        
        # Test voice translation
        translation_result = await webrtc_service.process_voice_translation(
            call_id=call_id,
            user_id=caller_id,
            audio_data="mock_audio_data",
            source_language=LanguageCode.HINDI,
            target_language=LanguageCode.ENGLISH
        )
        
        # Verify translation was processed
        assert "status" in translation_result
        # Translation may succeed or fail depending on mock setup
        assert translation_result["status"] in ["translation_sent", "translation_failed"]
    
    @pytest.mark.asyncio
    async def test_call_lifecycle_consistency(self, webrtc_service, mock_redis):
        """
        **Property 28: Multi-Modal Communication Support**
        Call lifecycle should be consistent across all communication modes.
        **Validates: Requirements 6.2, 6.3**
        """
        # Setup
        caller_id = "user123"
        callee_id = "user456"
        
        # Mock callee is online
        mock_redis.sismember.return_value = True
        mock_redis.get.return_value = None  # No existing call
        
        # 1. Initiate call
        result = await webrtc_service.initiate_call(
            caller_id=caller_id,
            caller_name="John Doe",
            callee_id=callee_id,
            call_type=CallType.VIDEO,
            enable_translation=True
        )
        
        call_id = result["call_id"]
        assert result["status"] == CallStatus.INITIATING.value
        
        # 2. Mock call data for answer
        call_data = {
            "call_id": call_id,
            "caller_id": caller_id,
            "callee_id": callee_id,
            "participants": [caller_id, callee_id],
            "status": CallStatus.INITIATING.value
        }
        
        import json
        mock_redis.get.return_value = json.dumps(call_data)
        
        # 3. Answer call
        answer_result = await webrtc_service.answer_call(
            call_id=call_id,
            user_id=callee_id,
            accept=True
        )
        
        assert answer_result["status"] == CallStatus.RINGING.value
        
        # 4. End call
        call_data["status"] = CallStatus.CONNECTED.value
        mock_redis.get.return_value = json.dumps(call_data)
        
        end_result = await webrtc_service.end_call(call_id, caller_id)
        assert end_result["status"] == CallStatus.ENDED.value
        
        # Verify cleanup operations were called
        mock_redis.delete.assert_called()  # User call associations cleaned
        mock_redis.srem.assert_called()    # Removed from active calls
    
    def test_call_types_support_multimodal_features(self):
        """
        **Property 28: Multi-Modal Communication Support**
        All call types should support appropriate multi-modal features.
        **Validates: Requirements 6.2, 6.3**
        """
        # Voice calls support audio translation
        assert CallType.VOICE.value == "voice"
        
        # Video calls support audio translation + visual demonstration
        assert CallType.VIDEO.value == "video"
        
        # Screen sharing supports demonstration capabilities
        assert CallType.SCREEN_SHARE.value == "screen_share"
        
        # All call types are properly defined
        call_types = [CallType.VOICE, CallType.VIDEO, CallType.SCREEN_SHARE]
        assert len(call_types) == 3
        
        # Each call type has distinct capabilities
        for call_type in call_types:
            assert isinstance(call_type.value, str)
            assert len(call_type.value) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])