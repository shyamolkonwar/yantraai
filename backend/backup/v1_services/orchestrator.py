import os
import json
import cv2
from datetime import datetime
from typing import List, Dict, Any

from app.services.ingest import ingest_document
from app.services.layout import LayoutService
from app.services.ocr import perform_ocr_ensemble
from app.services.text_normalization import TextNormalizationService
from app.services.pii_detection import PIIDetectionService
from app.services.trust_score import TrustScoreService
from app.services.pdf_redaction import create_redacted_pdf
from app.services.table_extraction import TableExtractionService

# Demo mode configuration
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

if DEMO_MODE:
    # Import demo pipeline when in demo mode
    import sys
    from pathlib import Path
    # Add demo folder to path to import demo_pipeline
    backend_root = Path(__file__).parent.parent.parent
    demo_dir = backend_root / "demo"
    sys.path.insert(0, str(demo_dir))
    from demo_pipeline import DemoPipeline
    print("🎭 DEMO MODE ENABLED - Using GPT-4o Vision Pipeline")



def process_job(job_id: str, job_dir: str) -> dict:
    """
    Layout-first, region-aware document processing pipeline
    """
    # Check if demo mode is enabled
    if DEMO_MODE:
        return process_job_demo(job_id, job_dir)
    
    # Initialize services
    layout_service = LayoutService()
    text_normalizer = TextNormalizationService()
    pii_detector = PIIDetectionService()
    trust_scorer = TrustScoreService()
    table_extractor = TableExtractionService()

    # Step 1: Ingest & preprocess images
    pages_dir, processed_images = ingest_document(job_id, job_dir)

    # Create regions folder for saving cropped region images
    regions_dir = os.path.join(job_dir, "regions")
    os.makedirs(regions_dir, exist_ok=True)

    fields = []
    region_id_counter = 1

    for page_num, processed_image_path in enumerate(processed_images, 1):
        # Load processed image for layout detection
        processed_image = cv2.imread(processed_image_path)
        
        # Validate image before processing
        if processed_image is None or processed_image.size == 0:
            print(f"ERROR: Invalid image for page {page_num} - image is None or empty")
            continue
        
        if len(processed_image.shape) < 2:
            print(f"ERROR: Invalid image shape for page {page_num}: {processed_image.shape}")
            continue
        
        height, width = processed_image.shape[:2]
        if height == 0 or width == 0:
            print(f"ERROR: Invalid image dimensions for page {page_num}: {width}x{height}")
            continue
        
        print(f"Processing page {page_num}: {width}x{height}, dtype={processed_image.dtype}")
        
        # Step 2: Layout detection - find semantic regions
        regions = layout_service.detect_regions(processed_image)

        # If no regions detected, treat whole page as one region
        if not regions:
            height, width = processed_image.shape[:2]
            regions = [{
                'bbox': [0, 0, width, height],
                'label': 'text',
                'confidence': 0.5
            }]

        for region in regions:
            region_id = f"r{region_id_counter}"
            region_id_counter += 1

            # Crop region from processed image
            x1, y1, x2, y2 = region['bbox']
            region_image = processed_image[y1:y2, x1:x2]

            if region_image.size == 0:
                continue  # Skip empty regions

            # Save cropped region image for debugging/review
            region_filename = f"{region_id}_page{page_num}_{region['label']}.png"
            region_path = os.path.join(regions_dir, region_filename)
            cv2.imwrite(region_path, region_image)

            # Step 3: Per-region language detection
            detected_language = detect_region_language(region_image)

            # Step 4: OCR ensemble with bbox for vertical text detection
            raw_text, ocr_conf = perform_ocr_ensemble(region_image, detected_language, bbox=region['bbox'])

            # Skip empty regions
            if not raw_text.strip():
                continue

            # Step 5: Post-OCR normalization
            normalization_result = text_normalizer.normalize_text(raw_text)
            normalized_text = normalization_result.get('normalized_text', raw_text)
            trans_conf = normalization_result.get('confidence', 0.5)

            # Step 6: PII detection ensemble
            pii_result = pii_detector.detect_pii(normalized_text)
            pii_entities = transform_pii_entities(pii_result.get('entities', []))

            # Step 7: Handle tables if detected
            if region['label'] == 'table':
                table_data = table_extractor.extract_tables_from_image(region_image)
                if table_data:
                    # Convert table to structured text
                    normalized_text = format_table_as_text(table_data)
                    trans_conf = 0.8  # Higher confidence for structured extraction

            # Step 8: Trust score calculation
            confidences = {
                'ocr_confidence': ocr_conf,
                'translation_confidence': trans_conf,
                'pii_confidence': pii_result.get('total_confidence', 1.0),
                'layout_confidence': region['confidence']
            }

            # Add penalties for certain conditions
            penalties = []
            if detected_language != 'english':
                penalties.append('indic_script')
            if region['label'] == 'handwritten':
                penalties.append('handwriting')
            if region['label'] == 'table':
                penalties.append('table')

            confidences['penalties'] = penalties

            trust_score = trust_scorer.calculate_trust_score(confidences)

            field = {
                "region_id": region_id,
                "page": page_num,
                "bbox": region['bbox'],
                "label": region['label'],
                "detected_language": detected_language,
                "raw_text": raw_text,
                "ocr_conf": ocr_conf,
                "normalized_text": normalized_text,
                "trans_conf": trans_conf,
                "pii": pii_entities,
                "trust_score": trust_score,
                "human_verified": False,
                "verified_value": None,
                "layout_conf": region['confidence']
            }
            fields.append(field)

    # Step 9: Create redacted PDF
    create_redacted_pdf(job_id, job_dir, fields)

    # Save result.json
    result = {
        "job_id": job_id,
        "status": "done",
        "pages": len(processed_images),
        "fields": fields,
        "created_at": datetime.now().isoformat(),
        "processing_meta": {
            "layout_model": "layoutparser:pubLayNet",
            "ocr_model": "microsoft/trocr-base-printed,easyocr",
            "lingua_model": "ai4bharat/indictrans"
        }
    }

    result_path = os.path.join(job_dir, "result.json")
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)

    return result

def detect_region_language(region_image: cv2.Mat) -> str:
    """
    Detect language of a region based on script presence
    """
    try:
        # Convert to grayscale and threshold
        if len(region_image.shape) == 3:
            gray = cv2.cvtColor(region_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = region_image

        # Simple approach: sample pixels and check for Devanagari unicode
        # In practice, you'd use a proper language detection model
        height, width = gray.shape

        # Sample some text regions (this is a simplified implementation)
        sample_text = ""

        # For now, default to English and let the OCR ensemble decide
        # A proper implementation would use fastText or similar
        return "english"

    except Exception as e:
        print(f"Language detection failed: {e}")
        return "english"

def format_table_as_text(table_data: Dict[str, Any]) -> str:
    """
    Format extracted table data as readable text
    """
    if not table_data or 'tables' not in table_data:
        return ""

    formatted_text = ""
    for table in table_data['tables']:
        if 'data' in table:
            for row in table['data']:
                formatted_text += " | ".join(str(cell) for cell in row) + "\n"
        formatted_text += "\n"

    return formatted_text.strip()

def transform_pii_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform PII entities to match the expected schema
    """
    transformed = []
    for entity in entities:
        transformed.append({
            'type': entity.get('entity_type', 'unknown'),
            'span': [entity.get('start', 0), entity.get('end', 0)],
            'confidence': entity.get('confidence', 0.0)
        })
    return transformed


def process_job_demo(job_id: str, job_dir: str) -> dict:
    """
    Demo mode processing using GPT-4o Vision
    This bypasses the local OCR pipeline and uses OpenAI's API
    """
    print(f"🎭 Processing job {job_id} in DEMO MODE")
    
    # Step 1: Ingest & preprocess images
    pages_dir, processed_images = ingest_document(job_id, job_dir)
    
    if not processed_images:
        raise ValueError("No images found to process")
    
    # Initialize demo pipeline
    demo_pipeline = DemoPipeline()
    
    # For demo, we'll process the first image (or combine multiple if needed)
    # Most demos will be single-page documents
    first_image = processed_images[0]
    
    print(f"📄 Processing image: {first_image}")
    
    # Process with GPT-4o Vision
    result = demo_pipeline.process_document(first_image, job_id=job_id)
    
    # Save result to job directory
    result_path = os.path.join(job_dir, "result.json")
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Demo processing complete for job {job_id}")
    
    # Optionally create a redacted PDF if PII was detected
    # (This would require implementing a simple redaction based on the demo result)
    # For now, we'll skip this in demo mode
    
    return result

