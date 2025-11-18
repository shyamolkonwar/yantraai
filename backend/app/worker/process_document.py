import os
import uuid
import tempfile
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pdf2image import convert_from_bytes
import cv2
import numpy as np

from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.models.page import Page
from app.models.region import Region
from app.services.storage import StorageService
from app.services.ocr import OCRService
from app.services.layout import LayoutService
from app.services.text_normalization import TextNormalizationService
from app.services.pii_detection import PIIDetectionService
from app.services.trust_score import TrustScoreService
from app.services.pdf_redaction import PDFRedactionService
from app.services.table_extraction import TableExtractionService
from app.crud.job import job_crud


def process_document_job(job_id: str) -> bool:
    """
    Process a document job through the complete pipeline
    """
    db = SessionLocal()
    try:
        # Get job
        job = job_crud.get(db, job_id=job_id)
        if not job:
            print(f"Job {job_id} not found")
            return False

        # Update job status to processing
        job_crud.update(db, db_obj=job, obj_in={"status": JobStatus.PROCESSING, "progress": "Starting document processing..."})

        # Initialize services
        storage = StorageService()
        ocr_service = OCRService()
        layout_service = LayoutService()
        text_service = TextNormalizationService()
        pii_service = PIIDetectionService()
        trust_service = TrustScoreService()
        redaction_service = PDFRedactionService()
        table_service = TableExtractionService()

        # Download PDF from storage
        pdf_path = os.path.join(tempfile.gettempdir(), f"{job_id}.pdf")
        storage.download_file(job.storage_path, pdf_path)

        # Read PDF bytes
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        # Convert PDF to images
        job_crud.update(db, db_obj=job, obj_in={"progress": "Converting PDF to images..."})
        images = convert_from_bytes(pdf_bytes, dpi=300)

        all_regions = []
        pages_data = []

        # Process each page
        for page_num, image in enumerate(images, 1):
            job_crud.update(db, db_obj=job, obj_in={"progress": f"Processing page {page_num}/{len(images)}..."})

            # Convert PIL image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Detect layout regions
            regions = layout_service.detect_regions(cv_image)

            # Create page record
            page_id = str(uuid.uuid4())
            page = Page(
                id=page_id,
                job_id=job_id,
                page_number=page_num,
                width=image.width,
                height=image.height
            )
            db.add(page)

            page_regions = []

            # Process each region
            for i, region in enumerate(regions):
                # Crop region
                x1, y1, x2, y2 = region['bbox']
                cropped_image = cv_image[y1:y2, x1:x2]
                region_label = region.get('label', 'text')

                # Initialize variables
                raw_text = ""
                ocr_confidence = 0.0
                normalized_text = ""
                translation_confidence = 1.0
                table_data = None

                if region_label == 'table':
                    # Table extraction
                    try:
                        tables = table_service.extract_tables_from_image(cropped_image)
                        if tables:
                            table_data = table_service.merge_table_data(tables)
                            # Convert table data to text representation
                            best_table = table_data.get('best_table', {})
                            if best_table and 'data' in best_table:
                                # Create a simple text representation of the table
                                rows = best_table['data']
                                if rows:
                                    headers = list(rows[0].keys())
                                    table_text = '\t'.join(headers) + '\n'
                                    for row in rows:
                                        table_text += '\t'.join(str(row.get(h, '')) for h in headers) + '\n'
                                    raw_text = table_text.strip()
                                    ocr_confidence = best_table.get('confidence', 0.8)
                    except Exception as e:
                        print(f"Table extraction failed for region {i}: {e}")
                        # Fallback to OCR
                        region_label = 'text'
                else:
                    # OCR processing for text regions
                    ocr_result = ocr_service.extract_text(cropped_image, region_label)
                    raw_text = ocr_result['text']
                    ocr_confidence = ocr_result['confidence']

                # Text normalization (skip for tables or empty text)
                if raw_text and region_label != 'table':
                    norm_result = text_service.normalize_text(raw_text)
                    normalized_text = norm_result['normalized_text']
                    translation_confidence = norm_result['confidence']
                else:
                    normalized_text = raw_text

                # PII detection
                pii_detected = []
                if normalized_text:
                    pii_result = pii_service.detect_pii(normalized_text)
                    pii_detected = pii_result['entities']

                # Calculate trust score
                trust_score = trust_service.calculate_trust_score({
                    'ocr_confidence': ocr_confidence,
                    'translation_confidence': translation_confidence,
                    'pii_confidence': max([e.get('confidence', 0) for e in pii_detected], default=1.0),
                    'layout_confidence': region.get('confidence', 0.8)
                })

                # Create region record
                region_id = str(uuid.uuid4())
                db_region = Region(
                    id=region_id,
                    job_id=job_id,
                    page_id=page_id,
                    bbox={'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
                    label=region_label,
                    raw_text=raw_text,
                    ocr_confidence=ocr_confidence,
                    normalized_text=normalized_text,
                    translation_confidence=translation_confidence,
                    pii_detected=pii_detected,
                    trust_score=trust_score
                )
                db.add(db_region)

                page_regions.append({
                    'id': region_id,
                    'bbox': [x1, y1, x2, y2],
                    'text': normalized_text,
                    'pii_detected': pii_detected,
                    'table_data': table_data
                })

            pages_data.append({
                'page_number': page_num,
                'regions': page_regions
            })

            all_regions.extend(page_regions)

        # Commit all pages and regions
        db.commit()

        # Create redacted PDF
        job_crud.update(db, db_obj=job, obj_in={"progress": "Creating redacted PDF..."})
        redacted_path = redaction_service.create_redacted_pdf(pdf_path, pages_data)
        redacted_storage_path = f"jobs/{job_id}/redacted.pdf"

        # Upload redacted PDF to storage
        storage.upload_file(redacted_path, redacted_storage_path)

        # Clean up temporary files
        os.unlink(pdf_path)
        os.unlink(redacted_path)

        # Update job status to done
        job_crud.update(db, db_obj=job, obj_in={
            "status": JobStatus.DONE,
            "progress": "Processing completed",
            "redacted_path": redacted_storage_path
        })

        print(f"Job {job_id} processed successfully")
        return True

    except Exception as e:
        print(f"Error processing job {job_id}: {str(e)}")
        # Update job status to failed
        job_crud.update(db, db_obj=job, obj_in={
            "status": JobStatus.FAILED,
            "error_message": str(e),
            "progress": "Processing failed"
        })
        return False

    finally:
        db.close()
