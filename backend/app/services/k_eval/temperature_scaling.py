"""
K-Eval - Temperature Scaling
Post-hoc calibration using temperature scaling
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.optimize import minimize_scalar


class TemperatureScaling:
    """
    Temperature scaling for confidence calibration
    """
    
    def __init__(
        self,
        optimal_temperature: float = 1.0,
        search_range: Tuple[float, float] = (0.5, 5.0)
    ):
        """
        Initialize temperature scaling
        
        Args:
            optimal_temperature: Pre-computed optimal T (default 1.0 = no scaling)
            search_range: Range for T search during calibration
        """
        self.optimal_temperature = optimal_temperature
        self.search_range = search_range
    
    def calibrate(
        self,
        confidences: List[float],
        correctness: List[bool],
        method: str = "ece"
    ) -> float:
        """
        Find optimal temperature T on validation data
        
        Args:
            confidences: Predicted confidence scores
            correctness: Whether predictions were correct
            method: "ece" (minimize ECE) or "nll" (minimize NLL)
        
        Returns:
            Optimal temperature T
        """
        confidences = np.array(confidences)
        correctness = np.array(correctness, dtype=float)
        
        if method == "ece":
            # Minimize Expected Calibration Error
            result = minimize_scalar(
                lambda t: self._compute_ece(confidences, correctness, t),
                bounds=self.search_range,
                method='bounded'
            )
        elif method == "nll":
            # Minimize Negative Log Likelihood
            result = minimize_scalar(
                lambda t: self._compute_nll(confidences, correctness, t),
                bounds=self.search_range,
                method='bounded'
            )
        else:
            raise ValueError(f"Unknown calibration method: {method}")
        
        self.optimal_temperature = result.x
        
        return self.optimal_temperature
    
    def apply_temperature_scaling(
        self,
        confidence: float,
        temperature: Optional[float] = None
    ) -> float:
        """
        Apply temperature scaling to confidence score
        
        Args:
            confidence: Original confidence (0.0-1.0)
            temperature: Temperature T (uses optimal_temperature if None)
        
        Returns:
            Calibrated confidence
        """
        if temperature is None:
            temperature = self.optimal_temperature
        
        # Convert confidence to logit
        # confidence = sigmoid(logit)
        # logit = log(confidence / (1 - confidence))
        
        # Avoid division by zero
        confidence = max(1e-7, min(1 - 1e-7, confidence))
        
        logit = np.log(confidence / (1 - confidence))
        
        # Scale logit by temperature
        scaled_logit = logit / temperature
        
        # Convert back to probability
        calibrated_confidence = 1 / (1 + np.exp(-scaled_logit))
        
        return float(calibrated_confidence)
    
    def _compute_ece(
        self,
        confidences: np.ndarray,
        correctness: np.ndarray,
        temperature: float,
        num_bins: int = 10
    ) -> float:
        """
        Compute Expected Calibration Error
        
        Args:
            confidences: Predicted confidences
            correctness: Ground truth correctness
            temperature: Temperature for scaling
            num_bins: Number of bins for ECE
        
        Returns:
            ECE value
        """
        # Apply temperature scaling
        scaled_confidences = np.array([
            self.apply_temperature_scaling(c, temperature)
            for c in confidences
        ])
        
        # Bin predictions by confidence
        bin_boundaries = np.linspace(0, 1, num_bins + 1)
        ece = 0.0
        
        for i in range(num_bins):
            # Find samples in this bin
            in_bin = (scaled_confidences >= bin_boundaries[i]) & \
                     (scaled_confidences < bin_boundaries[i + 1])
            
            if not np.any(in_bin):
                continue
            
            # Compute accuracy and confidence in bin
            bin_accuracy = np.mean(correctness[in_bin])
            bin_confidence = np.mean(scaled_confidences[in_bin])
            bin_size = np.sum(in_bin)
            
            # Add weighted contribution to ECE
            ece += (bin_size / len(confidences)) * abs(bin_accuracy - bin_confidence)
        
        return ece
    
    def _compute_nll(
        self,
        confidences: np.ndarray,
        correctness: np.ndarray,
        temperature: float
    ) -> float:
        """
        Compute Negative Log Likelihood
        
        Args:
            confidences: Predicted confidences
            correctness: Ground truth correctness
            temperature: Temperature for scaling
        
        Returns:
            NLL value
        """
        # Apply temperature scaling
        scaled_confidences = np.array([
            self.apply_temperature_scaling(c, temperature)
            for c in confidences
        ])
        
        # Compute NLL
        # NLL = -Σ [y * log(p) + (1-y) * log(1-p)]
        epsilon = 1e-7
        scaled_confidences = np.clip(scaled_confidences, epsilon, 1 - epsilon)
        
        nll = -np.mean(
            correctness * np.log(scaled_confidences) +
            (1 - correctness) * np.log(1 - scaled_confidences)
        )
        
        return nll
    
    def evaluate_calibration(
        self,
        confidences: List[float],
        correctness: List[bool],
        temperature: Optional[float] = None
    ) -> Dict:
        """
        Evaluate calibration quality
        
        Args:
            confidences: Predicted confidences
            correctness: Ground truth correctness
            temperature: Temperature (uses optimal if None)
        
        Returns:
            Dict with calibration metrics
        """
        if temperature is None:
            temperature = self.optimal_temperature
        
        confidences = np.array(confidences)
        correctness = np.array(correctness, dtype=float)
        
        # Compute metrics before and after scaling
        ece_before = self._compute_ece(confidences, correctness, 1.0)
        ece_after = self._compute_ece(confidences, correctness, temperature)
        
        nll_before = self._compute_nll(confidences, correctness, 1.0)
        nll_after = self._compute_nll(confidences, correctness, temperature)
        
        return {
            'temperature': temperature,
            'ece_before': float(ece_before),
            'ece_after': float(ece_after),
            'ece_improvement': float(ece_before - ece_after),
            'nll_before': float(nll_before),
            'nll_after': float(nll_after),
            'nll_improvement': float(nll_before - nll_after)
        }
