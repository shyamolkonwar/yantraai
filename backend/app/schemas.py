from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class PIIEntity(BaseModel):
    type: str
    span: List[int]
    confidence: float

class Field(BaseModel):
    region_id: str
    page: int
    bbox: List[float]
    label: str
    raw_text: str
    ocr_conf: float
    normalized_text: str
    trans_conf: float
    pii: List[PIIEntity]
    trust_score: float
    human_verified: bool
    verified_value: Optional[str]

class ProcessingMeta(BaseModel):
    layout_model: str
    ocr_model: str
    lingua_model: str

class JobResult(BaseModel):
    job_id: str
    status: str
    pages: int
    fields: List[Field]
    created_at: str
    processing_meta: ProcessingMeta

class JobResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[JobResult]

class ReviewItem(BaseModel):
    job_id: str
    region_id: str
    page: int
    bbox: List[float]
    raw_text: str
    normalized_text: str
    trust_score: float
    pii: List[PIIEntity]

class ReviewCorrection(BaseModel):
    user: str
    verified_value: str
    timestamp: datetime = datetime.now()

# K-Ingest v2.0 Schemas
class BoundingBox(BaseModel):
    """Bounding box coordinates for detected regions"""
    x1: int
    y1: int
    x2: int
    y2: int
    
    @property
    def width(self) -> int:
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        return self.y2 - self.y1
    
    class Config:
        json_schema_extra = {
            "example": {
                "x1": 100,
                "y1": 200,
                "x2": 500,
                "y2": 600
            }
        }

class Region(BaseModel):
    """Detected layout region with metadata"""
    region_id: str
    page_number: int
    bbox: BoundingBox
    confidence: float = Field(ge=0.0, le=1.0)
    class_id: int
    class_name: str
    
    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "region_id": "region_0_1",
                "page_number": 1,
                "bbox": {"x1": 100, "y1": 200, "x2": 500, "y2": 600},
                "confidence": 0.95,
                "class_id": 1,
                "class_name": "Text"
            }
        }

class CroppedRegion(BaseModel):
    """Cropped region with preprocessing metadata"""
    region: Region
    preprocessing_applied: List[str] = []
    rotation_applied: int = 0  # degrees
    
    class Config:
        arbitrary_types_allowed = True

class KIngestResult(BaseModel):
    """Complete K-Ingest pipeline result"""
    job_id: str
    total_pages: int
    total_regions: int
    detected_regions: List[Region]
    metadata: dict = {
        "processing_time_ms": 0,
        "avg_confidence": 0.0,
        "model_version": "doclayout_yolo_base_v1.0"
    }
    
    class Config:
        arbitrary_types_allowed = True
