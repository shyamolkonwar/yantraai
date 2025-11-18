import os
import uuid
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.deps.auth import get_current_active_user
from app.crud.job import job_crud
from app.models.user import User
from app.models.job import JobStatus
from app.schemas.job import Job, JobCreate, JobUpdate, JobResult, JobSummary
from app.services.storage import StorageService
from app.services.job_queue import enqueue_job

router = APIRouter()


# @router.post("/", response_model=Job)
# async def upload_document(
#     *,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     file: UploadFile = File(...),
#     metadata: str = Form(None)  # Optional JSON metadata
# ) -> Any:
#     """
#     Upload a PDF document for processing
#     """
#     # Validate file type
#     if file.content_type not in settings.ALLOWED_FILE_TYPES:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"File type {file.content_type} not allowed. Only PDF files are supported."
#         )

#     # Validate file size
#     file_size = 0
#     content = await file.read()
#     file_size = len(content)
#     if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
#         )

#     # Create job
#     job_in = JobCreate(original_filename=file.filename)
#     job = job_crud.create(db, obj_in=job_in, user_id=current_user.id)

#     try:
#         print(f"Creating job for user: {current_user.id}")
#         print(f"File content type: {file.content_type}")
#         print(f"File size: {file_size} bytes")

#         # Save file to storage
#         storage = StorageService()
#         file_key = f"jobs/{job.id}/original.pdf"
#         print(f"Uploading to: {file_key}")

#         storage.upload_file_obj(content, file_key)
#         print("Storage upload completed")

#         # Update job with storage path
#         job_update = JobUpdate(storage_path=file_key)
#         job_crud.update(db, db_obj=job, obj_in=job_update)
#         print("Job updated with storage path")

#         # Enqueue job for processing
#         enqueue_job(job.id)
#         print(f"Job enqueued for processing: {job.id}")

#     except Exception as e:
#         # Cleanup on error
#         print(f"Upload failed with error: {e}")
#         import traceback
#         traceback.print_exc()
#         job_crud.delete(db, job_id=job.id)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to upload file: {str(e)}"
#         ) from e

#     return job


@router.get("/", response_model=List[JobSummary])
async def list_jobs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    List user's jobs
    """
    jobs = job_crud.get_multi(db, user_id=current_user.id, skip=skip, limit=limit)
    return jobs


@router.get("/{job_id}", response_model=Job)
async def get_job(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    job_id: str
) -> Any:
    """
    Get job details
    """
    job = job_crud.get_user_job(db, job_id=job_id, user_id=current_user.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job


@router.get("/{job_id}/result", response_model=JobResult)
async def get_job_result(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    job_id: str
) -> Any:
    """
    Get job processing results
    """
    job = job_crud.get_user_job(db, job_id=job_id, user_id=current_user.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if job.status != JobStatus.DONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job processing not completed"
        )

    # Load full job data with relationships
    from app.models.page import Page
    from app.models.region import Region

    pages = db.query(Page).filter(Page.job_id == job_id).all()
    regions = db.query(Region).filter(Region.job_id == job_id).all()

    return JobResult(
        job=job,
        pages=pages,
        regions=regions
    )


@router.get("/{job_id}/redacted")
async def download_redacted_pdf(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    job_id: str
) -> Any:
    """
    Download redacted PDF
    """
    job = job_crud.get_user_job(db, job_id=job_id, user_id=current_user.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if job.status != JobStatus.DONE or not job.redacted_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Redacted PDF not available"
        )

    # Generate signed URL or download from storage
    storage = StorageService()
    file_path = storage.get_file_path(job.redacted_path)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Redacted file not found"
        )

    return FileResponse(
        path=file_path,
        filename=f"redacted_{job.original_filename}",
        media_type="application/pdf"
    )


@router.delete("/{job_id}")
async def delete_job(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    job_id: str
) -> Any:
    """
    Delete a job
    """
    job = job_crud.get_user_job(db, job_id=job_id, user_id=current_user.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Delete job and associated files
    success = job_crud.delete(db, job_id=job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )

    # TODO: Delete files from storage
    storage = StorageService()
    if job.storage_path:
        storage.delete_file(job.storage_path)
    if job.redacted_path:
        storage.delete_file(job.redacted_path)

    return {"message": "Job deleted successfully"}


@router.post("/process", response_model=JobResult)
async def process_document_sync(
    *,
    file: UploadFile = File(...)
) -> Any:
    """
    Process a PDF document synchronously and return structured data
    This endpoint demonstrates the full pipeline as described in backend_phase.txt
    No authentication or database required - pure local processing
    """
    # Validate file type
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Only PDF files are supported."
        )

    # Validate file size
    content = await file.read()
    file_size = len(content)
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
        )

    try:
        # Create a temporary job for processing
        job_id = str(uuid.uuid4())

        # Save file temporarily
        temp_path = os.path.join("/tmp", f"{job_id}.pdf")
        with open(temp_path, 'wb') as f:
            f.write(content)

        # Process the PDF synchronously
        print(f"Processing PDF synchronously: {file.filename}")

        # Convert PDF to images
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(temp_path, dpi=150)  # Lower DPI for faster processing
            print(f"Converted PDF to {len(images)} images")
        except ImportError:
            print("pdf2image not available, using mock data")
            images = []

        # Initialize ML services
        ocr_service = None
        layout_service = None
        text_service = None
        pii_service = None
        trust_service = None

        try:
            from app.services.ocr import OCRService
            ocr_service = OCRService()
        except Exception as e:
            print(f"OCR service not available: {e}")

        try:
            from app.services.layout import LayoutService
            layout_service = LayoutService()
        except Exception as e:
            print(f"Layout service not available: {e}")

        try:
            from app.services.text_normalization import TextNormalizationService
            text_service = TextNormalizationService()
        except Exception as e:
            print(f"Text normalization service not available: {e}")

        try:
            from app.services.pii_detection import PIIDetectionService
            pii_service = PIIDetectionService()
        except Exception as e:
            print(f"PII detection service not available: {e}")

        try:
            from app.services.trust_score import TrustScoreService
            trust_service = TrustScoreService()
        except Exception as e:
            print(f"Trust score service not available: {e}")

        # Process each page
        all_regions = []
        pages_data = []

        for page_num, image in enumerate(images[:2], 1):  # Process max 2 pages for demo
            print(f"Processing page {page_num}")

            # Convert PIL to numpy array for processing
            import numpy as np
            cv_image = np.array(image) if image else np.zeros((842, 595, 3), dtype=np.uint8)

            # Detect layout regions
            regions = []
            if layout_service and layout_service.model_loaded:
                try:
                    regions = layout_service.detect_regions(cv_image)
                    print(f"Detected {len(regions)} regions with LayoutParser")
                except Exception as e:
                    print(f"Layout detection failed: {e}")

            # If no regions detected, create a default text region
            if not regions:
                regions = [{
                    'bbox': [50, 100, cv_image.shape[1] - 50, cv_image.shape[0] - 100],
                    'label': 'text',
                    'confidence': 0.5
                }]
                print("Using fallback region detection")

            page_regions = []

            # Process each region
            for region in regions[:3]:  # Process max 3 regions per page
                x1, y1, x2, y2 = region['bbox']
                cropped_image = cv_image[y1:y2, x1:x2] if len(cv_image.shape) == 3 else cv_image[y1:y2, x1:x2]

                # OCR processing
                raw_text = ""
                ocr_confidence = 0.0

                if ocr_service and ocr_service.model_loaded:
                    try:
                        ocr_result = ocr_service.extract_text(cropped_image, region.get('label', 'text'))
                        raw_text = ocr_result['text']
                        ocr_confidence = ocr_result['confidence']
                        print(f"OCR extracted: {raw_text[:50]}...")
                    except Exception as e:
                        print(f"OCR failed: {e}")
                else:
                    # Mock OCR result
                    raw_text = f"Sample text from region at ({x1}, {y1})"
                    ocr_confidence = 0.8

                # Text normalization
                normalized_text = raw_text
                translation_confidence = 1.0

                if text_service:
                    try:
                        norm_result = text_service.normalize_text(raw_text)
                        normalized_text = norm_result['normalized_text']
                        translation_confidence = norm_result['confidence']
                    except Exception as e:
                        print(f"Text normalization failed: {e}")

                # PII detection
                pii_detected = []
                if pii_service:
                    try:
                        pii_result = pii_service.detect_pii(normalized_text)
                        pii_detected = pii_result['entities']
                        print(f"Detected {len(pii_detected)} PII entities")
                    except Exception as e:
                        print(f"PII detection failed: {e}")

                # Calculate trust score
                trust_score = 0.8  # Default
                if trust_service:
                    try:
                        trust_score = trust_service.calculate_trust_score({
                            'ocr_confidence': ocr_confidence,
                            'translation_confidence': translation_confidence,
                            'pii_confidence': max([e.get('confidence', 0) for e in pii_detected], default=1.0),
                            'layout_confidence': region.get('confidence', 0.8)
                        })
                    except Exception as e:
                        print(f"Trust score calculation failed: {e}")

                region_data = {
                    "id": str(uuid.uuid4()),
                    "job_id": job_id,
                    "page_id": str(uuid.uuid4()),
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "label": region.get('label', 'text'),
                    "raw_text": raw_text,
                    "ocr_confidence": ocr_confidence,
                    "normalized_text": normalized_text,
                    "translation_confidence": translation_confidence,
                    "pii_detected": pii_detected,
                    "trust_score": trust_score,
                    "human_verified": False,
                    "created_at": "2025-11-18T06:26:15Z",
                    "updated_at": "2025-11-18T06:26:15Z"
                }
                page_regions.append(region_data)

            pages_data.append({
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "page_number": page_num,
                "width": cv_image.shape[1] if len(cv_image.shape) >= 2 else 595,
                "height": cv_image.shape[0] if len(cv_image.shape) >= 1 else 842,
                "image_path": f"jobs/{job_id}/page_{page_num}.png"
            })

            all_regions.extend(page_regions)

        # Prepare results
        results = {
            "job": {
                "id": job_id,
                "user_id": "test-user-12345",  # Mock user ID
                "original_filename": file.filename,
                "status": "done",
                "storage_path": f"jobs/{job_id}/original.pdf",
                "redacted_path": None,
                "created_at": "2025-11-18T06:26:00Z",
                "updated_at": "2025-11-18T06:26:30Z"
            },
            "pages": [
                {
                    **page,
                    "created_at": "2025-11-18T06:26:15Z",
                    "updated_at": "2025-11-18T06:26:15Z"
                }
                for page in pages_data
            ],
            "regions": [
                {
                    **region,
                    "updated_at": region.get("updated_at", "2025-11-18T06:26:15Z")
                }
                for region in all_regions
            ]
        }

        # Clean up temporary file
        os.unlink(temp_path)

        print(f"PDF processing completed for: {file.filename}")
        print(f"Processed {len(pages_data)} pages with {len(all_regions)} regions")
        if all_regions:
            avg_trust = sum(r['trust_score'] for r in all_regions) / len(all_regions)
            print(f"Average trust score: {avg_trust:.2f}")

        return results

    except Exception as e:
        print(f"Processing failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )
