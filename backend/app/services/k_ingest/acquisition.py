"""
K-Ingest v2.0 - Document Acquisition Module
Handles document intake and RGB standardization
"""

import os
import cv2
import numpy as np
from pdf2image import convert_from_path
from typing import List, Tuple
from PIL import Image


def acquire_document(filepath: str, dpi: int = 300) -> List[np.ndarray]:
    """
    Acquire document and convert to standardized RGB images
    
    Args:
        filepath: Path to PDF or image file
        dpi: DPI for PDF rendering (default: 300)
    
    Returns:
        List of RGB numpy arrays (uint8)
    
    Raises:
        ValueError: If file format is unsupported or rendering fails
    """
    file_ext = os.path.splitext(filepath)[1].lower()
    
    if file_ext == '.pdf':
        return _acquire_pdf(filepath, dpi)
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        return _acquire_image(filepath)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


def _acquire_pdf(pdf_path: str, dpi: int) -> List[np.ndarray]:
    """
    Convert PDF to RGB images
    
    Args:
        pdf_path: Path to PDF file
        dpi: DPI for rendering
    
    Returns:
        List of RGB numpy arrays (uint8)
    """
    try:
        # Convert PDF to PIL images (RGB by default)
        pil_images = convert_from_path(pdf_path, dpi=dpi)
        
        if not pil_images:
            raise ValueError("Failed to render PDF - no pages extracted")
        
        # Convert PIL images to numpy arrays (RGB uint8)
        rgb_images = []
        for pil_img in pil_images:
            # Ensure RGB mode
            if pil_img.mode != 'RGB':
                pil_img = pil_img.convert('RGB')
            
            # Convert to numpy array (already RGB)
            np_img = np.array(pil_img, dtype=np.uint8)
            
            # Validate
            if not _validate_rgb_image(np_img):
                raise ValueError(f"Invalid image format: expected RGB uint8, got shape {np_img.shape}")
            
            rgb_images.append(np_img)
        
        return rgb_images
        
    except Exception as e:
        raise ValueError(f"Failed to acquire PDF: {str(e)}")


def _acquire_image(image_path: str) -> List[np.ndarray]:
    """
    Load image file as RGB
    
    Args:
        image_path: Path to image file
    
    Returns:
        List containing single RGB numpy array (uint8)
    """
    try:
        # Load with PIL (handles various formats)
        pil_img = Image.open(image_path)
        
        # Convert to RGB
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        # Convert to numpy array
        np_img = np.array(pil_img, dtype=np.uint8)
        
        # Validate
        if not _validate_rgb_image(np_img):
            raise ValueError(f"Invalid image format: expected RGB uint8, got shape {np_img.shape}")
        
        return [np_img]
        
    except Exception as e:
        raise ValueError(f"Failed to acquire image: {str(e)}")


def _validate_rgb_image(image: np.ndarray) -> bool:
    """
    Validate that image is RGB uint8
    
    Args:
        image: Numpy array to validate
    
    Returns:
        True if valid RGB uint8 image
    """
    if image is None:
        return False
    
    # Check shape (H, W, 3)
    if len(image.shape) != 3 or image.shape[2] != 3:
        return False
    
    # Check dtype
    if image.dtype != np.uint8:
        return False
    
    return True


def validate_document_quality(image: np.ndarray, min_resolution: Tuple[int, int] = (800, 600)) -> Tuple[bool, str]:
    """
    Validate document image quality
    
    Args:
        image: RGB numpy array to validate
        min_resolution: Minimum (width, height) resolution
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if image is valid RGB
    if not _validate_rgb_image(image):
        return False, "Invalid image format: expected RGB uint8"
    
    height, width = image.shape[:2]
    
    # Check minimum resolution
    if width < min_resolution[0] or height < min_resolution[1]:
        return False, f"Resolution too low: {width}x{height} (minimum: {min_resolution[0]}x{min_resolution[1]})"
    
    # Check for blank/corrupted image
    mean_brightness = np.mean(image)
    if mean_brightness < 5 or mean_brightness > 250:
        return False, f"Image appears blank or corrupted (mean brightness: {mean_brightness:.1f})"
    
    # Check variance (completely uniform images are suspicious)
    variance = np.var(image.astype(np.float32))
    if variance < 10:
        return False, "Image has extremely low variance - may be blank or corrupted"
    
    return True, ""


def validate_file_constraints(filepath: str, max_size_mb: int = 50) -> Tuple[bool, str]:
    """
    Validate file size and format constraints
    
    Args:
        filepath: Path to file
        max_size_mb: Maximum file size in MB
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file exists
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    
    # Check file size
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File too large: {file_size_mb:.1f}MB (maximum: {max_size_mb}MB)"
    
    # Check file extension
    file_ext = os.path.splitext(filepath)[1].lower()
    supported_formats = ['.pdf', '.png', '.jpg', '.jpeg']
    if file_ext not in supported_formats:
        return False, f"Unsupported format: {file_ext} (supported: {', '.join(supported_formats)})"
    
    return True, ""
