import os
from pdf2image import convert_from_path

def ingest_document(job_id: str, job_dir: str) -> tuple:
    pdf_path = os.path.join(job_dir, "original.pdf")
    pages_dir = os.path.join(job_dir, "pages")

    # Convert PDF to images
    images = convert_from_path(pdf_path, dpi=300)

    page_images = []
    for i, image in enumerate(images):
        page_path = os.path.join(pages_dir, f"page_{i+1}.png")
        image.save(page_path, "PNG")
        page_images.append(page_path)

    return pages_dir, page_images
