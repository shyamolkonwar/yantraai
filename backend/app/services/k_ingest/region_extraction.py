"""
K-Ingest v2.0 - Region Extraction Module
Handles smart region cropping and preprocessing
"""

import cv2
import numpy as np
from typing import List, Tuple
from app.schemas import Region, CroppedRegion


def extract_regions(
    image: np.ndarray,
    detections: List[Region],
    context_padding: int = 10,
    min_region_size: Tuple[int, int] = (20, 20)
) -> List[Tuple[np.ndarray, CroppedRegion]]:
    """
    Extract and crop detected regions from image
    
    Args:
        image: RGB uint8 numpy array
        detections: List of detected regions
        context_padding: Padding to add around crops (pixels)
        min_region_size: Minimum (width, height) for valid regions
    
    Returns:
        List of tuples (cropped_image, cropped_region_metadata)
    """
    height, width = image.shape[:2]
    extracted = []
    
    for region in detections:
        # Get bounding box
        bbox = region.bbox
        
        # Validate region size
        if bbox.width < min_region_size[0] or bbox.height < min_region_size[1]:
            continue
        
        # Add context padding
        x1 = max(0, bbox.x1 - context_padding)
        y1 = max(0, bbox.y1 - context_padding)
        x2 = min(width, bbox.x2 + context_padding)
        y2 = min(height, bbox.y2 + context_padding)
        
        # Crop region
        crop = image[y1:y2, x1:x2].copy()
        
        # Apply region-specific preprocessing
        processed_crop, preprocessing_applied, rotation = apply_region_preprocessing(
            crop,
            region.class_name
        )
        
        # Create cropped region metadata
        cropped_region = CroppedRegion(
            region=region,
            preprocessing_applied=preprocessing_applied,
            rotation_applied=rotation
        )
        
        extracted.append((processed_crop, cropped_region))
    
    return extracted


def apply_region_preprocessing(
    crop: np.ndarray,
    region_type: str
) -> Tuple[np.ndarray, List[str], int]:
    """
    Apply type-specific preprocessing to cropped region
    
    Args:
        crop: RGB uint8 numpy array
        region_type: Type of region (e.g., "Handwritten", "Table", "Text")
    
    Returns:
        Tuple of (processed_crop, preprocessing_steps, rotation_degrees)
    """
    processed = crop.copy()
    preprocessing_steps = []
    rotation = 0
    
    # Handwritten regions: binarization and additional denoising
    if region_type == "Handwritten":
        processed = _preprocess_handwritten(processed)
        preprocessing_steps.extend(["binarization", "denoise"])
    
    # Table regions: grid line enhancement
    elif region_type == "Table":
        processed = _preprocess_table(processed)
        preprocessing_steps.append("grid_enhancement")
    
    # Vertical text detection and rotation
    height, width = processed.shape[:2]
    if height > 2 * width:  # Likely vertical text
        processed = cv2.rotate(processed, cv2.ROTATE_90_CLOCKWISE)
        rotation = 90
        preprocessing_steps.append("rotation_90")
    
    # Add padding for better OCR boundary detection
    processed = add_context_padding(processed, padding_px=10)
    preprocessing_steps.append("padding")
    
    return processed, preprocessing_steps, rotation


def _preprocess_handwritten(crop: np.ndarray) -> np.ndarray:
    """
    Preprocess handwritten regions
    
    Args:
        crop: RGB uint8 numpy array
    
    Returns:
        Preprocessed RGB uint8 numpy array
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
        
        # Additional denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10)
        
        # Binarization using Otsu's method
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to RGB
        rgb = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
        
        return rgb
        
    except Exception as e:
        print(f"Handwritten preprocessing failed: {e}")
        return crop


def _preprocess_table(crop: np.ndarray) -> np.ndarray:
    """
    Preprocess table regions
    
    Args:
        crop: RGB uint8 numpy array
    
    Returns:
        Preprocessed RGB uint8 numpy array
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
        
        # Enhance grid lines using morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        enhanced = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Convert back to RGB
        rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
        
        return rgb
        
    except Exception as e:
        print(f"Table preprocessing failed: {e}")
        return crop


def add_context_padding(
    crop: np.ndarray,
    padding_px: int = 10,
    border_color: Tuple[int, int, int] = (255, 255, 255)
) -> np.ndarray:
    """
    Add white padding around crop for better OCR
    
    Args:
        crop: RGB uint8 numpy array
        padding_px: Padding size in pixels
        border_color: RGB color for border
    
    Returns:
        Padded RGB uint8 numpy array
    """
    try:
        padded = cv2.copyMakeBorder(
            crop,
            padding_px,
            padding_px,
            padding_px,
            padding_px,
            cv2.BORDER_CONSTANT,
            value=border_color
        )
        return padded
        
    except Exception as e:
        print(f"Padding failed: {e}")
        return crop


def filter_overlapping_regions(regions: List[Region], iou_threshold: float = 0.5) -> List[Region]:
    """
    Remove overlapping regions using NMS-like approach
    
    Args:
        regions: List of detected regions
        iou_threshold: IOU threshold for considering regions as overlapping
    
    Returns:
        Filtered list of regions
    """
    if len(regions) <= 1:
        return regions
    
    # Sort by confidence (descending)
    sorted_regions = sorted(regions, key=lambda r: r.confidence, reverse=True)
    
    keep = []
    
    for region in sorted_regions:
        # Check if this region overlaps significantly with any kept region
        should_keep = True
        
        for kept_region in keep:
            iou = _calculate_iou(region.bbox, kept_region.bbox)
            if iou > iou_threshold:
                should_keep = False
                break
        
        if should_keep:
            keep.append(region)
    
    return keep


def _calculate_iou(bbox1: 'BoundingBox', bbox2: 'BoundingBox') -> float:
    """
    Calculate Intersection over Union (IOU) between two bounding boxes
    
    Args:
        bbox1: First bounding box
        bbox2: Second bounding box
    
    Returns:
        IOU value (0.0 to 1.0)
    """
    # Calculate intersection
    x1 = max(bbox1.x1, bbox2.x1)
    y1 = max(bbox1.y1, bbox2.y1)
    x2 = min(bbox1.x2, bbox2.x2)
    y2 = min(bbox1.y2, bbox2.y2)
    
    if x2 < x1 or y2 < y1:
        return 0.0
    
    intersection = (x2 - x1) * (y2 - y1)
    
    # Calculate union
    area1 = bbox1.width * bbox1.height
    area2 = bbox2.width * bbox2.height
    union = area1 + area2 - intersection
    
    if union == 0:
        return 0.0
    
    return intersection / union
