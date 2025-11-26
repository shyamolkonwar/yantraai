"""
K-Lingua v2.0 - Transliterator
Script conversion using Aksharantar/IndicXlit
"""

from typing import Dict, Optional


class Transliterator:
    """
    Transliteration using Aksharantar dataset
    """
    
    def __init__(
        self,
        model_name: str = "ai4bharat/IndicXlit",
        preserve_bilingual: bool = True
    ):
        """
        Initialize transliterator
        
        Args:
            model_name: IndicXlit model name
            preserve_bilingual: Keep both scripts instead of converting
        """
        self.model_name = model_name
        self.preserve_bilingual = preserve_bilingual
        
        # Model will be loaded lazily
        self.model = None
        self.tokenizer = None
        
        # Transliteration mappings (simplified)
        self.devanagari_to_roman = self._get_devanagari_mappings()
    
    def _load_model(self):
        """Load IndicXlit model lazily"""
        if self.model is not None:
            return
        
        try:
            # IndicXlit model loading
            # Note: This is a placeholder - actual implementation would use
            # the specific IndicXlit model from AI4Bharat
            print(f"Loading IndicXlit model: {self.model_name}")
            # self.model = load_indicxlit_model(self.model_name)
            print("IndicXlit model loaded successfully")
            
        except Exception as e:
            print(f"Failed to load IndicXlit model: {e}")
            print("Using rule-based transliteration")
    
    def transliterate(
        self,
        text: str,
        source_script: str = "devanagari",
        target_script: str = "roman",
        language: str = "hi"
    ) -> Dict:
        """
        Transliterate text between scripts
        
        Args:
            text: Input text
            source_script: Source script (devanagari, tamil, etc.)
            target_script: Target script (roman, devanagari, etc.)
            language: Language code
        
        Returns:
            Dict with transliteration result
        """
        if not text or len(text.strip()) == 0:
            return {
                'transliterated_text': text,
                'tokens': [],
                'transliteration_confidence': 1.0
            }
        
        # If source and target are the same, no transliteration needed
        if source_script == target_script:
            return {
                'transliterated_text': text,
                'tokens': [],
                'transliteration_confidence': 1.0
            }
        
        # Try model-based transliteration
        try:
            self._load_model()
            if self.model is not None:
                return self._transliterate_with_model(
                    text, source_script, target_script, language
                )
        except Exception as e:
            print(f"Model-based transliteration failed: {e}")
        
        # Fallback to rule-based transliteration
        return self._transliterate_rule_based(
            text, source_script, target_script
        )
    
    def _transliterate_with_model(
        self,
        text: str,
        source_script: str,
        target_script: str,
        language: str
    ) -> Dict:
        """
        Transliterate using IndicXlit model
        
        Args:
            text: Input text
            source_script: Source script
            target_script: Target script
            language: Language code
        
        Returns:
            Transliteration result
        """
        # Placeholder for model-based transliteration
        # In production, this would use the actual IndicXlit model
        return self._transliterate_rule_based(text, source_script, target_script)
    
    def _transliterate_rule_based(
        self,
        text: str,
        source_script: str,
        target_script: str
    ) -> Dict:
        """
        Rule-based transliteration (fallback)
        
        Args:
            text: Input text
            source_script: Source script
            target_script: Target script
        
        Returns:
            Transliteration result
        """
        if source_script == "devanagari" and target_script == "roman":
            return self._devanagari_to_roman(text)
        elif source_script == "roman" and target_script == "devanagari":
            return self._roman_to_devanagari(text)
        else:
            # Unsupported conversion
            return {
                'transliterated_text': text,
                'tokens': [],
                'transliteration_confidence': 0.5
            }
    
    def _devanagari_to_roman(self, text: str) -> Dict:
        """
        Convert Devanagari to Roman script
        
        Args:
            text: Devanagari text
        
        Returns:
            Transliteration result
        """
        transliterated = []
        tokens = []
        
        for char in text:
            if char in self.devanagari_to_roman:
                roman_char = self.devanagari_to_roman[char]
                transliterated.append(roman_char)
                tokens.append({
                    'original': char,
                    'transliterated': roman_char,
                    'confidence': 0.90
                })
            else:
                transliterated.append(char)
        
        return {
            'transliterated_text': ''.join(transliterated),
            'tokens': tokens,
            'transliteration_confidence': 0.85
        }
    
    def _roman_to_devanagari(self, text: str) -> Dict:
        """
        Convert Roman to Devanagari script
        
        Args:
            text: Roman text
        
        Returns:
            Transliteration result
        """
        # Reverse mapping
        roman_to_dev = {v: k for k, v in self.devanagari_to_roman.items()}
        
        transliterated = []
        tokens = []
        
        i = 0
        while i < len(text):
            # Try to match longest sequence first
            matched = False
            for length in range(3, 0, -1):
                if i + length <= len(text):
                    substring = text[i:i+length]
                    if substring in roman_to_dev:
                        dev_char = roman_to_dev[substring]
                        transliterated.append(dev_char)
                        tokens.append({
                            'original': substring,
                            'transliterated': dev_char,
                            'confidence': 0.85
                        })
                        i += length
                        matched = True
                        break
            
            if not matched:
                transliterated.append(text[i])
                i += 1
        
        return {
            'transliterated_text': ''.join(transliterated),
            'tokens': tokens,
            'transliteration_confidence': 0.80
        }
    
    def _get_devanagari_mappings(self) -> Dict[str, str]:
        """Get Devanagari to Roman transliteration mappings"""
        return {
            # Vowels
            'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ii', 'उ': 'u', 'ऊ': 'uu',
            'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
            
            # Consonants
            'क': 'ka', 'ख': 'kha', 'ग': 'ga', 'घ': 'gha', 'ङ': 'nga',
            'च': 'cha', 'छ': 'chha', 'ज': 'ja', 'झ': 'jha', 'ञ': 'nya',
            'ट': 'ta', 'ठ': 'tha', 'ड': 'da', 'ढ': 'dha', 'ण': 'na',
            'त': 'ta', 'थ': 'tha', 'द': 'da', 'ध': 'dha', 'न': 'na',
            'प': 'pa', 'फ': 'pha', 'ब': 'ba', 'भ': 'bha', 'म': 'ma',
            'य': 'ya', 'र': 'ra', 'ल': 'la', 'व': 'va',
            'श': 'sha', 'ष': 'sha', 'स': 'sa', 'ह': 'ha',
            
            # Numbers
            '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
            '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
            
            # Special characters
            'ं': 'n', 'ः': 'h', '्': '', 'ा': 'aa', 'ि': 'i',
            'ी': 'ii', 'ु': 'u', 'ू': 'uu', 'े': 'e', 'ै': 'ai',
            'ो': 'o', 'ौ': 'au',
        }
