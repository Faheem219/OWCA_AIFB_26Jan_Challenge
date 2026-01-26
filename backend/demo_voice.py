#!/usr/bin/env python3
"""
Demo script for voice processing functionality.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.voice_service import VoiceService
from app.models.voice import (
    TextToSpeechRequest,
    VoiceType,
    AudioFormat,
    Gender,
    LanguageCode
)
from unittest.mock import Mock, AsyncMock


async def demo_voice_service():
    """Demo the voice service functionality."""
    print("🎤 Voice Processing Service Demo")
    print("=" * 50)
    
    # Create mock dependencies
    mock_db = Mock()
    mock_db.__getitem__ = Mock(return_value=AsyncMock())
    
    mock_redis = Mock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock()
    
    mock_translation_service = Mock()
    mock_translation_service.LANGUAGE_NAMES = {
        "hi": {"name": "Hindi", "native_name": "हिन्दी"},
        "en": {"name": "English", "native_name": "English"},
        "ta": {"name": "Tamil", "native_name": "தமிழ்"},
        "te": {"name": "Telugu", "native_name": "తెలుగు"},
        "bn": {"name": "Bengali", "native_name": "বাংলা"}
    }
    
    # Initialize voice service
    try:
        voice_service = VoiceService(mock_db, mock_redis, mock_translation_service)
        print("✅ Voice service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize voice service: {e}")
        return
    
    # Test voice capabilities
    print("\n📋 Testing voice capabilities...")
    try:
        capabilities = await voice_service.get_voice_capabilities()
        print(f"✅ Found {capabilities.total_languages} supported languages")
        print(f"✅ Found {capabilities.total_voices} available voices")
        
        for cap in capabilities.capabilities[:3]:  # Show first 3
            print(f"   - {cap.language_name}: {len(cap.available_voices)} voices")
            
    except Exception as e:
        print(f"❌ Failed to get voice capabilities: {e}")
    
    # Test voice selection
    print("\n🎯 Testing voice selection...")
    try:
        hindi_voice = voice_service._select_voice(
            LanguageCode.HINDI, 
            Gender.FEMALE, 
            VoiceType.STANDARD
        )
        print(f"✅ Selected Hindi female voice: {hindi_voice}")
        
        english_voice = voice_service._select_voice(
            LanguageCode.ENGLISH, 
            Gender.MALE, 
            VoiceType.NEURAL
        )
        print(f"✅ Selected English male voice: {english_voice}")
        
    except Exception as e:
        print(f"❌ Failed voice selection: {e}")
    
    # Test audio format conversion
    print("\n🔄 Testing audio format conversion...")
    try:
        mp3_format = voice_service._get_polly_format(AudioFormat.MP3)
        wav_format = voice_service._get_polly_format(AudioFormat.WAV)
        print(f"✅ MP3 -> Polly format: {mp3_format}")
        print(f"✅ WAV -> Polly format: {wav_format}")
        
    except Exception as e:
        print(f"❌ Failed format conversion: {e}")
    
    # Test cache key generation
    print("\n🔑 Testing cache key generation...")
    try:
        request = TextToSpeechRequest(
            text="नमस्ते, आप कैसे हैं?",
            language=LanguageCode.HINDI,
            voice_type=VoiceType.STANDARD,
            audio_format=AudioFormat.MP3,
            speed=1.0
        )
        
        cache_key = voice_service._generate_tts_cache_key(request)
        print(f"✅ Generated cache key: {cache_key[:50]}...")
        
    except Exception as e:
        print(f"❌ Failed cache key generation: {e}")
    
    # Test statistics
    print("\n📊 Testing statistics...")
    try:
        stats = await voice_service.get_voice_stats()
        print(f"✅ Retrieved voice stats:")
        print(f"   - TTS requests: {stats.total_tts_requests}")
        print(f"   - STT requests: {stats.total_stt_requests}")
        print(f"   - Voice translations: {stats.total_voice_translations}")
        
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")
    
    print("\n🎉 Voice service demo completed!")
    print("\nNote: This demo uses mock dependencies.")
    print("For full functionality, configure AWS Polly credentials in .env file.")


def main():
    """Run the demo."""
    try:
        asyncio.run(demo_voice_service())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")


if __name__ == "__main__":
    main()