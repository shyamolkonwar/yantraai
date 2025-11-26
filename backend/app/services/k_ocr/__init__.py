"""
K-OCR v2.0 - Main Pipeline
Multi-Track TrOCR with intelligent routing and post-processing
"""

import os
import yaml
import time
import numpy as np
from typing import Dict, Optional, Any

from .text_classifier import classify_text_type
from .trocr_engine import TrOCREngine
from .multi_track_ocr import MultiTrackOCR
from .post_processor import PostProcessor
from .confidence_scorer import ConfidenceScorer


class MultiTrackOCRPipeline:
    """
    K-OCR v2.0 Pipeline
    
    Orchestrates multi-track OCR with TrOCR, post-processing, and confidence scoring
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize K-OCR pipeline
        
        Args:
            config_path: Path to configuration YAML file
        """
        # Load configuration
        if config_path is None:
            config_path = "config/k_ocr_config.yaml"
        
        self.config = self._load_config(config_path)
        
        # Initialize components (lazy loading)
        self.trocr_engine = None
        self.multi_track_ocr = None
        self.post_processor = None
        self.confidence_scorer = None
        
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
            'models': {
                'printed': {
                    'model_name': 'microsoft/trocr-base-printed',
                    'device': 'cpu',
                    'fp16': False
                },
                'handwritten': {
                    'model_name': 'microsoft/trocr-large-handwritten',
                    'device': 'cpu',
                    'fp16': False
                }
            },
            'text_classifier': {
                'method': 'rule_based'
            },
            'multi_track': {
                'confidence_threshold': 0.70,
                'fallback_enabled': True
            },
            'post_processing': {
                'dictionaries': {
                    'enabled': True,
                    'directory': 'dictionaries'
                },
                'domain': {}
            },
            'confidence_scoring': {
                'weights': {
                    'ocr_confidence': 0.50,
                    'language_model_confidence': 0.20,
                    'dictionary_match': 0.15,
                    'pattern_validation': 0.15
                }
            }
        }
    
    def _initialize_components(self):
        """Initialize all pipeline components (lazy loading)"""
        if self.initialized:
            return
        
        print("Initializing K-OCR v2.0 pipeline...")
        
        # Initialize TrOCR engine
        models_config = self.config.get('models', {})
        printed_config = models_config.get('printed', {})
        handwritten_config = models_config.get('handwritten', {})
        
        device = printed_config.get('device', 'cpu')
        fp16 = printed_config.get('fp16', False)
        
        self.trocr_engine = TrOCREngine(device=device, fp16=fp16)
        
        # Load models
        try:
            self.trocr_engine.load_printed_model(
                model_name=printed_config.get('model_name', 'microsoft/trocr-base-printed'),
                model_path=printed_config.get('model_path')
            )
        except Exception as e:
            print(f"Warning: Failed to load printed model: {e}")
        
        try:
            self.trocr_engine.load_handwritten_model(
                model_name=handwritten_config.get('model_name', 'microsoft/trocr-large-handwritten'),
                model_path=handwritten_config.get('model_path')
            )
        except Exception as e:
            print(f"Warning: Failed to load handwritten model: {e}")
        
        # Initialize multi-track OCR
        multi_track_config = self.config.get('multi_track', {})
        self.multi_track_ocr = MultiTrackOCR(
            trocr_engine=self.trocr_engine,
            confidence_threshold=multi_track_config.get('confidence_threshold', 0.70),
            fallback_enabled=multi_track_config.get('fallback_enabled', True),
            log_switches=multi_track_config.get('log_model_switches', True)
        )
        
        # Initialize post-processor
        post_proc_config = self.config.get('post_processing', {})
        dict_config = post_proc_config.get('dictionaries', {})
        
        self.post_processor = PostProcessor(
            dictionaries_dir=dict_config.get('directory', 'dictionaries'),
            domain_corrections=post_proc_config.get('domain', {}),
            hinglish_enabled=post_proc_config.get('hinglish', {}).get('enabled', True)
        )
        
        # Initialize confidence scorer
        scoring_config = self.config.get('confidence_scoring', {})
        self.confidence_scorer = ConfidenceScorer(
            weights=scoring_config.get('weights'),
            thresholds=scoring_config.get('thresholds'),
            penalties=scoring_config.get('penalties')
        )
        
        self.initialized = True
        print("K-OCR v2.0 pipeline initialized successfully")
    
    def process_region(
        self,
        image: np.ndarray,
        field_type: Optional[str] = None,
        region_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process region through complete K-OCR pipeline
        
        Args:
            image: RGB uint8 numpy array
            field_type: Optional field type for pattern validation
            region_id: Optional region ID for tracking
        
        Returns:
            Dict with OCR results and metadata
        """
        # Initialize components if needed
        self._initialize_components()
        
        start_time = time.time()
        
        if region_id is None:
            region_id = f"region_{int(time.time() * 1000)}"
        
        print(f"[{region_id}] Processing region...")
        
        # Stage 1-4: Multi-track OCR (handles text classification internally)
        ocr_result = self.multi_track_ocr.process_region(image)
        
        # Stage 5: Post-processing
        post_proc_result = self.post_processor.process(
            text=ocr_result['text'],
            tokens=ocr_result.get('tokens')
        )
        
        # Stage 6: Confidence scoring
        pattern_score = self.confidence_scorer.validate_pattern(
            post_proc_result['text'],
            field_type=field_type
        )
        
        trust_score_result = self.confidence_scorer.calculate_trust_score(
            ocr_confidence=ocr_result['confidence'],
            lm_confidence=0.0,  # IndicBERT not implemented yet
            dictionary_match=post_proc_result['dictionary_match_score'],
            pattern_validation=pattern_score,
            model_switched=ocr_result['switched'],
            unknown_word_count=0  # TODO: Calculate from dictionary
        )
        
        # Calculate total processing time
        total_time = (time.time() - start_time) * 1000  # ms
        
        # Compile final result
        result = {
            'region_id': region_id,
            'text': post_proc_result['text'],
            'raw_text': ocr_result['raw_text'],
            'confidence': ocr_result['confidence'],
            'trust_score': trust_score_result['trust_score'],
            'text_type': ocr_result['text_type'],
            'model_used': ocr_result['model_used'],
            'switched': ocr_result['switched'],
            'corrections_applied': post_proc_result['corrections_applied'],
            'review_action': trust_score_result['review_action'],
            'needs_review': trust_score_result['needs_review'],
            'metadata': {
                'ocr_time_ms': ocr_result['processing_time_ms'],
                'total_time_ms': total_time,
                'text_type_confidence': ocr_result['text_type_confidence'],
                'primary_confidence': ocr_result['primary_confidence'],
                'fallback_confidence': ocr_result.get('fallback_confidence'),
                'dictionary_match': post_proc_result['dictionary_match_score'],
                'pattern_validation': pattern_score,
                'confidence_components': trust_score_result['components']
            }
        }
        
        print(f"[{region_id}] Completed: '{result['text']}' "
              f"(trust: {result['trust_score']:.3f}, action: {result['review_action']})")
        
        return result


# Convenience function
def process_region(
    image: np.ndarray,
    config_path: Optional[str] = None,
    field_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process region using K-OCR v2.0 pipeline
    
    Args:
        image: RGB uint8 numpy array
        config_path: Optional path to configuration file
        field_type: Optional field type for pattern validation
    
    Returns:
        Dict with OCR results
    """
    pipeline = MultiTrackOCRPipeline(config_path)
    return pipeline.process_region(image, field_type=field_type)
