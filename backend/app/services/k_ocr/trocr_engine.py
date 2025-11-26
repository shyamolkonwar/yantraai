"""
K-OCR v2.0 - TrOCR Engine
Handles TrOCR model loading and inference
"""

import os
import torch
import numpy as np
from PIL import Image
from typing import Tuple, List, Dict, Optional
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


class TrOCREngine:
    """
    TrOCR model inference engine
    """
    
    def __init__(self, device: str = "cpu", fp16: bool = False):
        """
        Initialize TrOCR engine
        
        Args:
            device: Device to run on ("cpu" or "cuda")
            fp16: Use half-precision (FP16) for faster inference
        """
        self.device = device
        self.fp16 = fp16 and device == "cuda"
        
        # Model caches
        self.printed_processor = None
        self.printed_model = None
        self.handwritten_processor = None
        self.handwritten_model = None
    
    def load_printed_model(
        self,
        model_name: str = "microsoft/trocr-base-printed",
        model_path: Optional[str] = None
    ):
        """
        Load TrOCR printed model
        
        Args:
            model_name: Hugging Face model name
            model_path: Local model path (optional)
        """
        try:
            # Load from local path if exists, otherwise from Hugging Face
            load_path = model_path if model_path and os.path.exists(model_path) else model_name
            
            print(f"Loading TrOCR printed model from {load_path}...")
            self.printed_processor = TrOCRProcessor.from_pretrained(load_path)
            self.printed_model = VisionEncoderDecoderModel.from_pretrained(load_path)
            
            # Move to device
            self.printed_model.to(self.device)
            
            # Enable FP16 if requested
            if self.fp16:
                self.printed_model.half()
            
            # Set to eval mode
            self.printed_model.eval()
            
            print(f"TrOCR printed model loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"Failed to load TrOCR printed model: {e}")
            raise
    
    def load_handwritten_model(
        self,
        model_name: str = "microsoft/trocr-large-handwritten",
        model_path: Optional[str] = None
    ):
        """
        Load TrOCR handwritten model
        
        Args:
            model_name: Hugging Face model name
            model_path: Local model path (optional)
        """
        try:
            # Load from local path if exists, otherwise from Hugging Face
            load_path = model_path if model_path and os.path.exists(model_path) else model_name
            
            print(f"Loading TrOCR handwritten model from {load_path}...")
            self.handwritten_processor = TrOCRProcessor.from_pretrained(load_path)
            self.handwritten_model = VisionEncoderDecoderModel.from_pretrained(load_path)
            
            # Move to device
            self.handwritten_model.to(self.device)
            
            # Enable FP16 if requested
            if self.fp16:
                self.handwritten_model.half()
            
            # Set to eval mode
            self.handwritten_model.eval()
            
            print(f"TrOCR handwritten model loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"Failed to load TrOCR handwritten model: {e}")
            raise
    
    def run_inference(
        self,
        image: np.ndarray,
        model_type: str = "printed",
        return_token_confidences: bool = True
    ) -> Tuple[str, float, Optional[List[Dict]]]:
        """
        Run TrOCR inference on image
        
        Args:
            image: RGB uint8 numpy array
            model_type: "printed" or "handwritten"
            return_token_confidences: Return per-token confidences
        
        Returns:
            Tuple of (text, confidence, tokens)
            text: Recognized text
            confidence: Average confidence (0.0-1.0)
            tokens: List of {character, confidence} dicts (if return_token_confidences=True)
        """
        try:
            # Select model and processor
            if model_type == "printed":
                processor = self.printed_processor
                model = self.printed_model
            elif model_type == "handwritten":
                processor = self.handwritten_processor
                model = self.handwritten_model
            else:
                raise ValueError(f"Invalid model_type: {model_type}")
            
            if processor is None or model is None:
                raise RuntimeError(f"{model_type} model not loaded")
            
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(image)
            
            # Process image
            pixel_values = processor(pil_image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            # Run inference
            with torch.no_grad():
                outputs = model.generate(
                    pixel_values,
                    max_length=128,
                    num_beams=4,
                    early_stopping=True,
                    output_scores=True,
                    return_dict_in_generate=True
                )
            
            # Decode text
            generated_ids = outputs.sequences
            generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Calculate confidence from scores
            if return_token_confidences and hasattr(outputs, 'scores') and outputs.scores:
                tokens, avg_confidence = self._extract_token_confidences(
                    outputs.scores,
                    generated_ids[0],
                    processor
                )
            else:
                # Estimate confidence (simplified)
                avg_confidence = self._estimate_confidence(generated_text)
                tokens = None
            
            return generated_text.strip(), avg_confidence, tokens
            
        except Exception as e:
            print(f"TrOCR inference failed: {e}")
            return "", 0.0, None
    
    def _extract_token_confidences(
        self,
        scores: Tuple[torch.Tensor],
        generated_ids: torch.Tensor,
        processor: TrOCRProcessor
    ) -> Tuple[List[Dict], float]:
        """
        Extract per-token confidences from model scores
        
        Args:
            scores: Model output scores
            generated_ids: Generated token IDs
            processor: TrOCR processor
        
        Returns:
            Tuple of (tokens, avg_confidence)
        """
        try:
            tokens = []
            confidences = []
            
            for i, score in enumerate(scores):
                # Get probabilities
                probs = torch.softmax(score[0], dim=-1)
                
                # Get predicted token ID
                if i + 1 < len(generated_ids):
                    token_id = generated_ids[i + 1].item()
                    
                    # Get confidence for this token
                    confidence = probs[token_id].item()
                    
                    # Decode token
                    token_text = processor.tokenizer.decode([token_id])
                    
                    tokens.append({
                        'character': token_text,
                        'confidence': confidence
                    })
                    confidences.append(confidence)
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return tokens, avg_confidence
            
        except Exception as e:
            print(f"Token confidence extraction failed: {e}")
            return [], 0.0
    
    def _estimate_confidence(self, text: str) -> float:
        """
        Estimate confidence for text (simplified heuristic)
        
        Args:
            text: Generated text
        
        Returns:
            Estimated confidence (0.0-1.0)
        """
        if not text or len(text.strip()) < 2:
            return 0.1
        
        # Base confidence
        confidence = 0.8
        
        # Penalize very short text
        if len(text.strip()) < 5:
            confidence *= 0.7
        
        # Penalize text with many special characters
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / len(text) if text else 0
        if special_ratio > 0.3:
            confidence *= 0.8
        
        return confidence
