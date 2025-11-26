"""
K-Ingest v2.0 - Main Pipeline
Orchestrates the complete document ingestion and layout detection pipeline
"""

import os
import time
import yaml
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

from app.schemas import Region, CroppedRegion, KIngestResult
from . import acquisition
from . import preprocessing
from . import layout_detection
from . import region_extraction
from . import validators


class KIngestPipeline:
    """
    K-Ingest v2.0 Pipeline
    
    Orchestrates document acquisition, preprocessing, layout detection,
    and region extraction with DocLayout-YOLO
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize K-Ingest pipeline
        
        Args:
            config_path: Path to configuration YAML file
        """
        # Load configuration
        if config_path is None:
            config_path = "config/k_ingest_config.yaml"
        
        self.config = self._load_config(config_path)
        
        # Initialize model (lazy loading)
        self.model = None
        self.model_loaded = False
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                return config
            else:
                print(f"Config file not found: {config_path}, using defaults")
                return self._get_default_config()
        except Exception as e:
            print(f"Failed to load config: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            'acquisition': {
                'pdf_dpi': 300,
                'min_resolution': [800, 600],
                'max_file_size_mb': 50
            },
            'preprocessing': {
                'denoise': {'enabled': True, 'h': 10, 'template_window_size': 7, 'search_window_size': 21},
                'deskew': {'enabled': True, 'angle_threshold': 0.5, 'interpolation': 'INTER_CUBIC'},
                'contrast_enhancement': {'enabled': True, 'clip_limit': 2.0, 'tile_grid_size': [8, 8]},
                'padding': {'enabled': True, 'border_size': 10, 'border_color': [255, 255, 255]}
            },
            'layout_detection': {
                'model_path': 'models/layout/doclayout_yolo_base.pt',
                'device': 'cpu',
                'confidence_threshold': 0.25,
                'iou_threshold': 0.45,
                'inference_size': 1024,
                'fp16': False,
                'class_names': {
                    0: "Header", 1: "Text", 2: "Table", 3: "Handwritten",
                    4: "Stamp", 5: "Signature", 6: "Date", 7: "Address",
                    8: "Amount", 9: "Logo", 10: "Footer", 11: "Form-Field"
                }
            },
            'region_extraction': {
                'context_padding': 10,
                'min_region_size': [20, 20]
            },
            'validation': {
                'min_detections': 0,
                'max_detections': 500,
                'enable_quality_checks': True
            }
        }
    
    def _load_model(self):
        """Load DocLayout-YOLO model (lazy loading)"""
        if self.model_loaded:
            return
        
        layout_config = self.config.get('layout_detection', {})
        model_path = layout_config.get('model_path', 'models/layout/doclayout_yolo_base.pt')
        device = layout_config.get('device', 'cpu')
        fp16 = layout_config.get('fp16', False)
        
        try:
            self.model = layout_detection.load_model(model_path, device, fp16)
            self.model_loaded = True
            print(f"Loaded DocLayout-YOLO model from {model_path}")
        except Exception as e:
            print(f"Warning: Failed to load model: {e}")
            print("Layout detection will be skipped")
            self.model = None
            self.model_loaded = False
    
    def process(
        self,
        file_path: str,
        job_id: Optional[str] = None,
        save_debug_images: bool = False
    ) -> KIngestResult:
        """
        Process document through complete K-Ingest pipeline
        
        Args:
            file_path: Path to PDF or image file
            job_id: Optional job ID for tracking
            save_debug_images: Save intermediate images for debugging
        
        Returns:
            KIngestResult with detected regions and metadata
        
        Raises:
            ValueError: If file validation fails
            RuntimeError: If processing fails
        """
        start_time = time.time()
        
        if job_id is None:
            job_id = f"kingest_{int(time.time() * 1000)}"
        
        print(f"[{job_id}] Starting K-Ingest v2.0 processing")
        
        # Stage 1: Validate file constraints
        acq_config = self.config.get('acquisition', {})
        max_size_mb = acq_config.get('max_file_size_mb', 50)
        
        is_valid, error = acquisition.validate_file_constraints(file_path, max_size_mb)
        if not is_valid:
            raise ValueError(f"File validation failed: {error}")
        
        # Stage 2: Acquire document
        print(f"[{job_id}] Acquiring document...")
        dpi = acq_config.get('pdf_dpi', 300)
        original_images = acquisition.acquire_document(file_path, dpi)
        
        print(f"[{job_id}] Acquired {len(original_images)} page(s)")
        
        # Stage 3: Validate image quality
        val_config = self.config.get('validation', {})
        if val_config.get('enable_quality_checks', True):
            min_res = tuple(acq_config.get('min_resolution', [800, 600]))
            for i, img in enumerate(original_images):
                is_valid, error = acquisition.validate_document_quality(img, min_res)
                if not is_valid:
                    print(f"[{job_id}] Warning: Page {i+1} quality check: {error}")
        
        # Stage 4: Preprocess images
        print(f"[{job_id}] Preprocessing images...")
        preprocessed_images = []
        prep_config = self.config.get('preprocessing', {})
        
        for img in original_images:
            preprocessed = preprocessing.preprocess_for_layout(img, config=prep_config)
            preprocessed_images.append(preprocessed)
        
        # Stage 5: Load model (lazy)
        self._load_model()
        
        # Stage 6: Detect layout
        print(f"[{job_id}] Detecting layout...")
        all_regions = []
        layout_config = self.config.get('layout_detection', {})
        
        if self.model is not None:
            for page_num, img in enumerate(preprocessed_images, start=1):
                regions = layout_detection.detect_layout(
                    self.model,
                    img,
                    conf_threshold=layout_config.get('confidence_threshold', 0.25),
                    iou_threshold=layout_config.get('iou_threshold', 0.45),
                    inference_size=layout_config.get('inference_size', 1024),
                    class_names=layout_config.get('class_names')
                )
                
                # Update page numbers
                for region in regions:
                    region.page_number = page_num
                
                # Post-process regions
                regions = layout_detection.post_process_regions(
                    regions,
                    min_confidence=layout_config.get('confidence_threshold', 0.25),
                    sort_by_reading_order=True
                )
                
                all_regions.extend(regions)
                print(f"[{job_id}] Page {page_num}: detected {len(regions)} region(s)")
        else:
            print(f"[{job_id}] Warning: Model not loaded, skipping layout detection")
        
        # Stage 7: Validate layout output
        if val_config.get('enable_quality_checks', True) and len(preprocessed_images) > 0:
            img_shape = preprocessed_images[0].shape[:2]
            is_valid, error = validators.validate_layout_output(
                all_regions,
                img_shape,
                min_detections=val_config.get('min_detections', 0),
                max_detections=val_config.get('max_detections', 500)
            )
            if not is_valid:
                print(f"[{job_id}] Warning: Layout validation: {error}")
        
        # Calculate metadata
        processing_time_ms = (time.time() - start_time) * 1000
        avg_confidence = np.mean([r.confidence for r in all_regions]) if all_regions else 0.0
        
        # Prepare result
        num_pages = len(original_images)
        result = KIngestResult(
            num_pages=num_pages,
            regions=all_regions,
            processing_time_ms=processing_time_ms
        )
        
        print(f"[{job_id}] K-Ingest completed in {processing_time_ms:.0f}ms")
        print(f"[{job_id}] Detected {len(all_regions)} total regions with avg confidence {avg_confidence:.3f}")
        
        return result
    
    def extract_region_crops(
        self,
        images: List[np.ndarray],
        regions: List[Region]
    ) -> List[Tuple[np.ndarray, CroppedRegion]]:
        """
        Extract cropped regions from images
        
        Args:
            images: List of RGB images (one per page)
            regions: List of detected regions
        
        Returns:
            List of (cropped_image, metadata) tuples
        """
        extraction_config = self.config.get('region_extraction', {})
        context_padding = extraction_config.get('context_padding', 10)
        min_region_size = tuple(extraction_config.get('min_region_size', [20, 20]))
        
        all_crops = []
        
        # Group regions by page
        regions_by_page = {}
        for region in regions:
            page_num = region.page_number
            if page_num not in regions_by_page:
                regions_by_page[page_num] = []
            regions_by_page[page_num].append(region)
        
        # Extract crops for each page
        for page_num, page_regions in regions_by_page.items():
            if page_num <= len(images):
                image = images[page_num - 1]  # 1-indexed to 0-indexed
                crops = region_extraction.extract_regions(
                    image,
                    page_regions,
                    context_padding=context_padding,
                    min_region_size=min_region_size
                )
                all_crops.extend(crops)
        
        return all_crops


# Convenience function for backward compatibility
def process_document(file_path: str, config_path: Optional[str] = None) -> KIngestResult:
    """
    Process document using K-Ingest v2.0 pipeline
    
    Args:
        file_path: Path to PDF or image file
        config_path: Optional path to configuration file
    
    Returns:
        KIngestResult with detected regions
    """
    pipeline = KIngestPipeline(config_path)
    return pipeline.process(file_path)
