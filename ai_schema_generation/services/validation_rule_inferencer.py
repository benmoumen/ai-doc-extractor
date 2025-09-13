"""
T033: ValidationRuleInferencer
Service for automatically inferring validation rules from extracted field patterns
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import Counter
from statistics import mean, median

from ..models.extracted_field import ExtractedField
from ..models.validation_rule_inference import ValidationRuleInference
from ..storage.analysis_storage import AIAnalysisStorage


class ValidationRuleInferencerError(Exception):
    """Custom exception for validation rule inference errors"""
    pass


class ValidationRuleInferencer:
    """Service for inferring validation rules from field data patterns."""

    # Common validation patterns
    COMMON_PATTERNS = {
        'email': {
            'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'description': 'Valid email address format'
        },
        'phone': {
            'pattern': r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$',
            'description': 'Valid phone number format'
        },
        'ssn': {
            'pattern': r'^\d{3}-?\d{2}-?\d{4}$',
            'description': 'Valid Social Security Number format'
        },
        'zipcode': {
            'pattern': r'^\d{5}(-\d{4})?$',
            'description': 'Valid ZIP code format'
        },
        'currency': {
            'pattern': r'^\$?[\d,]+\.?\d{0,2}$',
            'description': 'Valid currency format'
        },
        'date_mdy': {
            'pattern': r'^\d{1,2}\/\d{1,2}\/\d{4}$',
            'description': 'Date in MM/DD/YYYY format'
        },
        'date_dmy': {
            'pattern': r'^\d{1,2}\/\d{1,2}\/\d{4}$',
            'description': 'Date in DD/MM/YYYY format'
        },
        'date_iso': {
            'pattern': r'^\d{4}-\d{2}-\d{2}$',
            'description': 'Date in ISO format (YYYY-MM-DD)'
        },
        'url': {
            'pattern': r'^https?://[^\s<>"{}|\\^`\[\]]+$',
            'description': 'Valid URL format'
        }
    }

    # Field type specific rules
    FIELD_TYPE_RULES = {
        'email': ['email'],
        'phone': ['phone'],
        'date': ['date_mdy', 'date_dmy', 'date_iso'],
        'url': ['url'],
        'currency': ['currency']
    }

    def __init__(self, storage: Optional[AIAnalysisStorage] = None):
        """Initialize validation rule inferencer"""
        self.storage = storage or AIAnalysisStorage()

    def infer_validation_rules(self, analysis_result_id: str) -> List[ValidationRuleInference]:
        """
        Infer validation rules for all fields in an analysis result

        Args:
            analysis_result_id: ID of analysis result

        Returns:
            List of ValidationRuleInference instances

        Raises:
            ValidationRuleInferencerError: If inference fails
        """
        try:
            # Get extracted fields
            fields = self.storage.get_fields_for_analysis(analysis_result_id)
            if not fields:
                return []

            all_rules = []

            for field in fields:
                # Infer rules for individual field
                field_rules = self._infer_rules_for_field(field)
                all_rules.extend(field_rules)

                # Save rules to storage
                for rule in field_rules:
                    self.storage.save_validation_rule(rule)

            return all_rules

        except Exception as e:
            raise ValidationRuleInferencerError(f"Validation rule inference failed: {str(e)}")

    def _infer_rules_for_field(self, field: ExtractedField) -> List[ValidationRuleInference]:
        """Infer validation rules for a single field"""
        rules = []

        if not field.source_text:
            return rules

        # Pattern-based rules
        pattern_rules = self._infer_pattern_rules(field)
        rules.extend(pattern_rules)

        # Length-based rules
        length_rules = self._infer_length_rules(field)
        rules.extend(length_rules)

        # Format-specific rules
        format_rules = self._infer_format_rules(field)
        rules.extend(format_rules)

        # Range-based rules (for numeric fields)
        if field.field_type in ['number', 'currency']:
            range_rules = self._infer_range_rules(field)
            rules.extend(range_rules)

        return rules

    def _infer_pattern_rules(self, field: ExtractedField) -> List[ValidationRuleInference]:
        """Infer pattern-based validation rules"""
        rules = []
        source_text = field.source_text.strip()

        # Check field type specific patterns
        field_patterns = self.FIELD_TYPE_RULES.get(field.field_type, [])

        for pattern_name in field_patterns:
            if pattern_name in self.COMMON_PATTERNS:
                pattern_info = self.COMMON_PATTERNS[pattern_name]
                pattern = pattern_info['pattern']

                if re.match(pattern, source_text, re.IGNORECASE):
                    rule = ValidationRuleInference.create_pattern_rule(
                        field_id=field.id,
                        pattern=pattern,
                        description=pattern_info['description'],
                        confidence=0.9,
                        sample_matches=[source_text]
                    )
                    rule.priority = 8
                    rules.append(rule)

        # Infer custom patterns from content
        custom_pattern = self._analyze_content_for_patterns(source_text, field.field_type)
        if custom_pattern:
            rule = ValidationRuleInference.create_pattern_rule(
                field_id=field.id,
                pattern=custom_pattern['pattern'],
                description=custom_pattern['description'],
                confidence=custom_pattern['confidence'],
                sample_matches=[source_text]
            )
            rule.priority = 6
            rules.append(rule)

        return rules

    def _infer_length_rules(self, field: ExtractedField) -> List[ValidationRuleInference]:
        """Infer length-based validation rules"""
        rules = []
        text_length = len(field.source_text.strip())

        if text_length == 0:
            return rules

        # Common length patterns
        length_patterns = {
            'ssn': {'min': 9, 'max': 11, 'confidence': 0.9},
            'phone': {'min': 10, 'max': 15, 'confidence': 0.8},
            'zipcode': {'min': 5, 'max': 10, 'confidence': 0.9},
            'email': {'min': 5, 'max': 100, 'confidence': 0.7}
        }

        if field.field_type in length_patterns:
            pattern = length_patterns[field.field_type]
            rule = ValidationRuleInference.create_length_rule(
                field_id=field.id,
                min_length=pattern['min'],
                max_length=pattern['max'],
                confidence=pattern['confidence']
            )
            rule.priority = 7
            rules.append(rule)
        else:
            # Infer reasonable length constraints based on content
            min_length = max(1, text_length - 10)  # Allow some variation
            max_length = text_length + 20

            # Adjust based on field type
            if field.field_type == 'string':
                if text_length <= 50:  # Short text
                    max_length = text_length + 50
                elif text_length <= 200:  # Medium text
                    max_length = text_length + 100
                else:  # Long text
                    max_length = text_length + 200

            rule = ValidationRuleInference.create_length_rule(
                field_id=field.id,
                min_length=min_length,
                max_length=max_length,
                confidence=0.6
            )
            rule.priority = 4
            rules.append(rule)

        return rules

    def _infer_format_rules(self, field: ExtractedField) -> List[ValidationRuleInference]:
        """Infer format-specific validation rules"""
        rules = []
        source_text = field.source_text.strip()

        # Format validation for specific field types
        format_mappings = {
            'email': 'email',
            'phone': 'phone',
            'url': 'url',
            'currency': 'currency',
            'date': 'date'
        }

        if field.field_type in format_mappings:
            format_type = format_mappings[field.field_type]

            rule = ValidationRuleInference.create_format_rule(
                field_id=field.id,
                format_type=format_type,
                confidence=0.8
            )
            rule.priority = 9
            rules.append(rule)

        return rules

    def _infer_range_rules(self, field: ExtractedField) -> List[ValidationRuleInference]:
        """Infer range-based validation rules for numeric fields"""
        rules = []
        source_text = field.source_text.strip()

        try:
            # Extract numeric value
            numeric_text = re.sub(r'[^\d.-]', '', source_text)
            if not numeric_text:
                return rules

            value = float(numeric_text)

            # Define reasonable ranges based on field context
            range_suggestions = self._suggest_numeric_ranges(field.detected_name, value)

            for range_suggestion in range_suggestions:
                rule = ValidationRuleInference.create_range_rule(
                    field_id=field.id,
                    min_value=range_suggestion.get('min_value'),
                    max_value=range_suggestion.get('max_value'),
                    confidence=range_suggestion.get('confidence', 0.6)
                )
                rule.priority = range_suggestion.get('priority', 5)
                rule.rule_description = range_suggestion.get('description', rule.rule_description)
                rules.append(rule)

        except (ValueError, TypeError):
            # Not a valid number
            pass

        return rules

    def _analyze_content_for_patterns(self, content: str, field_type: str) -> Optional[Dict[str, Any]]:
        """Analyze content to discover custom patterns"""
        if len(content) < 2:
            return None

        # Letter and digit patterns
        has_letters = bool(re.search(r'[a-zA-Z]', content))
        has_digits = bool(re.search(r'\d', content))
        has_special = bool(re.search(r'[^\w\s]', content))

        pattern_parts = []
        confidence = 0.5

        if has_digits and not has_letters and not has_special:
            # Pure numeric
            pattern_parts.append(r'\d+')
            confidence = 0.8
        elif has_letters and not has_digits and not has_special:
            # Pure alphabetic
            pattern_parts.append(r'[a-zA-Z]+')
            confidence = 0.7
        elif has_digits and has_letters and not has_special:
            # Alphanumeric
            pattern_parts.append(r'[a-zA-Z0-9]+')
            confidence = 0.7

        # Look for common separators
        separators = ['-', '_', '.', '/', '\\', ' ']
        for sep in separators:
            if sep in content:
                pattern_parts.append(re.escape(sep))
                confidence += 0.1

        if pattern_parts and confidence > 0.6:
            # Build simple pattern
            pattern = '^' + ''.join(pattern_parts) + '$'
            pattern = pattern.replace(pattern_parts[0] + pattern_parts[0], pattern_parts[0] + '+')

            return {
                'pattern': pattern,
                'description': f'Custom pattern for {field_type} field',
                'confidence': min(confidence, 0.9)
            }

        return None

    def _suggest_numeric_ranges(self, field_name: str, value: float) -> List[Dict[str, Any]]:
        """Suggest reasonable numeric ranges based on field name and value"""
        suggestions = []

        # Common field ranges
        field_ranges = {
            'age': {'min': 0, 'max': 150, 'confidence': 0.9, 'priority': 8},
            'year': {'min': 1900, 'max': 2100, 'confidence': 0.8, 'priority': 7},
            'month': {'min': 1, 'max': 12, 'confidence': 0.9, 'priority': 9},
            'day': {'min': 1, 'max': 31, 'confidence': 0.9, 'priority': 9},
            'percentage': {'min': 0, 'max': 100, 'confidence': 0.8, 'priority': 7},
            'rating': {'min': 1, 'max': 10, 'confidence': 0.8, 'priority': 7},
            'quantity': {'min': 0, 'max': None, 'confidence': 0.7, 'priority': 6},
            'amount': {'min': 0, 'max': None, 'confidence': 0.6, 'priority': 5},
            'price': {'min': 0, 'max': None, 'confidence': 0.6, 'priority': 5}
        }

        # Check if field name matches known patterns
        for pattern, ranges in field_ranges.items():
            if pattern in field_name.lower():
                suggestion = {
                    'min_value': ranges['min'],
                    'max_value': ranges['max'],
                    'confidence': ranges['confidence'],
                    'priority': ranges['priority'],
                    'description': f'Expected range for {pattern} field'
                }
                suggestions.append(suggestion)

        # If no specific pattern, suggest based on value
        if not suggestions:
            if value == 0:
                suggestions.append({
                    'min_value': 0,
                    'max_value': None,
                    'confidence': 0.5,
                    'priority': 4,
                    'description': 'Non-negative values expected'
                })
            elif 0 < value < 1000:
                suggestions.append({
                    'min_value': 0,
                    'max_value': value * 10,
                    'confidence': 0.4,
                    'priority': 3,
                    'description': 'Reasonable range based on sample value'
                })
            elif value >= 1000:
                # For large numbers, suggest a wider range
                suggestions.append({
                    'min_value': 0,
                    'max_value': value * 5,
                    'confidence': 0.3,
                    'priority': 2,
                    'description': 'Wide range for large numeric values'
                })

        return suggestions

    def infer_rules_from_multiple_samples(self, field_name: str, field_type: str, samples: List[str]) -> List[ValidationRuleInference]:
        """
        Infer validation rules from multiple samples of the same field

        Args:
            field_name: Name of the field
            field_type: Type of the field
            samples: List of sample values

        Returns:
            List of inferred validation rules
        """
        if not samples:
            return []

        rules = []

        # Analyze patterns across all samples
        pattern_analysis = self._analyze_patterns_across_samples(samples)
        if pattern_analysis and pattern_analysis['confidence'] > 0.7:
            rule = ValidationRuleInference.create_pattern_rule(
                field_id='',  # Will be set later
                pattern=pattern_analysis['pattern'],
                description=pattern_analysis['description'],
                confidence=pattern_analysis['confidence'],
                sample_matches=samples[:5]  # First 5 samples as examples
            )
            rule.priority = 8
            rules.append(rule)

        # Length analysis
        lengths = [len(sample.strip()) for sample in samples if sample.strip()]
        if lengths:
            min_len = min(lengths)
            max_len = max(lengths)

            # If there's consistency in length (within small range)
            if max_len - min_len <= 5:
                rule = ValidationRuleInference.create_length_rule(
                    field_id='',
                    min_length=max(1, min_len - 2),
                    max_length=max_len + 2,
                    confidence=0.8
                )
                rule.priority = 7
                rules.append(rule)

        # Numeric range analysis
        if field_type in ['number', 'currency']:
            numeric_values = []
            for sample in samples:
                try:
                    # Extract numeric part
                    numeric_text = re.sub(r'[^\d.-]', '', sample.strip())
                    if numeric_text:
                        numeric_values.append(float(numeric_text))
                except (ValueError, TypeError):
                    continue

            if numeric_values and len(numeric_values) >= 2:
                min_val = min(numeric_values)
                max_val = max(numeric_values)

                # Expand range slightly for validation
                range_expansion = (max_val - min_val) * 0.2
                suggested_min = max(0, min_val - range_expansion) if min_val >= 0 else min_val - range_expansion
                suggested_max = max_val + range_expansion

                rule = ValidationRuleInference.create_range_rule(
                    field_id='',
                    min_value=suggested_min,
                    max_value=suggested_max,
                    confidence=0.7
                )
                rule.priority = 6
                rule.rule_description = f'Range inferred from {len(numeric_values)} samples'
                rules.append(rule)

        return rules

    def _analyze_patterns_across_samples(self, samples: List[str]) -> Optional[Dict[str, Any]]:
        """Analyze patterns that are consistent across multiple samples"""
        if len(samples) < 2:
            return None

        # Look for common structural patterns
        pattern_chars = []
        min_length = min(len(s) for s in samples)

        for i in range(min_length):
            char_types = set()
            for sample in samples:
                char = sample[i]
                if char.isdigit():
                    char_types.add('d')
                elif char.isalpha():
                    char_types.add('a')
                elif char.isspace():
                    char_types.add('s')
                else:
                    char_types.add('p')  # punctuation/special

            # If all samples have the same character type at this position
            if len(char_types) == 1:
                char_type = char_types.pop()
                if char_type == 'd':
                    pattern_chars.append(r'\d')
                elif char_type == 'a':
                    pattern_chars.append(r'[a-zA-Z]')
                elif char_type == 's':
                    pattern_chars.append(r'\s')
                else:
                    # Escape special characters
                    pattern_chars.append(re.escape(samples[0][i]))
            else:
                # Mixed character types at this position
                break

        if len(pattern_chars) >= 3:  # Meaningful pattern found
            pattern = '^' + ''.join(pattern_chars)

            # Check if pattern extends to end of strings
            if all(len(s) == min_length for s in samples):
                pattern += '$'
            else:
                pattern += r'.*$'

            # Test pattern against all samples
            matches = sum(1 for sample in samples if re.match(pattern, sample))
            confidence = matches / len(samples)

            if confidence >= 0.8:
                return {
                    'pattern': pattern,
                    'description': f'Consistent pattern across {matches}/{len(samples)} samples',
                    'confidence': confidence
                }

        return None

    def get_rule_recommendations(self, field_type: str, field_name: str) -> List[Dict[str, Any]]:
        """Get recommended validation rules for a field type/name combination"""
        recommendations = []

        # Type-based recommendations
        if field_type in self.FIELD_TYPE_RULES:
            for pattern_name in self.FIELD_TYPE_RULES[field_type]:
                if pattern_name in self.COMMON_PATTERNS:
                    pattern_info = self.COMMON_PATTERNS[pattern_name]
                    recommendations.append({
                        'type': 'pattern',
                        'rule': pattern_info['pattern'],
                        'description': pattern_info['description'],
                        'priority': 8,
                        'confidence': 0.9
                    })

        # Name-based recommendations
        name_recommendations = {
            'age': [{'type': 'range', 'min': 0, 'max': 150, 'description': 'Valid age range'}],
            'year': [{'type': 'range', 'min': 1900, 'max': 2100, 'description': 'Valid year range'}],
            'percentage': [{'type': 'range', 'min': 0, 'max': 100, 'description': 'Percentage range'}]
        }

        for name_pattern, rules in name_recommendations.items():
            if name_pattern in field_name.lower():
                recommendations.extend(rules)

        return recommendations

    def validate_rule_effectiveness(self, rule: ValidationRuleInference, test_values: List[str]) -> Dict[str, Any]:
        """Validate how effective a rule is against test values"""
        if not test_values:
            return {'effectiveness': 0.0, 'matches': 0, 'total': 0}

        matches = 0
        for value in test_values:
            if rule.test_rule_against_value(value):
                matches += 1

        effectiveness = matches / len(test_values)

        return {
            'effectiveness': effectiveness,
            'matches': matches,
            'total': len(test_values),
            'rule_strength': rule.get_rule_strength(),
            'recommended': effectiveness >= 0.8
        }

    def get_inference_stats(self) -> Dict[str, Any]:
        """Get validation rule inference statistics"""
        return {
            'common_patterns_count': len(self.COMMON_PATTERNS),
            'supported_field_types': list(self.FIELD_TYPE_RULES.keys()),
            'pattern_categories': ['email', 'phone', 'date', 'numeric', 'text'],
            'rule_types': ['pattern', 'length', 'range', 'format']
        }