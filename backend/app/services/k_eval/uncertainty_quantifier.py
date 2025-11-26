"""
K-Eval - Uncertainty Quantifier
Decomposes uncertainty into epistemic and aleatoric components
"""

import numpy as np
from typing import Dict, List, Optional


class UncertaintyQuantifier:
    """
    Quantify epistemic and aleatoric uncertainty
    """
    
    def __init__(self):
        """Initialize uncertainty quantifier"""
        pass
    
    def quantify_uncertainty(
        self,
        ensemble_confidences: List[float],
        ensemble_predictions: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Decompose uncertainty into epistemic and aleatoric
        
        Args:
            ensemble_confidences: Confidence scores from ensemble members
            ensemble_predictions: Optional detailed predictions from each member
        
        Returns:
            Dict with uncertainty decomposition
        """
        if not ensemble_confidences:
            return self._get_default_result()
        
        confidences = np.array(ensemble_confidences)
        
        # Epistemic uncertainty (model uncertainty)
        # Measured by disagreement between ensemble members
        epistemic = np.var(confidences)
        
        # Aleatoric uncertainty (data uncertainty)
        # Estimated from average prediction variance
        # For now, use simplified estimation
        aleatoric = self._estimate_aleatoric(confidences)
        
        # Total uncertainty
        total = epistemic + aleatoric
        
        return {
            'epistemic_uncertainty': float(epistemic),
            'aleatoric_uncertainty': float(aleatoric),
            'total_uncertainty': float(total),
            'mean_confidence': float(np.mean(confidences)),
            'std_confidence': float(np.std(confidences)),
            'min_confidence': float(np.min(confidences)),
            'max_confidence': float(np.max(confidences)),
            'confidence_range': float(np.max(confidences) - np.min(confidences))
        }
    
    def _estimate_aleatoric(self, confidences: np.ndarray) -> float:
        """
        Estimate aleatoric uncertainty
        
        For binary classification:
        Aleatoric = p * (1 - p) where p is predicted probability
        
        Args:
            confidences: Ensemble confidences
        
        Returns:
            Estimated aleatoric uncertainty
        """
        mean_conf = np.mean(confidences)
        aleatoric = mean_conf * (1 - mean_conf)
        
        return float(aleatoric)
    
    def detect_ood(
        self,
        epistemic_uncertainty: float,
        epistemic_threshold: float = 0.05
    ) -> bool:
        """
        Detect out-of-distribution samples using epistemic uncertainty
        
        Args:
            epistemic_uncertainty: Epistemic uncertainty value
            epistemic_threshold: Threshold for OOD detection
        
        Returns:
            True if OOD detected
        """
        return epistemic_uncertainty > epistemic_threshold
    
    def compute_uncertainty_score(
        self,
        epistemic: float,
        aleatoric: float,
        epistemic_weight: float = 0.6,
        aleatoric_weight: float = 0.4
    ) -> float:
        """
        Compute weighted uncertainty score
        
        Args:
            epistemic: Epistemic uncertainty
            aleatoric: Aleatoric uncertainty
            epistemic_weight: Weight for epistemic
            aleatoric_weight: Weight for aleatoric
        
        Returns:
            Combined uncertainty score
        """
        uncertainty_score = (
            epistemic_weight * epistemic +
            aleatoric_weight * aleatoric
        )
        
        return float(uncertainty_score)
    
    def _get_default_result(self) -> Dict:
        """Get default result when no data provided"""
        return {
            'epistemic_uncertainty': 0.0,
            'aleatoric_uncertainty': 0.0,
            'total_uncertainty': 0.0,
            'mean_confidence': 0.5,
            'std_confidence': 0.0,
            'min_confidence': 0.5,
            'max_confidence': 0.5,
            'confidence_range': 0.0
        }
