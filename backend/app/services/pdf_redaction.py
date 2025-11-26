import os
import json
from typing import List, Dict, Any
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black
from io import BytesIO

def create_redacted_pdf(job_id: str, job_dir: str, fields: List[Dict[str, Any]]):
    """
    Create redacted PDF with PII areas blacked out
    """
    original_pdf_path = os.path.join(job_dir, "original.pdf")
    redacted_pdf_path = os.path.join(job_dir, "redacted.pdf")
    audit_path = os.path.join(job_dir, "audit.jsonl")

    try:
        # For now, create a simple redaction by copying the original
        # TODO: Implement proper PDF redaction with overlays
        with open(original_pdf_path, "rb") as f:
            pdf_data = f.read()
        with open(redacted_pdf_path, "wb") as f:
            f.write(pdf_data)

        # Collect audit metadata for PII that would be redacted
        redaction_metadata = []
        for field in fields:
            if field.get('pii'):
                for pii_entity in field['pii']:
                    if pii_entity.get('confidence', 0) > 0.6:  # Only audit high-confidence PII
                        redaction_metadata.append({
                            'job_id': job_id,
                            'region_id': field['region_id'],
                            'page': field.get('page', 1),
                            'bbox': field.get('bbox', []),
                            'entity_type': pii_entity.get('type', 'unknown'),
                            'confidence': pii_entity.get('confidence', 0),
                            'original_text_hash': hash(field.get('raw_text', '')) % 1000000,  # Simple hash
                            'redaction_method': 'placeholder'  # Not actually redacted yet
                        })

        # Write audit metadata
        with open(audit_path, 'w') as f:
            for entry in redaction_metadata:
                f.write(json.dumps(entry) + '\n')

        print(f"PDF redaction placeholder created with {len(redaction_metadata)} potential redactions")

    except Exception as e:
        print(f"PDF redaction failed: {e}")
        # Fallback: copy original
        try:
            with open(original_pdf_path, "rb") as f:
                pdf_data = f.read()
            with open(redacted_pdf_path, "wb") as f:
                f.write(pdf_data)
        except Exception as e2:
            print(f"Fallback copy failed: {e2}")

def create_redaction_overlay(fields: List[Dict[str, Any]], page_width: float, page_height: float, page_num: int) -> BytesIO:
    """
    Create PDF overlay with redaction rectangles
    """
    try:
        buffer = BytesIO()

        # Create canvas for overlay
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        for field in fields:
            if not field.get('pii'):
                continue

            bbox = field.get('bbox', [])
            if len(bbox) != 4:
                continue

            # Convert normalized coordinates to actual coordinates
            # Assuming bbox is [x1, y1, x2, y2] in pixels
            x1, y1, x2, y2 = bbox

            # Convert to PDF coordinates (bottom-left origin)
            pdf_x1 = x1
            pdf_y1 = page_height - y2  # Flip Y coordinate
            pdf_width = x2 - x1
            pdf_height = y2 - y1

            # Draw black rectangle for redaction
            c.setFillColor(black)
            c.rect(pdf_x1, pdf_y1, pdf_width, pdf_height, fill=1, stroke=0)

        c.save()
        buffer.seek(0)
        return buffer

    except Exception as e:
        print(f"Failed to create redaction overlay: {e}")
        return None

def get_redaction_metadata(job_id: str, job_dir: str) -> List[Dict[str, Any]]:
    """
    Get redaction audit metadata
    """
    audit_path = os.path.join(job_dir, "audit.jsonl")
    metadata = []

    if os.path.exists(audit_path):
        try:
            with open(audit_path, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    metadata.append(entry)
        except Exception as e:
            print(f"Failed to read audit metadata: {e}")

    return metadata
