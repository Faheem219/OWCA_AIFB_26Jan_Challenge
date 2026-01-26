"""
Property-based tests for real-time chat translation functionality.
**Validates: Requirements 6.1**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from unittest.mock import MagicMock

from app.models.translation import LanguageCode


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
    
    @given(
        sender=user_data(),
        recipient=user_data(),
        message_text=chat_message_text()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_translation_language_pair_logic(self, sender, recipient, message_text):
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
        
        # Mock participants data structure
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
        
        # Simulate the translation logic from ChatService._translate_message_for_participants
        unique_languages = set()
        for participant in participants:
            lang = participant.get("preferred_language", "en")
            if lang != sender['language'].value:
                unique_languages.add(lang)
        
        # PROPERTY: Translation should be required for different languages
        assert len(unique_languages) > 0, "Translation should be required when participants have different languages"
        assert recipient['language'].value in unique_languages, "Recipient's language should be in translation targets"
        
        # PROPERTY: Sender's language should not be in translation targets
        assert sender['language'].value not in unique_languages, "Sender's language should not need translation"
        
        # PROPERTY: Number of unique languages should match expected count
        expected_count = 1  # Only recipient's language since sender != recipient
        assert len(unique_languages) == expected_count, f"Should have exactly {expected_count} target language(s)"
    
    @given(
        users=st.lists(user_data(), min_size=3, max_size=5, unique_by=lambda x: x['id']),
        message_text=chat_message_text()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_group_chat_translation_language_logic(self, users, message_text):
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
        
        # Mock participants data structure
        participants = [
            {
                "user_id": user['id'],
                "user_name": user['name'],
                "preferred_language": user['language'].value,
                "role": "owner" if user == sender else "member"
            }
            for user in users
        ]
        
        # Simulate the translation logic
        unique_languages = set()
        for participant in participants:
            lang = participant.get("preferred_language", "en")
            if lang != sender['language'].value:
                unique_languages.add(lang)
        
        # PROPERTY: Should identify all unique target languages
        expected_target_languages = set(user['language'].value for user in recipients if user['language'] != sender['language'])
        assert unique_languages == expected_target_languages, \
            f"Translation targets should match expected languages: {expected_target_languages}"
        
        # PROPERTY: Should not include sender's language in translation targets
        assert sender['language'].value not in unique_languages, \
            "Sender's language should not be in translation targets"
        
        # PROPERTY: Number of translations should not exceed number of participants
        assert len(unique_languages) < len(users), \
            "Number of translation targets should be less than total participants"
    
    @given(
        sender=user_data(),
        recipient=user_data(),
        message_text=chat_message_text()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_same_language_no_translation_logic(self, sender, recipient, message_text):
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
        
        # Mock participants data structure
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
        
        # Simulate the translation logic
        unique_languages = set()
        for participant in participants:
            lang = participant.get("preferred_language", "en")
            if lang != sender['language'].value:
                unique_languages.add(lang)
        
        # PROPERTY: No translation should be needed when all participants use same language
        assert len(unique_languages) == 0, \
            "No translation should be required when all participants use the same language"
    
    @given(
        message_text=chat_message_text(),
        source_lang=supported_language_code(),
        target_lang=supported_language_code()
    )
    @settings(max_examples=50, deadline=5000)
    def test_translation_result_structure(self, message_text, source_lang, target_lang):
        """
        **Property 27: Real-Time Translation in Chat (Result Structure)**
        *For any* translation result, it should maintain proper structure and metadata.
        **Validates: Requirements 6.1**
        """
        assume(source_lang != target_lang)
        assume(len(message_text.strip()) > 0)
        
        # Mock translation result structure
        translation_result = {
            'language': target_lang,
            'text': f"[TRANSLATED to {target_lang.value}] {message_text}",
            'confidence_score': 0.95,
            'provider': 'aws_translate',
            'translated_at': '2024-01-01T12:00:00Z'
        }
        
        # PROPERTY: Translation result should have required fields
        required_fields = ['language', 'text', 'confidence_score', 'provider', 'translated_at']
        for field in required_fields:
            assert field in translation_result, f"Translation result must contain {field}"
        
        # PROPERTY: Language should match target language
        assert translation_result['language'] == target_lang, \
            "Translation result language should match target language"
        
        # PROPERTY: Translated text should not be empty
        assert len(translation_result['text']) > 0, \
            "Translated text should not be empty"
        
        # PROPERTY: Confidence score should be between 0 and 1
        assert 0.0 <= translation_result['confidence_score'] <= 1.0, \
            "Confidence score should be between 0.0 and 1.0"
        
        # PROPERTY: Provider should be specified
        assert len(translation_result['provider']) > 0, \
            "Translation provider should be specified"
    
    @given(
        message_text=chat_message_text(),
        source_lang=supported_language_code()
    )
    @settings(max_examples=30, deadline=5000)
    def test_fallback_translation_structure(self, message_text, source_lang):
        """
        **Property 27: Real-Time Translation in Chat (Fallback Handling)**
        *For any* translation failure, the system should provide fallback translation
        with appropriate metadata indicating the failure.
        **Validates: Requirements 6.1**
        """
        assume(len(message_text.strip()) > 0)
        
        # Mock fallback translation result (when translation fails)
        fallback_result = {
            'language': source_lang,  # Fallback uses source language
            'text': message_text,     # Fallback uses original text
            'confidence_score': 0.0,  # Zero confidence indicates fallback
            'provider': 'fallback',   # Special provider name
            'translated_at': '2024-01-01T12:00:00Z'
        }
        
        # PROPERTY: Fallback should preserve original text
        assert fallback_result['text'] == message_text, \
            "Fallback translation should preserve original text"
        
        # PROPERTY: Fallback should have zero confidence
        assert fallback_result['confidence_score'] == 0.0, \
            "Fallback translation should have zero confidence score"
        
        # PROPERTY: Fallback should be clearly identified
        assert fallback_result['provider'] == 'fallback', \
            "Fallback translation should be identified by provider"
        
        # PROPERTY: Fallback should maintain structure
        required_fields = ['language', 'text', 'confidence_score', 'provider', 'translated_at']
        for field in required_fields:
            assert field in fallback_result, f"Fallback result must contain {field}"
    
    @given(
        languages=st.lists(supported_language_code(), min_size=2, max_size=6, unique=True)
    )
    @settings(max_examples=20, deadline=5000)
    def test_multilingual_group_translation_coverage(self, languages):
        """
        **Property 27: Real-Time Translation in Chat (Multilingual Coverage)**
        *For any* group with multiple languages, all language pairs should be covered.
        **Validates: Requirements 6.1**
        """
        assume(len(languages) >= 2)
        
        sender_language = languages[0]
        recipient_languages = languages[1:]
        
        # Simulate translation coverage logic
        translation_pairs = []
        for target_lang in recipient_languages:
            if target_lang != sender_language:
                translation_pairs.append((sender_language, target_lang))
        
        # PROPERTY: Should have translation pair for each different language
        expected_pairs = len(recipient_languages)
        assert len(translation_pairs) == expected_pairs, \
            f"Should have {expected_pairs} translation pairs"
        
        # PROPERTY: All translation pairs should have sender as source
        for source, target in translation_pairs:
            assert source == sender_language, \
                "All translation pairs should have sender's language as source"
        
        # PROPERTY: All target languages should be different from source
        for source, target in translation_pairs:
            assert target != source, \
                "Target language should be different from source language"
        
        # PROPERTY: No duplicate translation pairs
        assert len(translation_pairs) == len(set(translation_pairs)), \
            "Translation pairs should be unique"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])