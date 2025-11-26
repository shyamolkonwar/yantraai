from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
import os
import json
from datetime import datetime
from typing import Optional
import uuid

from app.services.orchestrator_v2 import process_job
from app.utils import create_job_folder, save_file_locally, generate_job_id
from pydantic import BaseModel
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

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "jobs")

@router.post("/jobs", response_model=JobResponse)
async def create_job(
    file: UploadFile = File(...),
    process_mode: str = Query("sync", enum=["sync", "async"])
):
    if not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="File must be PDF or image")

    job_id = generate_job_id()
    job_dir = create_job_folder(job_id)

    # Save original file
    file_path = save_file_locally(job_id, file)

    if process_mode == "sync":
        # Process synchronously
        result = process_job(job_id, job_dir)
        return JobResponse(job_id=job_id, status="done", result=result)
    else:
        # For async, we'd enqueue to RQ, but for now, process sync
        result = process_job(job_id, job_dir)
        return JobResponse(job_id=job_id, status="done", result=result)

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job_dir = os.path.join(DATA_DIR, job_id)
    result_path = os.path.join(job_dir, "result.json")

    if not os.path.exists(result_path):
        return {"job_id": job_id, "status": "processing"}

    with open(result_path, 'r') as f:
        result = json.load(f)

    return result

@router.get("/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    job_dir = os.path.join(DATA_DIR, job_id)
    result_path = os.path.join(job_dir, "result.json")

    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Result not found")

    return FileResponse(result_path, media_type='application/json', filename='result.json')

@router.get("/jobs/{job_id}/redacted")
async def get_redacted_pdf(job_id: str):
    job_dir = os.path.join(DATA_DIR, job_id)
    redacted_path = os.path.join(job_dir, "redacted.pdf")

    if not os.path.exists(redacted_path):
        raise HTTPException(status_code=404, detail="Redacted PDF not found")

    return FileResponse(redacted_path, media_type='application/pdf', filename='redacted.pdf')
