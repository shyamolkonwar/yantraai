"""
Orchestrator V2 - Document Processing Pipeline
Uses K-Ingest, K-OCR, K-Lingua, and K-Eval modules
"""

import os
import json
import time
import fitz  # PyMuPDF
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from app.services.k_ingest import KIngestPipeline
from app.services.k_ocr import MultiTrackOCRPipeline
from app.services.k_lingua import KLinguaPipeline
from app.services.k_eval import KEvalPipeline
from app.services.pii_detection import PIIDetectionService
from app.services.pdf_redaction import create_redacted_pdf


class DocumentProcessorV2:
    """
    V2 Document Processor using modular pipeline architecture
    """
    
    def __init__(self):
        """Initialize all pipeline modules"""
        self.k_ingest = KIngestPipeline(config_path="config/k_ingest_config.yaml")
        self.k_ocr = MultiTrackOCRPipeline(config_path="config/k_ocr_config.yaml")
        self.k_lingua = KLinguaPipeline(config_path="config/k_lingua_config.yaml")
        self.k_eval = KEvalPipeline(config_path="config/k_eval_config.yaml")
        self.pii_detector = PIIDetectionService()
    
    def process_document(self, pdf_path: str, job_id: str, job_dir: str) -> Dict[str, Any]:
        """
        Process document through complete V2 pipeline
        
        Args:
            pdf_path: Path to PDF file
            job_id: Unique job identifier
            job_dir: Job directory for outputs
            
        Returns:
            Processing result dictionary
        """
        start_time = time.time()
        
        print(f"🚀 [V2] Processing job {job_id}")
        
        # Stage 1: K-Ingest - Layout Detection & Region Extraction
        print("📄 Stage 1: K-Ingest - Layout Detection")
        ingest_result = self.k_ingest.process(pdf_path)
        
        print(f"  ✓ Detected {len(ingest_result.regions)} regions across {ingest_result.num_pages} page(s)")
        
        # Load PDF for region extraction
        doc = fitz.open(pdf_path)
        page = doc[0]  # Process first page
        pix = page.get_pixmap(dpi=300)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:  # RGBA to RGB
            img_array = img_array[:, :, :3]
        
        # Stage 2: K-OCR - Text Recognition
        print("🔍 Stage 2: K-OCR - Text Recognition")
        ocr_results = []
        
        for i, region in enumerate(ingest_result.regions, 1):
            # Extract cropped region
            x1, y1, x2, y2 = region.bbox.x1, region.bbox.y1, region.bbox.x2, region.bbox.y2
            cropped = img_array[y1:y2, x1:x2]
            
            if cropped.size == 0:
                continue
            
            # Run OCR
            ocr_result = self.k_ocr.process_region(
                image=cropped,
                region_id=region.region_id
            )
            
            ocr_results.append({
                'region_id': region.region_id,
                'page': region.page_number,
                'bbox': [x1, y1, x2, y2],
                'label': region.class_name,
                'raw_text': ocr_result['raw_text'],
                'text': ocr_result['text'],
                'ocr_conf': ocr_result['confidence'],
                'trust_score': ocr_result['trust_score'],
                'model_used': ocr_result['model_used'],
                'text_type': ocr_result['text_type']
            })
        
        print(f"  ✓ Extracted text from {len(ocr_results)} regions")
        
        # Stage 3: K-Lingua - Language Understanding & Normalization
        print("🌐 Stage 3: K-Lingua - Language Understanding")
        lingua_results = []
        
        for ocr_result in ocr_results:
            lingua_result = self.k_lingua.process_text(
                text=ocr_result['text'],
                ocr_confidence=ocr_result['ocr_conf'],
                domain="medical",
                region_id=ocr_result['region_id']
            )
            
            # Detect PII
            pii_result = self.pii_detector.detect_pii(lingua_result['normalized_text'])
            pii_entities = self._transform_pii_entities(pii_result.get('entities', []))
            
            lingua_results.append({
                'region_id': ocr_result['region_id'],
                'page': ocr_result['page'],
                'bbox': ocr_result['bbox'],
                'label': ocr_result['label'],
                'raw_text': ocr_result['raw_text'],
                'normalized_text': lingua_result['normalized_text'],
                'language': lingua_result['language'],
                'language_confidence': lingua_result['language_confidence'],
                'ocr_conf': ocr_result['ocr_conf'],
                'trans_conf': lingua_result['confidence_score'],
                'pii': pii_entities,
                'trust_score': ocr_result['trust_score'],
                'human_verified': False,
                'verified_value': None
            })
        
        print(f"  ✓ Processed {len(lingua_results)} texts")
        
        # Stage 4: K-Eval - Confidence Scoring & Review Routing
        print("⚖️  Stage 4: K-Eval - Confidence Scoring")
        
        # Calculate average confidences
        avg_ocr_conf = np.mean([r['ocr_conf'] for r in lingua_results]) if lingua_results else 0.0
        avg_lingua_conf = np.mean([r['trans_conf'] for r in lingua_results]) if lingua_results else 0.0
        
        eval_result = self.k_eval.score_and_route(
            ocr_confidence=float(avg_ocr_conf),
            lingua_confidence=float(avg_lingua_conf),
            comply_confidence=0.9  # Placeholder for K-Comply
        )
        
        print(f"  ✓ Final Confidence: {eval_result['final_confidence']:.3f}")
        print(f"  ✓ Review Action: {eval_result['review_action']}")
        
        # Create redacted PDF
        create_redacted_pdf(job_id, job_dir, lingua_results)
        
        # Compile final result
        total_time = (time.time() - start_time) * 1000
        
        result = {
            "job_id": job_id,
            "status": "done",
            "pages": ingest_result.num_pages,
            "fields": lingua_results,
            "created_at": datetime.now().isoformat(),
            "processing_meta": {
                "layout_model": "DocLayout-YOLO",
                "ocr_model": "TrOCR (multi-track)",
                "lingua_model": "IndicBERT",
                "eval_model": "K-Eval ensemble"
            },
            "confidence_metrics": {
                "avg_ocr_confidence": float(avg_ocr_conf),
                "avg_lingua_confidence": float(avg_lingua_conf),
                "final_confidence": eval_result['final_confidence'],
                "review_action": eval_result['review_action'],
                "needs_review": eval_result['needs_review']
            },
            "processing_time_ms": total_time
        }
        
        # Save result
        result_path = os.path.join(job_dir, "result.json")
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        doc.close()
        
        print(f"✅ [V2] Processing complete in {total_time:.0f}ms")
        
        return result
    
    def _transform_pii_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform PII entities to match schema"""
        transformed = []
        for entity in entities:
            transformed.append({
                'type': entity.get('entity_type', 'unknown'),
                'span': [entity.get('start', 0), entity.get('end', 0)],
                'confidence': entity.get('confidence', 0.0)
            })
        return transformed


def process_job(job_id: str, job_dir: str) -> dict:
    """
    Main entry point for document processing (V2)
    
    Args:
        job_id: Unique job identifier
        job_dir: Job directory containing original.pdf
        
    Returns:
        Processing result dictionary
    """
    pdf_path = os.path.join(job_dir, "original.pdf")
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    processor = DocumentProcessorV2()
    return processor.process_document(pdf_path, job_id, job_dir)
