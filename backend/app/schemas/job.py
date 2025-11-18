from typing import List, Optional, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.job import JobStatus


class JobBase(BaseModel):
    original_filename: str


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    error_message: Optional[str] = None
    progress: Optional[str] = None
    storage_path: Optional[str] = None
    redacted_path: Optional[str] = None


class Job(JobBase):
    id: Union[str, UUID]
    user_id: Union[str, UUID]
    storage_path: Optional[str] = None
    redacted_path: Optional[str] = None
    status: JobStatus
    error_message: Optional[str] = None
    progress: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str  # Convert UUID to string for JSON responses
        }


class JobSummary(BaseModel):
    id: Union[str, UUID]
    original_filename: str
    status: JobStatus
    progress: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str  # Convert UUID to string for JSON responses
        }


class RegionBase(BaseModel):
    bbox: dict
    label: str
    raw_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    normalized_text: Optional[str] = None
    translation_confidence: Optional[float] = None
    pii_detected: Optional[List[dict]] = None
    trust_score: Optional[float] = None
    human_verified: bool = False
    verified_value: Optional[str] = None


class Region(RegionBase):
    id: str
    job_id: str
    page_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PageBase(BaseModel):
    page_number: int
    width: Optional[int] = None
    height: Optional[int] = None


class Page(PageBase):
    id: str
    job_id: str
    image_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobResult(BaseModel):
    job: Job
    pages: List[Page]
    regions: List[Region]

    class Config:
        from_attributes = True


class RegionReview(BaseModel):
    verified_value: Optional[str] = None
    action: str  # approve, correct, skip


class ReviewQueueItem(BaseModel):
    region_id: str
    job_id: str
    job_filename: str
    page_number: int
    bbox: dict
    label: str
    raw_text: Optional[str] = None
    normalized_text: Optional[str] = None
    trust_score: Optional[float] = None
    pii_detected: Optional[List[dict]] = None
