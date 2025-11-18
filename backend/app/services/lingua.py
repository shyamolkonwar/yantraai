import re

def normalize_text(text: str) -> tuple:
    # Simple normalization for MVP
    normalized = text.strip()

    # Fix common spacing issues
    normalized = re.sub(r'\s+', ' ', normalized)

    # Normalize dates (basic)
    # TODO: more advanced normalization

    # For now, assume high confidence
    trans_conf = 1.0 if normalized != text else 0.8

    return normalized, trans_conf
