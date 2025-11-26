# Import from main schemas file for backward compatibility
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class BoundingBox(BaseModel):
    """Bounding box coordinates (xyxy format)"""
    x1: int
    y1: int
    x2: int
    y2: int
    
    class Config:
        arbitrary_types_allowed = True


class Region(BaseModel):
    """Region detected in document"""
    region_id: str
    page_number: int
    bbox: BoundingBox
    confidence: float
    class_id: int
    class_name: str
    
    class Config:
        arbitrary_types_allowed = True


class CroppedRegion(BaseModel):
    """Cropped region with image data"""
    region_type: str
    bbox: List[int]
    confidence: float
    page_num: int
    cropped_image: Any  # numpy array
    
    class Config:
        arbitrary_types_allowed = True


class KIngestResult(BaseModel):
    """Result from K-Ingest pipeline"""
    num_pages: int
    regions: List[Region]
    processing_time_ms: float
    
    class Config:
        arbitrary_types_allowed = True


class DocumentUpload(BaseModel):
    """Document upload schema"""
    filename: str
    content_type: str


# Try to import from main schemas if available
try:
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, parent_dir)
    from schemas import *
except:
    pass
