"""
K-Lingua v2.0 - Language Detector
Identifies languages and scripts using IndicBERT
"""

import numpy as np
from typing import Dict, List, Tuple, Optional


class LanguageDetector:
    """
    Language detection using IndicBERT embeddings
    """
    
    def __init__(
        self,
        model_name: str = "models/lingua/indicbert",
        device: str = "cpu",
        confidence_threshold: float = 0.60,
        detect_code_mixing: bool = True
    ):
        """
        Initialize language detector
        
        Args:
            model_name: IndicBERT model name
            device: Device to run on
            confidence_threshold: Confidence threshold for primary language
            detect_code_mixing: Enable code-mixing detection
        """
        self.model_name = model_name
        self.device = device
        self.confidence_threshold = confidence_threshold
        self.detect_code_mixing = detect_code_mixing
        
        # Model will be loaded lazily
        self.model = None
        self.tokenizer = None
        
        # Supported languages
        self.languages = {
            'en': {'name': 'English', 'scripts': ['latin']},
            'hi': {'name': 'Hindi', 'scripts': ['devanagari']},
            'ta': {'name': 'Tamil', 'scripts': ['tamil']},
            'te': {'name': 'Telugu', 'scripts': ['telugu']},
            'ml': {'name': 'Malayalam', 'scripts': ['malayalam']},
            'kn': {'name': 'Kannada', 'scripts': ['kannada']},
            'bn': {'name': 'Bengali', 'scripts': ['bengali']},
            'mr': {'name': 'Marathi', 'scripts': ['devanagari']},
            'gu': {'name': 'Gujarati', 'scripts': ['gujarati']},
            'pa': {'name': 'Punjabi', 'scripts': ['gurmukhi']},
            'or': {'name': 'Odia', 'scripts': ['odia']},
            'as': {'name': 'Assamese', 'scripts': ['bengali']},
        }
    
    def _load_model(self):
        """Load IndicBERT model lazily"""
        if self.model is not None:
            return
        
        try:
            from transformers import AutoTokenizer, AutoModel
            
            print(f"Loading IndicBERT model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            print("IndicBERT model loaded successfully")
            
        except Exception as e:
            print(f"Failed to load IndicBERT model: {e}")
            print("Falling back to rule-based detection")
    
    def detect_language(
        self,
        text: str
    ) -> Dict:
        """
        Detect language(s) in text
        
        Args:
            text: Input text
        
        Returns:
            Dict with language detection results
        """
        if not text or len(text.strip()) < 3:
            return self._get_default_result()
        
        # Try IndicBERT-based detection
        try:
            self._load_model()
            if self.model is not None:
                return self._detect_with_indicbert(text)
        except Exception as e:
            print(f"IndicBERT detection failed: {e}")
        
        # Fallback to rule-based detection
        return self._detect_rule_based(text)
    
    def _detect_with_indicbert(self, text: str) -> Dict:
        """
        Detect language using IndicBERT embeddings
        
        Args:
            text: Input text
        
        Returns:
            Language detection result
        """
        # This is a simplified implementation
        # In production, you would use IndicBERT's language classification head
        # or analyze token embeddings for language identification
        
        # For now, use rule-based as placeholder
        return self._detect_rule_based(text)
    
    def _detect_rule_based(self, text: str) -> Dict:
        """
        Rule-based language detection (fallback)
        
        Args:
            text: Input text
        
        Returns:
            Language detection result
        """
        # Detect script
        script = self._detect_script(text)
        
        # Infer language from script
        if script == 'latin':
            # Check for English vs Hinglish
            if self._has_indic_words(text):
                primary_lang = 'en'
                secondary_langs = ['hi']
                is_code_mixed = True
                primary_conf = 0.70
            else:
                primary_lang = 'en'
                secondary_langs = []
                is_code_mixed = False
                primary_conf = 0.90
        
        elif script == 'devanagari':
            primary_lang = 'hi'
            secondary_langs = []
            is_code_mixed = False
            primary_conf = 0.85
        
        elif script == 'tamil':
            primary_lang = 'ta'
            secondary_langs = []
            is_code_mixed = False
            primary_conf = 0.85
        
        elif script == 'telugu':
            primary_lang = 'te'
            secondary_langs = []
            is_code_mixed = False
            primary_conf = 0.85
        
        else:
            # Mixed or unknown
            primary_lang = 'en'
            secondary_langs = []
            is_code_mixed = True
            primary_conf = 0.60
        
        return {
            'primary_language': primary_lang,
            'primary_confidence': primary_conf,
            'secondary_languages': secondary_langs,
            'secondary_confidence': 0.30 if secondary_langs else 0.0,
            'primary_script': script,
            'secondary_scripts': [],
            'is_code_mixed': is_code_mixed,
            'code_mixing_confidence': 0.80 if is_code_mixed else 0.0
        }
    
    def _detect_script(self, text: str) -> str:
        """
        Detect writing script
        
        Args:
            text: Input text
        
        Returns:
            Script name
        """
        # Count characters by Unicode range
        latin_count = 0
        devanagari_count = 0
        tamil_count = 0
        telugu_count = 0
        
        for char in text:
            code = ord(char)
            
            # Latin (A-Z, a-z)
            if (0x0041 <= code <= 0x005A) or (0x0061 <= code <= 0x007A):
                latin_count += 1
            
            # Devanagari (Hindi, Marathi, etc.)
            elif 0x0900 <= code <= 0x097F:
                devanagari_count += 1
            
            # Tamil
            elif 0x0B80 <= code <= 0x0BFF:
                tamil_count += 1
            
            # Telugu
            elif 0x0C00 <= code <= 0x0C7F:
                telugu_count += 1
        
        # Determine dominant script
        total = latin_count + devanagari_count + tamil_count + telugu_count
        if total == 0:
            return 'latin'
        
        if devanagari_count > latin_count and devanagari_count > tamil_count:
            return 'devanagari'
        elif tamil_count > latin_count and tamil_count > devanagari_count:
            return 'tamil'
        elif telugu_count > latin_count:
            return 'telugu'
        else:
            return 'latin'
    
    def _has_indic_words(self, text: str) -> bool:
        """
        Check if text contains Indic language words (in Roman script)
        
        Args:
            text: Input text
        
        Returns:
            True if Indic words detected
        """
        # Common Hinglish words
        hinglish_words = {
            'hai', 'hain', 'ka', 'ke', 'ki', 'ko', 'se', 'mein', 'par',
            'aap', 'kya', 'kaise', 'kab', 'kahan', 'kyun', 'kaun',
            'yeh', 'woh', 'yahan', 'wahan', 'abhi', 'phir', 'aur',
            'ya', 'lekin', 'nahi', 'nahin', 'haan', 'ji'
        }
        
        words = text.lower().split()
        for word in words:
            if word in hinglish_words:
                return True
        
        return False
    
    def _get_default_result(self) -> Dict:
        """Get default language detection result"""
        return {
            'primary_language': 'en',
            'primary_confidence': 0.50,
            'secondary_languages': [],
            'secondary_confidence': 0.0,
            'primary_script': 'latin',
            'secondary_scripts': [],
            'is_code_mixed': False,
            'code_mixing_confidence': 0.0
        }
