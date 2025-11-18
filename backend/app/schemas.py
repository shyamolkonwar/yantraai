from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

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
