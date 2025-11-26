"""
K-Lingua v2.0 - Main Pipeline
Language understanding and normalization with IndicBERT
"""

import os
import yaml
import time
from typing import Dict, List, Optional, Any

from .language_detector import LanguageDetector
from .error_corrector import ErrorCorrector
from .transliterator import Transliterator
from .normalizer import Normalizer
from .code_mixer_handler import CodeMixerHandler
from .consistency_checker import ConsistencyChecker
from .confidence_scorer import ConfidenceScorer


class KLinguaPipeline:
    """
    K-Lingua v2.0 Pipeline
    
    Orchestrates language understanding, error correction, and normalization
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize K-Lingua pipeline
        
        Args:
            config_path: Path to configuration YAML file
        """
        # Load configuration
        if config_path is None:
            config_path = "config/k_lingua_config.yaml"
        
        self.config = self._load_config(config_path)
        
        # Initialize components (lazy loading)
        self.language_detector = None
        self.error_corrector = None
        self.transliterator = None
        self.normalizer = None
        self.code_mixer_handler = None
        self.consistency_checker = None
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
                'indicbert': {
                    'model_name': 'ai4bharat/IndicBERT',
                    'device': 'cpu',
                    'fp16': False
                },
                'transliterator': {
                    'model_name': 'ai4bharat/IndicXlit'
                }
            },
            'language_detection': {
                'method': 'IndicBERT',
                'primary_threshold': 0.60,
                'secondary_threshold': 0.15
            },
            'error_correction': {
                'enabled': True,
                'confidence_threshold': 0.75,
                'mlm_prediction_threshold': 0.85
            },
            'transliteration': {
                'enabled': True,
                'preserve_bilingual': True
            },
            'code_mixing': {
                'enabled': True,
                'preserve_original': True
            },
            'domains': {
                'medical': {'enabled': True},
                'logistics': {'enabled': True}
            },
            'confidence_scoring': {
                'weights': {
                    'ocr_confidence': 0.40,
                    'correction_confidence': 0.25,
                    'dictionary_match': 0.20,
                    'domain_validation': 0.10,
                    'language_coherence': 0.05
                }
            }
        }
    
    def _initialize_components(self):
        """Initialize all pipeline components (lazy loading)"""
        if self.initialized:
            return
        
        print("Initializing K-Lingua v2.0 pipeline...")
        
        # Initialize language detector
        lang_config = self.config.get('language_detection', {})
        indicbert_config = self.config.get('models', {}).get('indicbert', {})
        self.language_detector = LanguageDetector(
            model_name=indicbert_config.get('model_name', 'models/lingua/indicbert'),
            device=indicbert_config.get('device', 'cpu'),
            confidence_threshold=lang_config.get('primary_threshold', 0.60)
        )
        
        # Initialize error corrector
        error_config = self.config.get('error_correction', {})
        self.error_corrector = ErrorCorrector(
            mlm_model_name=indicbert_config.get('model_name', 'models/lingua/indicbert'), # Assuming mlm_model_name defaults to the same as model_name if not specified
            device=indicbert_config.get('device', 'cpu'),
            confidence_threshold=error_config.get('confidence_threshold', 0.75),
            mlm_prediction_threshold=error_config.get('mlm_prediction_threshold', 0.85),
            dictionaries_dir=error_config.get('dictionary_path', 'dictionaries')
        )
        
        # Initialize transliterator
        self.transliterator = Transliterator(
            model_name=self.config.get('models', {}).get('transliterator', {}).get('model_name', 'ai4bharat/IndicXlit'),
            preserve_bilingual=self.config.get('transliteration', {}).get('preserve_bilingual', True)
        )
        
        # Initialize normalizer (will be created per-domain)
        self.normalizer = None
        
        # Initialize code-mixer handler
        code_mix_config = self.config.get('code_mixing', {})
        self.code_mixer_handler = CodeMixerHandler(
            preserve_original=code_mix_config.get('preserve_original', True)
        )
        
        # Initialize consistency checker
        self.consistency_checker = ConsistencyChecker()
        
        # Initialize confidence scorer
        scoring_config = self.config.get('confidence_scoring', {})
        self.confidence_scorer = ConfidenceScorer(
            weights=scoring_config.get('weights')
        )
        
        self.initialized = True
        print("K-Lingua v2.0 pipeline initialized successfully")
    
    def process_text(
        self,
        text: str,
        ocr_confidence: float = 0.80,
        token_confidences: Optional[List[float]] = None,
        domain: str = "medical",
        region_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process text through complete K-Lingua pipeline
        
        Args:
            text: Input text from OCR
            ocr_confidence: OCR confidence score
            token_confidences: Per-token confidence scores
            domain: Domain (medical or logistics)
            region_id: Optional region ID for tracking
        
        Returns:
            Dict with normalized text and metadata
        """
        # Initialize components if needed
        self._initialize_components()
        
        start_time = time.time()
        
        if region_id is None:
            region_id = f"text_{int(time.time() * 1000)}"
        
        print(f"[{region_id}] Processing text: '{text[:50]}...'")
        
        # Stage 1: Language Detection
        lang_result = self.language_detector.detect_language(text)
        
        # Stage 2: Error Correction
        error_config = self.config.get('error_correction', {})
        if error_config.get('enabled', True):
            correction_result = self.error_corrector.correct_errors(
                text=text,
                token_confidences=token_confidences,
                language=lang_result['primary_language']
            )
            corrected_text = correction_result['corrected_text']
            correction_confidence = correction_result['correction_confidence']
        else:
            corrected_text = text
            correction_result = {'corrections': [], 'correction_confidence': 1.0}
            correction_confidence = 1.0
        
        # Stage 3: Transliteration (if code-mixed)
        trans_config = self.config.get('transliteration', {})
        if trans_config.get('enabled', True) and lang_result['is_code_mixed']:
            trans_result = self.transliterator.transliterate(
                text=corrected_text,
                source_script=lang_result['primary_script'],
                target_script='roman',
                language=lang_result['primary_language']
            )
            transliterated_text = trans_result['transliterated_text']
            trans_confidence = trans_result['transliteration_confidence']
        else:
            transliterated_text = corrected_text
            trans_result = {'transliteration_confidence': 1.0}
            trans_confidence = 1.0
        
        # Stage 4: Code-Mixing Handling
        code_mix_config = self.config.get('code_mixing', {})
        if code_mix_config.get('enabled', True):
            code_mix_result = self.code_mixer_handler.handle_code_mixing(
                text=transliterated_text,
                is_code_mixed=lang_result['is_code_mixed'],
                primary_language=lang_result['primary_language'],
                secondary_languages=lang_result['secondary_languages']
            )
            handled_text = code_mix_result['handled_text']
        else:
            handled_text = transliterated_text
            code_mix_result = {'strategy_used': 'disabled'}
        
        # Stage 5: Domain Normalization
        if self.normalizer is None or self.normalizer.domain != domain:
            self.normalizer = Normalizer(domain=domain)
        
        norm_result = self.normalizer.normalize(
            text=handled_text,
            language=lang_result['primary_language']
        )
        normalized_text = norm_result['normalized_text']
        
        # Stage 6: Confidence Scoring
        confidence_result = self.confidence_scorer.calculate_confidence(
            ocr_confidence=ocr_confidence,
            correction_confidence=correction_confidence,
            dictionary_match=norm_result['dict_match_score'],
            domain_validation=0.90,  # Placeholder
            language_coherence=1.0 - (0.2 if lang_result['is_code_mixed'] else 0.0)
        )
        
        # Calculate total processing time
        total_time = (time.time() - start_time) * 1000  # ms
        
        # Compile final result
        result = {
            'region_id': region_id,
            'original_text': text,
            'normalized_text': normalized_text,
            'language': lang_result['primary_language'],
            'language_confidence': lang_result['primary_confidence'],  # Added for compatibility
            'script': lang_result['primary_script'],
            'is_code_mixed': lang_result['is_code_mixed'],
            'corrections_applied': correction_result.get('corrections', []),
            'normalizations_applied': norm_result.get('normalizations_applied', []),
            'confidence_score': confidence_result['confidence_score'],
            'review_action': confidence_result['review_action'],
            'needs_review': confidence_result['needs_review'],
            'metadata': {
                'processing_time_ms': total_time,
                'language_confidence': lang_result['primary_confidence'],
                'correction_confidence': correction_confidence,
                'transliteration_confidence': trans_confidence,
                'dictionary_match': norm_result['dict_match_score'],
                'confidence_components': confidence_result['components']
            }
        }
        
        print(f"[{region_id}] Completed: '{result['normalized_text']}' "
              f"(confidence: {result['confidence_score']:.3f}, action: {result['review_action']})")
        
        return result
    
    def process_batch(
        self,
        texts: List[Dict],
        domain: str = "medical"
    ) -> List[Dict]:
        """
        Process multiple texts and check cross-field consistency
        
        Args:
            texts: List of text dicts with 'text', 'ocr_confidence', etc.
            domain: Domain
        
        Returns:
            List of processed results with consistency checks
        """
        # Process each text individually
        results = []
        for text_data in texts:
            result = self.process_text(
                text=text_data.get('text', ''),
                ocr_confidence=text_data.get('ocr_confidence', 0.80),
                token_confidences=text_data.get('token_confidences'),
                domain=domain,
                region_id=text_data.get('region_id')
            )
            results.append(result)
        
        # Check cross-field consistency
        if len(results) > 1:
            consistency_result = self.consistency_checker.check_consistency(
                fields=[{
                    'text': r['normalized_text'],
                    'field_type': r.get('field_type', 'unknown')
                } for r in results]
            )
            
            # Add consistency info to results
            for result in results:
                result['consistency'] = consistency_result
        
        return results


# Convenience function
def process_text(
    text: str,
    config_path: Optional[str] = None,
    ocr_confidence: float = 0.80,
    domain: str = "medical"
) -> Dict[str, Any]:
    """
    Process text using K-Lingua v2.0 pipeline
    
    Args:
        text: Input text
        config_path: Optional path to configuration file
        ocr_confidence: OCR confidence score
        domain: Domain (medical or logistics)
    
    Returns:
        Dict with processing results
    """
    pipeline = KLinguaPipeline(config_path)
    return pipeline.process_text(text, ocr_confidence=ocr_confidence, domain=domain)
