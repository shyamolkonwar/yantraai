"""
K-Ingest v2.0 - Preprocessing Module
Handles image preprocessing for optimal layout detection
"""

import cv2
import numpy as np
from typing import Tuple


def preprocess_for_layout(
    image: np.ndarray,
    denoise: bool = True,
    deskew: bool = True,
    enhance_contrast: bool = True,
    add_padding: bool = True,
    config: dict = None
) -> np.ndarray:
    """
    Apply preprocessing pipeline to image
    
    Args:
        image: RGB uint8 numpy array
        denoise: Apply denoising
        deskew: Apply deskew correction
        enhance_contrast: Apply CLAHE contrast enhancement
        add_padding: Add border padding
        config: Configuration dict with preprocessing parameters
    
    Returns:
        Preprocessed RGB uint8 numpy array
    """
    if config is None:
        config = _get_default_config()
    
    processed = image.copy()
    
    # Stage 1: Denoising
    if denoise and config.get('denoise', {}).get('enabled', True):
        processed = _denoise_image(processed, config['denoise'])
    
    # Stage 2: Deskew
    if deskew and config.get('deskew', {}).get('enabled', True):
        processed = _deskew_image(processed, config['deskew'])
    
    # Stage 3: Contrast Enhancement
    if enhance_contrast and config.get('contrast_enhancement', {}).get('enabled', True):
        processed = _enhance_contrast(processed, config['contrast_enhancement'])
    
    # Stage 4: Border Padding
    if add_padding and config.get('padding', {}).get('enabled', True):
        processed = _add_border_padding(processed, config['padding'])
    
    return processed


def _denoise_image(image: np.ndarray, config: dict) -> np.ndarray:
    """
    Apply denoising to RGB image
    
    Args:
        image: RGB uint8 numpy array
        config: Denoise configuration
    
    Returns:
        Denoised RGB uint8 numpy array
    """
    h = config.get('h', 10)
    template_window_size = config.get('template_window_size', 7)
    search_window_size = config.get('search_window_size', 21)
    
    try:
        denoised = cv2.fastNlMeansDenoisingColored(
            image,
            None,
            h=h,
            hColor=h,
            templateWindowSize=template_window_size,
            searchWindowSize=search_window_size
        )
        return denoised
    except Exception as e:
        print(f"Denoising failed: {e}")
        return image


def _deskew_image(image: np.ndarray, config: dict) -> np.ndarray:
    """
    Detect and correct image skew
    
    Args:
        image: RGB uint8 numpy array
        config: Deskew configuration
    
    Returns:
        Deskewed RGB uint8 numpy array
    """
    angle_threshold = config.get('angle_threshold', 0.5)
    interpolation = config.get('interpolation', 'INTER_CUBIC')
    
    try:
        # Convert to grayscale for angle detection
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Detect angle using Hough Line Transform
        angle = _detect_skew_angle(gray)
        
        # Only rotate if angle exceeds threshold
        if abs(angle) < angle_threshold:
            return image
        
        # Rotate image
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # Get interpolation method
        interp_method = getattr(cv2, interpolation, cv2.INTER_CUBIC)
        
        # Create rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Apply rotation
        rotated = cv2.warpAffine(
            image,
            M,
            (width, height),
            flags=interp_method,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated
        
    except Exception as e:
        print(f"Deskewing failed: {e}")
        return image


def _detect_skew_angle(gray: np.ndarray) -> float:
    """
    Detect skew angle using Hough Line Transform
    
    Args:
        gray: Grayscale image
    
    Returns:
        Skew angle in degrees
    """
    # Edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Hough Line Transform
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    
    if lines is None or len(lines) == 0:
        return 0.0
    
    # Calculate angles
    angles = []
    for rho, theta in lines[:, 0]:
        angle = np.degrees(theta) - 90
        # Filter out vertical and horizontal lines
        if -45 < angle < 45:
            angles.append(angle)
    
    if not angles:
        return 0.0
    
    # Return median angle
    return float(np.median(angles))


def _enhance_contrast(image: np.ndarray, config: dict) -> np.ndarray:
    """
    Apply CLAHE contrast enhancement
    
    Args:
        image: RGB uint8 numpy array
        config: Contrast enhancement configuration
    
    Returns:
        Enhanced RGB uint8 numpy array
    """
    clip_limit = config.get('clip_limit', 2.0)
    tile_grid_size = tuple(config.get('tile_grid_size', [8, 8]))
    
    try:
        # Convert RGB to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        
        # Split channels
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L-channel
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        l_enhanced = clahe.apply(l)
        
        # Merge channels
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        
        # Convert back to RGB
        rgb_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)
        
        return rgb_enhanced
        
    except Exception as e:
        print(f"Contrast enhancement failed: {e}")
        return image


def _add_border_padding(image: np.ndarray, config: dict) -> np.ndarray:
    """
    Add white border padding to image
    
    Args:
        image: RGB uint8 numpy array
        config: Padding configuration
    
    Returns:
        Padded RGB uint8 numpy array
    """
    border_size = config.get('border_size', 10)
    border_color = tuple(config.get('border_color', [255, 255, 255]))
    
    try:
        padded = cv2.copyMakeBorder(
            image,
            border_size,
            border_size,
            border_size,
            border_size,
            cv2.BORDER_CONSTANT,
            value=border_color
        )
        return padded
        
    except Exception as e:
        print(f"Border padding failed: {e}")
        return image


def _get_default_config() -> dict:
    """Get default preprocessing configuration"""
    return {
        'denoise': {
            'enabled': True,
            'h': 10,
            'template_window_size': 7,
            'search_window_size': 21
        },
        'deskew': {
            'enabled': True,
            'angle_threshold': 0.5,
            'interpolation': 'INTER_CUBIC'
        },
        'contrast_enhancement': {
            'enabled': True,
            'clip_limit': 2.0,
            'tile_grid_size': [8, 8]
        },
        'padding': {
            'enabled': True,
            'border_size': 10,
            'border_color': [255, 255, 255]
        }
    }
