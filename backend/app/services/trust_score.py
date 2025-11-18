from typing import Dict, Any, List
import numpy as np


class TrustScoreService:
    def __init__(self):
        # Weight configuration for different confidence sources
        # These weights can be tuned based on empirical data
        self.weights = {
            'ocr_confidence': 0.5,      # OCR quality is most important
            'translation_confidence': 0.25,  # Text normalization/transliteration
            'pii_confidence': 0.15,      # PII detection confidence
            'layout_confidence': 0.10    # Layout detection quality
        }

        # Minimum thresholds for each component
        self.thresholds = {
            'ocr_confidence': 0.3,
            'translation_confidence': 0.4,
            'pii_confidence': 0.5,
            'layout_confidence': 0.4
        }

        # Confidence penalties for different scenarios
        self.penalties = {
            'handwriting': 0.2,          # Handwritten text is harder to OCR
            'table': 0.1,               # Tables can be challenging
            'low_resolution': 0.3,      # Low quality images
            'multiple_columns': 0.15,   # Complex layouts
            'indic_script': 0.1,        # Indic languages might have lower accuracy
            'mixed_languages': 0.2      # Mixed language content
        }

    def calculate_trust_score(self, confidences: Dict[str, Any]) -> float:
        """
        Calculate overall trust score from component confidences
        """
        try:
            # Extract individual confidence scores
            ocr_conf = confidences.get('ocr_confidence', 0.5)
            translation_conf = confidences.get('translation_confidence', 0.5)
            pii_conf = confidences.get('pii_confidence', 1.0)  # Default to high if no PII
            layout_conf = confidences.get('layout_confidence', 0.8)

            # Apply minimum thresholds
            ocr_conf = max(ocr_conf, self.thresholds['ocr_confidence'])
            translation_conf = max(translation_conf, self.thresholds['translation_confidence'])
            pii_conf = max(pii_conf, self.thresholds['pii_confidence'])
            layout_conf = max(layout_conf, self.thresholds['layout_confidence'])

            # Calculate weighted average
            weighted_score = (
                ocr_conf * self.weights['ocr_confidence'] +
                translation_conf * self.weights['translation_confidence'] +
                pii_conf * self.weights['pii_confidence'] +
                layout_conf * self.weights['layout_confidence']
            )

            # Apply any contextual penalties
            penalties = confidences.get('penalties', [])
            for penalty in penalties:
                if penalty in self.penalties:
                    weighted_score *= (1 - self.penalties[penalty])

            # Ensure score is between 0 and 1
            trust_score = max(0.0, min(1.0, weighted_score))

            return round(trust_score, 3)

        except Exception as e:
            print(f"Trust score calculation failed: {e}")
            return 0.5  # Default to medium confidence

    def calculate_batch_trust_scores(self, confidences_list: List[Dict[str, Any]]) -> List[float]:
        """
        Calculate trust scores for a batch of confidences
        """
        return [self.calculate_trust_score(confidences) for confidences in confidences_list]

    def get_trust_score_distribution(self, trust_scores: List[float]) -> Dict[str, Any]:
        """
        Analyze distribution of trust scores
        """
        if not trust_scores:
            return {}

        scores = np.array(trust_scores)

        return {
            'mean': float(np.mean(scores)),
            'median': float(np.median(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'quartiles': {
                'q1': float(np.percentile(scores, 25)),
                'q2': float(np.percentile(scores, 50)),
                'q3': float(np.percentile(scores, 75))
            },
            'distribution': {
                'low_trust': int(np.sum(scores < 0.3)),
                'medium_trust': int(np.sum((scores >= 0.3) & (scores < 0.7))),
                'high_trust': int(np.sum(scores >= 0.7))
            }
        }

    def should_send_to_review(self, trust_score: float, region_type: str = 'text') -> bool:
        """
        Determine if a region should be sent for human review
        """
        # Different thresholds for different types of content
        review_thresholds = {
            'text': 0.6,
            'handwritten': 0.4,  # Be more lenient with handwriting
            'table': 0.7,        # Be stricter with tables
            'header': 0.5,       # Headers can be more forgiving
            'signature': 0.3     # Signatures are inherently variable
        }

        threshold = review_thresholds.get(region_type, 0.6)
        return trust_score < threshold

    def get_trust_score_explanation(self, trust_score: float, confidences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate human-readable explanation of trust score
        """
        explanation = {
            'overall_score': trust_score,
            'confidence_level': self._get_confidence_level(trust_score),
            'component_scores': {
                'ocr_quality': {
                    'score': confidences.get('ocr_confidence', 0.5),
                    'weight': self.weights['ocr_confidence'],
                    'description': 'Text extraction quality from OCR'
                },
                'text_normalization': {
                    'score': confidences.get('translation_confidence', 0.5),
                    'weight': self.weights['translation_confidence'],
                    'description': 'Text normalization and transliteration quality'
                },
                'pii_detection': {
                    'score': confidences.get('pii_confidence', 1.0),
                    'weight': self.weights['pii_confidence'],
                    'description': 'Confidence in PII detection results'
                },
                'layout_analysis': {
                    'score': confidences.get('layout_confidence', 0.8),
                    'weight': self.weights['layout_confidence'],
                    'description': 'Layout detection and region identification'
                }
            },
            'recommendations': self._get_recommendations(trust_score, confidences)
        }

        return explanation

    def _get_confidence_level(self, score: float) -> str:
        """
        Get confidence level label for score
        """
        if score >= 0.8:
            return 'very_high'
        elif score >= 0.6:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        elif score >= 0.2:
            return 'low'
        else:
            return 'very_low'

    def _get_recommendations(self, trust_score: float, confidences: Dict[str, Any]) -> List[str]:
        """
        Get recommendations based on trust score and component confidences
        """
        recommendations = []

        if trust_score < 0.3:
            recommendations.append("Low trust score - manual review recommended")
        elif trust_score < 0.6:
            recommendations.append("Medium trust score - consider human verification")

        # Specific component recommendations
        ocr_conf = confidences.get('ocr_confidence', 0.5)
        if ocr_conf < 0.4:
            recommendations.append("Low OCR confidence - check image quality")

        translation_conf = confidences.get('translation_confidence', 0.5)
        if translation_conf < 0.4:
            recommendations.append("Low normalization confidence - verify text processing")

        layout_conf = confidences.get('layout_confidence', 0.5)
        if layout_conf < 0.4:
            recommendations.append("Layout detection issues - review region boundaries")

        return recommendations

    def update_weights(self, new_weights: Dict[str, float]):
        """
        Update confidence weights based on feedback or training
        """
        # Normalize weights to sum to 1
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            for key in self.weights:
                if key in new_weights:
                    self.weights[key] = new_weights[key] / total_weight

    def calibrate_thresholds(self, calibration_data: List[Dict[str, Any]]):
        """
        Calibrate thresholds based on historical accuracy data
        """
        # This would typically use machine learning to optimize thresholds
        # For now, provide a simple heuristic approach
        for component in self.thresholds:
            accuracies = [item.get(f'{component}_accuracy', 0.5) for item in calibration_data]
            if accuracies:
                avg_accuracy = sum(accuracies) / len(accuracies)
                # Set threshold slightly below average accuracy
                self.thresholds[component] = max(0.1, avg_accuracy - 0.1)