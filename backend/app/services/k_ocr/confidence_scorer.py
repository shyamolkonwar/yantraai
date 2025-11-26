"""
K-OCR v2.0 - Confidence Scorer
Calculates comprehensive trust scores for OCR results
"""

import re
from typing import Dict, Optional


class ConfidenceScorer:
    """
    Comprehensive confidence scoring system
    """
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None,
        penalties: Optional[Dict[str, float]] = None
    ):
        """
        Initialize confidence scorer
        
        Args:
            weights: Component weights
            thresholds: Review routing thresholds
            penalties: Penalty values
        """
        # Default weights (must sum to 1.0)
        self.weights = weights or {
            'ocr_confidence': 0.50,
            'language_model_confidence': 0.20,
            'dictionary_match': 0.15,
            'pattern_validation': 0.15
        }
        
        # Default thresholds
        self.thresholds = thresholds or {
            'high_confidence': 0.85,
            'good_confidence': 0.75,
            'moderate_confidence': 0.60,
            'low_confidence': 0.00
        }
        
        # Default penalties
        self.penalties = penalties or {
            'model_switch_penalty': 0.10,
            'unknown_word_penalty': 0.05,
            'pattern_mismatch_penalty': 0.10
        }
    
    def calculate_trust_score(
        self,
        ocr_confidence: float,
        lm_confidence: float = 0.0,
        dictionary_match: float = 0.0,
        pattern_validation: float = 0.7,
        model_switched: bool = False,
        unknown_word_count: int = 0,
        pattern_matched: bool = True
    ) -> Dict:
        """
        Calculate comprehensive trust score
        
        Args:
            ocr_confidence: OCR model confidence (0.0-1.0)
            lm_confidence: Language model confidence (0.0-1.0)
            dictionary_match: Dictionary match score (0.0-1.0)
            pattern_validation: Pattern validation score (0.0-1.0)
            model_switched: Whether fallback model was used
            unknown_word_count: Number of unknown words
            pattern_matched: Whether pattern validation passed
        
        Returns:
            Dict with trust score and components
        """
        # Calculate weighted score
        trust_score = (
            ocr_confidence * self.weights['ocr_confidence'] +
            lm_confidence * self.weights['language_model_confidence'] +
            dictionary_match * self.weights['dictionary_match'] +
            pattern_validation * self.weights['pattern_validation']
        )
        
        # Apply penalties
        penalties_applied = []
        
        if model_switched:
            trust_score -= self.penalties['model_switch_penalty']
            penalties_applied.append('model_switch')
        
        if unknown_word_count > 0:
            penalty = min(unknown_word_count * self.penalties['unknown_word_penalty'], 0.20)
            trust_score -= penalty
            penalties_applied.append(f'unknown_words_{unknown_word_count}')
        
        if not pattern_matched:
            trust_score -= self.penalties['pattern_mismatch_penalty']
            penalties_applied.append('pattern_mismatch')
        
        # Clamp to [0.0, 1.0]
        trust_score = max(0.0, min(1.0, trust_score))
        
        # Determine review action
        review_action = self._get_review_action(trust_score)
        
        return {
            'trust_score': trust_score,
            'components': {
                'ocr_confidence': ocr_confidence,
                'lm_confidence': lm_confidence,
                'dictionary_match': dictionary_match,
                'pattern_validation': pattern_validation
            },
            'penalties_applied': penalties_applied,
            'review_action': review_action,
            'needs_review': review_action != 'auto_accept'
        }
    
    def _get_review_action(self, trust_score: float) -> str:
        """
        Determine review action based on trust score
        
        Args:
            trust_score: Calculated trust score
        
        Returns:
            Review action string
        """
        if trust_score >= self.thresholds['high_confidence']:
            return 'auto_accept'
        elif trust_score >= self.thresholds['good_confidence']:
            return 'light_review'
        elif trust_score >= self.thresholds['moderate_confidence']:
            return 'full_review'
        else:
            return 'manual_correction'
    
    def validate_pattern(
        self,
        text: str,
        field_type: Optional[str] = None
    ) -> float:
        """
        Validate text against expected pattern for field type
        
        Args:
            text: Text to validate
            field_type: Field type (date, phone, amount, etc.)
        
        Returns:
            Pattern validation score (0.0-1.0)
        """
        if not field_type:
            return 0.7  # Default score for generic text
        
        field_type = field_type.lower()
        
        # Date field
        if field_type == 'date':
            # Check for date patterns
            date_patterns = [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # DD/MM/YYYY or DD-MM-YYYY
                r'\d{2,4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD
                r'\d{1,2}\s+[A-Za-z]+\s+\d{2,4}'   # DD Month YYYY
            ]
            for pattern in date_patterns:
                if re.search(pattern, text):
                    return 1.0
            return 0.3
        
        # Phone field
        elif field_type == 'phone':
            # Check for phone number pattern
            if re.search(r'\d{10}', text.replace(' ', '').replace('-', '')):
                return 1.0
            return 0.2
        
        # Amount field
        elif field_type == 'amount':
            # Check for numeric pattern
            if re.search(r'^\d+(\.\d+)?$', text.strip()):
                return 1.0
            # Allow currency symbols
            if re.search(r'[₹$€£]\s*\d+', text):
                return 0.9
            return 0.4
        
        # Name field
        elif field_type == 'name':
            # Should not contain digits
            if not re.search(r'\d', text):
                return 1.0
            return 0.5
        
        # Address field
        elif field_type == 'address':
            # Check for common address keywords
            address_keywords = ['street', 'road', 'avenue', 'lane', 'nagar', 'colony', 'sector']
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in address_keywords):
                return 1.0
            return 0.5
        
        # Generic text
        else:
            return 0.7
