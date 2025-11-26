import os
import cv2
import numpy as np
from pdf2image import convert_from_path
from typing import List, Tuple

def ingest_document(job_id: str, job_dir: str) -> Tuple[str, List[str]]:
    """
    Ingest PDF document with preprocessing and corruption detection
    """
    pdf_path = os.path.join(job_dir, "original.pdf")
    pages_dir = os.path.join(job_dir, "pages")
    processed_dir = os.path.join(job_dir, "processed")

    os.makedirs(pages_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    # Enforce 300 DPI as per requirements
    dpi_options = [300]
    images = None

    for dpi in dpi_options:
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
            if images and validate_images(images):
                print(f"Successfully rendered PDF at {dpi} DPI")
                break
        except Exception as e:
            print(f"Failed to render at {dpi} DPI: {e}")
            continue

    if not images:
        raise ValueError("Failed to render PDF with any DPI setting")

    page_images = []
    processed_images = []

    for i, image in enumerate(images):
        # Convert PIL to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Validate rendered image for corruption
        if not validate_rendered_image(opencv_image):
            print(f"Warning: Page {i+1} shows signs of corruption, attempting alternative rendering")
            # Try alternative rendering for this specific page
            opencv_image = attempt_alternative_rendering(pdf_path, i)

        # Save original page image
        page_path = os.path.join(pages_dir, f"page_{i+1}.png")
        cv2.imwrite(page_path, opencv_image)
        page_images.append(page_path)

        # Apply preprocessing
        processed_image = preprocess_image(opencv_image)

        # Save processed image
        processed_path = os.path.join(processed_dir, f"page_{i+1}_processed.png")
        cv2.imwrite(processed_path, processed_image)
        processed_images.append(processed_path)

    return pages_dir, processed_images

def validate_images(images):
    """Validate that images are not corrupted"""
    if not images:
        return False

    for img in images:
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        if not validate_rendered_image(cv_img):
            return False
    return True

def validate_rendered_image(image):
    """
    Validate rendered image for corruption patterns
    Check for vertical barcode-like stripes and other artifacts
    """
    if image is None or image.size == 0:
        return False

    height, width = image.shape[:2]

    # Check for extreme aspect ratios (too narrow/wide)
    aspect_ratio = width / height
    if aspect_ratio < 0.1 or aspect_ratio > 10:
        return False

    # Check for vertical stripe patterns (barcode-like corruption)
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Sample vertical strips and check variance
    strip_width = max(1, width // 20)  # 20 strips across width
    high_variance_strips = 0

    for i in range(0, width, strip_width):
        strip = gray[:, i:i+strip_width]
        if strip.size > 0:
            variance = np.var(strip.astype(np.float32))
            # High variance in thin strips may indicate corruption
            if variance > 10000:  # Threshold for corruption detection
                high_variance_strips += 1

    # If more than 30% of strips show high variance, likely corrupted
    if high_variance_strips > len(range(0, width, strip_width)) * 0.3:
        return False

    return True

def attempt_alternative_rendering(pdf_path, page_num):
    """Attempt alternative rendering methods for corrupted pages"""
    try:
        # Try with different settings
        images = convert_from_path(pdf_path, dpi=300, first_page=page_num+1, last_page=page_num+1)
        if images:
            return cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Alternative rendering failed: {e}")

    # Return a placeholder or the original attempt
    raise ValueError(f"Could not render page {page_num+1} without corruption")

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Apply image preprocessing for better OCR and layout detection
    """
    try:
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Deskew the image
        gray = deskew_image(gray)

        # Denoise
        gray = cv2.bilateralFilter(gray, 9, 75, 75)  # Bilateral filter for noise reduction

        # Contrast enhancement with CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # Otsu's Binarization (better for noise removal)
        # First apply GaussianBlur to reduce noise
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Convert back to RGB for layout detection
        processed_rgb = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)

        return processed_rgb

    except Exception as e:
        print(f"Image preprocessing failed: {e}")
        return image

def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Deskew the image to correct rotation
    """
    try:
        # Find all contours
        contours, _ = cv2.findContours(
            cv2.bitwise_not(image), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return image

        # Find the largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Get minimum area rectangle
        rect = cv2.minAreaRect(largest_contour)
        angle = rect[2]

        # Correct angle if needed
        if angle < -45:
            angle = 90 + angle

        # Rotate the image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h),
                                flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)

        return rotated

    except Exception as e:
        print(f"Deskewing failed: {e}")
        return image
