"""
Property-based tests for real-time chat translation functionality.
**Validates: Requirements 6.1**
"""
import pytest
import asyncio
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.chat_service import ChatService
from app.services.translation_service import TranslationService
from app.models.chat import (
    ConversationCreateRequest, MessageCreateRequest, ConversationType,
    MessageType, Participant, ParticipantRole
)
from app.models.translation import LanguageCode, TranslationRequest, TranslationResult


# Test data generators
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
def chat_message_text(draw):
    """Generate realistic chat message text."""
    messages = [
        "Hello, how are you?",
        "What is the price of rice today?",
        "I am interested in buying wheat",
        "Can we negotiate the price?",
        "Thank you for your help",
        "When can you deliver?",
        "The quality looks good",
        "I need 100 kg of this product",
        "What payment methods do you accept?",
        "Is this organic certified?"
    ]
    return draw(st.sampled_from(messages))


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


class TestChatTranslationProperties:
    """Property-based tests for chat translation functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database."""
        db = AsyncMock()
        
        # Mock collections
        db.conversations = AsyncMock()
        db.messages = AsyncMock()
        db.users = AsyncMock()
        
        return db
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis cache."""
        redis = AsyncMock()
        redis.setex = AsyncMock()
        redis.get = AsyncMock()
        redis.delete = AsyncMock()
        redis.publish = AsyncMock()
        return redis
    
    @pytest.fixture
    def mock_translation_service(self):
        """Mock translation service."""
        service = AsyncMock(spec=TranslationService)
        return service
    
    @pytest.fixture
    def chat_service(self, mock_db, mock_redis, mock_translation_service):
        """Create chat service with mocked dependencies."""
        return ChatService(mock_db, mock_redis, mock_translation_service)
    
    @given(
        sender=user_data(),
        recipient=user_data(),
        message_text=chat_message_text()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_message_translation_for_different_languages(
        self, 
        chat_service, 
        mock_translation_service,
        mock_db,
        sender, 
        recipient, 
        message_text
    ):
        """
        **Property 27: Real-Time Translation in Chat**
        *For any* message sent in a supported language, the Communication_Hub should 
        provide real-time translation to all participants' preferred languages.
        **Validates: Requirements 6.1**
        """
        # Assume different languages for meaningful translation test
        assume(sender['language'] != recipient['language'])
        assume(len(sender['name']) > 0)
        assume(len(recipient['name']) > 0)
        assume(len(message_text.strip()) > 0)
        
        # Setup mock conversation data
        conversation_id = "test_conv_123"
        participants = [
            {
                "user_id": sender['id'],
                "user_name": sender['name'],
                "preferred_language": sender['language'].value,
                "role": "owner"
            },
            {
                "user_id": recipient['id'],
                "user_name": recipient['name'],
                "preferred_language": recipient['language'].value,
                "role": "member"
            }
        ]
        
        # Mock database responses
        mock_db.conversations.find_one.return_value = {
            "_id": conversation_id,
            "participants": participants,
            "type": "direct",
            "is_active": True
        }
        
        mock_db.messages.insert_one.return_value = MagicMock(inserted_id="msg_123")
        mock_db.conversations.update_one.return_value = MagicMock()
        
        # Mock translation service response
        translated_text = f"[TRANSLATED to {recipient['language'].value}] {message_text}"
        mock_translation_service.translate_text.return_value = TranslationResult(
            original_text=message_text,
            translated_text=translated_text,
            source_language=sender['language'],
            target_language=recipient['language'],
            confidence_score=0.95,
            provider="aws_translate",
            cached=False
        )
        
        # Create message request
        message_request = MessageCreateRequest(
            conversation_id=conversation_id,
            text=message_text,
            message_type=MessageType.TEXT
        )
        
        # Send message
        result = await chat_service.send_message(
            request=message_request,
            sender_id=sender['id'],
            sender_name=sender['name'],
            sender_language=sender['language']
        )
        
        # PROPERTY: Message should be successfully created
        assert result is not None, "Message creation should succeed"
        assert result.original_text == message_text, "Original text should be preserved"
        assert result.sender_id == sender['id'], "Sender ID should be correct"
        assert result.original_language == sender['language'], "Original language should be preserved"
        
        # PROPERTY: Translation should be requested for recipient's language
        mock_translation_service.translate_text.assert_called_once()
        translation_call = mock_translation_service.translate_text.call_args[0][0]
        assert translation_call.text == message_text, "Translation request should contain original text"
        assert translation_call.source_language == sender['language'], "Source language should match sender"
        assert translation_call.target_language == recipient['language'], "Target language should match recipient"
        
        # PROPERTY: Message should be stored in database
        mock_db.messages.insert_one.assert_called_once()
        stored_message = mock_db.messages.insert_one.call_args[0][0]
        assert stored_message['original_text'] == message_text, "Stored message should contain original text"
        assert stored_message['sender_id'] == sender['id'], "Stored message should have correct sender"
        assert recipient['language'].value in stored_message['translations'], "Translation should be stored for recipient"
        
        # PROPERTY: Conversation should be updated with last message info
        mock_db.conversations.update_one.assert_called_once()
        update_call = mock_db.conversations.update_one.call_args
        assert update_call[1]['$set']['last_message_preview'] == message_text[:100], "Conversation preview should be updated"
    
    @given(
        users=st.lists(user_data(), min_size=3, max_size=5, unique_by=lambda x: x['id']),
        message_text=chat_message_text()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_group_chat_translation_for_multiple_languages(
        self,
        chat_service,
        mock_translation_service,
        mock_db,
        users,
        message_text
    ):
        """
        **Property 27: Real-Time Translation in Chat (Group Chat)**
        *For any* message sent in a group conversation, translations should be provided
        for all participants who need them (different languages).
        **Validates: Requirements 6.1**
        """
        assume(len(set(user['language'] for user in users)) > 1)  # Multiple languages
        assume(all(len(user['name'].strip()) > 0 for user in users))
        assume(len(message_text.strip()) > 0)
        
        sender = users[0]
        recipients = users[1:]
        
        # Setup mock group conversation
        conversation_id = "group_conv_123"
        participants = [
            {
                "user_id": user['id'],
                "user_name": user['name'],
                "preferred_language": user['language'].value,
                "role": "owner" if user == sender else "member"
            }
            for user in users
        ]
        
        mock_db.conversations.find_one.return_value = {
            "_id": conversation_id,
            "participants": participants,
            "type": "group",
            "is_active": True
        }
        
        mock_db.messages.insert_one.return_value = MagicMock(inserted_id="msg_123")
        mock_db.conversations.update_one.return_value = MagicMock()
        
        # Mock translation for each unique target language
        unique_target_languages = set(user['language'] for user in recipients if user['language'] != sender['language'])
        
        def mock_translate(request):
            return TranslationResult(
                original_text=message_text,
                translated_text=f"[TRANSLATED to {request.target_language.value}] {message_text}",
                source_language=request.source_language,
                target_language=request.target_language,
                confidence_score=0.90,
                provider="aws_translate",
                cached=False
            )
        
        mock_translation_service.translate_text.side_effect = mock_translate
        
        # Create and send message
        message_request = MessageCreateRequest(
            conversation_id=conversation_id,
            text=message_text,
            message_type=MessageType.TEXT
        )
        
        result = await chat_service.send_message(
            request=message_request,
            sender_id=sender['id'],
            sender_name=sender['name'],
            sender_language=sender['language']
        )
        
        # PROPERTY: Message should be created successfully
        assert result is not None, "Group message creation should succeed"
        assert result.original_text == message_text, "Original text should be preserved"
        
        # PROPERTY: Translation should be called for each unique target language
        expected_translation_calls = len(unique_target_languages)
        assert mock_translation_service.translate_text.call_count == expected_translation_calls, \
            f"Should translate to {expected_translation_calls} unique languages"
        
        # PROPERTY: All translation calls should have correct parameters
        translation_calls = mock_translation_service.translate_text.call_args_list
        target_languages_called = set()
        
        for call in translation_calls:
            request = call[0][0]
            assert request.text == message_text, "All translation requests should contain original text"
            assert request.source_language == sender['language'], "All requests should have correct source language"
            target_languages_called.add(request.target_language)
        
        assert target_languages_called == unique_target_languages, \
            "Should translate to exactly the required target languages"
        
        # PROPERTY: Stored message should contain translations for all target languages
        mock_db.messages.insert_one.assert_called_once()
        stored_message = mock_db.messages.insert_one.call_args[0][0]
        
        for target_lang in unique_target_languages:
            assert target_lang.value in stored_message['translations'], \
                f"Translation for {target_lang.value} should be stored"
    
    @given(
        sender=user_data(),
        recipient=user_data(),
        message_text=chat_message_text()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_same_language_no_translation_needed(
        self,
        chat_service,
        mock_translation_service,
        mock_db,
        sender,
        recipient,
        message_text
    ):
        """
        **Property 27: Real-Time Translation in Chat (Same Language)**
        *For any* message sent when sender and recipient use the same language,
        no translation should be performed.
        **Validates: Requirements 6.1**
        """
        # Force same language
        recipient['language'] = sender['language']
        
        assume(len(sender['name'].strip()) > 0)
        assume(len(recipient['name'].strip()) > 0)
        assume(len(message_text.strip()) > 0)
        
        # Setup mock conversation
        conversation_id = "same_lang_conv"
        participants = [
            {
                "user_id": sender['id'],
                "user_name": sender['name'],
                "preferred_language": sender['language'].value,
                "role": "owner"
            },
            {
                "user_id": recipient['id'],
                "user_name": recipient['name'],
                "preferred_language": recipient['language'].value,
                "role": "member"
            }
        ]
        
        mock_db.conversations.find_one.return_value = {
            "_id": conversation_id,
            "participants": participants,
            "type": "direct",
            "is_active": True
        }
        
        mock_db.messages.insert_one.return_value = MagicMock(inserted_id="msg_123")
        mock_db.conversations.update_one.return_value = MagicMock()
        
        # Send message
        message_request = MessageCreateRequest(
            conversation_id=conversation_id,
            text=message_text,
            message_type=MessageType.TEXT
        )
        
        result = await chat_service.send_message(
            request=message_request,
            sender_id=sender['id'],
            sender_name=sender['name'],
            sender_language=sender['language']
        )
        
        # PROPERTY: Message should be created successfully
        assert result is not None, "Message creation should succeed"
        assert result.original_text == message_text, "Original text should be preserved"
        
        # PROPERTY: No translation should be performed when languages are the same
        mock_translation_service.translate_text.assert_not_called(), \
            "Translation service should not be called when all participants use same language"
        
        # PROPERTY: Message should still be stored in database
        mock_db.messages.insert_one.assert_called_once()
        stored_message = mock_db.messages.insert_one.call_args[0][0]
        assert stored_message['original_text'] == message_text, "Message should be stored with original text"
        assert len(stored_message['translations']) == 0, "No translations should be stored for same language"
    
    @given(
        sender=user_data(),
        recipient=user_data(),
        message_text=chat_message_text()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_translation_failure_fallback(
        self,
        chat_service,
        mock_translation_service,
        mock_db,
        sender,
        recipient,
        message_text
    ):
        """
        **Property 27: Real-Time Translation in Chat (Failure Handling)**
        *For any* message where translation fails, the system should gracefully
        handle the failure and still deliver the message with fallback text.
        **Validates: Requirements 6.1**
        """
        assume(sender['language'] != recipient['language'])
        assume(len(sender['name'].strip()) > 0)
        assume(len(recipient['name'].strip()) > 0)
        assume(len(message_text.strip()) > 0)
        
        # Setup mock conversation
        conversation_id = "failure_test_conv"
        participants = [
            {
                "user_id": sender['id'],
                "user_name": sender['name'],
                "preferred_language": sender['language'].value,
                "role": "owner"
            },
            {
                "user_id": recipient['id'],
                "user_name": recipient['name'],
                "preferred_language": recipient['language'].value,
                "role": "member"
            }
        ]
        
        mock_db.conversations.find_one.return_value = {
            "_id": conversation_id,
            "participants": participants,
            "type": "direct",
            "is_active": True
        }
        
        mock_db.messages.insert_one.return_value = MagicMock(inserted_id="msg_123")
        mock_db.conversations.update_one.return_value = MagicMock()
        
        # Mock translation service to raise an exception
        mock_translation_service.translate_text.side_effect = Exception("Translation service unavailable")
        
        # Send message
        message_request = MessageCreateRequest(
            conversation_id=conversation_id,
            text=message_text,
            message_type=MessageType.TEXT
        )
        
        result = await chat_service.send_message(
            request=message_request,
            sender_id=sender['id'],
            sender_name=sender['name'],
            sender_language=sender['language']
        )
        
        # PROPERTY: Message should still be created despite translation failure
        assert result is not None, "Message creation should succeed even when translation fails"
        assert result.original_text == message_text, "Original text should be preserved"
        
        # PROPERTY: Translation should have been attempted
        mock_translation_service.translate_text.assert_called_once()
        
        # PROPERTY: Message should be stored with fallback translation
        mock_db.messages.insert_one.assert_called_once()
        stored_message = mock_db.messages.insert_one.call_args[0][0]
        
        # Should have fallback translation (original text with low confidence)
        assert recipient['language'].value in stored_message['translations'], \
            "Fallback translation should be stored"
        
        fallback_translation = stored_message['translations'][recipient['language'].value]
        assert fallback_translation['text'] == message_text, \
            "Fallback should use original text"
        assert fallback_translation['confidence_score'] == 0.0, \
            "Fallback should have zero confidence"
        assert fallback_translation['provider'] == "fallback", \
            "Provider should indicate fallback"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])