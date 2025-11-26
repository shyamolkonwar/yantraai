"""
K-OCR v2.0 - Text Type Classifier
Distinguishes between printed, handwritten, and mixed text
"""

import cv2
import numpy as np
from typing import Tuple


def classify_text_type(
    image: np.ndarray,
    edge_density_threshold: float = 0.12,
    stroke_variance_threshold: float = 4.0,
    vertical_variance_threshold: float = 6.0
) -> Tuple[str, float]:
    """
    Classify text type using rule-based approach
    
    Args:
        image: RGB uint8 numpy array
        edge_density_threshold: Threshold for edge density
        stroke_variance_threshold: Threshold for stroke width variance
        vertical_variance_threshold: Threshold for vertical alignment variance
    
    Returns:
        Tuple of (text_type, confidence)
        text_type: 'printed', 'handwritten', or 'mixed'
        confidence: 0.0-1.0
    """
    try:
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Calculate features
        edge_density = _calculate_edge_density(gray)
        stroke_variance = _calculate_stroke_variance(gray)
        vertical_variance = _calculate_vertical_variance(gray)
        
        # Decision logic
        scores = {
            'printed': 0.0,
            'handwritten': 0.0,
            'mixed': 0.0
        }
        
        # Edge density: printed text has higher edge density
        if edge_density > edge_density_threshold:
            scores['printed'] += 0.4
        else:
            scores['handwritten'] += 0.4
        
        # Stroke variance: handwritten has higher variance
        if stroke_variance > stroke_variance_threshold:
            scores['handwritten'] += 0.3
        else:
            scores['printed'] += 0.3
        
        # Vertical variance: handwritten has higher variance
        if vertical_variance > vertical_variance_threshold:
            scores['handwritten'] += 0.3
        else:
            scores['printed'] += 0.3
        
        # Determine text type
        text_type = max(scores, key=scores.get)
        confidence = scores[text_type]
        
        # If scores are close, classify as mixed
        sorted_scores = sorted(scores.values(), reverse=True)
        if sorted_scores[0] - sorted_scores[1] < 0.2:
            text_type = 'mixed'
            confidence = 0.6
        
        return text_type, confidence
        
    except Exception as e:
        print(f"Text classification failed: {e}")
        return 'printed', 0.5  # Default to printed with low confidence


def _calculate_edge_density(gray: np.ndarray) -> float:
    """
    Calculate edge density using Canny edge detection
    
    Args:
        gray: Grayscale image
    
    Returns:
        Edge density (0.0-1.0)
    """
    try:
        # Canny edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Calculate density
        total_pixels = edges.size
        edge_pixels = np.count_nonzero(edges)
        density = edge_pixels / total_pixels if total_pixels > 0 else 0.0
        
        return density
        
    except Exception as e:
        print(f"Edge density calculation failed: {e}")
        return 0.0


def _calculate_stroke_variance(gray: np.ndarray) -> float:
    """
    Calculate stroke width variance
    
    Args:
        gray: Grayscale image
    
    Returns:
        Stroke width variance
    """
    try:
        # Binarize
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Distance transform to estimate stroke widths
        dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
        
        # Get non-zero distances (stroke widths)
        stroke_widths = dist_transform[dist_transform > 0]
        
        if len(stroke_widths) == 0:
            return 0.0
        
        # Calculate variance
        variance = np.var(stroke_widths)
        
        return float(variance)
        
    except Exception as e:
        print(f"Stroke variance calculation failed: {e}")
        return 0.0


def _calculate_vertical_variance(gray: np.ndarray) -> float:
    """
    Calculate vertical alignment variance
    
    Args:
        gray: Grayscale image
    
    Returns:
        Vertical variance
    """
    try:
        # Binarize
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Horizontal projection
        projection = np.sum(binary, axis=1)
        
        # Find text line positions (peaks in projection)
        threshold = np.max(projection) * 0.3
        line_positions = np.where(projection > threshold)[0]
        
        if len(line_positions) < 2:
            return 0.0
        
        # Calculate differences between consecutive line positions
        diffs = np.diff(line_positions)
        
        # Calculate variance of differences
        variance = np.var(diffs) if len(diffs) > 0 else 0.0
        
        return float(variance)
        
    except Exception as e:
        print(f"Vertical variance calculation failed: {e}")
        return 0.0


# CNN-based classifier (placeholder for future implementation)
class CNNTextClassifier:
    """
    CNN-based text type classifier (future enhancement)
    """
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
    
    def load_model(self):
        """Load CNN model"""
        # TODO: Implement CNN model loading
        raise NotImplementedError("CNN classifier not yet implemented")
    
    def classify(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Classify text type using CNN
        
        Args:
            image: RGB uint8 numpy array
        
        Returns:
            Tuple of (text_type, confidence)
        """
        # TODO: Implement CNN classification
        raise NotImplementedError("CNN classifier not yet implemented")
