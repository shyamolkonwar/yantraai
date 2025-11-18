import os
import json
from datetime import datetime

from app.services.ingest import ingest_document
from app.services.ocr import perform_ocr
from app.services.lingua import normalize_text
from app.services.comply import detect_pii
from app.services.eval import calculate_trust_score
from app.services.pdf_redaction import create_redacted_pdf

def process_job(job_id: str, job_dir: str) -> dict:
    # Step A: Convert PDF to images
    pages_dir, page_images = ingest_document(job_id, job_dir)

    fields = []
    region_id_counter = 1

    for page_num, page_image_path in enumerate(page_images, 1):
        # For MVP: treat whole page as one region
        region_id = f"r{region_id_counter}"
        region_id_counter += 1

        # Step C: OCR on whole page
        raw_text, ocr_conf = perform_ocr(page_image_path)

        # Step D: Normalization
        normalized_text, trans_conf = normalize_text(raw_text)

        # Step E: PII detection
        pii_entities = detect_pii(normalized_text)

        # Step F: Trust score
        trust_score = calculate_trust_score(ocr_conf, trans_conf, pii_entities)

        field = {
            "region_id": region_id,
            "page": page_num,
            "bbox": [0, 0, 1000, 1000],  # Placeholder bbox
            "label": "page_text",
            "raw_text": raw_text,
            "ocr_conf": ocr_conf,
            "normalized_text": normalized_text,
            "trans_conf": trans_conf,
            "pii": pii_entities,
            "trust_score": trust_score,
            "human_verified": False,
            "verified_value": None
        }
        fields.append(field)

    # Step G: Create redacted PDF
    create_redacted_pdf(job_id, job_dir, fields)

    # Save result.json
    result = {
        "job_id": job_id,
        "status": "done",
        "pages": len(page_images),
        "fields": fields,
        "created_at": datetime.now().isoformat(),
        "processing_meta": {
            "layout_model": "layoutparser:pubLayNet",
            "ocr_model": "microsoft/trocr-base-printed",
            "lingua_model": "ai4bharat/indictrans"
        }
    }

    result_path = os.path.join(job_dir, "result.json")
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)

    return result
