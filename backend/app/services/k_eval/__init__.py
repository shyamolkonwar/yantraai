"""
K-Eval - Main Pipeline
Confidence scoring and review routing with ensemble aggregation
"""

import os
import yaml
import time
from typing import Dict, List, Optional, Any

from .ensemble_aggregator import EnsembleAggregator
from .temperature_scaling import TemperatureScaling
from .selective_classifier import SelectiveClassifier
from .calibration_metrics import CalibrationMetrics
from .uncertainty_quantifier import UncertaintyQuantifier


class KEvalPipeline:
    """
    K-Eval Pipeline
    
    Aggregates confidence scores and routes documents for review
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize K-Eval pipeline
        
        Args:
            config_path: Path to configuration YAML file
        """
        # Load configuration
        if config_path is None:
            config_path = "config/k_eval_config.yaml"
        
        self.config = self._load_config(config_path)
        
        # Initialize components (lazy loading)
        self.ensemble_aggregator = None
        self.temperature_scaling = None
        self.selective_classifier = None
        self.calibration_metrics = None
        self.uncertainty_quantifier = None
        
        self.initialized = False
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                return config
            else:
                print(f"Config file not found: {config_path}, using defaults")
                return self._get_default_config()
        except Exception as e:
            print(f"Failed to load config: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            'ensemble': {
                'aggregation_method': 'variance_weighted',
                'variance_penalty': 0.15
            },
            'calibration': {
                'optimal_temperatures': {
                    'global': 1.0,
                    'medical': 1.0,
                    'logistics': 1.0
                }
            },
            'confidence_scoring': {
                'weights': {
                    'ocr_confidence': 0.40,
                    'lingua_confidence': 0.35,
                    'comply_confidence': 0.25
                }
            },
            'selective_classification': {
                'thresholds': {
                    'auto_accept': 0.90,
                    'light_review': 0.80,
                    'full_review': 0.70,
                    'manual_correction': 0.00
                },
                'domain_overrides': {
                    'medical': {
                        'auto_accept': 0.95,
                        'light_review': 0.85
                    },
                    'logistics': {
                        'auto_accept': 0.85,
                        'light_review': 0.75
                    }
                }
            }
        }
    
    def _initialize_components(self):
        """Initialize all pipeline components"""
        if self.initialized:
            return
        
        print("Initializing K-Eval pipeline...")
        
        # Initialize ensemble aggregator
        ensemble_config = self.config.get('ensemble', {})
        self.ensemble_aggregator = EnsembleAggregator(
            aggregation_method=ensemble_config.get('aggregation_method', 'variance_weighted'),
            variance_penalty=ensemble_config.get('variance_penalty', 0.15)
        )
        
        # Initialize temperature scaling
        calibration_config = self.config.get('calibration', {})
        optimal_temps = calibration_config.get('optimal_temperatures', {})
        self.temperature_scaling = TemperatureScaling(
            optimal_temperature=optimal_temps.get('global', 1.0)
        )
        
        # Initialize selective classifier
        selective_config = self.config.get('selective_classification', {})
        self.selective_classifier = SelectiveClassifier(
            thresholds=selective_config.get('thresholds'),
            domain_overrides=selective_config.get('domain_overrides')
        )
        
        # Initialize calibration metrics
        self.calibration_metrics = CalibrationMetrics(num_bins=10)
        
        # Initialize uncertainty quantifier
        self.uncertainty_quantifier = UncertaintyQuantifier()
        
        self.initialized = True
        print("K-Eval pipeline initialized successfully")
    
    def score_and_route(
        self,
        ocr_confidence: float,
        lingua_confidence: float,
        comply_confidence: float,
        domain: str = "general",
        is_anomalous: bool = False,
        is_ood: bool = False,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Score confidence and route document for review
        
        Args:
            ocr_confidence: K-OCR confidence
            lingua_confidence: K-Lingua confidence
            comply_confidence: K-Comply confidence
            domain: Domain (medical, logistics, general)
            is_anomalous: Whether document is anomalous
            is_ood: Whether document is out-of-distribution
            document_id: Optional document ID for tracking
        
        Returns:
            Dict with final confidence and routing decision
        """
        # Initialize components if needed
        self._initialize_components()
        
        start_time = time.time()
        
        if document_id is None:
            document_id = f"doc_{int(time.time() * 1000)}"
        
        print(f"[{document_id}] Scoring confidence: OCR={ocr_confidence:.3f}, "
              f"Lingua={lingua_confidence:.3f}, Comply={comply_confidence:.3f}")
        
        # Stage 1: Aggregate component confidences
        scoring_config = self.config.get('confidence_scoring', {})
        component_weights = scoring_config.get('weights')
        
        aggregation_result = self.ensemble_aggregator.aggregate_component_confidences(
            ocr_confidence=ocr_confidence,
            lingua_confidence=lingua_confidence,
            comply_confidence=comply_confidence,
            component_weights=component_weights
        )
        
        aggregated_confidence = aggregation_result['aggregated_confidence']
        
        # Stage 2: Apply temperature scaling
        calibration_config = self.config.get('calibration', {})
        optimal_temps = calibration_config.get('optimal_temperatures', {})
        domain_temp = optimal_temps.get(domain, optimal_temps.get('global', 1.0))
        
        calibrated_confidence = self.temperature_scaling.apply_temperature_scaling(
            confidence=aggregated_confidence,
            temperature=domain_temp
        )
        
        # Stage 3: Route based on confidence
        routing_result = self.selective_classifier.classify(
            confidence=calibrated_confidence,
            domain=domain,
            is_anomalous=is_anomalous,
            is_ood=is_ood
        )
        
        # Calculate total processing time
        total_time = (time.time() - start_time) * 1000  # ms
        
        # Compile final result
        result = {
            'document_id': document_id,
            'final_confidence': calibrated_confidence,
            'aggregated_confidence': aggregated_confidence,
            'review_action': routing_result['review_action'],
            'priority': routing_result['priority'],
            'needs_review': routing_result['needs_review'],
            'review_percentage': routing_result.get('review_percentage', 0.0),
            'component_breakdown': aggregation_result['component_breakdown'],
            'component_weights': aggregation_result.get('component_weights', {}),
            'variance': aggregation_result['variance'],
            'disagreement': aggregation_result['disagreement'],
            'temperature_applied': domain_temp,
            'routing_reason': routing_result['reason'],
            'penalties_applied': routing_result.get('penalties_applied', []),
            'domain': domain,
            'metadata': {
                'processing_time_ms': total_time,
                'is_anomalous': is_anomalous,
                'is_ood': is_ood,
                'thresholds_used': routing_result.get('thresholds_used', {})
            }
        }
        
        print(f"[{document_id}] Routed to {result['review_action']} "
              f"(confidence: {result['final_confidence']:.3f})")
        
        return result
    
    def calibrate(
        self,
        confidences: List[float],
        correctness: List[bool],
        domain: str = "global"
    ) -> Dict:
        """
        Calibrate temperature on validation data
        
        Args:
            confidences: Predicted confidence scores
            correctness: Ground truth correctness
            domain: Domain to calibrate for
        
        Returns:
            Dict with calibration results
        """
        self._initialize_components()
        
        # Find optimal temperature
        optimal_temp = self.temperature_scaling.calibrate(
            confidences=confidences,
            correctness=correctness,
            method="ece"
        )
        
        # Evaluate calibration
        calibration_eval = self.temperature_scaling.evaluate_calibration(
            confidences=confidences,
            correctness=correctness,
            temperature=optimal_temp
        )
        
        # Compute all metrics
        metrics = self.calibration_metrics.compute_all_metrics(
            confidences=confidences,
            correctness=correctness
        )
        
        print(f"Calibration for {domain}:")
        print(f"  Optimal Temperature: {optimal_temp:.3f}")
        print(f"  ECE Before: {calibration_eval['ece_before']:.4f}")
        print(f"  ECE After: {calibration_eval['ece_after']:.4f}")
        print(f"  Improvement: {calibration_eval['ece_improvement']:.4f}")
        
        return {
            'domain': domain,
            'optimal_temperature': optimal_temp,
            'calibration_evaluation': calibration_eval,
            'metrics': metrics
        }


# Convenience function
def score_and_route(
    ocr_confidence: float,
    lingua_confidence: float,
    comply_confidence: float,
    config_path: Optional[str] = None,
    domain: str = "general"
) -> Dict[str, Any]:
    """
    Score confidence and route document
    
    Args:
        ocr_confidence: K-OCR confidence
        lingua_confidence: K-Lingua confidence
        comply_confidence: K-Comply confidence
        config_path: Optional path to configuration file
        domain: Domain (medical, logistics, general)
    
    Returns:
        Dict with routing decision
    """
    pipeline = KEvalPipeline(config_path)
    return pipeline.score_and_route(
        ocr_confidence, lingua_confidence, comply_confidence, domain=domain
    )
