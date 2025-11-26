"""
K-OCR v2.0 - Post-Processor
Handles error correction, Hinglish normalization, and domain-specific corrections
"""

import os
import re
from typing import Dict, List, Optional, Set, Tuple


class PostProcessor:
    """
    Post-processing for OCR output
    """
    
    def __init__(
        self,
        dictionaries_dir: str = "dictionaries",
        domain_corrections: Optional[Dict] = None,
        hinglish_enabled: bool = True
    ):
        """
        Initialize post-processor
        
        Args:
            dictionaries_dir: Directory containing dictionary files
            domain_corrections: Domain-specific correction mappings
            hinglish_enabled: Enable Hinglish normalization
        """
        self.dictionaries_dir = dictionaries_dir
        self.domain_corrections = domain_corrections or {}
        self.hinglish_enabled = hinglish_enabled
        
        # Load dictionaries
        self.dictionaries = self._load_dictionaries()
    
    def _load_dictionaries(self) -> Dict[str, Set[str]]:
        """Load all dictionary files"""
        dictionaries = {}
        
        dict_files = {
            'medical_en': 'medical_terms_en.txt',
            'medical_hi': 'medical_terms_hi.txt',
            'medical_hinglish': 'medical_terms_hinglish.txt',
            'logistics_en': 'logistics_terms_en.txt',
            'hinglish_common': 'common_hinglish_words.txt'
        }
        
        for dict_name, filename in dict_files.items():
            filepath = os.path.join(self.dictionaries_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        words = set(line.strip().lower() for line in f if line.strip())
                    dictionaries[dict_name] = words
                    print(f"Loaded {len(words)} words from {dict_name}")
                except Exception as e:
                    print(f"Failed to load {dict_name}: {e}")
                    dictionaries[dict_name] = set()
            else:
                dictionaries[dict_name] = set()
        
        return dictionaries
    
    def process(
        self,
        text: str,
        tokens: Optional[List[Dict]] = None,
        confidence_threshold: float = 0.75
    ) -> Dict:
        """
        Apply post-processing to OCR text
        
        Args:
            text: Raw OCR text
            tokens: Per-token confidences (optional)
            confidence_threshold: Threshold for low-confidence tokens
        
        Returns:
            Dict with corrected text and metadata
        """
        corrections_applied = []
        
        # Stage 1: Basic cleanup
        cleaned_text = self._basic_cleanup(text)
        if cleaned_text != text:
            corrections_applied.append("basic_cleanup")
        
        # Stage 2: Domain-specific corrections
        corrected_text, domain_corrections = self._apply_domain_corrections(cleaned_text)
        if domain_corrections:
            corrections_applied.extend(domain_corrections)
        
        # Stage 3: Hinglish normalization (preserve bilingual)
        if self.hinglish_enabled:
            normalized_text = self._normalize_hinglish(corrected_text)
            if normalized_text != corrected_text:
                corrections_applied.append("hinglish_normalization")
                corrected_text = normalized_text
        
        # Stage 4: Dictionary validation
        dict_match_score = self._calculate_dictionary_match(corrected_text)
        
        return {
            'text': corrected_text,
            'raw_text': text,
            'corrections_applied': corrections_applied,
            'dictionary_match_score': dict_match_score,
            'correction_count': len(corrections_applied)
        }
    
    def _basic_cleanup(self, text: str) -> str:
        """
        Basic text cleanup
        
        Args:
            text: Input text
        
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Fix common OCR errors
        # 0 vs O, 1 vs l, etc. (context-dependent, simplified here)
        
        return text
    
    def _apply_domain_corrections(self, text: str) -> Tuple[str, List[str]]:
        """
        Apply domain-specific corrections
        
        Args:
            text: Input text
        
        Returns:
            Tuple of (corrected_text, corrections_applied)
        """
        corrected = text
        corrections = []
        
        # Medical abbreviations
        medical_abbrev = self.domain_corrections.get('medical', {}).get('abbreviations', {})
        for abbrev, expansion in medical_abbrev.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, corrected, re.IGNORECASE):
                corrected = re.sub(pattern, expansion, corrected, flags=re.IGNORECASE)
                corrections.append(f"medical_abbrev_{abbrev}")
        
        # Logistics abbreviations
        logistics_abbrev = self.domain_corrections.get('logistics', {}).get('abbreviations', {})
        for abbrev, expansion in logistics_abbrev.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, corrected, re.IGNORECASE):
                corrected = re.sub(pattern, expansion, corrected, flags=re.IGNORECASE)
                corrections.append(f"logistics_abbrev_{abbrev}")
        
        return corrected, corrections
    
    def _normalize_hinglish(self, text: str) -> str:
        """
        Normalize Hinglish text (preserve bilingual)
        
        Args:
            text: Input text
        
        Returns:
            Normalized text
        """
        # Preserve as-is (no transliteration)
        # Just basic normalization
        normalized = text
        
        # Standardize common Hinglish patterns
        # (Add specific patterns as needed)
        
        return normalized
    
    def _calculate_dictionary_match(self, text: str) -> float:
        """
        Calculate percentage of words in dictionaries
        
        Args:
            text: Input text
        
        Returns:
            Dictionary match score (0.0-1.0)
        """
        words = text.lower().split()
        if not words:
            return 0.0
        
        # Combine all dictionaries
        all_words = set()
        for dict_words in self.dictionaries.values():
            all_words.update(dict_words)
        
        # Count matches
        matched = sum(1 for word in words if word in all_words)
        
        return matched / len(words)
