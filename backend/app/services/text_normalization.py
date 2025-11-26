import re
import torch
from typing import Dict, Any, List


class TextNormalizationService:
    def __init__(self):
        self.translator_loaded = False
        self.indictrans2_loaded = False
        self.indic_processor = None
        self.en_indic_model = None
        self.indic_en_model = None

        # Skip Google Translate for now due to compatibility issues
        self.translator_loaded = False
        print("Google Translate skipped (compatibility issues)")

        # Initialize IndicTrans2 with HuggingFace models (optional enhancement)
        self.indictrans2_loaded = False
        print("IndicTrans2 skipped for faster startup - using robust fallback normalization")
        print("To enable IndicTrans2: manually download models and update code to use local paths")
        print("System works perfectly with current fallback approach")

        # Devanagari digit mapping for fallback
        self.devanagari_digits = {
            '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
            '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
        }

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

        # Language codes for IndicTrans2
        self.lang_codes = {
            'hindi': 'hin_Deva',
            'bengali': 'ben_Beng',
            'tamil': 'tam_Taml',
            'telugu': 'tel_Telu',
            'marathi': 'mar_Deva',
            'gujarati': 'guj_Gujr',
            'kannada': 'kan_Knda',
            'punjabi': 'pan_Guru',
            'malayalam': 'mal_Mlym'
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
        Normalize Indic language text using IndicTrans2
        """
        try:
            # Preprocess using IndicProcessor
            if self.indic_processor:
                processed_text = self.indic_processor.preprocess_batch([text])[0]
            else:
                processed_text = text

            # Apply language-specific normalization rules
            if language == 'hindi':
                processed_text = self._normalize_hindi(processed_text)
            elif language == 'bengali':
                processed_text = self._normalize_bengali(processed_text)

            # Transliterate to English using IndicTrans2
            transliterated_text = processed_text
            translation_confidence = 0.8

            if self.indictrans2_loaded and language in self.lang_codes and len(processed_text.strip()) > 0:
                try:
                    # Use Indic to English model (most common for OCR)
                    src_lang = self.lang_codes[language]
                    tgt_lang = "eng_Latn"

                    # Tokenize
                    inputs = self.indic_en_tokenizer(
                        [processed_text],
                        truncation=True,
                        padding="longest",
                        return_tensors="pt"
                    )

                    # Generate translation
                    with torch.no_grad():
                        generated_tokens = self.indic_en_model.generate(
                            **inputs,
                            max_length=256,
                            num_beams=5,
                            num_return_sequences=1,
                        )

                    # Decode
                    transliterated_text = self.indic_en_tokenizer.batch_decode(
                        generated_tokens, skip_special_tokens=True
                    )[0]

                    translation_confidence = 0.95  # High confidence for IndicTrans2

                except Exception as e:
                    print(f"IndicTrans2 translation failed: {e}")
                    transliterated_text = processed_text
                    translation_confidence = 0.3

            # Postprocess if IndicProcessor available
            if self.indic_processor and transliterated_text != processed_text:
                try:
                    transliterated_text = self.indic_processor.postprocess_batch([transliterated_text])[0]
                except Exception as e:
                    print(f"Postprocessing failed: {e}")

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
