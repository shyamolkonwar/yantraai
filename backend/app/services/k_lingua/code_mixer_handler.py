"""
K-Lingua v2.0 - Code-Mixer Handler
Handles Hinglish and code-mixed text
"""

from typing import Dict, List, Tuple


class CodeMixerHandler:
    """
    Handle code-mixing and Hinglish text
    """
    
    def __init__(
        self,
        preserve_original: bool = True,
        threshold: float = 0.10
    ):
        """
        Initialize code-mixer handler
        
        Args:
            preserve_original: Preserve bilingual content
            threshold: Secondary language score to flag as mixed
        """
        self.preserve_original = preserve_original
        self.threshold = threshold
    
    def handle_code_mixing(
        self,
        text: str,
        is_code_mixed: bool,
        primary_language: str,
        secondary_languages: List[str]
    ) -> Dict:
        """
        Handle code-mixed text
        
        Args:
            text: Input text
            is_code_mixed: Whether text is code-mixed
            primary_language: Primary language code
            secondary_languages: Secondary language codes
        
        Returns:
            Dict with handled text and metadata
        """
        if not is_code_mixed:
            # No code-mixing, return as-is
            return {
                'handled_text': text,
                'strategy_used': 'no_action',
                'language_boundaries': [],
                'is_code_mixed': False
            }
        
        # Detect language boundaries
        boundaries = self._detect_language_boundaries(
            text,
            primary_language,
            secondary_languages
        )
        
        # Apply handling strategy
        if self.preserve_original:
            # Preserve bilingual content
            handled_text = text
            strategy = 'preserve_bilingual'
        else:
            # Convert to primary language
            handled_text = self._convert_to_primary(text, boundaries, primary_language)
            strategy = 'convert_to_primary'
        
        return {
            'handled_text': handled_text,
            'strategy_used': strategy,
            'language_boundaries': boundaries,
            'is_code_mixed': True
        }
    
    def _detect_language_boundaries(
        self,
        text: str,
        primary_language: str,
        secondary_languages: List[str]
    ) -> List[Dict]:
        """
        Detect language boundaries in code-mixed text
        
        Args:
            text: Input text
            primary_language: Primary language
            secondary_languages: Secondary languages
        
        Returns:
            List of language boundary markers
        """
        boundaries = []
        words = text.split()
        
        for i, word in enumerate(words):
            # Detect script
            script = self._detect_word_script(word)
            
            # Infer language
            if script == 'devanagari':
                language = 'hi' if 'hi' in secondary_languages else secondary_languages[0] if secondary_languages else 'hi'
            elif script == 'latin':
                language = primary_language
            else:
                language = 'unknown'
            
            boundaries.append({
                'text': word,
                'language': language,
                'script': script,
                'position': i
            })
        
        return boundaries
    
    def _detect_word_script(self, word: str) -> str:
        """
        Detect script of a single word
        
        Args:
            word: Input word
        
        Returns:
            Script name
        """
        for char in word:
            code = ord(char)
            
            # Devanagari
            if 0x0900 <= code <= 0x097F:
                return 'devanagari'
            
            # Tamil
            elif 0x0B80 <= code <= 0x0BFF:
                return 'tamil'
            
            # Telugu
            elif 0x0C00 <= code <= 0x0C7F:
                return 'telugu'
        
        return 'latin'
    
    def _convert_to_primary(
        self,
        text: str,
        boundaries: List[Dict],
        primary_language: str
    ) -> str:
        """
        Convert code-mixed text to primary language
        
        Args:
            text: Input text
            boundaries: Language boundaries
            primary_language: Primary language
        
        Returns:
            Converted text
        """
        # Placeholder - in production, this would use translation
        # For now, just return original
        return text
