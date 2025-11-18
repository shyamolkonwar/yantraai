from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Initialize engines
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def detect_pii(text: str) -> list:
    results = analyzer.analyze(text=text, language='en')

    pii_entities = []
    for result in results:
        pii_entities.append({
            "type": result.entity_type,
            "span": [result.start, result.end],
            "confidence": result.score
        })

    return pii_entities
