"""
T063: Confidence calculation utilities
Advanced confidence scoring for AI-generated schemas and extracted data
"""

import math
import statistics
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence level categories"""
    VERY_HIGH = "very_high"  # 90-100%
    HIGH = "high"           # 75-89%
    MEDIUM = "medium"       # 50-74%
    LOW = "low"            # 25-49%
    VERY_LOW = "very_low"  # 0-24%


@dataclass
class ConfidenceScore:
    """Confidence score with metadata"""
    score: float  # 0.0 to 1.0
    level: ConfidenceLevel
    factors: Dict[str, float]
    reasoning: List[str]
    timestamp: datetime


class ConfidenceCalculator:
    """Advanced confidence calculation for AI schema generation"""

    def __init__(self):
        """Initialize confidence calculator"""
        self.ai_model_confidence_weights = {
            'claude': 0.95,
            'gpt-4': 0.90,
            'gpt-3.5': 0.80,
            'llama': 0.85,
            'mistral': 0.82,
            'gemini': 0.88
        }

        # Field type confidence factors
        self.field_type_confidence = {
            'string': 0.90,
            'number': 0.85,
            'integer': 0.85,
            'boolean': 0.90,
            'date': 0.80,
            'datetime': 0.75,
            'email': 0.85,
            'phone': 0.80,
            'url': 0.85,
            'json': 0.70,
            'array': 0.75
        }

    def calculate_field_confidence(self, field_name: str, field_value: Any,
                                 field_config: Dict[str, Any],
                                 ai_metadata: Optional[Dict[str, Any]] = None) -> ConfidenceScore:
        """
        Calculate confidence score for a single extracted field

        Args:
            field_name: Name of the field
            field_value: Extracted value
            field_config: Field configuration from schema
            ai_metadata: AI model metadata

        Returns:
            ConfidenceScore with detailed breakdown
        """
        factors = {}
        reasoning = []

        # 1. Base confidence from field type
        field_type = field_config.get('type', 'string')
        type_confidence = self.field_type_confidence.get(field_type, 0.75)
        factors['type_confidence'] = type_confidence

        # 2. Value quality assessment
        value_confidence = self._assess_value_quality(field_value, field_type)
        factors['value_quality'] = value_confidence

        # 3. Schema compliance
        schema_compliance = self._check_schema_compliance(field_value, field_config)
        factors['schema_compliance'] = schema_compliance

        # 4. AI model confidence (if available)
        if ai_metadata and 'model_confidence' in ai_metadata:
            model_confidence = ai_metadata['model_confidence']
            # Adjust based on model type
            model_type = ai_metadata.get('model_type', 'unknown').lower()
            model_weight = self.ai_model_confidence_weights.get(model_type, 0.80)
            factors['ai_model'] = model_confidence * model_weight
        else:
            factors['ai_model'] = 0.75  # Default when no AI confidence available

        # 5. Context consistency (field name vs value)
        name_consistency = self._assess_name_value_consistency(field_name, field_value, field_type)
        factors['name_consistency'] = name_consistency

        # 6. Validation rule compliance
        validation_compliance = self._check_validation_compliance(field_value, field_config)
        factors['validation_compliance'] = validation_compliance

        # Calculate weighted score
        weights = {
            'type_confidence': 0.15,
            'value_quality': 0.25,
            'schema_compliance': 0.20,
            'ai_model': 0.20,
            'name_consistency': 0.10,
            'validation_compliance': 0.10
        }

        score = sum(factors[factor] * weights[factor] for factor in factors)
        score = max(0.0, min(1.0, score))  # Clamp to [0, 1]

        # Generate reasoning
        reasoning = self._generate_confidence_reasoning(factors, field_name, field_type)

        # Determine confidence level
        level = self._get_confidence_level(score)

        return ConfidenceScore(
            score=score,
            level=level,
            factors=factors,
            reasoning=reasoning,
            timestamp=datetime.now()
        )

    def calculate_schema_confidence(self, schema_data: Dict[str, Any],
                                  schema_definition: Dict[str, Any],
                                  ai_metadata: Optional[Dict[str, Any]] = None) -> ConfidenceScore:
        """
        Calculate overall confidence for an entire schema

        Args:
            schema_data: Extracted data
            schema_definition: Schema definition
            ai_metadata: AI generation metadata

        Returns:
            Overall schema confidence score
        """
        factors = {}
        reasoning = []
        field_scores = []

        schema_fields = schema_definition.get('fields', {})

        # 1. Calculate confidence for each field
        for field_name, field_config in schema_fields.items():
            field_value = schema_data.get(field_name)
            field_confidence = self.calculate_field_confidence(
                field_name, field_value, field_config, ai_metadata
            )
            field_scores.append(field_confidence.score)

        # 2. Coverage analysis
        expected_fields = len(schema_fields)
        extracted_fields = len([v for v in schema_data.values() if v is not None])
        coverage_ratio = extracted_fields / expected_fields if expected_fields > 0 else 0
        factors['coverage'] = coverage_ratio

        # 3. Required field completion
        required_fields = [name for name, config in schema_fields.items()
                          if config.get('required', False)]
        completed_required = len([name for name in required_fields
                                if schema_data.get(name) is not None])
        required_completion = completed_required / len(required_fields) if required_fields else 1.0
        factors['required_completion'] = required_completion

        # 4. Data consistency across fields
        consistency_score = self._assess_cross_field_consistency(schema_data, schema_fields)
        factors['cross_field_consistency'] = consistency_score

        # 5. AI generation confidence (if available)
        if ai_metadata:
            generation_confidence = ai_metadata.get('generation_confidence', 0.75)
            factors['ai_generation'] = generation_confidence
        else:
            factors['ai_generation'] = 0.75

        # 6. Schema structure quality
        structure_quality = self._assess_schema_structure_quality(schema_definition)
        factors['structure_quality'] = structure_quality

        # Calculate field-level average
        if field_scores:
            field_average = statistics.mean(field_scores)
            factors['field_average'] = field_average
        else:
            factors['field_average'] = 0.0

        # Calculate weighted overall score
        weights = {
            'coverage': 0.20,
            'required_completion': 0.25,
            'cross_field_consistency': 0.15,
            'ai_generation': 0.15,
            'structure_quality': 0.10,
            'field_average': 0.15
        }

        score = sum(factors[factor] * weights[factor] for factor in factors)
        score = max(0.0, min(1.0, score))

        # Generate reasoning
        reasoning = self._generate_schema_reasoning(factors, expected_fields, extracted_fields)

        level = self._get_confidence_level(score)

        return ConfidenceScore(
            score=score,
            level=level,
            factors=factors,
            reasoning=reasoning,
            timestamp=datetime.now()
        )

    def _assess_value_quality(self, value: Any, field_type: str) -> float:
        """Assess quality of extracted value"""
        if value is None or value == "":
            return 0.0

        try:
            str_value = str(value).strip()

            # Empty or placeholder-like values
            if not str_value or str_value.lower() in ['n/a', 'null', 'none', 'unknown', '---', 'tbd']:
                return 0.1

            # Very short values (might be incomplete)
            if len(str_value) < 2:
                return 0.4

            # Type-specific quality checks
            if field_type == 'email':
                return 0.9 if '@' in str_value and '.' in str_value else 0.3

            elif field_type == 'phone':
                digits = ''.join(filter(str.isdigit, str_value))
                if len(digits) >= 10:
                    return 0.9
                elif len(digits) >= 7:
                    return 0.7
                else:
                    return 0.3

            elif field_type == 'url':
                return 0.9 if any(proto in str_value.lower() for proto in ['http', 'www.', '.com', '.org']) else 0.4

            elif field_type in ['number', 'integer', 'float']:
                try:
                    float(str_value.replace(',', ''))
                    return 0.9
                except ValueError:
                    return 0.2

            elif field_type == 'date':
                # Look for date-like patterns
                if any(sep in str_value for sep in ['-', '/', '.']):
                    return 0.8
                return 0.4

            # General string quality
            if len(str_value) >= 3:
                return 0.8
            else:
                return 0.5

        except Exception:
            return 0.2

    def _check_schema_compliance(self, value: Any, field_config: Dict[str, Any]) -> float:
        """Check if value complies with schema requirements"""
        if value is None:
            return 0.0 if field_config.get('required', False) else 0.8

        compliance_score = 1.0

        # Check type compliance
        field_type = field_config.get('type', 'string')
        if not self._value_matches_expected_type(value, field_type):
            compliance_score *= 0.5

        return compliance_score

    def _assess_name_value_consistency(self, field_name: str, field_value: Any, field_type: str) -> float:
        """Assess consistency between field name and extracted value"""
        if field_value is None:
            return 0.5

        try:
            str_value = str(field_value).lower()
            field_name_lower = field_name.lower()

            # Exact or partial matches
            if field_name_lower in str_value or any(part in str_value for part in field_name_lower.split('_')):
                return 0.9

            # Type-specific consistency checks
            if field_type == 'email' and ('email' in field_name_lower or 'mail' in field_name_lower):
                if '@' in str_value:
                    return 0.9
                else:
                    return 0.3

            elif field_type == 'phone' and ('phone' in field_name_lower or 'tel' in field_name_lower):
                digits = ''.join(filter(str.isdigit, str_value))
                return 0.9 if len(digits) >= 7 else 0.4

            elif field_type in ['date', 'datetime'] and ('date' in field_name_lower or 'time' in field_name_lower):
                return 0.8

            # Default consistency
            return 0.7

        except Exception:
            return 0.5

    def _check_validation_compliance(self, value: Any, field_config: Dict[str, Any]) -> float:
        """Check compliance with validation rules"""
        validation_rules = field_config.get('validation_rules', [])

        if not validation_rules:
            return 1.0  # No rules to violate

        if value is None:
            return 0.0

        compliance_count = 0
        total_rules = len(validation_rules)

        for rule in validation_rules:
            try:
                if self._check_single_validation_rule(value, rule):
                    compliance_count += 1
            except Exception:
                pass  # Rule check failed, don't count as compliant

        return compliance_count / total_rules if total_rules > 0 else 1.0

    def _check_single_validation_rule(self, value: Any, rule: Dict[str, Any]) -> bool:
        """Check a single validation rule"""
        rule_type = rule.get('type')

        if rule_type == 'length':
            length = len(str(value))
            min_length = rule.get('min')
            max_length = rule.get('max')

            if min_length and length < min_length:
                return False
            if max_length and length > max_length:
                return False
            return True

        elif rule_type == 'range':
            try:
                numeric_value = float(str(value))
                min_value = rule.get('min')
                max_value = rule.get('max')

                if min_value and numeric_value < min_value:
                    return False
                if max_value and numeric_value > max_value:
                    return False
                return True
            except ValueError:
                return False

        elif rule_type == 'pattern':
            import re
            pattern = rule.get('pattern')
            if pattern:
                return bool(re.match(pattern, str(value)))
            return True

        elif rule_type == 'enum':
            allowed_values = rule.get('values', [])
            return value in allowed_values

        return True  # Unknown rule types pass by default

    def _assess_cross_field_consistency(self, schema_data: Dict[str, Any],
                                       schema_fields: Dict[str, Any]) -> float:
        """Assess consistency across multiple fields"""
        # Simple heuristics for cross-field consistency
        consistency_score = 1.0

        # Check for conflicting information (basic checks)
        date_fields = []
        name_fields = []

        for field_name, field_config in schema_fields.items():
            field_type = field_config.get('type', 'string')
            field_value = schema_data.get(field_name)

            if field_type in ['date', 'datetime'] and field_value:
                date_fields.append((field_name, field_value))

            if 'name' in field_name.lower() and field_value:
                name_fields.append((field_name, field_value))

        # Basic consistency checks could be added here
        # For now, return high consistency as cross-field validation is complex

        return consistency_score

    def _assess_schema_structure_quality(self, schema_definition: Dict[str, Any]) -> float:
        """Assess quality of schema structure itself"""
        quality_factors = []

        fields = schema_definition.get('fields', {})
        if not fields:
            return 0.0

        # Field count (reasonable number)
        field_count = len(fields)
        if 5 <= field_count <= 50:
            quality_factors.append(0.9)
        elif 1 <= field_count <= 100:
            quality_factors.append(0.7)
        else:
            quality_factors.append(0.5)

        # Required fields ratio
        required_count = sum(1 for f in fields.values() if f.get('required', False))
        required_ratio = required_count / field_count
        if 0.2 <= required_ratio <= 0.8:  # Good balance
            quality_factors.append(0.9)
        else:
            quality_factors.append(0.6)

        # Fields with validation rules
        validated_count = sum(1 for f in fields.values() if f.get('validation_rules'))
        validation_coverage = validated_count / field_count
        quality_factors.append(validation_coverage)

        # Schema metadata quality
        metadata = schema_definition.get('metadata', {})
        if metadata.get('description') and metadata.get('version'):
            quality_factors.append(0.9)
        elif metadata.get('description') or metadata.get('version'):
            quality_factors.append(0.7)
        else:
            quality_factors.append(0.5)

        return statistics.mean(quality_factors) if quality_factors else 0.5

    def _value_matches_expected_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        if expected_type == 'string':
            return True  # Almost anything can be a string

        elif expected_type == 'number':
            try:
                float(str(value))
                return True
            except (ValueError, TypeError):
                return False

        elif expected_type == 'integer':
            try:
                int(float(str(value)))
                return True
            except (ValueError, TypeError):
                return False

        elif expected_type == 'boolean':
            return isinstance(value, bool) or str(value).lower() in ['true', 'false', 'yes', 'no', '1', '0']

        elif expected_type == 'email':
            return '@' in str(value) if value else False

        elif expected_type == 'phone':
            digits = ''.join(filter(str.isdigit, str(value))) if value else ''
            return len(digits) >= 7

        # For other types, be permissive
        return True

    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert numeric score to confidence level"""
        if score >= 0.90:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.75:
            return ConfidenceLevel.HIGH
        elif score >= 0.50:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.25:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _generate_confidence_reasoning(self, factors: Dict[str, float],
                                     field_name: str, field_type: str) -> List[str]:
        """Generate human-readable reasoning for confidence score"""
        reasoning = []

        # Value quality reasoning
        if factors.get('value_quality', 0) >= 0.8:
            reasoning.append(f"High quality {field_type} value extracted")
        elif factors.get('value_quality', 0) <= 0.3:
            reasoning.append(f"Low quality or missing {field_type} value")

        # AI model confidence
        if factors.get('ai_model', 0) >= 0.85:
            reasoning.append("High AI model confidence in extraction")
        elif factors.get('ai_model', 0) <= 0.6:
            reasoning.append("Lower AI model confidence")

        # Schema compliance
        if factors.get('schema_compliance', 0) >= 0.9:
            reasoning.append("Fully compliant with schema requirements")
        elif factors.get('schema_compliance', 0) <= 0.5:
            reasoning.append("Some schema compliance issues detected")

        # Name consistency
        if factors.get('name_consistency', 0) >= 0.8:
            reasoning.append("Field name and value are consistent")

        # Validation compliance
        if factors.get('validation_compliance', 0) < 1.0:
            reasoning.append("Some validation rules not met")

        return reasoning

    def _generate_schema_reasoning(self, factors: Dict[str, float],
                                 expected_fields: int, extracted_fields: int) -> List[str]:
        """Generate reasoning for schema-level confidence"""
        reasoning = []

        # Coverage
        coverage = factors.get('coverage', 0)
        if coverage >= 0.9:
            reasoning.append("Excellent field coverage")
        elif coverage >= 0.7:
            reasoning.append("Good field coverage")
        elif coverage <= 0.5:
            reasoning.append("Limited field coverage")

        # Required fields
        required_completion = factors.get('required_completion', 0)
        if required_completion >= 0.9:
            reasoning.append("All required fields extracted")
        elif required_completion < 1.0:
            reasoning.append("Some required fields missing")

        # Overall extraction
        if extracted_fields == expected_fields:
            reasoning.append(f"All {expected_fields} fields extracted")
        else:
            reasoning.append(f"{extracted_fields}/{expected_fields} fields extracted")

        # AI generation quality
        ai_gen = factors.get('ai_generation', 0)
        if ai_gen >= 0.8:
            reasoning.append("High AI generation confidence")
        elif ai_gen <= 0.6:
            reasoning.append("Moderate AI generation confidence")

        return reasoning

    def calculate_confidence_trend(self, confidence_history: List[ConfidenceScore]) -> Dict[str, Any]:
        """Calculate confidence trends over time"""
        if not confidence_history:
            return {'trend': 'no_data', 'change': 0.0}

        scores = [cs.score for cs in confidence_history]

        if len(scores) == 1:
            return {'trend': 'single_point', 'change': 0.0}

        # Calculate trend
        recent_avg = statistics.mean(scores[-3:])  # Last 3 scores
        older_avg = statistics.mean(scores[:-3]) if len(scores) > 3 else scores[0]

        change = recent_avg - older_avg

        if abs(change) < 0.05:
            trend = 'stable'
        elif change > 0:
            trend = 'improving'
        else:
            trend = 'declining'

        return {
            'trend': trend,
            'change': change,
            'current_avg': recent_avg,
            'historical_avg': statistics.mean(scores),
            'volatility': statistics.stdev(scores) if len(scores) > 1 else 0.0
        }


# Global calculator instance
_confidence_calculator = None

def get_confidence_calculator() -> ConfidenceCalculator:
    """Get singleton confidence calculator instance"""
    global _confidence_calculator
    if _confidence_calculator is None:
        _confidence_calculator = ConfidenceCalculator()
    return _confidence_calculator


def calculate_extraction_confidence(schema_data: Dict[str, Any],
                                   schema_definition: Dict[str, Any],
                                   ai_metadata: Optional[Dict[str, Any]] = None) -> ConfidenceScore:
    """
    Convenience function to calculate extraction confidence

    Returns:
        Overall confidence score for the extraction
    """
    calculator = get_confidence_calculator()
    return calculator.calculate_schema_confidence(schema_data, schema_definition, ai_metadata)