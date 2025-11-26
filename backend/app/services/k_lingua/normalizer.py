"""
K-Lingua v2.0 - Normalizer
Domain-specific normalization for medical and logistics
"""

import os
import json
import re
from typing import Dict, List, Optional


class Normalizer:
    """
    Domain-specific text normalization
    """
    
    def __init__(
        self,
        dictionaries_dir: str = "dictionaries",
        domain: str = "medical"
    ):
        """
        Initialize normalizer
        
        Args:
            dictionaries_dir: Path to dictionaries
            domain: Domain (medical or logistics)
        """
        self.dictionaries_dir = dictionaries_dir
        self.domain = domain
        
        # Load abbreviations
        self.abbreviations = self._load_abbreviations()
    
    def _load_abbreviations(self) -> Dict[str, str]:
        """Load domain-specific abbreviations"""
        abbreviations = {}
        
        # Medical abbreviations
        if self.domain == "medical":
            abbreviations.update({
                'BD': 'twice daily',
                'OD': 'once daily',
                'TDS': 'three times daily',
                'QID': 'four times daily',
                'AC': 'before meals',
                'PC': 'after meals',
                'HS': 'at bedtime',
                'PRN': 'as needed',
                'Tab': 'tablet',
                'Cap': 'capsule',
                'Syr': 'syrup',
                'Inj': 'injection',
                'mg': 'milligrams',
                'ml': 'milliliters',
                'gm': 'grams',
                'mcg': 'micrograms',
            })
        
        # Logistics abbreviations
        elif self.domain == "logistics":
            abbreviations.update({
                'PTR': 'parcel tracking reference',
                'AWB': 'airway bill',
                'POD': 'proof of delivery',
                'Qty': 'quantity',
                'Wt': 'weight',
                'Pkg': 'package',
            })
        
        return abbreviations
    
    def normalize(
        self,
        text: str,
        language: str = "en"
    ) -> Dict:
        """
        Apply domain-specific normalization
        
        Args:
            text: Input text
            language: Language code
        
        Returns:
            Dict with normalized text and metadata
        """
        if not text or len(text.strip()) == 0:
            return {
                'normalized_text': text,
                'normalizations_applied': [],
                'domain_validation': {},
                'dict_match_score': 0.0
            }
        
        normalized_text = text
        normalizations = []
        
        # Stage 1: Expand abbreviations
        normalized_text, abbrev_normalizations = self._expand_abbreviations(normalized_text)
        normalizations.extend(abbrev_normalizations)
        
        # Stage 2: Format standardization
        normalized_text, format_normalizations = self._standardize_format(normalized_text)
        normalizations.extend(format_normalizations)
        
        # Stage 3: Domain validation
        validation = self._validate_domain(normalized_text)
        
        # Stage 4: Calculate dictionary match score
        dict_score = self._calculate_dict_match(normalized_text)
        
        return {
            'normalized_text': normalized_text,
            'normalizations_applied': normalizations,
            'domain_validation': validation,
            'dict_match_score': dict_score
        }
    
    def _expand_abbreviations(self, text: str) -> tuple:
        """
        Expand domain-specific abbreviations
        
        Args:
            text: Input text
        
        Returns:
            Tuple of (normalized_text, normalizations_list)
        """
        normalized = text
        normalizations = []
        
        for abbrev, expansion in self.abbreviations.items():
            # Case-insensitive pattern with word boundaries
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            
            if re.search(pattern, normalized, re.IGNORECASE):
                normalized = re.sub(pattern, expansion, normalized, flags=re.IGNORECASE)
                normalizations.append({
                    'type': 'abbreviation_expansion',
                    'from': abbrev,
                    'to': expansion
                })
        
        return normalized, normalizations
    
    def _standardize_format(self, text: str) -> tuple:
        """
        Standardize text formatting
        
        Args:
            text: Input text
        
        Returns:
            Tuple of (normalized_text, normalizations_list)
        """
        normalized = text
        normalizations = []
        
        # Remove extra whitespace
        if re.search(r'\s{2,}', normalized):
            normalized = re.sub(r'\s+', ' ', normalized)
            normalizations.append({
                'type': 'whitespace_normalization',
                'from': 'multiple spaces',
                'to': 'single space'
            })
        
        # Standardize punctuation spacing
        normalized = re.sub(r'\s+([.,;:!?])', r'\1', normalized)
        normalized = re.sub(r'([.,;:!?])([^\s])', r'\1 \2', normalized)
        
        # Trim
        normalized = normalized.strip()
        
        return normalized, normalizations
    
    def _validate_domain(self, text: str) -> Dict:
        """
        Validate text against domain rules
        
        Args:
            text: Input text
        
        Returns:
            Validation results
        """
        validation = {}
        
        if self.domain == "medical":
            # Check for valid dosage format
            dosage_pattern = r'\d+\s*(milligrams?|mg|tablets?|capsules?)'
            validation['has_dosage'] = bool(re.search(dosage_pattern, text, re.IGNORECASE))
            
            # Check for frequency
            frequency_pattern = r'(once|twice|three times|four times)\s+daily'
            validation['has_frequency'] = bool(re.search(frequency_pattern, text, re.IGNORECASE))
            
            validation['valid_medication'] = True  # Placeholder
            validation['safe_dosage'] = True  # Placeholder
        
        elif self.domain == "logistics":
            # Check for tracking code format
            tracking_pattern = r'[A-Z0-9]{10,}'
            validation['has_tracking_code'] = bool(re.search(tracking_pattern, text))
            
            # Check for pincode
            pincode_pattern = r'\b\d{6}\b'
            validation['has_pincode'] = bool(re.search(pincode_pattern, text))
        
        return validation
    
    def _calculate_dict_match(self, text: str) -> float:
        """
        Calculate percentage of words in domain dictionaries
        
        Args:
            text: Input text
        
        Returns:
            Dictionary match score (0.0-1.0)
        """
        words = text.lower().split()
        if not words:
            return 0.0
        
        # For now, return a placeholder score
        # In production, this would check against actual dictionaries
        return 0.85
