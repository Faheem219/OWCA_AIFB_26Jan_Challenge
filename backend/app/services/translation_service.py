"""
Translation service with dictionary-based fallback for multilingual support.

This service provides real-time translation capabilities with a local dictionary
fallback when AWS Translate is unavailable, along with caching layer for performance.
"""

import logging
import hashlib
import random
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("AWS SDK not available, using mock translation")

from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.redis import cache, get_cached_translation, cache_translation

logger = logging.getLogger(__name__)


class TranslationRequest(BaseModel):
    """Translation request model."""
    text: str = Field(..., min_length=1, max_length=10000)
    source_language: str = Field(..., min_length=2, max_length=5)
    target_language: str = Field(..., min_length=2, max_length=5)
    context: Optional[str] = Field(None, max_length=500)


class BulkTranslationRequest(BaseModel):
    """Bulk translation request model."""
    texts: List[str] = Field(..., min_items=1, max_items=100)
    source_language: str = Field(..., min_length=2, max_length=5)
    target_language: str = Field(..., min_length=2, max_length=5)
    context: Optional[str] = Field(None, max_length=500)


class TranslationResult(BaseModel):
    """Translation result model."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence_score: Optional[float] = None
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LanguageDetectionResult(BaseModel):
    """Language detection result model."""
    text: str
    detected_language: str
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BulkTranslationResult(BaseModel):
    """Bulk translation result model."""
    results: List[TranslationResult]
    total_count: int
    successful_count: int
    failed_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TranslationService:
    """Translation service with dictionary-based fallback mechanisms."""
    
    def __init__(self):
        """Initialize the translation service."""
        self.translate_client = None
        self._initialize_aws_client()
        
        # Language code mappings
        self.language_mappings = {
            "hi": "hi",      # Hindi
            "en": "en",      # English
            "ta": "ta",      # Tamil
            "te": "te",      # Telugu
            "kn": "kn",      # Kannada
            "ml": "ml",      # Malayalam
            "gu": "gu",      # Gujarati
            "pa": "pa",      # Punjabi
            "bn": "bn",      # Bengali
            "mr": "mr",      # Marathi
        }
        
        # Local translation dictionary for common terms (English to other languages)
        self.translation_dict = {
            "hi": {  # Hindi
                "product": "उत्पाद", "price": "कीमत", "seller": "विक्रेता", "buyer": "खरीदार",
                "vegetables": "सब्जियां", "fruits": "फल", "grains": "अनाज", "spices": "मसाले",
                "pulses": "दालें", "quality": "गुणवत्ता", "quantity": "मात्रा", "kg": "किलो",
                "good": "अच्छा", "fresh": "ताज़ा", "available": "उपलब्ध", "not available": "उपलब्ध नहीं",
                "hello": "नमस्ते", "thank you": "धन्यवाद", "yes": "हाँ", "no": "नहीं",
                "buy": "खरीदें", "sell": "बेचें", "negotiate": "बातचीत करें", "order": "आदेश",
                "delivery": "डिलीवरी", "payment": "भुगतान", "chat": "चैट", "search": "खोजें"
            },
            "ta": {  # Tamil
                "product": "தயாரிப்பு", "price": "விலை", "seller": "விற்பனையாளர்", "buyer": "வாங்குபவர்",
                "vegetables": "காய்கறிகள்", "fruits": "பழங்கள்", "grains": "தானியங்கள்", "spices": "மசாலா",
                "pulses": "பருப்புகள்", "quality": "தரம்", "quantity": "அளவு", "kg": "கிலோ",
                "good": "நல்ல", "fresh": "புதிய", "available": "கிடைக்கும்", "not available": "கிடைக்காது",
                "hello": "வணக்கம்", "thank you": "நன்றி", "yes": "ஆம்", "no": "இல்லை",
                "buy": "வாங்கு", "sell": "விற்க", "negotiate": "பேசுவோம்", "order": "ஆர்டர்",
                "delivery": "டெலிவரி", "payment": "செலுத்தல்", "chat": "அரட்டை", "search": "தேடு"
            },
            "te": {  # Telugu
                "product": "ఉత్పత్తి", "price": "ధర", "seller": "అమ్మేవాడు", "buyer": "కొనుగోలుదారు",
                "vegetables": "కూరగాయలు", "fruits": "పండ్లు", "grains": "ధాన్యాలు", "spices": "మసాలా",
                "pulses": "పప్పులు", "quality": "నాణ్యత", "quantity": "పరిమాణం", "kg": "కిలో",
                "good": "మంచి", "fresh": "తాజా", "available": "అందుబాటులో", "not available": "అందుబాటులో లేదు",
                "hello": "నమస్కారం", "thank you": "ధన్యవాదాలు", "yes": "అవును", "no": "కాదు",
                "buy": "కొనండి", "sell": "అమ్మండి", "negotiate": "చర్చించు", "order": "ఆర్డర్",
                "delivery": "డెలివరీ", "payment": "చెల్లింపు", "chat": "చాట్", "search": "వెతకండి"
            },
            "kn": {  # Kannada
                "product": "ಉತ್ಪನ್ನ", "price": "ಬೆಲೆ", "seller": "ಮಾರಾಟಗಾರ", "buyer": "ಖರೀದಿದಾರ",
                "vegetables": "ತರಕಾರಿಗಳು", "fruits": "ಹಣ್ಣುಗಳು", "grains": "ಧಾನ್ಯಗಳು", "spices": "ಮಸಾಲೆ",
                "pulses": "ದಾಲ್", "quality": "ಗುಣಮಟ್ಟ", "quantity": "ಪ್ರಮಾಣ", "kg": "ಕೆಜಿ",
                "good": "ಒಳ್ಳೆಯದು", "fresh": "ತಾಜಾ", "available": "ಲಭ್ಯವಿದೆ", "not available": "ಲಭ್ಯವಿಲ್ಲ",
                "hello": "ನಮಸ್ಕಾರ", "thank you": "ಧನ್ಯವಾದಗಳು", "yes": "ಹೌದು", "no": "ಇಲ್ಲ",
                "buy": "ಖರೀದಿಸು", "sell": "ಮಾರು", "negotiate": "ಚರ್ಚಿಸು", "order": "ಆರ್ಡರ್",
                "delivery": "ವಿತರಣೆ", "payment": "ಪಾವತಿ", "chat": "ಚಾಟ್", "search": "ಹುಡುಕು"
            },
            "ml": {  # Malayalam
                "product": "ഉത്പന്നം", "price": "വില", "seller": "വില്പനക്കാരന്", "buyer": "വാങ്ങുന്നയാൾ",
                "vegetables": "പച്ചക്കറികൾ", "fruits": "പഴങ്ങൾ", "grains": "ധാന്യങ്ങൾ", "spices": "സുഗന്ധവ്യഞ്ജനങ്ങൾ",
                "pulses": "പയർ", "quality": "ഗുണനിലവാരം", "quantity": "അളവ്", "kg": "കിലോ",
                "good": "നല്ലത്", "fresh": "പുതിയ", "available": "ലഭ്യമാണ്", "not available": "ലഭ്യമല്ല",
                "hello": "നമസ്കാരം", "thank you": "നന്ദി", "yes": "അതെ", "no": "ഇല്ല",
                "buy": "വാങ്ങുക", "sell": "വില്ക്കുക", "negotiate": "ചർച്ച ചെയ്യുക", "order": "ഓർഡർ",
                "delivery": "ഡെലിവറി", "payment": "പേയ്മെന്റ്", "chat": "ചാറ്റ്", "search": "തിരയുക"
            },
            "gu": {  # Gujarati
                "product": "ઉત્પાદન", "price": "કિંમત", "seller": "વેચનાર", "buyer": "ખરીદદાર",
                "vegetables": "શાકભાજી", "fruits": "ફળો", "grains": "અનાજ", "spices": "મસાલા",
                "pulses": "દાળ", "quality": "ગુણવત્તા", "quantity": "જથ્થો", "kg": "કિલો",
                "good": "સારું", "fresh": "તાજું", "available": "ઉપલબ્ધ", "not available": "ઉપલબ્ધ નથી",
                "hello": "નમસ્તે", "thank you": "આભાર", "yes": "હા", "no": "ના",
                "buy": "ખરીદો", "sell": "વેચો", "negotiate": "વાટાઘાટ", "order": "ઓર્ડર",
                "delivery": "ડિલિવરી", "payment": "ચુકવણી", "chat": "ચેટ", "search": "શોધો"
            },
            "pa": {  # Punjabi
                "product": "ਉਤਪਾਦ", "price": "ਕੀਮਤ", "seller": "ਵੇਚਣ ਵਾਲਾ", "buyer": "ਖਰੀਦਦਾਰ",
                "vegetables": "ਸਬਜ਼ੀਆਂ", "fruits": "ਫਲ", "grains": "ਅਨਾਜ", "spices": "ਮਸਾਲੇ",
                "pulses": "ਦਾਲਾਂ", "quality": "ਗੁਣਵੱਤਾ", "quantity": "ਮਾਤਰਾ", "kg": "ਕਿਲੋ",
                "good": "ਚੰਗਾ", "fresh": "ਤਾਜ਼ਾ", "available": "ਉਪਲਬਧ", "not available": "ਉਪਲਬਧ ਨਹੀਂ",
                "hello": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "thank you": "ਧੰਨਵਾਦ", "yes": "ਹਾਂ", "no": "ਨਹੀਂ",
                "buy": "ਖਰੀਦੋ", "sell": "ਵੇਚੋ", "negotiate": "ਗੱਲਬਾਤ", "order": "ਆਰਡਰ",
                "delivery": "ਡਿਲਿਵਰੀ", "payment": "ਭੁਗਤਾਨ", "chat": "ਚੈਟ", "search": "ਖੋਜ"
            },
            "bn": {  # Bengali
                "product": "পণ্য", "price": "দাম", "seller": "বিক্রেতা", "buyer": "ক্রেতা",
                "vegetables": "সবজি", "fruits": "ফল", "grains": "শস্য", "spices": "মসলা",
                "pulses": "ডাল", "quality": "মান", "quantity": "পরিমাণ", "kg": "কেজি",
                "good": "ভাল", "fresh": "তাজা", "available": "উপলব্ধ", "not available": "উপলব্ধ নেই",
                "hello": "নমস্কার", "thank you": "ধন্যবাদ", "yes": "হ্যাঁ", "no": "না",
                "buy": "কিনুন", "sell": "বিক্রি", "negotiate": "আলোচনা", "order": "অর্ডার",
                "delivery": "ডেলিভারি", "payment": "পেমেন্ট", "chat": "চ্যাট", "search": "খোঁজা"
            },
            "mr": {  # Marathi
                "product": "उत्पादन", "price": "किंमत", "seller": "विक्रेता", "buyer": "खरेदीदार",
                "vegetables": "भाज्या", "fruits": "फळे", "grains": "धान्य", "spices": "मसाले",
                "pulses": "डाळी", "quality": "गुणवत्ता", "quantity": "प्रमाण", "kg": "किलो",
                "good": "चांगले", "fresh": "ताजे", "available": "उपलब्ध", "not available": "उपलब्ध नाही",
                "hello": "नमस्कार", "thank you": "धन्यवाद", "yes": "होय", "no": "नाही",
                "buy": "खरेदी", "sell": "विक्री", "negotiate": "चर्चा", "order": "ऑर्डर",
                "delivery": "डिलिव्हरी", "payment": "पेमेंट", "chat": "चॅट", "search": "शोधा"
            }
        }
        
        # Supported language pairs
        self.supported_pairs = self._get_supported_language_pairs()
    
    def _initialize_aws_client(self) -> None:
        """Initialize AWS Translate client if available."""
        if not AWS_AVAILABLE:
            logger.info("AWS SDK not available, using dictionary-based translation")
            return
            
        try:
            if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
                self.translate_client = boto3.client(
                    'translate',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_TRANSLATE_REGION
                )
                logger.info("AWS Translate client initialized successfully")
            else:
                logger.info("AWS credentials not configured, using dictionary-based translation")
                
        except Exception as e:
            logger.warning(f"Failed to initialize AWS Translate client: {e}")
            logger.info("Falling back to dictionary-based translation")
            self.translate_client = None
    
    def _get_supported_language_pairs(self) -> Dict[str, List[str]]:
        """Get supported language pairs for translation."""
        # For MVP, we'll support all combinations of our supported languages
        supported_langs = list(self.language_mappings.keys())
        pairs = {}
        
        for source in supported_langs:
            pairs[source] = [target for target in supported_langs if target != source]
        
        return pairs
    
    def _generate_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key for translation."""
        # Create a hash of the text for consistent caching
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"translation:{source_lang}:{target_lang}:{text_hash}"
    
    def _validate_language_codes(self, source_lang: str, target_lang: str) -> Tuple[bool, str]:
        """Validate language codes and check if translation is supported."""
        if source_lang not in self.language_mappings:
            return False, f"Source language '{source_lang}' is not supported"
        
        if target_lang not in self.language_mappings:
            return False, f"Target language '{target_lang}' is not supported"
        
        if source_lang == target_lang:
            return False, "Source and target languages cannot be the same"
        
        if target_lang not in self.supported_pairs.get(source_lang, []):
            return False, f"Translation from '{source_lang}' to '{target_lang}' is not supported"
        
        return True, ""
    
    async def detect_language(self, text: str) -> LanguageDetectionResult:
        """
        Detect the language of given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language detection result
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            # Check cache first
            cache_key = f"language_detection:{hashlib.md5(text.encode('utf-8')).hexdigest()}"
            cached_result = await cache.get(cache_key)
            
            if cached_result:
                logger.info("Language detection result retrieved from cache")
                return LanguageDetectionResult(**cached_result)
            
            # Try AWS Translate if available
            if self.translate_client and AWS_AVAILABLE:
                try:
                    response = self.translate_client.detect_dominant_language(Text=text)
                    
                    if response.get('Languages'):
                        dominant_language = response['Languages'][0]
                        language_code = dominant_language['LanguageCode']
                        confidence = dominant_language['Score']
                        
                        # Map AWS language code to our supported languages
                        mapped_language = None
                        for our_code, aws_code in self.language_mappings.items():
                            if aws_code == language_code:
                                mapped_language = our_code
                                break
                        
                        if not mapped_language:
                            mapped_language = "en"
                            confidence = 0.5
                        
                        result = LanguageDetectionResult(
                            text=text,
                            detected_language=mapped_language,
                            confidence_score=confidence
                        )
                        
                        # Cache the result
                        await cache.set(cache_key, result.dict(), settings.TRANSLATION_CACHE_TTL)
                        
                        logger.info(f"Language detected: {mapped_language} (confidence: {confidence:.2f})")
                        return result
                except Exception as e:
                    logger.warning(f"AWS language detection failed: {e}")
            
            # Simple heuristic-based detection as fallback
            detected_lang = self._heuristic_language_detection(text)
            result = LanguageDetectionResult(
                text=text,
                detected_language=detected_lang,
                confidence_score=0.6
            )
            
            # Cache the result
            await cache.set(cache_key, result.dict(), settings.TRANSLATION_CACHE_TTL)
            return result
            
        except Exception as e:
            logger.error(f"Error during language detection: {e}")
            # Default to English
            return LanguageDetectionResult(
                text=text,
                detected_language="en",
                confidence_score=0.1
            )
    
    def _heuristic_language_detection(self, text: str) -> str:
        """Simple heuristic-based language detection."""
        # Check for common words in each language
        text_lower = text.lower()
        
        # Check each language's dictionary for matches
        best_match = "en"
        best_score = 0
        
        for lang_code, translations in self.translation_dict.items():
            score = sum(1 for word in translations.values() if word.lower() in text_lower)
            if score > best_score:
                best_score = score
                best_match = lang_code
        
        # If no matches found, default to English
        if best_score == 0:
            # Check if text contains mostly ASCII (likely English)
            ascii_chars = sum(1 for c in text if ord(c) < 128)
            if ascii_chars / len(text) > 0.8:
                return "en"
            # Otherwise, return Hindi as default for Indian scripts
            return "hi"
        
        return best_match
    
    async def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> TranslationResult:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            context: Optional context for better translation
            
        Returns:
            Translation result
            
        Raises:
            ValueError: If input validation fails
            RuntimeError: If translation service is unavailable
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Validate language codes
        is_valid, error_msg = self._validate_language_codes(source_language, target_language)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Check cache first
        cached_translation = await get_cached_translation(text, source_language, target_language)
        if cached_translation:
            logger.info("Translation retrieved from cache")
            return TranslationResult(
                original_text=text,
                translated_text=cached_translation,
                source_language=source_language,
                target_language=target_language,
                cached=True
            )
        
        # Perform translation
        try:
            translated_text = await self._perform_translation(
                text, source_language, target_language, context
            )
            
            # Cache the translation
            await cache_translation(text, source_language, target_language, translated_text)
            
            result = TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                cached=False
            )
            
            logger.info(f"Text translated from {source_language} to {target_language}")
            return result
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # Fallback mechanism
            return await self._handle_translation_fallback(
                text, source_language, target_language
            )
    
    async def _perform_translation(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> str:
        """
        Perform the actual translation using AWS Translate or dictionary fallback.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            context: Optional context
            
        Returns:
            Translated text
        """
        # Try AWS Translate first if available
        if self.translate_client and AWS_AVAILABLE:
            try:
                return await self._aws_translate(text, source_language, target_language, context)
            except Exception as e:
                logger.warning(f"AWS Translate failed, falling back to dictionary: {e}")
        
        # Use dictionary-based translation as fallback
        return await self._dictionary_translate(text, source_language, target_language)
    
    async def _aws_translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> str:
        """Perform translation using AWS Translate."""
        # Map our language codes to AWS language codes
        aws_source = self.language_mappings[source_language]
        aws_target = self.language_mappings[target_language]
        
        # Prepare translation request
        translate_params = {
            'Text': text,
            'SourceLanguageCode': aws_source,
            'TargetLanguageCode': aws_target
        }
        
        # Add context if provided
        if context:
            translate_params['Text'] = f"Context: {context}\n\nText: {text}"
        
        # Call AWS Translate
        response = self.translate_client.translate_text(**translate_params)
        translated_text = response['TranslatedText']
        
        # Extract text if context was added
        if context and "Text: " in translated_text:
            translated_text = translated_text.split("Text: ", 1)[1]
        
        return translated_text.strip()
    
    async def _dictionary_translate(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> str:
        """
        Perform dictionary-based translation for common terms.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Translated text (or original if not in dictionary)
        """
        text_lower = text.lower().strip()
        
        # If source is English, translate to target
        if source_language == "en" and target_language in self.translation_dict:
            target_dict = self.translation_dict[target_language]
            if text_lower in target_dict:
                return target_dict[text_lower]
        
        # If target is English, reverse lookup from source
        elif target_language == "en" and source_language in self.translation_dict:
            source_dict = self.translation_dict[source_language]
            for en_word, translated_word in source_dict.items():
                if translated_word == text or translated_word.lower() == text_lower:
                    return en_word
        
        # Try word-by-word translation for multi-word text
        words = text.split()
        if len(words) > 1 and source_language == "en" and target_language in self.translation_dict:
            target_dict = self.translation_dict[target_language]
            translated_words = []
            for word in words:
                word_lower = word.lower().strip('.,!?')
                if word_lower in target_dict:
                    translated_words.append(target_dict[word_lower])
                else:
                    translated_words.append(word)
            return " ".join(translated_words)
        
        # If no translation found, return original with marker
        logger.info(f"No dictionary translation for '{text}' from {source_language} to {target_language}")
        return text
    
    async def _handle_translation_fallback(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> TranslationResult:
        """
        Handle translation fallback when primary translation fails.
        
        Args:
            text: Original text
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Fallback translation result
        """
        logger.warning(f"Using fallback for translation from {source_language} to {target_language}")
        
        # Try dictionary-based translation as final fallback
        try:
            translated_text = await self._dictionary_translate(text, source_language, target_language)
            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                confidence_score=0.5,
                cached=False
            )
        except Exception:
            # If all else fails, return original text
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                confidence_score=0.0,
                cached=False
            )
    
    async def bulk_translate(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> BulkTranslationResult:
        """
        Translate multiple texts in a single request.
        
        Args:
            texts: List of texts to translate
            source_language: Source language code
            target_language: Target language code
            context: Optional context for better translation
            
        Returns:
            Bulk translation result
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        if len(texts) > 100:
            raise ValueError("Maximum 100 texts allowed per bulk request")
        
        # Validate language codes
        is_valid, error_msg = self._validate_language_codes(source_language, target_language)
        if not is_valid:
            raise ValueError(error_msg)
        
        results = []
        successful_count = 0
        failed_count = 0
        
        # Process each text individually
        for text in texts:
            try:
                if not text or not text.strip():
                    # Skip empty texts
                    failed_count += 1
                    continue
                
                result = await self.translate_text(
                    text, source_language, target_language, context
                )
                results.append(result)
                successful_count += 1
                
            except Exception as e:
                logger.error(f"Failed to translate text in bulk request: {e}")
                # Add failed result
                results.append(TranslationResult(
                    original_text=text,
                    translated_text=f"[Translation failed] {text}",
                    source_language=source_language,
                    target_language=target_language,
                    confidence_score=0.0
                ))
                failed_count += 1
        
        return BulkTranslationResult(
            results=results,
            total_count=len(texts),
            successful_count=successful_count,
            failed_count=failed_count
        )
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported languages.
        
        Returns:
            Dictionary mapping language codes to language names
        """
        language_names = {
            "hi": "Hindi",
            "en": "English",
            "ta": "Tamil",
            "te": "Telugu",
            "kn": "Kannada",
            "ml": "Malayalam",
            "gu": "Gujarati",
            "pa": "Punjabi",
            "bn": "Bengali",
            "mr": "Marathi",
        }
        
        return language_names
    
    def get_supported_language_pairs(self) -> Dict[str, List[str]]:
        """
        Get supported language pairs for translation.
        
        Returns:
            Dictionary mapping source languages to list of target languages
        """
        return self.supported_pairs.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the translation service.
        
        Returns:
            Health status information
        """
        health_status = {
            "service": "translation",
            "status": "healthy",
            "translation_method": "dictionary-based",
            "cache": "available",
            "supported_languages": len(self.language_mappings),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check AWS Translate availability
        if self.translate_client and AWS_AVAILABLE:
            health_status["translation_method"] = "aws-translate"
            try:
                # Test with a simple translation
                test_response = self.translate_client.translate_text(
                    Text="Hello",
                    SourceLanguageCode="en",
                    TargetLanguageCode="hi"
                )
                if test_response.get('TranslatedText'):
                    health_status["aws_translate"] = "available"
                else:
                    health_status["aws_translate"] = "error"
                    health_status["translation_method"] = "dictionary-based"
            except Exception as e:
                logger.warning(f"AWS Translate health check failed: {e}")
                health_status["aws_translate"] = "unavailable"
                health_status["translation_method"] = "dictionary-based"
        else:
            health_status["aws_translate"] = "not-configured"
        
        # Check cache availability
        try:
            test_key = "health_check_test"
            await cache.set(test_key, "test", 10)
            cached_value = await cache.get(test_key)
            await cache.delete(test_key)
            
            if cached_value != "test":
                health_status["cache"] = "error"
                if health_status["status"] == "healthy":
                    health_status["status"] = "degraded"
                    
        except Exception as e:
            logger.warning(f"Cache health check failed: {e}")
            health_status["cache"] = "error"
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
        
        return health_status


# Global translation service instance
translation_service = TranslationService()