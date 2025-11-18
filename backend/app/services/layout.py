import cv2
import numpy as np
from typing import List, Dict, Any
import layoutparser as lp


class LayoutService:
    def __init__(self):
        self.model_loaded = False
        try:
            # Try to import layoutparser
            import layoutparser as lp

            # Initialize layout detection model
            # Using a general model for document layout detection
            self.model = lp.AutoLayoutModel(
                "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x",
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8]
            )
            self.model_loaded = True
            print("LayoutParser model loaded successfully")
        except ImportError as e:
            print(f"LayoutParser not available: {e}")
            self.model_loaded = False
        except Exception as e:
            print(f"Failed to load layout model: {e}")
            self.model_loaded = False

    def detect_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect layout regions in the image
        """
        if not self.model_loaded:
            return self._detect_regions_fallback(image)

        try:
            # Convert BGR to RGB for layoutparser
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image

            # Detect layout
            layout = self.model.detect(image_rgb)

            regions = []
            for block in layout:
                # Convert layoutparser block to our format
                x1, y1, x2, y2 = block.coordinates
                label = self._map_layout_label(block.type)
                confidence = block.score

                regions.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'label': label,
                    'confidence': confidence
                })

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
