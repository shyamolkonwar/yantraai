import easyocr

# Initialize reader (global for performance)
reader = easyocr.Reader(['en', 'hi'])  # English and Hindi

def perform_ocr(image_path: str) -> tuple:
    results = reader.readtext(image_path)

    if not results:
        return "", 0.0

    # Combine all text
    texts = [result[1] for result in results]
    confidences = [result[2] for result in results]

    raw_text = " ".join(texts)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    return raw_text, avg_conf
