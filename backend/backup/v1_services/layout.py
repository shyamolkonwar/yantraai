import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
import layoutparser as lp


class LayoutService:
    def __init__(self):
        self.model_loaded = False
        try:
            # Import layoutparser
            import layoutparser as lp

            print("Loading LayoutParser PubLayNet model...")

            # Initialize layout detection model with PubLayNet
            # Using the standard PubLayNet model with 0.25 confidence threshold
            self.model = lp.AutoLayoutModel(
                "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x",
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.25]
            )
            self.model_loaded = True
            print("LayoutParser PubLayNet model loaded successfully")
        except ImportError as e:
            print(f"LayoutParser not available: {e}")
            self.model_loaded = False
        except Exception as e:
            print(f"Failed to load layout model: {e}")
            import traceback
            traceback.print_exc()
            self.model_loaded = False

    def detect_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect layout regions in the image
        """
        if not self.model_loaded or self.model is None:
            return self._detect_regions_fallback(image)

        try:
            # Validate input image
            if image is None or image.size == 0:
                print("ERROR: Invalid input image to detect_regions - image is None or empty")
                return self._detect_regions_fallback(image)
            
            if len(image.shape) < 2:
                print(f"ERROR: Invalid image shape: {image.shape}")
                return self._detect_regions_fallback(image)
            
            height, width = image.shape[:2]
            print(f"Layout detection input: {width}x{height}, channels={image.shape[2] if len(image.shape)==3 else 1}, dtype={image.dtype}")
            
            # Convert BGR to RGB
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                print(f"Converted BGR to RGB for LayoutParser")
            else:
                image_rgb = image
                print(f"Using image as-is (grayscale or already RGB)")
            
            # Validate RGB image before passing to model
            if image_rgb is None or image_rgb.size == 0:
                print("ERROR: RGB conversion resulted in None or empty image")
                return self._detect_regions_fallback(image)

            # Detect layout using LayoutParser
            print(f"Calling LayoutParser model.detect() with image shape: {image_rgb.shape}")
            layout = self.model.detect(image_rgb)
            print(f"LayoutParser returned {len(layout)} regions")

            regions = []
            for block in layout:
                # Convert layoutparser block to our format
                x1, y1, x2, y2 = block.coordinates
                label = self._map_layout_label(block.type)
                confidence = block.score

                regions.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'label': label,
                    'confidence': float(confidence)
                })

            # If no regions detected, use fallback
            if not regions:
                print("WARNING: No regions detected by LayoutParser, using fallback")
                return self._detect_regions_fallback(image)

            # Post-process regions to merge and filter
            regions = self._postprocess_regions(regions, image.shape[:2])

            return regions

        except Exception as e:
            print(f"Layout detection failed, using fallback: {e}")
            return self._detect_regions_fallback(image)

    def _detect_regions_fallback(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Fallback region detection using basic image processing
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Apply adaptive threshold
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )

            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            regions = []
            height, width = gray.shape

            # Filter contours by area and aspect ratio
            min_area = (width * height) * 0.001  # 0.1% of image area
            max_area = (width * height) * 0.8    # 80% of image area

            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(contour)

                    # Filter by aspect ratio
                    aspect_ratio = w / h
                    if 0.1 < aspect_ratio < 10:  # Reasonable aspect ratios
                        regions.append({
                            'bbox': [x, y, x + w, y + h],
                            'label': 'text',  # Default label
                            'confidence': 0.5  # Lower confidence for fallback
                        })

            return regions

        except Exception as e:
            print(f"Fallback region detection failed: {e}")
            # Return the entire image as a single region
            height, width = image.shape[:2]
            return [{
                'bbox': [0, 0, width, height],
                'label': 'text',
                'confidence': 0.1
            }]

    def _map_layout_label(self, layout_label: str) -> str:
        """
        Map layoutparser labels to our internal labels
        """
        label_mapping = {
            'Text': 'text',
            'Title': 'header',
            'List': 'text',
            'Table': 'table',
            'Figure': 'image',
            'Caption': 'text',
            'Footer': 'text',
            'Header': 'header',
            'Reference': 'text'
        }

        return label_mapping.get(layout_label, 'text')

    def detect_tables(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Specifically detect table regions
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Use morphological operations to detect table structure
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
            refined = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(refined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            tables = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area_ratio = cv2.contourArea(contour) / (w * h)

                # Table regions typically have high density
                if area_ratio > 0.7 and w > 100 and h > 50:
                    tables.append({
                        'bbox': [x, y, x + w, y + h],
                        'label': 'table',
                        'confidence': 0.7
                    })

            return tables

        except Exception as e:
            print(f"Table detection failed: {e}")
            return []

    def _postprocess_regions(self, regions: List[Dict[str, Any]], image_size: Tuple[int, int]) -> List[Dict[str, Any]]:
        """
        Post-process layout regions to merge nearby boxes and filter tiny fragments
        """
        if not regions:
            return regions

        height, width = image_size
        min_area_px = max(2000, int(width * height * 0.001))  # Minimum area: 2000px or 0.1% of image
        merge_gap_px = max(10, int(min(width, height) * 0.01))  # 1% of smaller dimension

        # Filter out tiny regions
        filtered_regions = []
        for region in regions:
            x1, y1, x2, y2 = region['bbox']
            area = (x2 - x1) * (y2 - y1)
            if area >= min_area_px:
                filtered_regions.append(region)

        if len(filtered_regions) <= 1:
            return filtered_regions

        # Sort by y-coordinate (top to bottom)
        filtered_regions.sort(key=lambda r: r['bbox'][1])

        # Merge vertically contiguous regions
        merged_regions = []
        current_group = [filtered_regions[0]]

        for region in filtered_regions[1:]:
            prev_region = current_group[-1]
            prev_x1, prev_y1, prev_x2, prev_y2 = prev_region['bbox']
            curr_x1, curr_y1, curr_x2, curr_y2 = region['bbox']

            # Check if regions are vertically contiguous and similar horizontally
            vertical_gap = curr_y1 - prev_y2
            horizontal_overlap = min(prev_x2, curr_x2) - max(prev_x1, curr_x1)
            horizontal_overlap_ratio = horizontal_overlap / (prev_x2 - prev_x1) if (prev_x2 - prev_x1) > 0 else 0

            if vertical_gap <= merge_gap_px and horizontal_overlap_ratio > 0.5:
                # Merge regions
                merged_x1 = min(prev_x1, curr_x1)
                merged_y1 = min(prev_y1, curr_y1)
                merged_x2 = max(prev_x2, curr_x2)
                merged_y2 = max(prev_y2, curr_y2)

                # Use the higher confidence and most common label
                merged_confidence = max(prev_region['confidence'], region['confidence'])
                merged_label = prev_region['label'] if prev_region['confidence'] >= region['confidence'] else region['label']

                merged_region = {
                    'bbox': [merged_x1, merged_y1, merged_x2, merged_y2],
                    'label': merged_label,
                    'confidence': merged_confidence
                }
                current_group[-1] = merged_region
            else:
                # Start new group
                current_group.append(region)

        merged_regions = current_group

        # If we still have too many tiny regions, fall back to projection-based detection
        if len(merged_regions) > 20:  # Arbitrary threshold for "too many"
            print(f"Too many regions detected ({len(merged_regions)}), falling back to projection detection")
            return self._detect_regions_projection(filtered_regions, image_size)

        return merged_regions

    def _detect_regions_projection(self, regions: List[Dict[str, Any]], image_size: Tuple[int, int]) -> List[Dict[str, Any]]:
        """
        Fallback: Use horizontal projection to detect text lines
        """
        try:
            height, width = image_size

            # Group regions by similar y-coordinates (lines)
            lines = []
            sorted_regions = sorted(regions, key=lambda r: r['bbox'][1])  # Sort by y1

            current_line = [sorted_regions[0]]
            line_y_center = (sorted_regions[0]['bbox'][1] + sorted_regions[0]['bbox'][3]) / 2

            for region in sorted_regions[1:]:
                region_y_center = (region['bbox'][1] + region['bbox'][3]) / 2
                if abs(region_y_center - line_y_center) <= 20:  # 20px tolerance for same line
                    current_line.append(region)
                else:
                    # Process current line
                    if current_line:
                        lines.append(self._merge_line_regions(current_line))
                    current_line = [region]
                    line_y_center = region_y_center

            # Process last line
            if current_line:
                lines.append(self._merge_line_regions(current_line))

            return lines

        except Exception as e:
            print(f"Projection-based detection failed: {e}")
            return regions

    def _merge_line_regions(self, line_regions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple regions in the same line into one bounding box
        """
        if not line_regions:
            return None

        if len(line_regions) == 1:
            return line_regions[0]

        # Find overall bounding box
        x1 = min(r['bbox'][0] for r in line_regions)
        y1 = min(r['bbox'][1] for r in line_regions)
        x2 = max(r['bbox'][2] for r in line_regions)
        y2 = max(r['bbox'][3] for r in line_regions)

        # Use highest confidence and most common label
        max_confidence = max(r['confidence'] for r in line_regions)
        labels = [r['label'] for r in line_regions]
        most_common_label = max(set(labels), key=labels.count)

        return {
            'bbox': [x1, y1, x2, y2],
            'label': most_common_label,
            'confidence': max_confidence
        }
