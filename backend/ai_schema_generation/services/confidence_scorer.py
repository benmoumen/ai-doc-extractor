"""
T035: ConfidenceScorer
Service for computing and analyzing confidence scores across the AI analysis pipeline
"""

from typing import List, Dict, Any, Optional, Tuple
from statistics import mean, median, stdev
from datetime import datetime
import math

from ..models.analysis_result import AIAnalysisResult
from ..models.extracted_field import ExtractedField
from ..models.validation_rule_inference import ValidationRuleInference
from ..models.document_type_suggestion import DocumentTypeSuggestion
from ..models.generated_schema import GeneratedSchema
from ..storage.analysis_storage import AIAnalysisStorage


class ConfidenceScoringError(Exception):
    """Custom exception for confidence scoring errors"""
    pass


class ConfidenceScorer:
    """Service for advanced confidence scoring and analysis."""

    # Confidence level thresholds
    CONFIDENCE_LEVELS = {
        'very_high': 0.9,
        'high': 0.8,
        'medium': 0.6,
        'low': 0.4,
        'very_low': 0.0
    }

    # Weight factors for different confidence components
    CONFIDENCE_WEIGHTS = {
        'field_extraction': 0.3,
        'document_type': 0.2,
        'validation_rules': 0.2,
        'visual_quality': 0.15,
        'consistency': 0.15
    }

    # Model-specific confidence adjustments
    MODEL_CONFIDENCE_FACTORS = {
        'groq/llama-3.1-70b-versatile': 1.0,
        'mistral/mistral-small-latest': 0.95,
        'gpt-4o-mini': 1.05
    }

    def __init__(self, storage: Optional[AIAnalysisStorage] = None):
        """Initialize confidence scorer"""
        self.storage = storage or AIAnalysisStorage()

    def calculate_comprehensive_confidence(self, analysis_result_id: str) -> Dict[str, Any]:
        """
        Calculate comprehensive confidence score for entire analysis

        Args:
            analysis_result_id: ID of analysis result

        Returns:
            Dictionary with detailed confidence analysis

        Raises:
            ConfidenceScoringError: If scoring fails
        """
        try:
            # Get analysis components
            analysis_result = self.storage.get_analysis_result(analysis_result_id)
            if not analysis_result:
                raise ConfidenceScoringError("Analysis result not found")

            fields = self.storage.get_fields_for_analysis(analysis_result_id)
            doc_type_suggestion = self.storage.get_suggestion_for_analysis(analysis_result_id)

            # Calculate component scores
            field_confidence = self._calculate_field_extraction_confidence(fields)
            document_type_confidence = self._calculate_document_type_confidence(doc_type_suggestion)
            validation_confidence = self._calculate_validation_confidence(fields)
            visual_quality = self._calculate_visual_quality_score(fields)
            consistency_score = self._calculate_consistency_score(fields)

            # Calculate weighted overall confidence
            component_scores = {
                'field_extraction': field_confidence,
                'document_type': document_type_confidence,
                'validation_rules': validation_confidence,
                'visual_quality': visual_quality,
                'consistency': consistency_score
            }

            overall_confidence = sum(
                score * self.CONFIDENCE_WEIGHTS[component]
                for component, score in component_scores.items()
            )

            # Apply model-specific adjustment
            model_factor = self.MODEL_CONFIDENCE_FACTORS.get(analysis_result.model_used, 1.0)
            adjusted_confidence = min(1.0, overall_confidence * model_factor)

            # Determine confidence level
            confidence_level = self._determine_confidence_level(adjusted_confidence)

            # Generate recommendations
            recommendations = self._generate_confidence_recommendations(
                component_scores, adjusted_confidence, fields
            )

            return {
                'overall_confidence': adjusted_confidence,
                'confidence_level': confidence_level,
                'component_scores': component_scores,
                'model_adjustment_factor': model_factor,
                'recommendations': recommendations,
                'field_count': len(fields),
                'high_confidence_fields': sum(1 for f in fields if f.overall_confidence_score >= 0.8),
                'needs_review': adjusted_confidence < 0.6
            }

        except Exception as e:
            raise ConfidenceScoringError(f"Confidence calculation failed: {str(e)}")

    def _calculate_field_extraction_confidence(self, fields: List[ExtractedField]) -> float:
        """Calculate confidence score for field extraction"""
        if not fields:
            return 0.0

        # Collect individual field confidence scores
        field_scores = [field.overall_confidence_score for field in fields]

        # Base score is the mean of field confidences
        base_score = mean(field_scores)

        # Penalty for high variance (inconsistent confidence)
        if len(field_scores) > 1:
            score_variance = stdev(field_scores)
            variance_penalty = min(0.2, score_variance * 0.5)
            base_score -= variance_penalty

        # Bonus for having many fields
        field_count_bonus = min(0.1, len(fields) * 0.01)
        base_score += field_count_bonus

        # Penalty for too many low confidence fields
        low_confidence_fields = sum(1 for score in field_scores if score < 0.4)
        if low_confidence_fields > len(fields) * 0.3:  # More than 30% low confidence
            base_score -= 0.15

        return max(0.0, min(1.0, base_score))

    def _calculate_document_type_confidence(self, doc_type_suggestion: Optional[DocumentTypeSuggestion]) -> float:
        """Calculate confidence score for document type detection"""
        if not doc_type_suggestion:
            return 0.5  # Neutral score if no suggestion

        base_confidence = doc_type_suggestion.type_confidence

        # Bonus for having supporting indicators
        indicator_bonus = min(0.1, len(doc_type_suggestion.key_indicators) * 0.02)
        base_confidence += indicator_bonus

        # Penalty for too many alternative suggestions (indicates uncertainty)
        alternatives_count = len(doc_type_suggestion.alternative_types)
        if alternatives_count > 3:
            alternatives_penalty = min(0.15, (alternatives_count - 3) * 0.03)
            base_confidence -= alternatives_penalty

        # Bonus for template matches
        template_bonus = min(0.05, len(doc_type_suggestion.matched_templates) * 0.02)
        base_confidence += template_bonus

        return max(0.0, min(1.0, base_confidence))

    def _calculate_validation_confidence(self, fields: List[ExtractedField]) -> float:
        """Calculate confidence score for validation rules"""
        if not fields:
            return 0.0

        total_confidence = 0.0
        total_rules = 0

        for field in fields:
            # Get validation rules for this field
            rules = self.storage.get_rules_for_field(field.id)
            if rules:
                # Calculate average rule confidence
                rule_confidences = [rule.confidence_score for rule in rules if rule.is_recommended]
                if rule_confidences:
                    field_validation_confidence = mean(rule_confidences)
                    total_confidence += field_validation_confidence
                    total_rules += 1

        if total_rules == 0:
            return 0.3  # Low score if no validation rules

        average_validation_confidence = total_confidence / total_rules

        # Bonus for having validation rules on most fields
        fields_with_rules = total_rules
        coverage_ratio = fields_with_rules / len(fields)
        coverage_bonus = coverage_ratio * 0.2

        return min(1.0, average_validation_confidence + coverage_bonus)

    def _calculate_visual_quality_score(self, fields: List[ExtractedField]) -> float:
        """Calculate visual quality score based on field clarity"""
        if not fields:
            return 0.0

        # Collect visual clarity scores
        clarity_scores = [
            field.visual_clarity_score for field in fields
            if field.visual_clarity_score > 0
        ]

        if not clarity_scores:
            return 0.5  # Neutral if no visual clarity data

        base_score = mean(clarity_scores)

        # Bonus for consistent visual quality
        if len(clarity_scores) > 1 and stdev(clarity_scores) < 0.2:
            base_score += 0.1

        # Penalty for many fields with poor visual clarity
        poor_clarity_count = sum(1 for score in clarity_scores if score < 0.4)
        if poor_clarity_count > len(clarity_scores) * 0.3:
            base_score -= 0.15

        return max(0.0, min(1.0, base_score))

    def _calculate_consistency_score(self, fields: List[ExtractedField]) -> float:
        """Calculate consistency score across field extractions"""
        if len(fields) < 2:
            return 0.8  # High score for single field (no consistency issues)

        consistency_factors = []

        # Check type consistency for similar field names
        field_groups = self._group_similar_fields(fields)
        for group_fields in field_groups.values():
            if len(group_fields) > 1:
                types = [f.field_type for f in group_fields]
                type_consistency = len(set(types)) / len(types)  # 1.0 = all same, lower = mixed
                consistency_factors.append(type_consistency)

        # Check confidence score consistency
        confidence_scores = [f.overall_confidence_score for f in fields]
        if stdev(confidence_scores) < 0.3:  # Low standard deviation = consistent
            consistency_factors.append(0.8)
        else:
            consistency_factors.append(0.4)

        # Check location consistency (fields should be distributed across document)
        fields_with_location = [f for f in fields if f.bounding_box]
        if len(fields_with_location) > 1:
            y_positions = [f.bounding_box['y'] for f in fields_with_location]
            y_range = max(y_positions) - min(y_positions)
            # Higher range indicates better distribution
            distribution_score = min(1.0, y_range / 500)  # Normalize assuming ~500px document height
            consistency_factors.append(distribution_score)

        if not consistency_factors:
            return 0.6  # Default moderate consistency

        return mean(consistency_factors)

    def _group_similar_fields(self, fields: List[ExtractedField]) -> Dict[str, List[ExtractedField]]:
        """Group fields with similar names"""
        groups = {}

        for field in fields:
            # Simple grouping by first word of field name
            base_name = field.detected_name.split('_')[0]
            if base_name not in groups:
                groups[base_name] = []
            groups[base_name].append(field)

        # Only return groups with multiple fields
        return {k: v for k, v in groups.items() if len(v) > 1}

    def _determine_confidence_level(self, confidence_score: float) -> str:
        """Determine confidence level string from numeric score"""
        for level, threshold in reversed(list(self.CONFIDENCE_LEVELS.items())):
            if confidence_score >= threshold:
                return level
        return 'very_low'

    def _generate_confidence_recommendations(self,
                                           component_scores: Dict[str, float],
                                           overall_confidence: float,
                                           fields: List[ExtractedField]) -> List[str]:
        """Generate recommendations based on confidence analysis"""
        recommendations = []

        # Overall confidence recommendations
        if overall_confidence < 0.4:
            recommendations.append("Overall confidence is very low - consider re-analyzing with different model")
        elif overall_confidence < 0.6:
            recommendations.append("Moderate confidence - manual review recommended before production use")
        elif overall_confidence >= 0.8:
            recommendations.append("High confidence - minimal review needed")

        # Component-specific recommendations
        if component_scores['field_extraction'] < 0.5:
            recommendations.append("Field extraction confidence is low - check document quality and clarity")

        if component_scores['document_type'] < 0.6:
            recommendations.append("Document type detection uncertain - manual verification recommended")

        if component_scores['validation_rules'] < 0.4:
            recommendations.append("Few validation rules inferred - consider adding manual validation rules")

        if component_scores['visual_quality'] < 0.5:
            recommendations.append("Poor visual quality detected - document may be blurry or low resolution")

        if component_scores['consistency'] < 0.5:
            recommendations.append("Inconsistent field extraction detected - review for accuracy")

        # Field-specific recommendations
        low_confidence_fields = [f for f in fields if f.overall_confidence_score < 0.4]
        if low_confidence_fields:
            recommendations.append(f"{len(low_confidence_fields)} fields have low confidence - review individually")

        fields_needing_review = [f for f in fields if f.requires_review]
        if fields_needing_review:
            recommendations.append(f"{len(fields_needing_review)} fields marked for review")

        return recommendations

    def analyze_schema_confidence(self, schema: GeneratedSchema) -> Dict[str, Any]:
        """
        Analyze confidence metrics for a generated schema

        Args:
            schema: GeneratedSchema instance

        Returns:
            Dictionary with schema confidence analysis
        """
        field_confidences = []

        for field_name, field_config in schema.fields.items():
            ai_metadata = field_config.get('ai_metadata', {})
            confidence = ai_metadata.get('confidence_score', 0.0)
            field_confidences.append(confidence)

        if not field_confidences:
            return {
                'schema_confidence': 0.0,
                'field_confidence_stats': {},
                'quality_assessment': 'no_fields',
                'production_readiness': False
            }

        # Calculate statistics
        confidence_stats = {
            'mean': mean(field_confidences),
            'median': median(field_confidences),
            'min': min(field_confidences),
            'max': max(field_confidences),
            'std_dev': stdev(field_confidences) if len(field_confidences) > 1 else 0.0
        }

        # Distribution analysis
        distribution = {
            'very_high': sum(1 for c in field_confidences if c >= 0.9),
            'high': sum(1 for c in field_confidences if 0.8 <= c < 0.9),
            'medium': sum(1 for c in field_confidences if 0.6 <= c < 0.8),
            'low': sum(1 for c in field_confidences if 0.4 <= c < 0.6),
            'very_low': sum(1 for c in field_confidences if c < 0.4)
        }

        # Overall schema confidence
        schema_confidence = schema.generation_confidence

        # Quality assessment
        high_confidence_ratio = (distribution['very_high'] + distribution['high']) / len(field_confidences)

        if high_confidence_ratio >= 0.8 and schema_confidence >= 0.8:
            quality_assessment = 'excellent'
        elif high_confidence_ratio >= 0.6 and schema_confidence >= 0.6:
            quality_assessment = 'good'
        elif high_confidence_ratio >= 0.4:
            quality_assessment = 'fair'
        else:
            quality_assessment = 'poor'

        # Production readiness
        production_ready = (
            schema.is_ready_for_production() and
            quality_assessment in ['excellent', 'good'] and
            distribution['very_low'] == 0
        )

        return {
            'schema_confidence': schema_confidence,
            'field_confidence_stats': confidence_stats,
            'confidence_distribution': distribution,
            'quality_assessment': quality_assessment,
            'production_readiness': production_ready,
            'total_fields': len(field_confidences),
            'high_confidence_fields': schema.high_confidence_fields,
            'user_modified_fields': len(schema.user_modified_fields),
            'review_status': schema.user_review_status,
            'validation_status': schema.validation_status
        }

    def compare_analysis_confidence(self, analysis_ids: List[str]) -> Dict[str, Any]:
        """
        Compare confidence scores across multiple analyses

        Args:
            analysis_ids: List of analysis result IDs

        Returns:
            Comparative confidence analysis
        """
        if len(analysis_ids) < 2:
            raise ConfidenceScoringError("Need at least 2 analyses for comparison")

        analyses_data = []

        for analysis_id in analysis_ids:
            try:
                confidence_data = self.calculate_comprehensive_confidence(analysis_id)
                analysis_result = self.storage.get_analysis_result(analysis_id)

                analyses_data.append({
                    'analysis_id': analysis_id,
                    'model': analysis_result.model_used if analysis_result else 'unknown',
                    'confidence_data': confidence_data
                })
            except Exception:
                continue  # Skip failed analyses

        if len(analyses_data) < 2:
            raise ConfidenceScoringError("Not enough valid analyses for comparison")

        # Find best analysis
        best_analysis = max(analyses_data, key=lambda x: x['confidence_data']['overall_confidence'])
        worst_analysis = min(analyses_data, key=lambda x: x['confidence_data']['overall_confidence'])

        # Calculate averages
        avg_confidence = mean([a['confidence_data']['overall_confidence'] for a in analyses_data])

        component_averages = {}
        for component in self.CONFIDENCE_WEIGHTS.keys():
            component_scores = [a['confidence_data']['component_scores'][component] for a in analyses_data]
            component_averages[component] = mean(component_scores)

        return {
            'comparison_summary': {
                'total_analyses': len(analyses_data),
                'average_confidence': avg_confidence,
                'best_confidence': best_analysis['confidence_data']['overall_confidence'],
                'worst_confidence': worst_analysis['confidence_data']['overall_confidence'],
                'confidence_range': best_analysis['confidence_data']['overall_confidence'] - worst_analysis['confidence_data']['overall_confidence']
            },
            'best_analysis': {
                'id': best_analysis['analysis_id'],
                'model': best_analysis['model'],
                'confidence': best_analysis['confidence_data']['overall_confidence']
            },
            'component_averages': component_averages,
            'model_performance': self._analyze_model_performance(analyses_data),
            'detailed_analyses': analyses_data
        }

    def _analyze_model_performance(self, analyses_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by model"""
        model_performance = {}

        for analysis in analyses_data:
            model = analysis['model']
            confidence = analysis['confidence_data']['overall_confidence']

            if model not in model_performance:
                model_performance[model] = []
            model_performance[model].append(confidence)

        # Calculate statistics per model
        model_stats = {}
        for model, confidences in model_performance.items():
            model_stats[model] = {
                'count': len(confidences),
                'average_confidence': mean(confidences),
                'best_confidence': max(confidences),
                'worst_confidence': min(confidences)
            }

        return model_stats

    def get_confidence_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze confidence trends over time

        Args:
            days: Number of days to analyze

        Returns:
            Trend analysis data
        """
        # This would require date-based queries to storage
        # For now, return basic trend structure
        return {
            'period_days': days,
            'total_analyses': 0,
            'average_confidence_trend': [],
            'model_trends': {},
            'quality_improvements': [],
            'recommendations': [
                "Implement trend analysis with date-based storage queries",
                "Track confidence improvements over time",
                "Monitor model performance trends"
            ]
        }

    def get_confidence_scoring_stats(self) -> Dict[str, Any]:
        """Get confidence scoring service statistics"""
        return {
            'confidence_levels': self.CONFIDENCE_LEVELS,
            'component_weights': self.CONFIDENCE_WEIGHTS,
            'supported_models': list(self.MODEL_CONFIDENCE_FACTORS.keys()),
            'scoring_components': [
                'field_extraction',
                'document_type',
                'validation_rules',
                'visual_quality',
                'consistency'
            ]
        }