def calculate_trust_score(ocr_conf: float, trans_conf: float, pii_entities: list) -> float:
    # MVP heuristic aggregator
    base_score = 0.5 * ocr_conf + 0.25 * trans_conf + 0.25 * 0.5  # default for layout/ner

    # If PII detected, ensure minimum threshold
    if pii_entities:
        base_score = max(base_score, 0.6)  # Force review for PII

    return min(base_score, 1.0)
