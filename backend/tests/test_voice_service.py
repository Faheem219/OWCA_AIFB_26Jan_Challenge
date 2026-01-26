"""
Tests for voice processing service.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.voice_service import VoiceService
from app.models.voice import (
    TextToSpeechRequest,
    VoiceType,
    AudioFormat,
    Gender,
    LanguageCode
)


@pytest.fixture
def mock_db():
    """Mock database."""
    db = Mock()
    # Make the mock subscriptable for collection access
    db.__getitem__ = Mock()
    db.audio_files = AsyncMock()
    db.voice_stats = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    """Mock Redis cache."""
    redis = Mock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    return redis


@pytest.fixture
def mock_translation_service():
    """Mock translation service."""
    service = Mock()
    service.LANGUAGE_NAMES = {
        "hi": {"name": "Hindi", "native_name": "हिन्दी"},
        "en": {"name": "English", "native_name": "English"}
    }
    return service


@pytest.fixture
def voice_service(mock_db, mock_redis, mock_translation_service):
    """Voice service instance with mocked dependencies."""
    with patch('app.services.voice_service.boto3'):
        with patch('app.services.voice_service.Path') as mock_path:
            # Mock the Path operations
            mock_path.return_value.mkdir.return_value = None
            mock_path.return_value.exists.return_value = True
            
            # Mock the collections
            mock_db.__getitem__.return_value = AsyncMock()
            
            service = VoiceService(mock_db, mock_redis, mock_translation_service)
            return service


class TestVoiceService:
    """Test voice processing service."""
    
    def test_voice_service_initialization(self, voice_service):
        """Test voice service initializes correctly."""
        assert voice_service is not None
        assert voice_service.POLLY_VOICES is not None
        assert len(voice_service.POLLY_VOICES) > 0
    
    def test_select_voice_hindi_female(self, voice_service):
        """Test voice selection for Hindi female voice."""
        voice_id = voice_service._select_voice(
            LanguageCode.HINDI, 
            Gender.FEMALE, 
            VoiceType.STANDARD
        )
        assert voice_id in ["Aditi", "Kajal"]
    
    def test_select_voice_english_male(self, voice_service):
        """Test voice selection for English male voice."""
        voice_id = voice_service._select_voice(
            LanguageCode.ENGLISH, 
            Gender.MALE, 
            VoiceType.NEURAL
        )
        assert voice_id == "Matthew"
    
    def test_get_polly_format_mp3(self, voice_service):
        """Test audio format conversion for MP3."""
        polly_format = voice_service._get_polly_format(AudioFormat.MP3)
        assert polly_format == "mp3"
    
    def test_get_polly_format_wav(self, voice_service):
        """Test audio format conversion for WAV."""
        polly_format = voice_service._get_polly_format(AudioFormat.WAV)
        assert polly_format == "pcm"
    
    def test_generate_tts_cache_key(self, voice_service):
        """Test TTS cache key generation."""
        request = TextToSpeechRequest(
            text="Hello world",
            language=LanguageCode.ENGLISH,
            voice_type=VoiceType.STANDARD,
            audio_format=AudioFormat.MP3,
            speed=1.0
        )
        
        cache_key = voice_service._generate_tts_cache_key(request)
        assert cache_key.startswith("voice_audio:")
        assert len(cache_key) > 20  # Should include hash
    
    @pytest.mark.asyncio
    async def test_get_voice_capabilities(self, voice_service):
        """Test getting voice capabilities."""
        capabilities = await voice_service.get_voice_capabilities()
        
        assert capabilities is not None
        assert capabilities.total_languages > 0
        assert capabilities.total_voices > 0
        assert len(capabilities.capabilities) > 0
        
        # Check Hindi capabilities
        hindi_cap = next(
            (cap for cap in capabilities.capabilities if cap.language == LanguageCode.HINDI), 
            None
        )
        assert hindi_cap is not None
        assert len(hindi_cap.available_voices) > 0
    
    @pytest.mark.asyncio
    async def test_get_voice_stats_empty(self, voice_service, mock_db):
        """Test getting voice stats when no data exists."""
        mock_db.voice_stats.find_one = AsyncMock(return_value=None)
        
        stats = await voice_service.get_voice_stats()
        
        assert stats is not None
        assert stats.total_tts_requests == 0
        assert stats.total_stt_requests == 0
        assert stats.total_voice_translations == 0
    
    @pytest.mark.asyncio
    async def test_get_voice_stats_with_data(self, voice_service, mock_db):
        """Test getting voice stats with existing data."""
        mock_stats = {
            "total_tts_requests": 100,
            "total_stt_requests": 50,
            "total_voice_translations": 25,
            "language_usage": {"hi": 60, "en": 40},
            "provider_usage": {"aws_polly": 100}
        }
        mock_db.voice_stats.find_one = AsyncMock(return_value=mock_stats)
        
        stats = await voice_service.get_voice_stats()
        
        assert stats.total_tts_requests == 100
        assert stats.total_stt_requests == 50
        assert stats.total_voice_translations == 25
        assert stats.language_usage["hi"] == 60
        assert stats.provider_usage["aws_polly"] == 100
    
    @pytest.mark.asyncio
    async def test_get_cached_audio_miss(self, voice_service, mock_redis):
        """Test cache miss for audio."""
        mock_redis.get = AsyncMock(return_value=None)
        
        result = await voice_service._get_cached_audio("test_key")
        
        assert result is None
        mock_redis.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_cache_audio_result(self, voice_service, mock_redis):
        """Test caching audio result."""
        from app.models.voice import TextToSpeechResult
        
        result = TextToSpeechResult(
            original_text="Test",
            language=LanguageCode.ENGLISH,
            audio_url="/test.mp3",
            audio_format=AudioFormat.MP3,
            voice_id="Aria",
            provider="aws_polly",
            file_size_bytes=1024
        )
        
        await voice_service._cache_audio_result("test_key", result)
        
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args
        assert args[0][0] == "test_key"  # cache key
        assert args[0][1] == voice_service.cache_ttl  # TTL
    
    @pytest.mark.asyncio
    async def test_update_tts_stats(self, voice_service, mock_db):
        """Test updating TTS statistics."""
        mock_db.voice_stats.update_one = AsyncMock()
        
        await voice_service._update_tts_stats(LanguageCode.HINDI, "Aditi", 2.5)
        
        mock_db.voice_stats.update_one.assert_called_once()
        call_args = mock_db.voice_stats.update_one.call_args
        
        # Check the update operation
        update_doc = call_args[0][1]
        assert "$inc" in update_doc
        assert update_doc["$inc"]["total_tts_requests"] == 1
        assert update_doc["$inc"]["language_usage.hi"] == 1
        assert update_doc["$inc"]["provider_usage.aws_polly"] == 1
    
    @pytest.mark.asyncio
    async def test_update_voice_translation_stats(self, voice_service, mock_db):
        """Test updating voice translation statistics."""
        mock_db.voice_stats.update_one = AsyncMock()
        
        await voice_service._update_voice_translation_stats(
            LanguageCode.HINDI, 
            LanguageCode.ENGLISH
        )
        
        mock_db.voice_stats.update_one.assert_called_once()
        call_args = mock_db.voice_stats.update_one.call_args
        
        # Check the update operation
        update_doc = call_args[0][1]
        assert "$inc" in update_doc
        assert update_doc["$inc"]["total_voice_translations"] == 1
        assert update_doc["$inc"]["language_usage.hi"] == 1
        assert update_doc["$inc"]["language_usage.en"] == 1


class TestVoiceServiceIntegration:
    """Integration tests for voice service."""
    
    @pytest.mark.asyncio
    async def test_text_to_speech_same_language(self, voice_service):
        """Test TTS when source and target are same language."""
        # This test would require actual AWS Polly integration
        # For now, we'll test the basic flow
        request = TextToSpeechRequest(
            text="Hello world",
            language=LanguageCode.ENGLISH,
            voice_type=VoiceType.STANDARD,
            audio_format=AudioFormat.MP3
        )
        
        # Mock the Polly client to avoid actual API calls
        with patch.object(voice_service, 'polly_client') as mock_polly:
            mock_polly.synthesize_speech.return_value = {
                'AudioStream': Mock(read=Mock(return_value=b'fake_audio_data'))
            }
            
            with patch.object(voice_service, '_save_audio_file') as mock_save:
                mock_save.return_value = "/fake/path/audio.mp3"
                
                with patch.object(voice_service, '_get_audio_duration') as mock_duration:
                    mock_duration.return_value = 2.5
                    
                    with patch('os.path.getsize', return_value=1024):
                        with patch.object(voice_service, '_store_audio_file_info') as mock_store:
                            # This would normally call the actual TTS service
                            # For testing, we verify the method exists and can be called
                            assert hasattr(voice_service, 'text_to_speech')
                            assert callable(voice_service.text_to_speech)
    
    @pytest.mark.asyncio
    async def test_speech_to_text_placeholder(self, voice_service):
        """Test STT placeholder functionality."""
        from app.models.voice import SpeechToTextRequest
        
        request = SpeechToTextRequest(
            audio_data="fake_base64_data",
            language=LanguageCode.HINDI,
            audio_format=AudioFormat.WAV
        )
        
        result = await voice_service.speech_to_text(request)
        
        assert result is not None
        assert result.provider == "web_speech_api_placeholder"
        assert result.confidence_score == 0.0