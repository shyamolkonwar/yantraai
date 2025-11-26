"""
K-OCR v2.0 - Multi-Track OCR Orchestrator
Coordinates model selection, fallback logic, and intelligent routing
"""

import time
from typing import Tuple, Optional, Dict, Any
import numpy as np

from .text_classifier import classify_text_type
from .trocr_engine import TrOCREngine


class MultiTrackOCR:
    """
    Multi-track OCR with intelligent routing and fallback
    """
    
    def __init__(
        self,
        trocr_engine: TrOCREngine,
        confidence_threshold: float = 0.70,
        text_type_detection_threshold: float = 0.75,
        fallback_enabled: bool = True,
        model_priority: str = "printed",
        log_switches: bool = True
    ):
        """
        Initialize multi-track OCR
        
        Args:
            trocr_engine: TrOCR engine instance
            confidence_threshold: Threshold for attempting fallback
            text_type_detection_threshold: Threshold for committing to one model
            fallback_enabled: Enable fallback to alternate model
            model_priority: Which model to try first if uncertain ("printed" or "handwritten")
            log_switches: Log model switch events
        """
        self.trocr_engine = trocr_engine
        self.confidence_threshold = confidence_threshold
        self.text_type_detection_threshold = text_type_detection_threshold
        self.fallback_enabled = fallback_enabled
        self.model_priority = model_priority
        self.log_switches = log_switches
    
    def process_region(
        self,
        image: np.ndarray,
        classifier_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process region with multi-track OCR
        
        Args:
            image: RGB uint8 numpy array
            classifier_config: Text classifier configuration
        
        Returns:
            Dict with OCR results and metadata
        """
        start_time = time.time()
        
        # Stage 1: Text type classification
        if classifier_config is None:
            classifier_config = {}
        
        text_type, type_confidence = classify_text_type(image, **classifier_config)
        
        # Stage 2: Select primary model
        primary_model = self._select_primary_model(text_type, type_confidence)
        
        # Stage 3: Run primary model
        primary_text, primary_conf, primary_tokens = self.trocr_engine.run_inference(
            image,
            model_type=primary_model,
            return_token_confidences=True
        )
        
        # Stage 4: Fallback decision
        switched = False
        fallback_text = None
        fallback_conf = None
        final_model = primary_model
        
        if self.fallback_enabled and primary_conf < self.confidence_threshold:
            # Try alternate model
            alternate_model = "handwritten" if primary_model == "printed" else "printed"
            
            fallback_text, fallback_conf, fallback_tokens = self.trocr_engine.run_inference(
                image,
                model_type=alternate_model,
                return_token_confidences=True
            )
            
            # Compare and select better result
            if fallback_conf > primary_conf:
                final_text = fallback_text
                final_conf = fallback_conf
                final_tokens = fallback_tokens
                final_model = alternate_model
                switched = True
                
                if self.log_switches:
                    print(f"Switched from {primary_model} to {alternate_model} "
                          f"(conf: {fallback_conf:.3f} vs {primary_conf:.3f})")
            else:
                final_text = primary_text
                final_conf = primary_conf
                final_tokens = primary_tokens
        else:
            final_text = primary_text
            final_conf = primary_conf
            final_tokens = primary_tokens
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        
        # Return result
        return {
            'text': final_text,
            'raw_text': primary_text,
            'confidence': final_conf,
            'text_type': text_type,
            'text_type_confidence': type_confidence,
            'model_used': final_model,
            'primary_model': primary_model,
            'switched': switched,
            'primary_confidence': primary_conf,
            'fallback_confidence': fallback_conf if switched else None,
            'tokens': final_tokens,
            'processing_time_ms': processing_time
        }
    
    def _select_primary_model(
        self,
        text_type: str,
        type_confidence: float
    ) -> str:
        """
        Select primary model based on text type classification
        
        Args:
            text_type: Classified text type
            type_confidence: Classification confidence
        
        Returns:
            Model type ("printed" or "handwritten")
        """
        # If classification is confident, use that
        if type_confidence >= self.text_type_detection_threshold:
            if text_type == "printed":
                return "printed"
            elif text_type == "handwritten":
                return "handwritten"
            else:  # mixed
                return self.model_priority
        else:
            # Low confidence classification, use priority model
            return self.model_priority
