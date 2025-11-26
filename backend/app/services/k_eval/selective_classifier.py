"""
K-Eval - Selective Classifier
Routes documents based on confidence with reject option
"""

from typing import Dict, Optional


class SelectiveClassifier:
    """
    Selective classification with 4-tier routing
    """
    
    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        domain_overrides: Optional[Dict[str, Dict[str, float]]] = None
    ):
        """
        Initialize selective classifier
        
        Args:
            thresholds: Confidence thresholds for routing
            domain_overrides: Domain-specific threshold adjustments
        """
        # Default thresholds
        self.thresholds = thresholds or {
            'auto_accept': 0.90,
            'light_review': 0.80,
            'full_review': 0.70,
            'manual_correction': 0.00
        }
        
        # Domain-specific overrides
        self.domain_overrides = domain_overrides or {
            'medical': {
                'auto_accept': 0.95,  # Stricter for medical
                'light_review': 0.85
            },
            'logistics': {
                'auto_accept': 0.85,  # More lenient for logistics
                'light_review': 0.75
            }
        }
    
    def classify(
        self,
        confidence: float,
        domain: str = "general",
        is_anomalous: bool = False,
        is_ood: bool = False
    ) -> Dict:
        """
        Route document based on confidence
        
        Args:
            confidence: Final confidence score (0.0-1.0)
            domain: Domain (medical, logistics, general)
            is_anomalous: Whether document flagged as anomalous
            is_ood: Whether document is out-of-distribution
        
        Returns:
            Dict with routing decision
        """
        # Apply domain-specific thresholds
        thresholds = self._get_domain_thresholds(domain)
        
        # Apply penalties for anomalies and OOD
        adjusted_confidence = confidence
        penalties_applied = []
        
        if is_anomalous:
            # Route anomalies to full review regardless of confidence
            return {
                'review_action': 'FULL_REVIEW',
                'confidence': confidence,
                'adjusted_confidence': confidence,
                'priority': 'HIGH',
                'needs_review': True,
                'reason': 'Document flagged as anomalous',
                'penalties_applied': ['anomaly_detected']
            }
        
        if is_ood:
            # Penalize OOD samples
            adjusted_confidence -= 0.15
            penalties_applied.append('ood_detected')
        
        # Clamp adjusted confidence
        adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))
        
        # Determine routing tier
        if adjusted_confidence >= thresholds['auto_accept']:
            review_action = 'AUTO_ACCEPT'
            priority = 'NONE'
            needs_review = False
            review_percentage = 0.0
            reason = f"High confidence ({adjusted_confidence:.3f} >= {thresholds['auto_accept']:.2f})"
        
        elif adjusted_confidence >= thresholds['light_review']:
            review_action = 'LIGHT_REVIEW'
            priority = 'LOW'
            needs_review = True
            review_percentage = 10.0  # Spot check 10%
            reason = f"Good confidence ({adjusted_confidence:.3f} >= {thresholds['light_review']:.2f})"
        
        elif adjusted_confidence >= thresholds['full_review']:
            review_action = 'FULL_REVIEW'
            priority = 'HIGH'
            needs_review = True
            review_percentage = 100.0
            reason = f"Moderate confidence ({adjusted_confidence:.3f} >= {thresholds['full_review']:.2f})"
        
        else:
            review_action = 'MANUAL_CORRECTION'
            priority = 'CRITICAL'
            needs_review = True
            review_percentage = 100.0
            reason = f"Low confidence ({adjusted_confidence:.3f} < {thresholds['full_review']:.2f})"
        
        return {
            'review_action': review_action,
            'confidence': confidence,
            'adjusted_confidence': adjusted_confidence,
            'priority': priority,
            'needs_review': needs_review,
            'review_percentage': review_percentage,
            'reason': reason,
            'penalties_applied': penalties_applied,
            'thresholds_used': thresholds,
            'domain': domain
        }
    
    def _get_domain_thresholds(self, domain: str) -> Dict[str, float]:
        """
        Get thresholds for specific domain
        
        Args:
            domain: Domain name
        
        Returns:
            Dict of thresholds
        """
        # Start with default thresholds
        thresholds = self.thresholds.copy()
        
        # Apply domain overrides if available
        if domain in self.domain_overrides:
            thresholds.update(self.domain_overrides[domain])
        
        return thresholds
    
    def compute_risk_coverage(
        self,
        confidences: list,
        correctness: list,
        threshold: float
    ) -> Dict:
        """
        Compute risk-coverage tradeoff at given threshold
        
        Args:
            confidences: List of confidence scores
            correctness: List of ground truth correctness
            threshold: Confidence threshold
        
        Returns:
            Dict with risk and coverage metrics
        """
        # Coverage: % of samples accepted
        accepted = [c >= threshold for c in confidences]
        coverage = sum(accepted) / len(confidences) if confidences else 0.0
        
        # Risk: % of accepted samples that are wrong
        if sum(accepted) > 0:
            accepted_correctness = [
                correctness[i] for i in range(len(confidences))
                if accepted[i]
            ]
            risk = 1.0 - (sum(accepted_correctness) / len(accepted_correctness))
        else:
            risk = 0.0
        
        return {
            'threshold': threshold,
            'coverage': coverage,
            'risk': risk,
            'num_accepted': sum(accepted),
            'num_rejected': len(confidences) - sum(accepted)
        }
