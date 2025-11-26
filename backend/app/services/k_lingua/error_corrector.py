"""
K-Lingua v2.0 - Error Corrector
Context-aware error correction using IndicBERT MLM
"""

import re
from typing import Dict, List, Optional, Tuple


class ErrorCorrector:
    """
    Error correction using Masked Language Modeling
    """
    
    def __init__(
        self,
        mlm_model_name: str = "models/lingua/indicbert_mlm",
        device: str = "cpu",
        confidence_threshold: float = 0.75,
        mlm_prediction_threshold: float = 0.85,
        dictionaries_dir: str = "dictionaries"
    ):
        """
        Initialize error corrector
        
        Args:
            mlm_model_name: IndicBERT MLM model name
            device: Device to run on
            confidence_threshold: OCR confidence below this triggers correction
            mlm_prediction_threshold: IndicBERT confidence to accept prediction
            dictionaries_dir: Path to dictionary files
        """
        self.model_name = mlm_model_name
        self.device = device
        self.confidence_threshold = confidence_threshold
        self.mlm_prediction_threshold = mlm_prediction_threshold
        self.dictionaries_dir = dictionaries_dir
        
        # Model will be loaded lazily
        self.model = None
        self.tokenizer = None
        self.fill_mask_pipeline = None
        
        # Load dictionaries
        self.dictionaries = {}
    
    def _load_model(self):
        """Load IndicBERT model for MLM"""
        if self.model is not None:
            return
        
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForMaskedLM
            
            print(f"Loading IndicBERT MLM model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForMaskedLM.from_pretrained(self.model_name)
            
            # Create fill-mask pipeline
            self.fill_mask_pipeline = pipeline(
                "fill-mask",
                model=self.model,
                tokenizer=self.tokenizer
            )
            
            print("IndicBERT MLM model loaded successfully")
            
        except Exception as e:
            print(f"Failed to load IndicBERT MLM model: {e}")
            print("Error correction will be limited")
    
    def correct_errors(
        self,
        text: str,
        token_confidences: Optional[List[float]] = None,
        language: str = "en"
    ) -> Dict:
        """
        Correct errors in text using MLM
        
        Args:
            text: Input text
            token_confidences: Per-token confidence scores from OCR
            language: Detected language
        
        Returns:
            Dict with corrected text and corrections list
        """
        if not text or len(text.strip()) < 2:
            return {
                'corrected_text': text,
                'corrections': [],
                'total_corrections': 0,
                'correction_confidence': 1.0
            }
        
        # Identify low-confidence tokens
        low_conf_positions = self._identify_low_confidence_tokens(
            text,
            token_confidences
        )
        
        if not low_conf_positions:
            # No corrections needed
            return {
                'corrected_text': text,
                'corrections': [],
                'total_corrections': 0,
                'correction_confidence': 1.0
            }
        
        # Try MLM-based correction
        try:
            self._load_model()
            if self.fill_mask_pipeline is not None:
                return self._correct_with_mlm(text, low_conf_positions, language)
        except Exception as e:
            print(f"MLM correction failed: {e}")
        
        # Fallback to rule-based correction
        return self._correct_rule_based(text, low_conf_positions)
    
    def _identify_low_confidence_tokens(
        self,
        text: str,
        token_confidences: Optional[List[float]]
    ) -> List[int]:
        """
        Identify positions of low-confidence tokens
        
        Args:
            text: Input text
            token_confidences: Per-token confidences
        
        Returns:
            List of word positions with low confidence
        """
        words = text.split()
        low_conf_positions = []
        
        if token_confidences is None:
            # No confidence data, use heuristics
            for i, word in enumerate(words):
                if self._looks_suspicious(word):
                    low_conf_positions.append(i)
        else:
            # Use confidence scores
            # Map character-level confidences to word-level
            char_idx = 0
            for i, word in enumerate(words):
                word_len = len(word)
                if char_idx + word_len <= len(token_confidences):
                    word_conf = sum(token_confidences[char_idx:char_idx+word_len]) / word_len
                    if word_conf < self.confidence_threshold:
                        low_conf_positions.append(i)
                char_idx += word_len + 1  # +1 for space
        
        return low_conf_positions
    
    def _looks_suspicious(self, word: str) -> bool:
        """
        Check if word looks suspicious (likely OCR error)
        
        Args:
            word: Word to check
        
        Returns:
            True if suspicious
        """
        # Very short words
        if len(word) < 2:
            return False
        
        # Contains unusual character patterns
        if re.search(r'[0-9][a-z]|[a-z][0-9]', word, re.IGNORECASE):
            return True
        
        # Unusual consonant clusters
        if re.search(r'[bcdfghjklmnpqrstvwxyz]{4,}', word, re.IGNORECASE):
            return True
        
        return False
    
    def _correct_with_mlm(
        self,
        text: str,
        low_conf_positions: List[int],
        language: str
    ) -> Dict:
        """
        Correct errors using IndicBERT MLM
        
        Args:
            text: Input text
            low_conf_positions: Positions of low-confidence words
            language: Detected language
        
        Returns:
            Correction result
        """
        words = text.split()
        corrections = []
        corrected_words = words.copy()
        
        for pos in low_conf_positions:
            if pos >= len(words):
                continue
            
            original_word = words[pos]
            
            # Create masked text
            masked_words = words.copy()
            masked_words[pos] = self.tokenizer.mask_token
            masked_text = " ".join(masked_words)
            
            try:
                # Get MLM predictions
                predictions = self.fill_mask_pipeline(masked_text, top_k=3)
                
                if predictions and len(predictions) > 0:
                    best_prediction = predictions[0]
                    predicted_word = best_prediction['token_str'].strip()
                    confidence = best_prediction['score']
                    
                    # Accept if confidence is high enough
                    if confidence >= self.mlm_prediction_threshold:
                        # Validate against dictionary if enabled
                        if self.use_dictionary_validation:
                            if not self._is_valid_word(predicted_word, language):
                                continue
                        
                        corrected_words[pos] = predicted_word
                        corrections.append({
                            'original': original_word,
                            'corrected': predicted_word,
                            'confidence': float(confidence),
                            'position': pos,
                            'method': 'IndicBERT_MLM'
                        })
            
            except Exception as e:
                print(f"MLM prediction failed for position {pos}: {e}")
                continue
        
        corrected_text = " ".join(corrected_words)
        avg_confidence = sum(c['confidence'] for c in corrections) / len(corrections) if corrections else 1.0
        
        return {
            'corrected_text': corrected_text,
            'corrections': corrections,
            'total_corrections': len(corrections),
            'correction_confidence': avg_confidence
        }
    
    def _correct_rule_based(
        self,
        text: str,
        low_conf_positions: List[int]
    ) -> Dict:
        """
        Rule-based error correction (fallback)
        
        Args:
            text: Input text
            low_conf_positions: Positions of low-confidence words
        
        Returns:
            Correction result
        """
        # Common OCR error patterns
        error_patterns = {
            r'\brn\b': 'm',  # 'rn' often misread as 'm'
            r'\bvv\b': 'w',  # 'vv' often misread as 'w'
            r'\bl\b': '1',   # 'l' vs '1'
            r'\bO\b': '0',   # 'O' vs '0'
        }
        
        corrected_text = text
        corrections = []
        
        for pattern, replacement in error_patterns.items():
            if re.search(pattern, corrected_text, re.IGNORECASE):
                original = re.search(pattern, corrected_text, re.IGNORECASE).group()
                corrected_text = re.sub(pattern, replacement, corrected_text, flags=re.IGNORECASE)
                corrections.append({
                    'original': original,
                    'corrected': replacement,
                    'confidence': 0.70,
                    'position': -1,
                    'method': 'Rule_Based'
                })
        
        return {
            'corrected_text': corrected_text,
            'corrections': corrections,
            'total_corrections': len(corrections),
            'correction_confidence': 0.70 if corrections else 1.0
        }
    
    def _is_valid_word(self, word: str, language: str) -> bool:
        """
        Validate word against dictionary
        
        Args:
            word: Word to validate
            language: Language code
        
        Returns:
            True if valid
        """
        # Simplified validation - always return True for now
        # In production, load and check against actual dictionaries
        return True
