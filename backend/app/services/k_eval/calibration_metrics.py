"""
K-Eval - Calibration Metrics
Metrics for evaluating confidence calibration quality
"""

import numpy as np
from typing import Dict, List, Tuple
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


class CalibrationMetrics:
    """
    Compute calibration quality metrics
    """
    
    def __init__(self, num_bins: int = 10):
        """
        Initialize calibration metrics
        
        Args:
            num_bins: Number of bins for ECE calculation
        """
        self.num_bins = num_bins
    
    def compute_ece(
        self,
        confidences: List[float],
        correctness: List[bool]
    ) -> float:
        """
        Compute Expected Calibration Error
        
        Args:
            confidences: Predicted confidence scores
            correctness: Ground truth correctness
        
        Returns:
            ECE value
        """
        confidences = np.array(confidences)
        correctness = np.array(correctness, dtype=float)
        
        bin_boundaries = np.linspace(0, 1, self.num_bins + 1)
        ece = 0.0
        
        for i in range(self.num_bins):
            in_bin = (confidences >= bin_boundaries[i]) & \
                     (confidences < bin_boundaries[i + 1])
            
            if not np.any(in_bin):
                continue
            
            bin_accuracy = np.mean(correctness[in_bin])
            bin_confidence = np.mean(confidences[in_bin])
            bin_size = np.sum(in_bin)
            
            ece += (bin_size / len(confidences)) * abs(bin_accuracy - bin_confidence)
        
        return float(ece)
    
    def compute_mce(
        self,
        confidences: List[float],
        correctness: List[bool]
    ) -> float:
        """
        Compute Maximum Calibration Error
        
        Args:
            confidences: Predicted confidence scores
            correctness: Ground truth correctness
        
        Returns:
            MCE value
        """
        confidences = np.array(confidences)
        correctness = np.array(correctness, dtype=float)
        
        bin_boundaries = np.linspace(0, 1, self.num_bins + 1)
        max_error = 0.0
        
        for i in range(self.num_bins):
            in_bin = (confidences >= bin_boundaries[i]) & \
                     (confidences < bin_boundaries[i + 1])
            
            if not np.any(in_bin):
                continue
            
            bin_accuracy = np.mean(correctness[in_bin])
            bin_confidence = np.mean(confidences[in_bin])
            
            error = abs(bin_accuracy - bin_confidence)
            max_error = max(max_error, error)
        
        return float(max_error)
    
    def compute_brier_score(
        self,
        confidences: List[float],
        correctness: List[bool]
    ) -> float:
        """
        Compute Brier Score
        
        Args:
            confidences: Predicted confidence scores
            correctness: Ground truth correctness
        
        Returns:
            Brier score
        """
        confidences = np.array(confidences)
        correctness = np.array(correctness, dtype=float)
        
        brier = np.mean((confidences - correctness) ** 2)
        
        return float(brier)
    
    def compute_nll(
        self,
        confidences: List[float],
        correctness: List[bool]
    ) -> float:
        """
        Compute Negative Log Likelihood
        
        Args:
            confidences: Predicted confidence scores
            correctness: Ground truth correctness
        
        Returns:
            NLL value
        """
        confidences = np.array(confidences)
        correctness = np.array(correctness, dtype=float)
        
        epsilon = 1e-7
        confidences = np.clip(confidences, epsilon, 1 - epsilon)
        
        nll = -np.mean(
            correctness * np.log(confidences) +
            (1 - correctness) * np.log(1 - confidences)
        )
        
        return float(nll)
    
    def compute_all_metrics(
        self,
        confidences: List[float],
        correctness: List[bool]
    ) -> Dict:
        """
        Compute all calibration metrics
        
        Args:
            confidences: Predicted confidence scores
            correctness: Ground truth correctness
        
        Returns:
            Dict with all metrics
        """
        return {
            'ece': self.compute_ece(confidences, correctness),
            'mce': self.compute_mce(confidences, correctness),
            'brier_score': self.compute_brier_score(confidences, correctness),
            'nll': self.compute_nll(confidences, correctness),
            'num_samples': len(confidences),
            'avg_confidence': float(np.mean(confidences)),
            'avg_accuracy': float(np.mean(correctness))
        }
    
    def generate_reliability_diagram(
        self,
        confidences: List[float],
        correctness: List[bool],
        output_path: str = "reliability_diagram.png"
    ) -> str:
        """
        Generate reliability diagram
        
        Args:
            confidences: Predicted confidence scores
            correctness: Ground truth correctness
            output_path: Path to save diagram
        
        Returns:
            Path to saved diagram
        """
        confidences = np.array(confidences)
        correctness = np.array(correctness, dtype=float)
        
        bin_boundaries = np.linspace(0, 1, self.num_bins + 1)
        bin_centers = []
        bin_accuracies = []
        bin_confidences = []
        bin_counts = []
        
        for i in range(self.num_bins):
            in_bin = (confidences >= bin_boundaries[i]) & \
                     (confidences < bin_boundaries[i + 1])
            
            if not np.any(in_bin):
                continue
            
            bin_centers.append((bin_boundaries[i] + bin_boundaries[i + 1]) / 2)
            bin_accuracies.append(np.mean(correctness[in_bin]))
            bin_confidences.append(np.mean(confidences[in_bin]))
            bin_counts.append(np.sum(in_bin))
        
        # Create plot
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Plot perfect calibration line
        ax.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')
        
        # Plot actual calibration
        ax.scatter(bin_confidences, bin_accuracies, s=np.array(bin_counts) * 10,
                  alpha=0.6, label='Model Calibration')
        
        ax.set_xlabel('Confidence')
        ax.set_ylabel('Accuracy')
        ax.set_title('Reliability Diagram')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        return output_path
