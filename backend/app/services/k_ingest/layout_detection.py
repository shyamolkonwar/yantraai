"""
K-Ingest v2.0 - Layout Detection Module
Handles DocLayout-YOLO integration for layout detection
"""

import os
import numpy as np
from typing import List, Optional
from app.schemas import Region, BoundingBox

# YOLO will be imported dynamically to handle missing dependency gracefully
YOLO = None


def load_model(model_path: str, device: str = "cpu", fp16: bool = False):
    """
    Load DocLayout-YOLO model
    
    Args:
        model_path: Path to model weights (.pt file)
        device: Device to run on ("cpu" or "cuda")
        fp16: Use half-precision (FP16) for faster inference
    
    Returns:
        Loaded YOLO model
    
    Raises:
        ImportError: If doclayout_yolo is not installed
        FileNotFoundError: If model file doesn't exist
    """
    global YOLO
    
    # Import YOLO dynamically - try doclayout_yolo first, then ultralytics
    if YOLO is None:
        try:
            from doclayout_yolo import YOLOv10
            YOLO = YOLOv10
            print("Using doclayout_yolo.YOLOv10 for model loading")
        except ImportError:
            try:
                from ultralytics import YOLO as YOLOModel
                YOLO = YOLOModel
                print("Using ultralytics.YOLO for model loading")
            except ImportError:
                raise ImportError(
                    "Neither doclayout_yolo nor ultralytics package found. "
                    "Install with: pip install doclayout_yolo"
                )
    
    # Check model file exists
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load model
    try:
        model = YOLO(model_path)
        
        # Set device
        if hasattr(model, 'to'):
            model.to(device)
        
        # Enable FP16 if requested and on GPU
        if fp16 and device == "cuda" and hasattr(model, 'half'):
            model.half()
        
        return model
        
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {str(e)}")


def detect_layout(
    model,
    image: np.ndarray,
    conf_threshold: float = 0.25,
    iou_threshold: float = 0.45,
    inference_size: int = 1024,
    class_names: dict = None
) -> List[Region]:
    """
    Detect layout regions using DocLayout-YOLO
    
    Args:
        model: Loaded YOLO model
        image: RGB uint8 numpy array
        conf_threshold: Confidence threshold for detections
        iou_threshold: IOU threshold for NMS
        inference_size: Input size for model
        class_names: Dict mapping class IDs to names
    
    Returns:
        List of detected regions
    """
    if class_names is None:
        class_names = _get_default_class_names()
    
    try:
        # Run inference
        results = model.predict(
            image,
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=inference_size,
            verbose=False
        )
        
        # Extract detections
        regions = []
        
        if len(results) > 0:
            result = results[0]  # Single image
            
            # Get boxes, confidences, and classes
            boxes = result.boxes
            
            if boxes is not None and len(boxes) > 0:
                for i, box in enumerate(boxes):
                    # Extract box coordinates (xyxy format)
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # Extract confidence
                    confidence = float(box.conf[0].cpu().numpy())
                    
                    # Extract class
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = class_names.get(class_id, f"Unknown_{class_id}")
                    
                    # Create region
                    region = Region(
                        region_id=f"region_{i}",
                        page_number=1,  # Will be updated by caller
                        bbox=BoundingBox(
                            x1=int(x1),
                            y1=int(y1),
                            x2=int(x2),
                            y2=int(y2)
                        ),
                        confidence=confidence,
                        class_id=class_id,
                        class_name=class_name
                    )
                    
                    regions.append(region)
        
        return regions
        
    except Exception as e:
        print(f"Layout detection failed: {e}")
        return []


def post_process_regions(
    regions: List[Region],
    min_confidence: float = 0.25,
    sort_by_reading_order: bool = True
) -> List[Region]:
    """
    Post-process detected regions
    
    Args:
        regions: List of detected regions
        min_confidence: Minimum confidence threshold
        sort_by_reading_order: Sort by reading order (top-to-bottom, left-to-right)
    
    Returns:
        Filtered and sorted list of regions
    """
    # Filter by confidence
    filtered = [r for r in regions if r.confidence >= min_confidence]
    
    # Sort by reading order if requested
    if sort_by_reading_order:
        filtered = _sort_by_reading_order(filtered)
    
    # Update region IDs after sorting
    for i, region in enumerate(filtered):
        region.region_id = f"region_{region.page_number}_{i}"
    
    return filtered


def _sort_by_reading_order(regions: List[Region]) -> List[Region]:
    """
    Sort regions by reading order (top-to-bottom, left-to-right)
    
    Args:
        regions: List of regions to sort
    
    Returns:
        Sorted list of regions
    """
    # Sort by y1 (top), then by x1 (left)
    sorted_regions = sorted(
        regions,
        key=lambda r: (r.bbox.y1, r.bbox.x1)
    )
    
    return sorted_regions


def _get_default_class_names() -> dict:
    """Get default class names for DocLayout-YOLO"""
    return {
        0: "Header",
        1: "Text",
        2: "Table",
        3: "Handwritten",
        4: "Stamp",
        5: "Signature",
        6: "Date",
        7: "Address",
        8: "Amount",
        9: "Logo",
        10: "Footer",
        11: "Form-Field"
    }


def get_model_info(model) -> dict:
    """
    Get model information
    
    Args:
        model: Loaded YOLO model
    
    Returns:
        Dict with model metadata
    """
    try:
        return {
            "model_type": "DocLayout-YOLO",
            "architecture": model.model.__class__.__name__ if hasattr(model, 'model') else "Unknown",
            "device": str(model.device) if hasattr(model, 'device') else "Unknown",
            "num_classes": len(_get_default_class_names())
        }
    except Exception as e:
        return {
            "model_type": "DocLayout-YOLO",
            "error": str(e)
        }
