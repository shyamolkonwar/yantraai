"""
K-Eval - Ensemble Aggregator
Aggregates confidence scores from multiple sources
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


class EnsembleAggregator:
    """
    Aggregates confidence scores using ensemble methods
    """
    
    def __init__(
        self,
        aggregation_method: str = "variance_weighted",
        variance_penalty: float = 0.15
    ):
        """
        Initialize ensemble aggregator
        
        Args:
            aggregation_method: "mean", "median", "variance_weighted"
            variance_penalty: Penalty factor for high variance
        """
        self.aggregation_method = aggregation_method
        self.variance_penalty = variance_penalty
    
    def aggregate_confidences(
        self,
        confidences: List[float],
        weights: Optional[List[float]] = None
    ) -> Dict:
        """
        Aggregate multiple confidence scores
        
        Args:
            confidences: List of confidence scores (0.0-1.0)
            weights: Optional weights for each confidence
        
        Returns:
            Dict with aggregated confidence and metadata
        """
        if not confidences:
            return self._get_default_result()
        
        confidences = np.array(confidences)
        
        # Apply weights if provided
        if weights is not None:
            weights = np.array(weights)
            weights = weights / weights.sum()  # Normalize
        else:
            weights = np.ones(len(confidences)) / len(confidences)
        
        # Calculate aggregated confidence
        if self.aggregation_method == "mean":
            aggregated = self._aggregate_mean(confidences, weights)
        elif self.aggregation_method == "median":
            aggregated = self._aggregate_median(confidences)
        elif self.aggregation_method == "variance_weighted":
            aggregated = self._aggregate_variance_weighted(confidences, weights)
        else:
            aggregated = self._aggregate_mean(confidences, weights)
        
        # Calculate variance and uncertainty
        variance = np.var(confidences)
        std_dev = np.std(confidences)
        
        return {
            'aggregated_confidence': float(aggregated),
            'variance': float(variance),
            'std_dev': float(std_dev),
            'min_confidence': float(np.min(confidences)),
            'max_confidence': float(np.max(confidences)),
            'num_sources': len(confidences),
            'disagreement': float(std_dev)  # High std = high disagreement
        }
    
    def _aggregate_mean(
        self,
        confidences: np.ndarray,
        weights: np.ndarray
    ) -> float:
        """Weighted mean aggregation"""
        return float(np.average(confidences, weights=weights))
    
    def _aggregate_median(self, confidences: np.ndarray) -> float:
        """Median aggregation (robust to outliers)"""
        return float(np.median(confidences))
    
    def _aggregate_variance_weighted(
        self,
        confidences: np.ndarray,
        weights: np.ndarray
    ) -> float:
        """
        Variance-weighted aggregation
        High variance → Lower final confidence
        """
        mean_conf = np.average(confidences, weights=weights)
        variance = np.var(confidences)
        std_dev = np.sqrt(variance)
        
        # Penalize high variance (uncertainty)
        penalized_conf = mean_conf - (self.variance_penalty * std_dev)
        
        # Clamp to [0.0, 1.0]
        return float(max(0.0, min(1.0, penalized_conf)))
    
    def aggregate_component_confidences(
        self,
        ocr_confidence: float,
        lingua_confidence: float,
        comply_confidence: float,
        component_weights: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Aggregate confidence from K-OCR, K-Lingua, K-Comply
        
        Args:
            ocr_confidence: K-OCR confidence
            lingua_confidence: K-Lingua confidence
            comply_confidence: K-Comply confidence
            component_weights: Optional custom weights
        
        Returns:
            Dict with aggregated confidence
        """
        # Default weights
        if component_weights is None:
            component_weights = {
                'ocr': 0.40,
                'lingua': 0.35,
                'comply': 0.25
            }
        
        confidences = [ocr_confidence, lingua_confidence, comply_confidence]
        weights = [
            component_weights['ocr'],
            component_weights['lingua'],
            component_weights['comply']
        ]
        
        result = self.aggregate_confidences(confidences, weights)
        
        # Add component breakdown
        result['component_breakdown'] = {
            'ocr_confidence': ocr_confidence,
            'lingua_confidence': lingua_confidence,
            'comply_confidence': comply_confidence
        }
        result['component_weights'] = component_weights
        
        return result
    
    def _get_default_result(self) -> Dict:
        """Get default result when no confidences provided"""
        return {
            'aggregated_confidence': 0.5,
            'variance': 0.0,
            'std_dev': 0.0,
            'min_confidence': 0.5,
            'max_confidence': 0.5,
            'num_sources': 0,
            'disagreement': 0.0
        }
