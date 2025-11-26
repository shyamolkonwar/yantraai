"""
K-Ingest v2.0 - Validators Module
Quality assurance and validation functions
"""

import numpy as np
from typing import Tuple, List
from app.schemas import Region


def validate_image_quality(
    image: np.ndarray,
    min_resolution: Tuple[int, int] = (800, 600)
) -> Tuple[bool, str]:
    """
    Validate image quality
    
    Args:
        image: RGB uint8 numpy array
        min_resolution: Minimum (width, height) resolution
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if image is valid
    if image is None or image.size == 0:
        return False, "Image is None or empty"
    
    # Check color space
    is_valid_cs, cs_error = validate_color_space(image)
    if not is_valid_cs:
        return False, cs_error
    
    height, width = image.shape[:2]
    
    # Check minimum resolution
    if width < min_resolution[0] or height < min_resolution[1]:
        return False, f"Resolution too low: {width}x{height} (minimum: {min_resolution[0]}x{min_resolution[1]})"
    
    # Check for blank page
    mean_brightness = np.mean(image)
    if mean_brightness < 5 or mean_brightness > 250:
        return False, f"Image appears blank (mean brightness: {mean_brightness:.1f})"
    
    # Check variance
    variance = np.var(image.astype(np.float32))
    if variance < 10:
        return False, "Image has extremely low variance - may be blank"
    
    return True, ""


def validate_color_space(image: np.ndarray) -> Tuple[bool, str]:
    """
    Validate that image is RGB uint8
    
    Args:
        image: Numpy array to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if image is None:
        return False, "Image is None"
    
    # Check shape (H, W, 3)
    if len(image.shape) != 3:
        return False, f"Invalid shape: expected 3 dimensions, got {len(image.shape)}"
    
    if image.shape[2] != 3:
        return False, f"Invalid channels: expected 3 (RGB), got {image.shape[2]}"
    
    # Check dtype
    if image.dtype != np.uint8:
        return False, f"Invalid dtype: expected uint8, got {image.dtype}"
    
    # Check value range
    if np.min(image) < 0 or np.max(image) > 255:
        return False, f"Invalid value range: expected 0-255, got {np.min(image)}-{np.max(image)}"
    
    return True, ""


def validate_layout_output(
    detections: List[Region],
    image_shape: Tuple[int, int],
    min_detections: int = 0,
    max_detections: int = 500
) -> Tuple[bool, str]:
    """
    Validate layout detection output
    
    Args:
        detections: List of detected regions
        image_shape: (height, width) of source image
        min_detections: Minimum number of detections required
        max_detections: Maximum number of detections allowed
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    height, width = image_shape
    
    # Check detection count
    num_detections = len(detections)
    if num_detections < min_detections:
        return False, f"Too few detections: {num_detections} (minimum: {min_detections})"
    
    if num_detections > max_detections:
        return False, f"Too many detections: {num_detections} (maximum: {max_detections})"
    
    # Validate each detection
    for i, region in enumerate(detections):
        # Check bounding box is within image bounds
        bbox = region.bbox
        
        if bbox.x1 < 0 or bbox.y1 < 0:
            return False, f"Region {i}: negative coordinates ({bbox.x1}, {bbox.y1})"
        
        if bbox.x2 > width or bbox.y2 > height:
            return False, f"Region {i}: coordinates exceed image bounds ({bbox.x2}, {bbox.y2}) > ({width}, {height})"
        
        if bbox.x1 >= bbox.x2 or bbox.y1 >= bbox.y2:
            return False, f"Region {i}: invalid box coordinates (x1={bbox.x1}, x2={bbox.x2}, y1={bbox.y1}, y2={bbox.y2})"
        
        # Check confidence range
        if region.confidence < 0.0 or region.confidence > 1.0:
            return False, f"Region {i}: invalid confidence {region.confidence} (must be 0.0-1.0)"
    
    return True, ""


def validate_preprocessing_output(
    original: np.ndarray,
    preprocessed: np.ndarray
) -> Tuple[bool, str]:
    """
    Validate preprocessing output
    
    Args:
        original: Original RGB image
        preprocessed: Preprocessed RGB image
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check preprocessed image is valid RGB
    is_valid_cs, cs_error = validate_color_space(preprocessed)
    if not is_valid_cs:
        return False, f"Preprocessed image: {cs_error}"
    
    # Check preprocessed image is not smaller than original (padding should be added)
    orig_h, orig_w = original.shape[:2]
    prep_h, prep_w = preprocessed.shape[:2]
    
    if prep_h < orig_h or prep_w < orig_w:
        return False, f"Preprocessed image is smaller than original: ({prep_w}x{prep_h}) < ({orig_w}x{orig_h})"
    
    return True, ""


class ValidationResult:
    """Container for validation results"""
    
    def __init__(self, is_valid: bool, error_message: str = ""):
        self.is_valid = is_valid
        self.error_message = error_message
    
    def __bool__(self):
        return self.is_valid
    
    def __str__(self):
        if self.is_valid:
            return "Validation passed"
        return f"Validation failed: {self.error_message}"
