import cv2
import numpy as np
import easyocr
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from typing import Tuple, List, Dict, Any
import torch
from difflib import SequenceMatcher
from langdetect import detect, LangDetectException

# Initialize models (global for performance)

# Helper functions for OCR improvements
def add_padding_to_crop(image: np.ndarray, padding: int = 10) -> np.ndarray:
    """
    Add padding around image to prevent tight crops
    """
    return cv2.copyMakeBorder(
        image, padding, padding, padding, padding,
        cv2.BORDER_CONSTANT, value=[255, 255, 255]  # White padding
    )

def is_vertical_text(bbox: List[int]) -> bool:
    """
    Check if bbox indicates vertical text (height > 5 * width)
    
    Conservative threshold to avoid false positives:
    - Ratio 2:1 = Normal tall region (e.g., column of text)
    - Ratio 5:1 = Likely vertical text (e.g., side margin notes)
    """
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    
    # Require very tall/skinny ratio AND minimum dimensions
    # to avoid rotating small regions
    if width < 20:  # Too narrow to be reliable
        return False
    
    ratio = height / width if width > 0 else 0
    return ratio > 5.0  # Changed from 2.0 to 5.0

def rotate_if_vertical(image: np.ndarray, bbox: List[int]) -> Tuple[np.ndarray, bool]:
    """
    Rotate image 90° counterclockwise if bbox indicates vertical text
    Returns: (rotated_image, was_rotated)
    """
    if is_vertical_text(bbox):
        rotated = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return rotated, True
    return image, False
easyocr_reader = easyocr.Reader(['en', 'hi'], gpu=False)  # English and Hindi

# TrOCR models
trocr_processor = None
trocr_model = None
trocr_handwritten_processor = None
trocr_handwritten_model = None

def initialize_trocr():
    """Initialize TrOCR models lazily"""
    global trocr_processor, trocr_model, trocr_handwritten_processor, trocr_handwritten_model

    if trocr_processor is None:
        try:
            trocr_processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
            trocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')
            print("TrOCR printed model loaded successfully")
        except Exception as e:
            print(f"Failed to load TrOCR printed model: {e}")

    if trocr_handwritten_processor is None:
        try:
            trocr_handwritten_processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
            trocr_handwritten_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')
            print("TrOCR handwritten model loaded successfully")
        except Exception as e:
            print(f"Failed to load TrOCR handwritten model: {e}")

def perform_ocr_ensemble(image: np.ndarray, language: str = "english", bbox: List[int] = None) -> Tuple[str, float]:
    """
    OCR ensemble with TrOCR and EasyOCR
    Includes: padding, vertical text rotation, and handwritten model switching
    """
    initialize_trocr()

    # Fix 3: Add padding to prevent tight crops
    image = add_padding_to_crop(image, padding=10)

    # Fix 1: Check for vertical text and rotate if needed
    was_rotated = False
    if bbox:
        image, was_rotated = rotate_if_vertical(image, bbox)
        if was_rotated:
            print(f"Rotated vertical text region: {bbox}")

    # Detect language
    language_detected = detect_language(image)
    print(f"Detected language: {language_detected}")

    # Routing Logic
    if language_detected == 'hi':
        # Hindi/Indic -> Use EasyOCR directly
        easyocr_text, easyocr_conf = perform_easyocr(image)
        return easyocr_text, easyocr_conf
    
    # English/Other -> Use TrOCR with line segmentation
    # Segment lines for TrOCR (it fails on paragraphs)
    lines = segment_lines(image)
    
    full_text_parts = []
    confidences = []
    model_types = []
    
    for line_img in lines:
        # Fix 2: Try printed model first, fall back to handwritten if low confidence
        if trocr_processor and trocr_model:
            # Try printed model first (faster)
            line_text_printed, conf_printed = perform_trocr_ocr(line_img, handwritten=False)
            
            # If confidence is high, use printed result
            if conf_printed >= 0.70:
                if line_text_printed.strip():
                    full_text_parts.append(line_text_printed)
                    confidences.append(conf_printed)
                    model_types.append('printed')
            else:
                # Low confidence - try handwritten model
                if trocr_handwritten_processor and trocr_handwritten_model:
                    line_text_handwritten, conf_handwritten = perform_trocr_ocr(line_img, handwritten=True)
                    
                    # Use better result
                    if conf_handwritten > conf_printed:
                        if line_text_handwritten.strip():
                            full_text_parts.append(line_text_handwritten)
                            confidences.append(conf_handwritten)
                            model_types.append('handwritten')
                            print(f"Switched to handwritten model (conf: {conf_handwritten:.3f} vs {conf_printed:.3f})")
                    else:
                        if line_text_printed.strip():
                            full_text_parts.append(line_text_printed)
                            confidences.append(conf_printed)
                            model_types.append('printed')
                else:
                    # Handwritten model not available, use printed result
                    if line_text_printed.strip():
                        full_text_parts.append(line_text_printed)
                        confidences.append(conf_printed)
                        model_types.append('printed')
        else:
            # Fallback if TrOCR not loaded
            line_text, line_conf = perform_easyocr(line_img)
            if line_text.strip():
                full_text_parts.append(line_text)
                confidences.append(line_conf)
                model_types.append('easyocr')
                
    final_text = " ".join(full_text_parts)
    final_conf = sum(confidences) / len(confidences) if confidences else 0.0
    
    # Log model usage
    if model_types:
        print(f"Model usage: {dict((x, model_types.count(x)) for x in set(model_types))}")
    
    return final_text, final_conf

def perform_trocr_ocr(image: np.ndarray, handwritten: bool = False) -> Tuple[str, float]:
    """
    Perform OCR using TrOCR model
    """
    try:
        if handwritten:
            processor = trocr_handwritten_processor
            model = trocr_handwritten_model
        else:
            processor = trocr_processor
            model = trocr_model

        if not processor or not model:
            return "", 0.0

        # Convert to PIL Image
        pil_image = cv2_to_pil(image)

        # Process image
        pixel_values = processor(pil_image, return_tensors="pt").pixel_values

        # Generate text
        with torch.no_grad():
            generated_ids = model.generate(
                pixel_values,
                max_length=128,
                num_beams=4,
                early_stopping=True
            )

        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        # Estimate confidence (simplified - use model logits if available)
        # For now, use a proxy confidence based on text length and content
        confidence = estimate_trocr_confidence(generated_text)

        return generated_text.strip(), confidence

    except Exception as e:
        print(f"TrOCR OCR failed: {e}")
        return "", 0.0

def perform_easyocr(image: np.ndarray) -> Tuple[str, float]:
    """
    Perform OCR using EasyOCR
    """
    try:
        # EasyOCR can work with numpy arrays directly
        results = easyocr_reader.readtext(image)

        if not results:
            return "", 0.0

        # Combine all text
        texts = [result[1] for result in results]
        confidences = [result[2] for result in results]

        raw_text = " ".join(texts)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        return raw_text.strip(), avg_conf

    except Exception as e:
        print(f"EasyOCR failed: {e}")
        return "", 0.0

def ensemble_decision(ocr_results: List[Dict[str, Any]]) -> Tuple[str, float]:
    """
    Make ensemble decision from multiple OCR results
    """
    if len(ocr_results) == 1:
        return ocr_results[0]['text'], ocr_results[0]['confidence']

    # Sort by confidence
    ocr_results.sort(key=lambda x: x['confidence'], reverse=True)

    # Use highest confidence result as primary
    primary_result = ocr_results[0]

    # Check agreement with other results
    agreement_scores = []
    for result in ocr_results[1:]:
        similarity = calculate_text_similarity(primary_result['text'], result['text'])
        agreement_scores.append(similarity)

    # Boost confidence if there's agreement
    avg_agreement = sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0.0

    # Ensemble confidence: weighted combination of primary confidence and agreement
    ensemble_conf = 0.7 * primary_result['confidence'] + 0.3 * avg_agreement

    # If agreement is low, use LM scoring as fallback
    if avg_agreement < 0.5:
        lm_score = calculate_lm_score(primary_result['text'])
        ensemble_conf = 0.8 * ensemble_conf + 0.2 * lm_score

    return primary_result['text'], min(ensemble_conf, 1.0)

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using Levenshtein ratio
    """
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def calculate_lm_score(text: str) -> float:
    """
    Calculate language model score as proxy for OCR quality
    Simplified implementation - in practice, use a proper LM
    """
    if not text or len(text.strip()) < 3:
        return 0.0

    # Simple heuristics for text quality
    words = text.split()
    if not words:
        return 0.0

    # Average word length (reasonable words are 3-10 chars)
    avg_word_len = sum(len(word) for word in words) / len(words)
    length_score = 1.0 if 3 <= avg_word_len <= 10 else 0.5

    # Presence of common English words (simplified)
    common_words = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that']
    common_count = sum(1 for word in words if word.lower() in common_words)
    common_score = min(common_count / len(words), 0.5) * 2  # Scale to 0-1

    return (length_score + common_score) / 2

def estimate_trocr_confidence(text: str) -> float:
    """
    Estimate confidence for TrOCR output
    """
    if not text or len(text.strip()) < 2:
        return 0.1

    # Simple heuristics
    confidence = 0.8  # Base confidence

    # Penalize very short text
    if len(text.strip()) < 5:
        confidence *= 0.7

    # Penalize text with many special characters
    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    special_ratio = special_chars / len(text) if text else 0
    if special_ratio > 0.3:
        confidence *= 0.8

    return confidence

def cv2_to_pil(image: np.ndarray):
    """
    Convert OpenCV image to PIL Image
    """
    from PIL import Image
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(image)

# Legacy function for backward compatibility
def perform_ocr(image_path: str) -> Tuple[str, float]:
    """
    Legacy OCR function for backward compatibility
    """
    image = cv2.imread(image_path)
    return perform_ocr_ensemble(image)

def detect_language(image: np.ndarray) -> str:
    """
    Detect language using Tesseract OSD or langdetect on initial OCR pass
    """
    try:
        # Fast initial pass with EasyOCR to get some text
        text, _ = perform_easyocr(image)
        if not text or len(text.strip()) < 5:
            return 'en'
            
        try:
            lang = detect(text)
            return lang
        except LangDetectException:
            return 'en'
            
    except Exception as e:
        print(f"Language detection failed: {e}")
        return 'en'

def segment_lines(image: np.ndarray) -> List[np.ndarray]:
    """
    Segment image into lines using horizontal projection
    """
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Invert if needed (text should be white on black for projection)
        # Assuming standard document (black text on white bg), so invert
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Horizontal projection
        proj = np.sum(binary, axis=1)
        
        # Find gaps
        lines = []
        start_idx = None
        
        # Threshold for "text present" in a row
        threshold = np.max(proj) * 0.05
        
        for i, val in enumerate(proj):
            if val > threshold and start_idx is None:
                start_idx = i
            elif val <= threshold and start_idx is not None:
                # End of line
                if i - start_idx > 5: # Minimum line height
                    # Add padding
                    y1 = max(0, start_idx - 2)
                    y2 = min(image.shape[0], i + 2)
                    lines.append(image[y1:y2, :])
                start_idx = None
                
        # Handle last line
        if start_idx is not None:
             lines.append(image[start_idx:, :])
             
        if not lines:
            return [image]
            
        return lines
        
    except Exception as e:
        print(f"Line segmentation failed: {e}")
        return [image]
