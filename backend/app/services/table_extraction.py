import cv2
import numpy as np
from typing import List, Dict, Any, Optional


class TableExtractionService:
    def __init__(self):
        self.camelot_available = False
        self.tabula_available = False

        try:
            import camelot
            self.camelot_available = True
            print("Camelot loaded successfully")
        except ImportError:
            print("Camelot not available, table extraction will be limited")

        try:
            import tabula
            self.tabula_available = True
            print("Tabula loaded successfully")
        except ImportError:
            print("Tabula not available, table extraction will be limited")

    def extract_tables_from_image(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extract tables from image using Camelot/Tabula
        """
        tables = []

        try:
            # Save image temporarily for table extraction tools
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                cv2.imwrite(temp_path, image)

            try:
                # Try Camelot first (better for complex tables)
                if self.camelot_available:
                    tables.extend(self._extract_with_camelot(temp_path))

                # Fallback to Tabula if Camelot fails or not available
                if not tables and self.tabula_available:
                    tables.extend(self._extract_with_tabula(temp_path))

            finally:
                # Clean up temp file
                os.unlink(temp_path)

        except Exception as e:
            print(f"Table extraction from image failed: {e}")

        return tables

    def _extract_with_camelot(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extract tables using Camelot
        """
        tables = []

        try:
            # Camelot works with PDFs, but we can try with images
            # Note: Camelot is primarily designed for PDFs
            # This is a simplified implementation
            tables_data = camelot.read_pdf(image_path, flavor='lattice')

            for table in tables_data:
                df = table.df
                tables.append({
                    'data': df.to_dict('records'),
                    'shape': df.shape,
                    'method': 'camelot',
                    'confidence': 0.8,
                    'bbox': table._bbox if hasattr(table, '_bbox') else None
                })

        except Exception as e:
            print(f"Camelot extraction failed: {e}")

        return tables

    def _extract_with_tabula(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extract tables using Tabula
        """
        tables = []

        try:
            # Tabula also works with PDFs, but we can try with images
            # This is a simplified implementation
            dfs = tabula.read_pdf(image_path, pages='all', multiple_tables=True)

            for df in dfs:
                tables.append({
                    'data': df.to_dict('records'),
                    'shape': df.shape,
                    'method': 'tabula',
                    'confidence': 0.7,
                    'bbox': None  # Tabula doesn't provide bbox info
                })

        except Exception as e:
            print(f"Tabula extraction failed: {e}")

        return tables

    def extract_tables_from_pdf(self, pdf_path: str, page_number: int = None) -> List[Dict[str, Any]]:
        """
        Extract tables directly from PDF (preferred method)
        """
        tables = []

        try:
            # Try Camelot first
            if self.camelot_available:
                tables.extend(self._extract_from_pdf_camelot(pdf_path, page_number))

            # Fallback to Tabula
            if not tables and self.tabula_available:
                tables.extend(self._extract_from_pdf_tabula(pdf_path, page_number))

        except Exception as e:
            print(f"PDF table extraction failed: {e}")

        return tables

    def _extract_from_pdf_camelot(self, pdf_path: str, page_number: int = None) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF using Camelot
        """
        tables = []

        try:
            # Read tables from PDF
            if page_number:
                tables_data = camelot.read_pdf(pdf_path, pages=str(page_number))
            else:
                tables_data = camelot.read_pdf(pdf_path, pages='all')

            for table in tables_data:
                df = table.df
                tables.append({
                    'data': df.to_dict('records'),
                    'shape': df.shape,
                    'method': 'camelot_pdf',
                    'confidence': 0.9,
                    'bbox': table._bbox if hasattr(table, '_bbox') else None,
                    'page': page_number or table.page
                })

        except Exception as e:
            print(f"Camelot PDF extraction failed: {e}")

        return tables

    def _extract_from_pdf_tabula(self, pdf_path: str, page_number: int = None) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF using Tabula
        """
        tables = []

        try:
            # Read tables from PDF
            if page_number:
                dfs = tabula.read_pdf(pdf_path, pages=page_number, multiple_tables=True)
            else:
                dfs = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)

            for i, df in enumerate(dfs):
                tables.append({
                    'data': df.to_dict('records'),
                    'shape': df.shape,
                    'method': 'tabula_pdf',
                    'confidence': 0.8,
                    'bbox': None,
                    'page': page_number or (i + 1)
                })

        except Exception as e:
            print(f"Tabula PDF extraction failed: {e}")

        return tables

    def detect_table_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect table regions in an image using computer vision
        """
        table_regions = []

        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Apply morphological operations to detect table structure
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            height, width = gray.shape

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                aspect_ratio = w / h

                # Filter for table-like regions
                if (area > (width * height * 0.05) and  # At least 5% of image area
                    aspect_ratio > 1.5 and  # Wider than tall
                    w > 100 and h > 50):   # Minimum size

                    table_regions.append({
                        'bbox': [x, y, x + w, y + h],
                        'confidence': 0.6,
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })

        except Exception as e:
            print(f"Table region detection failed: {e}")

        return table_regions

    def merge_table_data(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple table extractions into a single result
        """
        if not tables:
            return {'tables': [], 'summary': {}}

        # For now, return the table with highest confidence
        best_table = max(tables, key=lambda x: x.get('confidence', 0))

        return {
            'tables': tables,
            'best_table': best_table,
            'summary': {
                'total_tables': len(tables),
                'methods_used': list(set(t['method'] for t in tables)),
                'avg_confidence': sum(t.get('confidence', 0) for t in tables) / len(tables)
            }
        }

    def validate_table_structure(self, table_data: Dict[str, Any]) -> bool:
        """
        Validate if extracted data has proper table structure
        """
        try:
            data = table_data.get('data', [])
            if not data:
                return False

            # Check if all rows have similar structure
            if len(data) < 2:
                return False

            first_row_keys = set(data[0].keys())
            for row in data[1:]:
                if set(row.keys()) != first_row_keys:
                    return False

            # Check for minimum content
            total_cells = len(data) * len(first_row_keys)
            non_empty_cells = sum(1 for row in data for cell in row.values() if cell and str(cell).strip())

            # At least 50% of cells should have content
            return (non_empty_cells / total_cells) > 0.5

        except Exception as e:
            print(f"Table validation failed: {e}")
            return False
