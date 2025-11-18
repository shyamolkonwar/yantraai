import re
from typing import Dict, Any, List
from googletrans import Translator
from ai4bharat.transliteration import XlitEngine


class TextNormalizationService:
    def __init__(self):
        self.translator_loaded = False
        self.xlit_loaded = False

        try:
            from googletrans import Translator
            self.translator = Translator()
            self.translator_loaded = True
            print("Google Translate loaded successfully")
        except ImportError as e:
            print(f"Google Translate not available: {e}")
            self.translator_loaded = False
        except Exception as e:
            print(f"Failed to initialize translator: {e}")
            self.translator_loaded = False

        # Initialize IndicTrans transliteration engine
        try:
            from ai4bharat.transliteration import XlitEngine
            self.xlit_engine = XlitEngine("hi", beam_width=10, rescore=True)
            self.xlit_loaded = True
            print("IndicTrans loaded successfully")
        except ImportError as e:
            print(f"IndicTrans not available: {e}")
            self.xlit_loaded = False
        except Exception as e:
            print(f"Failed to initialize IndicTrans: {e}")
            self.xlit_loaded = False

        # Common Indic language patterns
        self.indic_patterns = {
            'hindi': r'[\u0900-\u097F]',
            'bengali': r'[\u0980-\u09FF]',
            'tamil': r'[\u0B80-\u0BFF]',
            'telugu': r'[\u0C00-\u0C7F]',
            'marathi': r'[\u0900-\u097F]',
            'gujarati': r'[\u0A80-\u0AFF]',
            'kannada': r'[\u0C80-\u0CFF]',
            'punjabi': r'[\u0A00-\u0A7F]',
            'malayalam': r'[\u0D00-\u0D7F]'
        }

        # Language codes for IndicTrans
        self.lang_codes = {
            'hindi': 'hi',
            'bengali': 'bn',
            'tamil': 'ta',
            'telugu': 'te',
            'marathi': 'mr',
            'gujarati': 'gu',
            'kannada': 'kn',
            'punjabi': 'pa',
            'malayalam': 'ml'
        }

    def normalize_text(self, text: str) -> Dict[str, Any]:
        """
        Normalize and transliterate text
        """
        if not text or not text.strip():
            return {
                'normalized_text': '',
                'confidence': 0.0,
                'detected_language': 'unknown',
                'original_language': 'unknown'
            }

        try:
            # Clean the text first
            cleaned_text = self._clean_text(text)

            # Detect language
            detected_language = self._detect_language(cleaned_text)

            # Normalize based on detected language
            if detected_language in self.indic_patterns:
                normalized_result = self._normalize_indic_text(cleaned_text, detected_language)
            else:
                normalized_result = self._normalize_english_text(cleaned_text)

            return normalized_result

        except Exception as e:
            print(f"Text normalization failed: {e}")
            return {
                'normalized_text': text,
                'confidence': 0.1,
                'detected_language': 'unknown',
                'original_language': 'unknown',
                'error': str(e)
            }

    def _clean_text(self, text: str) -> str:
        """
        Clean and preprocess text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\-\.,;:!?()[\]{}"\'/\\]', '', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def _detect_language(self, text: str) -> str:
        """
        Detect the language of the text
        """
        # Check for Indic languages first
        for lang, pattern in self.indic_patterns.items():
            if re.search(pattern, text):
                return lang

        # Default to English if no Indic characters found
        return 'english'

    def _normalize_indic_text(self, text: str, language: str) -> Dict[str, Any]:
        """
        Normalize Indic language text
        """
        try:
            # Standardize common Indic numerals and symbols
            normalized = text

            # Apply language-specific normalization rules
            if language == 'hindi':
                normalized = self._normalize_hindi(normalized)
            elif language == 'bengali':
                normalized = self._normalize_bengali(normalized)
            # Add more languages as needed

            # Transliterate to English using IndicTrans
            transliterated_text = normalized
            translation_confidence = 0.8

            if self.xlit_loaded and language in self.lang_codes and len(normalized.strip()) > 0:
                try:
                    lang_code = self.lang_codes[language]
                    # Create engine for specific language
                    engine = XlitEngine(lang_code, beam_width=10, rescore=True)
                    transliterated_text = engine.translit_sentence(normalized)
                    translation_confidence = 0.9  # High confidence for IndicTrans
                except Exception as e:
                    print(f"IndicTrans transliteration failed: {e}")
                    # Fallback to google translate
                    if self.translator_loaded:
                        try:
                            result = self.translator.translate(normalized, dest='en')
                            transliterated_text = result.text
                            translation_confidence = 0.7
                        except Exception as e2:
                            print(f"Google translate fallback failed: {e2}")

            return {
                'normalized_text': transliterated_text,
                'confidence': translation_confidence,
                'detected_language': language,
                'original_language': language
            }

        except Exception as e:
            print(f"Indic text normalization failed: {e}")
            return {
                'normalized_text': text,
                'confidence': 0.2,
                'detected_language': language,
                'original_language': language
            }

    def _normalize_english_text(self, text: str) -> Dict[str, Any]:
        """
        Normalize English text
        """
        # Standard English normalization
        normalized = text.strip()

        # Fix common OCR errors
        corrections = {
            'l': ['1', '|'],  # Lowercase l might be confused with 1 or |
            'O': ['0'],       # Uppercase O might be confused with 0
            'I': ['1', '|'],  # Uppercase I might be confused with 1 or |
        }

        # Apply basic corrections (this is a simplified approach)
        for correct, incorrect_list in corrections.items():
            for incorrect in incorrect_list:
                # Only replace if it makes sense in context
                normalized = self._contextual_replace(normalized, incorrect, correct)

        return {
            'normalized_text': normalized,
            'confidence': 0.9,  # High confidence for English
            'detected_language': 'english',
            'original_language': 'english'
        }

    def _normalize_hindi(self, text: str) -> str:
        """
        Hindi-specific normalization
        """
        # Add Hindi-specific normalization rules here
        # For example: handling different vowel signs, conjunct consonants, etc.
        return text

    def _normalize_bengali(self, text: str) -> str:
        """
        Bengali-specific normalization
        """
        # Add Bengali-specific normalization rules here
        return text

    def _contextual_replace(self, text: str, old_char: str, new_char: str) -> str:
        """
        Context-aware character replacement
        """
        # This is a simplified implementation
        # In practice, you'd want more sophisticated context analysis
        return text.replace(old_char, new_char)

    def batch_normalize(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Normalize multiple texts
        """
        results = []
        for text in texts:
            result = self.normalize_text(text)
            results.append(result)
        return results
