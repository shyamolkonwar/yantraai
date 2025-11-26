"""
K-Lingua v2.0 - Confidence Scorer
Comprehensive confidence scoring for language understanding
"""

from typing import Dict, Optional


class ConfidenceScorer:
    """
    5-component confidence scoring system
    """
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None
    ):
        """
        Initialize confidence scorer
        
        Args:
            weights: Component weights
            thresholds: Review routing thresholds
        """
        # Default weights (must sum to 1.0)
        self.weights = weights or {
            'ocr_confidence': 0.40,
            'correction_confidence': 0.25,
            'dictionary_match': 0.20,
            'domain_validation': 0.10,
            'language_coherence': 0.05
        }
        
        # Default thresholds
        self.thresholds = thresholds or {
            'high_confidence': 0.90,
            'good_confidence': 0.80,
            'moderate_confidence': 0.70,
            'low_confidence': 0.00
        }
    
    def calculate_confidence(
        self,
        ocr_confidence: float,
        correction_confidence: float = 1.0,
        dictionary_match: float = 0.85,
        domain_validation: float = 0.90,
        language_coherence: float = 1.0
    ) -> Dict:
        """
        Calculate comprehensive confidence score
        
        Args:
            ocr_confidence: OCR model confidence
            correction_confidence: Error correction confidence
            dictionary_match: Dictionary match score
            domain_validation: Domain validation score
            language_coherence: Language consistency score
        
        Returns:
            Dict with confidence score and review action
        """
        # Calculate weighted score
        confidence_score = (
            ocr_confidence * self.weights['ocr_confidence'] +
            correction_confidence * self.weights['correction_confidence'] +
            dictionary_match * self.weights['dictionary_match'] +
            domain_validation * self.weights['domain_validation'] +
            language_coherence * self.weights['language_coherence']
        )
        
        # Clamp to [0.0, 1.0]
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        # Determine review action
        review_action = self._get_review_action(confidence_score)
        
        return {
            'confidence_score': confidence_score,
            'components': {
                'ocr_confidence': ocr_confidence,
                'correction_confidence': correction_confidence,
                'dictionary_match': dictionary_match,
                'domain_validation': domain_validation,
                'language_coherence': language_coherence
            },
            'review_action': review_action,
            'needs_review': review_action != 'AUTO_ACCEPT'
        }
    
    def _get_review_action(self, confidence_score: float) -> str:
        """
        Determine review action based on confidence score
        
        Args:
            confidence_score: Calculated confidence score
        
        Returns:
            Review action string
        """
        if confidence_score >= self.thresholds['high_confidence']:
            return 'AUTO_ACCEPT'
        elif confidence_score >= self.thresholds['good_confidence']:
            return 'LIGHT_REVIEW'
        elif confidence_score >= self.thresholds['moderate_confidence']:
            return 'FULL_REVIEW'
        else:
            return 'MANUAL_CORRECTION'
