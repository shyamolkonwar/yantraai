import re
from typing import Dict, Any, List
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine



class PIIDetectionService:
    def __init__(self):
        self.presidio_loaded = False
        self.indic_ner_loaded = False

        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            self.presidio_loaded = True
            print("Presidio loaded successfully")
        except ImportError as e:
            print(f"Presidio not available: {e}")
            self.presidio_loaded = False
        except Exception as e:
            print(f"Failed to initialize Presidio: {e}")
            self.presidio_loaded = False

        # Custom regex patterns for Indic languages and specific patterns
        self.custom_patterns = {
            # Indian patterns
            'INDIAN_PAN': {
                'regex': r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
                'confidence': 0.9,
                'description': 'Indian PAN Card number'
            },
            'INDIAN_AADHAR': {
                'regex': r'\b\d{4}\s?\d{4}\s?\d{4}\b',
                'confidence': 0.8,
                'description': 'Indian Aadhar number'
            },
            'INDIAN_PHONE': {
                'regex': r'(\+91[-\s]?)?[6-9]\d{9}',
                'confidence': 0.9,
                'description': 'Indian phone number'
            },
            'INDIAN_PINCODE': {
                'regex': r'\b\d{6}\b',
                'confidence': 0.7,
                'description': 'Indian PIN code'
            },
            'EMAIL': {
                'regex': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'confidence': 0.95,
                'description': 'Email address'
            },
            'CREDIT_CARD': {
                'regex': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                'confidence': 0.9,
                'description': 'Credit card number'
            },
            'SSN': {
                'regex': r'\b\d{3}-\d{2}-\d{4}\b',
                'confidence': 0.9,
                'description': 'Social Security Number'
            },
            # Indic text patterns (simplified)
            'HINDI_NAME': {
                'regex': r'[\u0900-\u097F]{2,}(?:\s[\u0900-\u097F]{2,})+',
                'confidence': 0.5,
                'description': 'Potential Hindi name'
            }
        }

        # Language codes for IndicNER
        self.indic_lang_codes = {
            'hindi': 'hi',
            'bengali': 'bn',
            'tamil': 'ta',
            'telugu': 'te',
            'marathi': 'mr',
            'gujarati': 'gu',
            'kannada': 'kn',
            'punjabi': 'pa',
            'malayalam': 'ml'
        }

    def detect_pii(self, text: str) -> Dict[str, Any]:
        """
        Detect PII in the given text
        """
        if not text or not text.strip():
            return {
                'entities': [],
                'has_pii': False,
                'total_confidence': 0.0
            }

        entities = []

        try:
            # Use Presidio if available
            if self.presidio_loaded:
                entities.extend(self._detect_with_presidio(text))

            # Use IndicNER for Indic languages
            if self.indic_ner_loaded:
                entities.extend(self._detect_with_indic_ner(text))

            # Always use custom patterns for Indian context
            entities.extend(self._detect_with_custom_patterns(text))

            # Remove duplicates and sort by position
            entities = self._deduplicate_entities(entities)

            # Calculate total confidence
            total_confidence = 0.0
            if entities:
                total_confidence = sum(entity['confidence'] for entity in entities) / len(entities)

            return {
                'entities': entities,
                'has_pii': len(entities) > 0,
                'total_confidence': total_confidence,
                'entity_count': len(entities)
            }

        except Exception as e:
            print(f"PII detection failed: {e}")
            return {
                'entities': [],
                'has_pii': False,
                'total_confidence': 0.0,
                'error': str(e)
            }

    def _detect_with_presidio(self, text: str) -> List[Dict[str, Any]]:
        """
        Use Presidio to detect PII entities
        """
        entities = []
        try:
            results = self.analyzer.analyze(
                text=text,
                language='en',
                entities=['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'IBAN_CODE',
                         'CREDIT_CARD', 'IP_ADDRESS', 'LOCATION', 'DATE_TIME',
                         'NRP', 'URL', 'US_SSN', 'UK_NHS', 'IT_FISCAL_CODE']
            )

            for result in results:
                entities.append({
                    'entity_type': result.entity_type,
                    'start': result.start,
                    'end': result.end,
                    'text': text[result.start:result.end],
                    'confidence': result.score,
                    'source': 'presidio'
                })

        except Exception as e:
            print(f"Presidio detection failed: {e}")

        return entities

    def _detect_with_indic_ner(self, text: str) -> List[Dict[str, Any]]:
        """
        Use IndicNER to detect named entities in Indic languages
        """
        entities = []
        try:
            # Detect language (simplified - check for Indic scripts)
            detected_lang = None
            for lang, pattern in self.indic_lang_codes.items():
                if re.search(r'[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F]', text):
                    detected_lang = lang
                    break

            if not detected_lang:
                return entities

            lang_code = self.indic_lang_codes.get(detected_lang, 'hi')

            # Run IndicNER
            ner_results = self.indic_ner.ner(text, lang=lang_code)

            # Process results
            for result in ner_results:
                if result['prediction'] in ['B-PER', 'I-PER', 'B-LOC', 'I-LOC']:  # Person and Location entities
                    entity_type = 'PERSON' if 'PER' in result['prediction'] else 'LOCATION'
                    confidence = result.get('confidence', 0.8)

                    entities.append({
                        'entity_type': entity_type,
                        'start': result['start'],
                        'end': result['end'],
                        'text': text[result['start']:result['end']],
                        'confidence': confidence,
                        'source': 'indic_ner',
                        'language': detected_lang
                    })

        except Exception as e:
            print(f"IndicNER detection failed: {e}")

        return entities

    def _detect_with_custom_patterns(self, text: str) -> List[Dict[str, Any]]:
        """
        Use custom regex patterns to detect PII
        """
        entities = []
        for entity_type, pattern_info in self.custom_patterns.items():
            try:
                matches = re.finditer(
                    pattern_info['regex'],
                    text,
                    re.IGNORECASE | re.MULTILINE
                )

                for match in matches:
                    entities.append({
                        'entity_type': entity_type,
                        'start': match.start(),
                        'end': match.end(),
                        'text': match.group(),
                        'confidence': pattern_info['confidence'],
                        'source': 'custom_regex',
                        'description': pattern_info['description']
                    })

            except Exception as e:
                print(f"Custom pattern {entity_type} failed: {e}")

        return entities

    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate entities and sort by position
        """
        if not entities:
            return entities

        # Sort by start position
        entities.sort(key=lambda x: x['start'])

        # Remove overlapping entities (keep higher confidence ones)
        deduplicated = []
        for entity in entities:
            should_add = True
            for existing in deduplicated:
                # Check if entities overlap
                if (entity['start'] < existing['end'] and
                    entity['end'] > existing['start']):
                    # Keep the one with higher confidence
                    if entity['confidence'] > existing['confidence']:
                        deduplicated.remove(existing)
                    else:
                        should_add = False
                        break

            if should_add:
                deduplicated.append(entity)

        return deduplicated

    def redact_text(self, text: str, entities: List[Dict[str, Any]]) -> str:
        """
        Redact PII entities from text
        """
        if not entities:
            return text

        # Sort entities by start position in reverse order to avoid index shifting
        sorted_entities = sorted(entities, key=lambda x: x['start'], reverse=True)

        redacted_text = text
        for entity in sorted_entities:
            start = entity['start']
            end = entity['end']
            redaction_char = self._get_redaction_char(entity['entity_type'])
            redacted_text = redacted_text[:start] + redaction_char * (end - start) + redacted_text[end:]

        return redacted_text

    def _get_redaction_char(self, entity_type: str) -> str:
        """
        Get appropriate redaction character based on entity type
        """
        if entity_type in ['EMAIL_ADDRESS', 'URL']:
            return '@'
        elif entity_type in ['PHONE_NUMBER', 'INDIAN_PHONE']:
            return '*'
        else:
            return '█'

    def get_redaction_metadata(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate metadata for PDF redaction
        """
        redaction_metadata = []
        for entity in entities:
            if entity['confidence'] > 0.6:  # Only redact high-confidence entities
                redaction_metadata.append({
                    'start': entity['start'],
                    'end': entity['end'],
                    'type': entity['entity_type'],
                    'confidence': entity['confidence'],
                    'redaction_method': 'full'
                })

        return redaction_metadata

    def batch_detect_pii(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Detect PII in multiple texts
        """
        results = []
        for text in texts:
            result = self.detect_pii(text)
            results.append(result)
        return results
