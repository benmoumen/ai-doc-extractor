"""
T024: ValidationRuleInference model
Automatically generated validation rules based on field content patterns
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import json
import re


@dataclass
class ValidationRuleInference:
    """Validation rules inferred from field analysis."""

    id: str
    extracted_field_id: str

    # Rule definition
    rule_type: str  # 'pattern' | 'length' | 'range' | 'format' | 'custom'
    rule_value: Any  # Rule parameter (regex, number, dict, etc.)
    rule_description: str

    # Confidence and validation
    confidence_score: float  # 0.0-1.0
    sample_matches: List[str] = field(default_factory=list)
    sample_non_matches: List[str] = field(default_factory=list)

    # Rule metadata
    inference_method: str = "pattern_analysis"
    is_recommended: bool = True
    priority: int = 1  # 1-10, higher = more important

    # Alternative rules
    alternative_rules: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Validate rule data after initialization"""
        # Validate rule type
        valid_types = ['pattern', 'length', 'range', 'format', 'custom']
        if self.rule_type not in valid_types:
            raise ValueError(f"Invalid rule_type: {self.rule_type}. Must be one of {valid_types}")

        # Validate confidence score
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError(f"confidence_score must be between 0.0 and 1.0, got {self.confidence_score}")

        # Validate priority
        if not (1 <= self.priority <= 10):
            raise ValueError(f"priority must be between 1 and 10, got {self.priority}")

        # Validate rule value based on type
        self._validate_rule_value()

    def _validate_rule_value(self):
        """Validate rule value based on rule type"""
        if self.rule_type == 'pattern':
            if not isinstance(self.rule_value, str):
                raise ValueError("Pattern rule value must be a string (regex)")
            try:
                re.compile(self.rule_value)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")

        elif self.rule_type == 'length':
            if not isinstance(self.rule_value, dict):
                raise ValueError("Length rule value must be a dictionary")
            valid_keys = {'min_length', 'max_length'}
            if not any(key in self.rule_value for key in valid_keys):
                raise ValueError("Length rule must specify min_length and/or max_length")
            for key in self.rule_value:
                if key not in valid_keys or not isinstance(self.rule_value[key], int) or self.rule_value[key] < 0:
                    raise ValueError(f"Invalid length constraint: {key}")

        elif self.rule_type == 'range':
            if not isinstance(self.rule_value, dict):
                raise ValueError("Range rule value must be a dictionary")
            valid_keys = {'min_value', 'max_value'}
            if not any(key in self.rule_value for key in valid_keys):
                raise ValueError("Range rule must specify min_value and/or max_value")

        elif self.rule_type == 'format':
            if not isinstance(self.rule_value, dict) or 'format' not in self.rule_value:
                raise ValueError("Format rule value must be a dictionary with 'format' key")

    @classmethod
    def create_pattern_rule(
        cls,
        field_id: str,
        pattern: str,
        description: str,
        confidence: float,
        sample_matches: Optional[List[str]] = None
    ) -> 'ValidationRuleInference':
        """Create pattern validation rule"""
        import uuid

        return cls(
            id=str(uuid.uuid4()),
            extracted_field_id=field_id,
            rule_type='pattern',
            rule_value=pattern,
            rule_description=description,
            confidence_score=confidence,
            sample_matches=sample_matches or []
        )

    @classmethod
    def create_length_rule(
        cls,
        field_id: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        confidence: float = 0.8
    ) -> 'ValidationRuleInference':
        """Create length validation rule"""
        import uuid

        if min_length is None and max_length is None:
            raise ValueError("Must specify at least one of min_length or max_length")

        rule_value = {}
        description_parts = []

        if min_length is not None:
            rule_value['min_length'] = min_length
            description_parts.append(f"at least {min_length} characters")

        if max_length is not None:
            rule_value['max_length'] = max_length
            description_parts.append(f"at most {max_length} characters")

        description = f"Length must be {' and '.join(description_parts)}"

        return cls(
            id=str(uuid.uuid4()),
            extracted_field_id=field_id,
            rule_type='length',
            rule_value=rule_value,
            rule_description=description,
            confidence_score=confidence
        )

    @classmethod
    def create_range_rule(
        cls,
        field_id: str,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        confidence: float = 0.8
    ) -> 'ValidationRuleInference':
        """Create range validation rule for numeric fields"""
        import uuid

        if min_value is None and max_value is None:
            raise ValueError("Must specify at least one of min_value or max_value")

        rule_value = {}
        description_parts = []

        if min_value is not None:
            rule_value['min_value'] = min_value
            description_parts.append(f"at least {min_value}")

        if max_value is not None:
            rule_value['max_value'] = max_value
            description_parts.append(f"at most {max_value}")

        description = f"Value must be {' and '.join(description_parts)}"

        return cls(
            id=str(uuid.uuid4()),
            extracted_field_id=field_id,
            rule_type='range',
            rule_value=rule_value,
            rule_description=description,
            confidence_score=confidence
        )

    @classmethod
    def create_format_rule(
        cls,
        field_id: str,
        format_type: str,
        confidence: float,
        format_details: Optional[Dict[str, Any]] = None
    ) -> 'ValidationRuleInference':
        """Create format validation rule"""
        import uuid

        valid_formats = ['email', 'phone', 'date', 'url', 'currency', 'ssn', 'zipcode']
        if format_type not in valid_formats:
            raise ValueError(f"Invalid format_type: {format_type}. Must be one of {valid_formats}")

        rule_value = {'format': format_type}
        if format_details:
            rule_value.update(format_details)

        description = f"Must be a valid {format_type}"

        return cls(
            id=str(uuid.uuid4()),
            extracted_field_id=field_id,
            rule_type='format',
            rule_value=rule_value,
            rule_description=description,
            confidence_score=confidence
        )

    def test_rule_against_value(self, value: str) -> bool:
        """Test if a value passes this validation rule"""
        if not value:
            return not self.is_recommended  # Empty values only pass if rule is not recommended

        try:
            if self.rule_type == 'pattern':
                return bool(re.match(self.rule_value, value))

            elif self.rule_type == 'length':
                length = len(value)
                if 'min_length' in self.rule_value and length < self.rule_value['min_length']:
                    return False
                if 'max_length' in self.rule_value and length > self.rule_value['max_length']:
                    return False
                return True

            elif self.rule_type == 'range':
                # Try to convert to number
                try:
                    num_value = float(value)
                except ValueError:
                    return False

                if 'min_value' in self.rule_value and num_value < self.rule_value['min_value']:
                    return False
                if 'max_value' in self.rule_value and num_value > self.rule_value['max_value']:
                    return False
                return True

            elif self.rule_type == 'format':
                format_type = self.rule_value['format']
                return self._validate_format(value, format_type)

            else:  # custom
                # Custom rules would need specific implementation
                return True

        except Exception:
            return False

    def _validate_format(self, value: str, format_type: str) -> bool:
        """Validate value against specific format"""
        format_patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$',
            'date': r'^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}$',
            'url': r'^https?://[^\s<>"{}|\\^`\[\]]+$',
            'currency': r'^\$?[\d,]+\.?\d{0,2}$',
            'ssn': r'^\d{3}-?\d{2}-?\d{4}$',
            'zipcode': r'^\d{5}(-\d{4})?$'
        }

        pattern = format_patterns.get(format_type)
        if not pattern:
            return True  # Unknown format, assume valid

        return bool(re.match(pattern, value))

    def add_sample_match(self, sample_value: str):
        """Add sample value that matches this rule"""
        if sample_value not in self.sample_matches:
            self.sample_matches.append(sample_value)

    def add_sample_non_match(self, sample_value: str):
        """Add sample value that doesn't match this rule"""
        if sample_value not in self.sample_non_matches:
            self.sample_non_matches.append(sample_value)

    def add_alternative_rule(self, rule_data: Dict[str, Any]):
        """Add alternative rule interpretation"""
        required_keys = ['rule_type', 'rule_value', 'confidence']
        if not all(key in rule_data for key in required_keys):
            raise ValueError(f"Alternative rule must contain: {required_keys}")

        self.alternative_rules.append(rule_data)

    def get_rule_strength(self) -> float:
        """Calculate rule strength based on confidence and sample data"""
        base_strength = self.confidence_score

        # Boost strength if we have supporting samples
        if self.sample_matches:
            sample_boost = min(0.2, len(self.sample_matches) * 0.05)
            base_strength += sample_boost

        # Reduce strength if we have contradicting samples
        if self.sample_non_matches:
            contradiction_penalty = min(0.1, len(self.sample_non_matches) * 0.02)
            base_strength -= contradiction_penalty

        return max(0.0, min(1.0, base_strength))

    def get_javascript_validation(self) -> str:
        """Generate JavaScript validation code for this rule"""
        if self.rule_type == 'pattern':
            return f"/{self.rule_value}/.test(value)"

        elif self.rule_type == 'length':
            conditions = []
            if 'min_length' in self.rule_value:
                conditions.append(f"value.length >= {self.rule_value['min_length']}")
            if 'max_length' in self.rule_value:
                conditions.append(f"value.length <= {self.rule_value['max_length']}")
            return " && ".join(conditions)

        elif self.rule_type == 'range':
            conditions = []
            if 'min_value' in self.rule_value:
                conditions.append(f"parseFloat(value) >= {self.rule_value['min_value']}")
            if 'max_value' in self.rule_value:
                conditions.append(f"parseFloat(value) <= {self.rule_value['max_value']}")
            return " && ".join(conditions)

        elif self.rule_type == 'format':
            format_type = self.rule_value['format']
            format_patterns = {
                'email': r'/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(value)',
                'phone': r'/^[\+]?[1-9][\d\s\-\(\)]{7,15}$/.test(value)',
                'date': r'/^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}$/.test(value)',
                'url': r'/^https?:\/\/[^\s<>"{}|\\^`\[\]]+$/.test(value)',
                'currency': r'/^\$?[\d,]+\.?\d{0,2}$/.test(value)'
            }
            return format_patterns.get(format_type, 'true')

        return 'true'  # Default for custom rules

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            'id': self.id,
            'extracted_field_id': self.extracted_field_id,
            'rule_type': self.rule_type,
            'rule_value': self.rule_value,
            'rule_description': self.rule_description,
            'confidence_score': self.confidence_score,
            'sample_matches': self.sample_matches,
            'sample_non_matches': self.sample_non_matches,
            'inference_method': self.inference_method,
            'is_recommended': self.is_recommended,
            'priority': self.priority,
            'alternative_rules': self.alternative_rules
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationRuleInference':
        """Create from dictionary (for loading from storage)"""
        return cls(
            id=data['id'],
            extracted_field_id=data['extracted_field_id'],
            rule_type=data['rule_type'],
            rule_value=data['rule_value'],
            rule_description=data['rule_description'],
            confidence_score=data['confidence_score'],
            sample_matches=data.get('sample_matches', []),
            sample_non_matches=data.get('sample_non_matches', []),
            inference_method=data.get('inference_method', 'pattern_analysis'),
            is_recommended=data.get('is_recommended', True),
            priority=data.get('priority', 1),
            alternative_rules=data.get('alternative_rules', [])
        )