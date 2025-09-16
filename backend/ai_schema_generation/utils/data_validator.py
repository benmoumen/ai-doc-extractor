"""
T061: Data validation utilities
Comprehensive data validation for AI schema generation pipeline
"""

import re
import json
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import NumberParseException
from urllib.parse import urlparse


class ValidationResult:
    """Result of a validation operation"""

    def __init__(self, is_valid: bool = True, error_message: str = None,
                 normalized_value: Any = None, confidence: float = 1.0):
        self.is_valid = is_valid
        self.error_message = error_message
        self.normalized_value = normalized_value
        self.confidence = confidence

    def __bool__(self):
        return self.is_valid

    def __str__(self):
        if self.is_valid:
            return f"Valid (confidence: {self.confidence:.2f})"
        return f"Invalid: {self.error_message}"


class DataValidator:
    """Comprehensive data validation system for AI extraction results"""

    # Common validation patterns
    PATTERNS = {
        'phone': r'^[\+]?[1-9][\d]{0,15}$',
        'ssn': r'^\d{3}-?\d{2}-?\d{4}$',
        'credit_card': r'^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$',
        'zip_code': r'^\d{5}(-\d{4})?$',
        'ip_address': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
        'mac_address': r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
        'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    }

    def __init__(self):
        """Initialize data validator"""
        self.validation_cache = {}

    def validate_field(self, value: Any, field_config: Dict[str, Any]) -> ValidationResult:
        """
        Validate a field value against its configuration

        Args:
            value: The value to validate
            field_config: Field configuration with type and validation rules

        Returns:
            ValidationResult with validation outcome
        """
        if value is None or value == "":
            if field_config.get('required', False):
                return ValidationResult(False, "Required field cannot be empty")
            return ValidationResult(True, normalized_value=None)

        field_type = field_config.get('type', 'string').lower()

        # Type-based validation
        type_result = self._validate_by_type(value, field_type)
        if not type_result.is_valid:
            return type_result

        # Apply validation rules
        validation_rules = field_config.get('validation_rules', [])
        for rule in validation_rules:
            rule_result = self._apply_validation_rule(type_result.normalized_value, rule)
            if not rule_result.is_valid:
                return rule_result

        return type_result

    def _validate_by_type(self, value: Any, field_type: str) -> ValidationResult:
        """Validate value by its expected type"""

        if field_type == 'string':
            return self._validate_string(value)
        elif field_type == 'number':
            return self._validate_number(value)
        elif field_type == 'integer':
            return self._validate_integer(value)
        elif field_type == 'float':
            return self._validate_float(value)
        elif field_type == 'boolean':
            return self._validate_boolean(value)
        elif field_type == 'date':
            return self._validate_date(value)
        elif field_type == 'datetime':
            return self._validate_datetime(value)
        elif field_type == 'email':
            return self._validate_email(value)
        elif field_type == 'phone':
            return self._validate_phone(value)
        elif field_type == 'url':
            return self._validate_url(value)
        elif field_type == 'json':
            return self._validate_json(value)
        elif field_type == 'array':
            return self._validate_array(value)
        else:
            # Default to string validation for unknown types
            return self._validate_string(value)

    def _validate_string(self, value: Any) -> ValidationResult:
        """Validate string value"""
        try:
            str_value = str(value).strip()
            return ValidationResult(True, normalized_value=str_value)
        except Exception as e:
            return ValidationResult(False, f"Cannot convert to string: {e}")

    def _validate_number(self, value: Any) -> ValidationResult:
        """Validate numeric value (int or float)"""
        try:
            if isinstance(value, (int, float)):
                return ValidationResult(True, normalized_value=value)

            # Try to parse string as number
            str_value = str(value).strip().replace(',', '')

            if '.' in str_value:
                normalized = float(str_value)
            else:
                normalized = int(str_value)

            return ValidationResult(True, normalized_value=normalized)

        except (ValueError, TypeError) as e:
            return ValidationResult(False, f"Invalid number format: {e}")

    def _validate_integer(self, value: Any) -> ValidationResult:
        """Validate integer value"""
        try:
            if isinstance(value, int):
                return ValidationResult(True, normalized_value=value)

            str_value = str(value).strip().replace(',', '')
            normalized = int(float(str_value))  # Handle "123.0" format

            return ValidationResult(True, normalized_value=normalized)

        except (ValueError, TypeError) as e:
            return ValidationResult(False, f"Invalid integer format: {e}")

    def _validate_float(self, value: Any) -> ValidationResult:
        """Validate float value"""
        try:
            if isinstance(value, float):
                return ValidationResult(True, normalized_value=value)

            str_value = str(value).strip().replace(',', '')
            normalized = float(str_value)

            return ValidationResult(True, normalized_value=normalized)

        except (ValueError, TypeError) as e:
            return ValidationResult(False, f"Invalid float format: {e}")

    def _validate_boolean(self, value: Any) -> ValidationResult:
        """Validate boolean value"""
        if isinstance(value, bool):
            return ValidationResult(True, normalized_value=value)

        if isinstance(value, str):
            str_value = value.strip().lower()
            if str_value in ('true', 'yes', '1', 'on', 'enabled'):
                return ValidationResult(True, normalized_value=True)
            elif str_value in ('false', 'no', '0', 'off', 'disabled'):
                return ValidationResult(True, normalized_value=False)

        return ValidationResult(False, f"Invalid boolean value: {value}")

    def _validate_date(self, value: Any) -> ValidationResult:
        """Validate date value"""
        if isinstance(value, date):
            return ValidationResult(True, normalized_value=value.isoformat())

        if isinstance(value, datetime):
            return ValidationResult(True, normalized_value=value.date().isoformat())

        if isinstance(value, str):
            # Try common date formats
            date_formats = [
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y/%m/%d',
                '%m-%d-%Y',
                '%d-%m-%Y'
            ]

            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(value.strip(), fmt).date()
                    return ValidationResult(True, normalized_value=parsed_date.isoformat())
                except ValueError:
                    continue

        return ValidationResult(False, f"Invalid date format: {value}")

    def _validate_datetime(self, value: Any) -> ValidationResult:
        """Validate datetime value"""
        if isinstance(value, datetime):
            return ValidationResult(True, normalized_value=value.isoformat())

        if isinstance(value, date):
            dt = datetime.combine(value, datetime.min.time())
            return ValidationResult(True, normalized_value=dt.isoformat())

        if isinstance(value, str):
            # Try common datetime formats
            datetime_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%m/%d/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M:%S'
            ]

            for fmt in datetime_formats:
                try:
                    parsed_dt = datetime.strptime(value.strip(), fmt)
                    return ValidationResult(True, normalized_value=parsed_dt.isoformat())
                except ValueError:
                    continue

        return ValidationResult(False, f"Invalid datetime format: {value}")

    def _validate_email(self, value: Any) -> ValidationResult:
        """Validate email address"""
        try:
            str_value = str(value).strip()
            validated_email = validate_email(str_value)
            return ValidationResult(True, normalized_value=validated_email.email)
        except EmailNotValidError as e:
            return ValidationResult(False, f"Invalid email: {e}")
        except Exception as e:
            return ValidationResult(False, f"Email validation error: {e}")

    def _validate_phone(self, value: Any) -> ValidationResult:
        """Validate phone number"""
        try:
            str_value = str(value).strip()

            # Try to parse with phonenumbers library
            try:
                parsed = phonenumbers.parse(str_value, None)
                if phonenumbers.is_valid_number(parsed):
                    formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                    return ValidationResult(True, normalized_value=formatted)
            except NumberParseException:
                pass

            # Fallback to pattern matching
            if re.match(self.PATTERNS['phone'], str_value):
                return ValidationResult(True, normalized_value=str_value, confidence=0.7)

            return ValidationResult(False, "Invalid phone number format")

        except Exception as e:
            return ValidationResult(False, f"Phone validation error: {e}")

    def _validate_url(self, value: Any) -> ValidationResult:
        """Validate URL"""
        try:
            str_value = str(value).strip()

            # Add protocol if missing
            if not str_value.startswith(('http://', 'https://', 'ftp://')):
                str_value = 'https://' + str_value

            parsed = urlparse(str_value)

            if not all([parsed.scheme, parsed.netloc]):
                return ValidationResult(False, "Invalid URL format")

            return ValidationResult(True, normalized_value=str_value)

        except Exception as e:
            return ValidationResult(False, f"URL validation error: {e}")

    def _validate_json(self, value: Any) -> ValidationResult:
        """Validate JSON value"""
        try:
            if isinstance(value, (dict, list)):
                return ValidationResult(True, normalized_value=value)

            str_value = str(value).strip()
            parsed = json.loads(str_value)
            return ValidationResult(True, normalized_value=parsed)

        except json.JSONDecodeError as e:
            return ValidationResult(False, f"Invalid JSON: {e}")
        except Exception as e:
            return ValidationResult(False, f"JSON validation error: {e}")

    def _validate_array(self, value: Any) -> ValidationResult:
        """Validate array/list value"""
        try:
            if isinstance(value, list):
                return ValidationResult(True, normalized_value=value)

            if isinstance(value, str):
                # Try to parse as JSON array
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return ValidationResult(True, normalized_value=parsed)
                except json.JSONDecodeError:
                    pass

                # Try to split by common delimiters
                for delimiter in [',', ';', '|', '\n']:
                    if delimiter in value:
                        array_value = [item.strip() for item in value.split(delimiter)]
                        return ValidationResult(True, normalized_value=array_value, confidence=0.8)

            # Convert single value to array
            return ValidationResult(True, normalized_value=[value], confidence=0.6)

        except Exception as e:
            return ValidationResult(False, f"Array validation error: {e}")

    def _apply_validation_rule(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Apply a specific validation rule"""
        rule_type = rule.get('type')

        if rule_type == 'length':
            return self._validate_length(value, rule)
        elif rule_type == 'range':
            return self._validate_range(value, rule)
        elif rule_type == 'pattern':
            return self._validate_pattern(value, rule)
        elif rule_type == 'enum':
            return self._validate_enum(value, rule)
        elif rule_type == 'custom':
            return self._validate_custom(value, rule)
        else:
            return ValidationResult(True)  # Unknown rule types are ignored

    def _validate_length(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate string/array length"""
        try:
            length = len(str(value)) if not isinstance(value, (list, dict)) else len(value)

            min_length = rule.get('min')
            max_length = rule.get('max')

            if min_length is not None and length < min_length:
                return ValidationResult(False, f"Length {length} is below minimum {min_length}")

            if max_length is not None and length > max_length:
                return ValidationResult(False, f"Length {length} exceeds maximum {max_length}")

            return ValidationResult(True)

        except Exception as e:
            return ValidationResult(False, f"Length validation error: {e}")

    def _validate_range(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate numeric range"""
        try:
            if not isinstance(value, (int, float)):
                numeric_value = float(str(value))
            else:
                numeric_value = value

            min_value = rule.get('min')
            max_value = rule.get('max')

            if min_value is not None and numeric_value < min_value:
                return ValidationResult(False, f"Value {numeric_value} is below minimum {min_value}")

            if max_value is not None and numeric_value > max_value:
                return ValidationResult(False, f"Value {numeric_value} exceeds maximum {max_value}")

            return ValidationResult(True)

        except (ValueError, TypeError) as e:
            return ValidationResult(False, f"Range validation error: {e}")

    def _validate_pattern(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate against regex pattern"""
        try:
            pattern = rule.get('pattern')
            if not pattern:
                return ValidationResult(True)

            str_value = str(value)

            if re.match(pattern, str_value):
                return ValidationResult(True)
            else:
                return ValidationResult(False, f"Value does not match pattern: {pattern}")

        except Exception as e:
            return ValidationResult(False, f"Pattern validation error: {e}")

    def _validate_enum(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate against allowed values"""
        allowed_values = rule.get('values', [])

        if value in allowed_values:
            return ValidationResult(True)

        # Try case-insensitive string matching
        if isinstance(value, str):
            str_value = value.lower()
            for allowed in allowed_values:
                if isinstance(allowed, str) and str_value == allowed.lower():
                    return ValidationResult(True, normalized_value=allowed)

        return ValidationResult(False, f"Value not in allowed list: {allowed_values}")

    def _validate_custom(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Apply custom validation logic"""
        # Placeholder for custom validation functions
        # In a real implementation, this would support custom validation functions
        return ValidationResult(True)

    def validate_schema_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """
        Validate entire data dictionary against schema

        Args:
            data: Dictionary of extracted data
            schema: Schema definition with field configurations

        Returns:
            Dictionary mapping field names to ValidationResult objects
        """
        results = {}
        schema_fields = schema.get('fields', {})

        # Validate each field in the schema
        for field_name, field_config in schema_fields.items():
            field_value = data.get(field_name)
            results[field_name] = self.validate_field(field_value, field_config)

        # Check for unexpected fields in data
        for field_name in data:
            if field_name not in schema_fields:
                results[f"_unexpected_{field_name}"] = ValidationResult(
                    False, f"Unexpected field not in schema: {field_name}"
                )

        return results

    def get_validation_summary(self, validation_results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """Get summary of validation results"""
        total_fields = len(validation_results)
        valid_fields = sum(1 for result in validation_results.values() if result.is_valid)
        invalid_fields = total_fields - valid_fields

        errors = []
        warnings = []

        for field_name, result in validation_results.items():
            if not result.is_valid:
                if field_name.startswith('_unexpected_'):
                    warnings.append(f"{field_name}: {result.error_message}")
                else:
                    errors.append(f"{field_name}: {result.error_message}")

        return {
            'total_fields': total_fields,
            'valid_fields': valid_fields,
            'invalid_fields': invalid_fields,
            'validation_rate': valid_fields / total_fields if total_fields > 0 else 0,
            'errors': errors,
            'warnings': warnings,
            'is_valid': invalid_fields == 0
        }


# Global validator instance
_data_validator = None

def get_data_validator() -> DataValidator:
    """Get singleton data validator instance"""
    global _data_validator
    if _data_validator is None:
        _data_validator = DataValidator()
    return _data_validator


def validate_extracted_data(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[Dict[str, ValidationResult], Dict[str, Any]]:
    """
    Convenience function to validate extracted data

    Returns:
        Tuple of (validation_results, summary)
    """
    validator = get_data_validator()
    results = validator.validate_schema_data(data, schema)
    summary = validator.get_validation_summary(results)
    return results, summary