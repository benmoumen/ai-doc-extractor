"""
T062: Schema validation utilities
Comprehensive validation for schema definitions and compliance checking
"""

import re
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from datetime import datetime
import json


class SchemaValidationError(Exception):
    """Exception raised for schema validation errors"""

    def __init__(self, message: str, field_path: str = None, error_code: str = None):
        super().__init__(message)
        self.field_path = field_path
        self.error_code = error_code
        self.timestamp = datetime.now()


class SchemaValidationResult:
    """Result of schema validation"""

    def __init__(self, is_valid: bool = True, errors: List[str] = None,
                 warnings: List[str] = None, metadata: Dict[str, Any] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def __bool__(self):
        return self.is_valid

    def add_error(self, error: str, field_path: str = None):
        """Add validation error"""
        if field_path:
            error = f"{field_path}: {error}"
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str, field_path: str = None):
        """Add validation warning"""
        if field_path:
            warning = f"{field_path}: {warning}"
        self.warnings.append(warning)

    def merge(self, other: 'SchemaValidationResult'):
        """Merge another validation result"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False
        self.metadata.update(other.metadata)


class SchemaValidator:
    """Comprehensive schema validation system"""

    # Supported field types
    SUPPORTED_TYPES = {
        'string', 'number', 'integer', 'float', 'boolean',
        'date', 'datetime', 'email', 'phone', 'url',
        'json', 'array', 'object', 'text', 'decimal'
    }

    # Supported validation rule types
    SUPPORTED_VALIDATION_RULES = {
        'length', 'range', 'pattern', 'enum', 'custom',
        'format', 'unique', 'dependency'
    }

    # Reserved field names that cannot be used
    RESERVED_FIELD_NAMES = {
        'id', '__internal__', '_metadata', '_validation',
        '_confidence', '_ai_generated'
    }

    def __init__(self):
        """Initialize schema validator"""
        self.validation_cache = {}

    def validate_schema(self, schema: Dict[str, Any],
                       strict: bool = False) -> SchemaValidationResult:
        """
        Validate a complete schema definition

        Args:
            schema: Schema definition to validate
            strict: Whether to apply strict validation rules

        Returns:
            SchemaValidationResult with validation outcome
        """
        result = SchemaValidationResult()

        # Validate schema structure
        self._validate_schema_structure(schema, result)

        # Validate schema metadata
        self._validate_schema_metadata(schema, result)

        # Validate fields
        fields = schema.get('fields', {})
        if not fields:
            result.add_error("Schema must contain at least one field")
        else:
            self._validate_fields(fields, result, strict)

        # Cross-field validations
        self._validate_cross_field_dependencies(fields, result)

        # Schema-level business rules
        self._validate_business_rules(schema, result, strict)

        # Calculate validation metrics
        result.metadata = self._calculate_validation_metrics(schema, result)

        return result

    def _validate_schema_structure(self, schema: Dict[str, Any],
                                  result: SchemaValidationResult):
        """Validate basic schema structure"""
        required_fields = ['id', 'name', 'fields']

        for field in required_fields:
            if field not in schema:
                result.add_error(f"Missing required schema field: {field}")

        # Validate schema ID
        schema_id = schema.get('id')
        if schema_id:
            if not isinstance(schema_id, str) or not schema_id.strip():
                result.add_error("Schema ID must be a non-empty string")
            elif not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', schema_id):
                result.add_error("Schema ID must start with letter and contain only letters, numbers, underscore, hyphen")

        # Validate schema name
        schema_name = schema.get('name')
        if schema_name and (not isinstance(schema_name, str) or not schema_name.strip()):
            result.add_error("Schema name must be a non-empty string")

        # Validate fields structure
        fields = schema.get('fields')
        if fields is not None and not isinstance(fields, dict):
            result.add_error("Schema fields must be a dictionary")

    def _validate_schema_metadata(self, schema: Dict[str, Any],
                                 result: SchemaValidationResult):
        """Validate schema metadata"""
        metadata = schema.get('metadata', {})

        if not isinstance(metadata, dict):
            result.add_error("Schema metadata must be a dictionary")
            return

        # Validate creation date
        created_date = metadata.get('created_date')
        if created_date:
            try:
                datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                result.add_warning("Invalid created_date format in metadata")

        # Validate version
        version = metadata.get('version')
        if version and not isinstance(version, (str, int, float)):
            result.add_warning("Schema version should be a string or number")

    def _validate_fields(self, fields: Dict[str, Any],
                        result: SchemaValidationResult, strict: bool = False):
        """Validate all fields in schema"""
        field_names = set()

        for field_name, field_config in fields.items():
            # Track duplicate field names (case insensitive)
            lower_name = field_name.lower()
            if lower_name in field_names:
                result.add_error(f"Duplicate field name (case insensitive): {field_name}")
            field_names.add(lower_name)

            # Validate individual field
            field_result = self.validate_field(field_name, field_config, strict)
            result.merge(field_result)

    def validate_field(self, field_name: str, field_config: Dict[str, Any],
                      strict: bool = False) -> SchemaValidationResult:
        """
        Validate a single field configuration

        Args:
            field_name: Name of the field
            field_config: Field configuration dictionary
            strict: Whether to apply strict validation

        Returns:
            SchemaValidationResult for the field
        """
        result = SchemaValidationResult()
        field_path = f"fields.{field_name}"

        # Validate field name
        if not self._is_valid_field_name(field_name):
            result.add_error("Invalid field name format", field_path)

        if field_name in self.RESERVED_FIELD_NAMES:
            result.add_error(f"Field name '{field_name}' is reserved", field_path)

        # Validate field configuration structure
        if not isinstance(field_config, dict):
            result.add_error("Field configuration must be a dictionary", field_path)
            return result

        # Validate required field properties
        field_type = field_config.get('type')
        if not field_type:
            result.add_error("Field type is required", field_path)
        elif field_type not in self.SUPPORTED_TYPES:
            result.add_error(f"Unsupported field type: {field_type}", field_path)

        # Validate optional properties
        self._validate_field_display_name(field_config, result, field_path)
        self._validate_field_description(field_config, result, field_path)
        self._validate_field_required(field_config, result, field_path)
        self._validate_field_default(field_config, result, field_path, strict)
        self._validate_field_examples(field_config, result, field_path)
        self._validate_field_validation_rules(field_config, result, field_path)

        # Type-specific validations
        if field_type in self.SUPPORTED_TYPES:
            self._validate_type_specific_rules(field_type, field_config, result, field_path)

        return result

    def _is_valid_field_name(self, field_name: str) -> bool:
        """Check if field name follows valid naming conventions"""
        if not isinstance(field_name, str) or not field_name:
            return False

        # Must start with letter or underscore, contain only alphanumeric, underscore, hyphen
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', field_name) is not None

    def _validate_field_display_name(self, field_config: Dict[str, Any],
                                   result: SchemaValidationResult, field_path: str):
        """Validate field display name"""
        display_name = field_config.get('display_name')
        if display_name is not None:
            if not isinstance(display_name, str) or not display_name.strip():
                result.add_error("Display name must be a non-empty string", field_path)

    def _validate_field_description(self, field_config: Dict[str, Any],
                                  result: SchemaValidationResult, field_path: str):
        """Validate field description"""
        description = field_config.get('description')
        if description is not None and not isinstance(description, str):
            result.add_warning("Field description should be a string", field_path)

    def _validate_field_required(self, field_config: Dict[str, Any],
                               result: SchemaValidationResult, field_path: str):
        """Validate field required flag"""
        required = field_config.get('required')
        if required is not None and not isinstance(required, bool):
            result.add_error("Required field must be a boolean", field_path)

    def _validate_field_default(self, field_config: Dict[str, Any],
                              result: SchemaValidationResult, field_path: str, strict: bool):
        """Validate field default value"""
        default_value = field_config.get('default')
        if default_value is not None:
            field_type = field_config.get('type')

            # In strict mode, validate default value matches field type
            if strict and field_type:
                if not self._value_matches_type(default_value, field_type):
                    result.add_error(f"Default value doesn't match field type {field_type}", field_path)

    def _validate_field_examples(self, field_config: Dict[str, Any],
                               result: SchemaValidationResult, field_path: str):
        """Validate field examples"""
        examples = field_config.get('examples')
        if examples is not None:
            if not isinstance(examples, list):
                result.add_error("Examples must be a list", field_path)
            elif len(examples) > 10:  # Reasonable limit
                result.add_warning("Consider limiting examples to 10 or fewer", field_path)

    def _validate_field_validation_rules(self, field_config: Dict[str, Any],
                                       result: SchemaValidationResult, field_path: str):
        """Validate field validation rules"""
        validation_rules = field_config.get('validation_rules', [])

        if not isinstance(validation_rules, list):
            result.add_error("Validation rules must be a list", field_path)
            return

        for i, rule in enumerate(validation_rules):
            rule_path = f"{field_path}.validation_rules[{i}]"
            self._validate_validation_rule(rule, result, rule_path)

    def _validate_validation_rule(self, rule: Dict[str, Any],
                                result: SchemaValidationResult, rule_path: str):
        """Validate a single validation rule"""
        if not isinstance(rule, dict):
            result.add_error("Validation rule must be a dictionary", rule_path)
            return

        rule_type = rule.get('type')
        if not rule_type:
            result.add_error("Validation rule type is required", rule_path)
            return

        if rule_type not in self.SUPPORTED_VALIDATION_RULES:
            result.add_error(f"Unsupported validation rule type: {rule_type}", rule_path)
            return

        # Type-specific rule validation
        if rule_type == 'length':
            self._validate_length_rule(rule, result, rule_path)
        elif rule_type == 'range':
            self._validate_range_rule(rule, result, rule_path)
        elif rule_type == 'pattern':
            self._validate_pattern_rule(rule, result, rule_path)
        elif rule_type == 'enum':
            self._validate_enum_rule(rule, result, rule_path)

    def _validate_length_rule(self, rule: Dict[str, Any],
                            result: SchemaValidationResult, rule_path: str):
        """Validate length validation rule"""
        min_length = rule.get('min')
        max_length = rule.get('max')

        if min_length is not None:
            if not isinstance(min_length, int) or min_length < 0:
                result.add_error("Length rule min must be a non-negative integer", rule_path)

        if max_length is not None:
            if not isinstance(max_length, int) or max_length < 0:
                result.add_error("Length rule max must be a non-negative integer", rule_path)

        if min_length is not None and max_length is not None:
            if min_length > max_length:
                result.add_error("Length rule min cannot be greater than max", rule_path)

    def _validate_range_rule(self, rule: Dict[str, Any],
                           result: SchemaValidationResult, rule_path: str):
        """Validate range validation rule"""
        min_value = rule.get('min')
        max_value = rule.get('max')

        if min_value is not None and not isinstance(min_value, (int, float)):
            result.add_error("Range rule min must be a number", rule_path)

        if max_value is not None and not isinstance(max_value, (int, float)):
            result.add_error("Range rule max must be a number", rule_path)

        if min_value is not None and max_value is not None:
            if min_value > max_value:
                result.add_error("Range rule min cannot be greater than max", rule_path)

    def _validate_pattern_rule(self, rule: Dict[str, Any],
                             result: SchemaValidationResult, rule_path: str):
        """Validate pattern validation rule"""
        pattern = rule.get('pattern')
        if not pattern:
            result.add_error("Pattern rule requires a pattern", rule_path)
            return

        if not isinstance(pattern, str):
            result.add_error("Pattern must be a string", rule_path)
            return

        try:
            re.compile(pattern)
        except re.error as e:
            result.add_error(f"Invalid regex pattern: {e}", rule_path)

    def _validate_enum_rule(self, rule: Dict[str, Any],
                          result: SchemaValidationResult, rule_path: str):
        """Validate enum validation rule"""
        values = rule.get('values')
        if not values:
            result.add_error("Enum rule requires values list", rule_path)
            return

        if not isinstance(values, list):
            result.add_error("Enum values must be a list", rule_path)
            return

        if len(values) == 0:
            result.add_error("Enum values cannot be empty", rule_path)
        elif len(set(values)) != len(values):
            result.add_warning("Enum values contain duplicates", rule_path)

    def _validate_type_specific_rules(self, field_type: str, field_config: Dict[str, Any],
                                    result: SchemaValidationResult, field_path: str):
        """Validate type-specific field rules"""
        validation_rules = field_config.get('validation_rules', [])

        # Check compatibility between field type and validation rules
        for rule in validation_rules:
            rule_type = rule.get('type')

            if rule_type == 'length' and field_type not in ('string', 'text', 'array'):
                result.add_warning(f"Length rule may not be suitable for {field_type} field", field_path)

            elif rule_type == 'range' and field_type not in ('number', 'integer', 'float', 'decimal'):
                result.add_warning(f"Range rule may not be suitable for {field_type} field", field_path)

            elif rule_type == 'pattern' and field_type not in ('string', 'text', 'email', 'phone', 'url'):
                result.add_warning(f"Pattern rule may not be suitable for {field_type} field", field_path)

    def _validate_cross_field_dependencies(self, fields: Dict[str, Any],
                                         result: SchemaValidationResult):
        """Validate cross-field dependencies"""
        # Check for dependency validation rules
        for field_name, field_config in fields.items():
            validation_rules = field_config.get('validation_rules', [])

            for rule in validation_rules:
                if rule.get('type') == 'dependency':
                    depends_on = rule.get('depends_on')
                    if depends_on and depends_on not in fields:
                        result.add_error(f"Field '{field_name}' depends on non-existent field '{depends_on}'")

    def _validate_business_rules(self, schema: Dict[str, Any],
                               result: SchemaValidationResult, strict: bool):
        """Validate business logic rules"""
        fields = schema.get('fields', {})

        # Check for reasonable number of fields
        if len(fields) > 100:
            result.add_warning("Schema has over 100 fields, consider breaking into multiple schemas")
        elif len(fields) == 0:
            result.add_error("Schema must have at least one field")

        # In strict mode, apply additional business rules
        if strict:
            required_fields = sum(1 for f in fields.values() if f.get('required', False))
            if required_fields == 0:
                result.add_warning("Consider having at least one required field")

            # Check for description coverage
            fields_with_description = sum(1 for f in fields.values() if f.get('description'))
            if fields_with_description / len(fields) < 0.5:
                result.add_warning("Consider adding descriptions to more fields")

    def _value_matches_type(self, value: Any, field_type: str) -> bool:
        """Check if a value matches the expected field type"""
        if field_type == 'string' or field_type == 'text':
            return isinstance(value, str)
        elif field_type == 'number':
            return isinstance(value, (int, float))
        elif field_type == 'integer':
            return isinstance(value, int)
        elif field_type == 'float':
            return isinstance(value, float)
        elif field_type == 'boolean':
            return isinstance(value, bool)
        elif field_type == 'array':
            return isinstance(value, list)
        elif field_type == 'object' or field_type == 'json':
            return isinstance(value, dict)
        else:
            # For other types, be permissive
            return True

    def _calculate_validation_metrics(self, schema: Dict[str, Any],
                                    result: SchemaValidationResult) -> Dict[str, Any]:
        """Calculate validation metrics"""
        fields = schema.get('fields', {})

        total_fields = len(fields)
        required_fields = sum(1 for f in fields.values() if f.get('required', False))
        fields_with_validation = sum(1 for f in fields.values() if f.get('validation_rules'))
        fields_with_examples = sum(1 for f in fields.values() if f.get('examples'))
        fields_with_description = sum(1 for f in fields.values() if f.get('description'))

        return {
            'total_fields': total_fields,
            'required_fields': required_fields,
            'fields_with_validation': fields_with_validation,
            'fields_with_examples': fields_with_examples,
            'fields_with_description': fields_with_description,
            'validation_coverage': fields_with_validation / total_fields if total_fields > 0 else 0,
            'documentation_coverage': fields_with_description / total_fields if total_fields > 0 else 0,
            'error_count': len(result.errors),
            'warning_count': len(result.warnings)
        }

    def validate_schema_compatibility(self, schema1: Dict[str, Any],
                                    schema2: Dict[str, Any]) -> SchemaValidationResult:
        """
        Check compatibility between two schemas

        Args:
            schema1: First schema (typically the new/updated one)
            schema2: Second schema (typically the existing one)

        Returns:
            SchemaValidationResult indicating compatibility
        """
        result = SchemaValidationResult()

        fields1 = schema1.get('fields', {})
        fields2 = schema2.get('fields', {})

        # Check for removed fields
        removed_fields = set(fields2.keys()) - set(fields1.keys())
        for field in removed_fields:
            if fields2[field].get('required', False):
                result.add_error(f"Required field '{field}' was removed")
            else:
                result.add_warning(f"Optional field '{field}' was removed")

        # Check for type changes
        common_fields = set(fields1.keys()) & set(fields2.keys())
        for field in common_fields:
            type1 = fields1[field].get('type')
            type2 = fields2[field].get('type')

            if type1 != type2:
                result.add_error(f"Field '{field}' type changed from '{type2}' to '{type1}'")

            # Check if required status changed
            req1 = fields1[field].get('required', False)
            req2 = fields2[field].get('required', False)

            if req1 and not req2:
                result.add_error(f"Field '{field}' became required")
            elif not req1 and req2:
                result.add_warning(f"Field '{field}' became optional")

        # Check for new required fields
        new_fields = set(fields1.keys()) - set(fields2.keys())
        for field in new_fields:
            if fields1[field].get('required', False):
                result.add_error(f"New required field '{field}' added")
            else:
                result.add_warning(f"New optional field '{field}' added")

        result.metadata = {
            'removed_fields': list(removed_fields),
            'new_fields': list(new_fields),
            'common_fields': list(common_fields),
            'breaking_changes': len([e for e in result.errors if 'required' in e.lower()])
        }

        return result

    def suggest_schema_improvements(self, schema: Dict[str, Any]) -> List[str]:
        """Suggest improvements for schema definition"""
        suggestions = []
        fields = schema.get('fields', {})

        # Suggest adding descriptions
        fields_without_description = [name for name, config in fields.items()
                                    if not config.get('description')]
        if fields_without_description:
            suggestions.append(f"Add descriptions to fields: {', '.join(fields_without_description[:5])}")

        # Suggest adding examples
        fields_without_examples = [name for name, config in fields.items()
                                 if not config.get('examples')]
        if len(fields_without_examples) > len(fields) * 0.7:
            suggestions.append("Consider adding examples to more fields to improve clarity")

        # Suggest validation rules
        fields_without_validation = [name for name, config in fields.items()
                                   if not config.get('validation_rules')]
        if len(fields_without_validation) > len(fields) * 0.5:
            suggestions.append("Consider adding validation rules to ensure data quality")

        # Suggest schema metadata
        if not schema.get('description'):
            suggestions.append("Add a description to explain the schema's purpose")

        if not schema.get('metadata', {}).get('version'):
            suggestions.append("Consider adding version information to track schema changes")

        return suggestions


# Global validator instance
_schema_validator = None

def get_schema_validator() -> SchemaValidator:
    """Get singleton schema validator instance"""
    global _schema_validator
    if _schema_validator is None:
        _schema_validator = SchemaValidator()
    return _schema_validator


def validate_schema_definition(schema: Dict[str, Any], strict: bool = False) -> SchemaValidationResult:
    """
    Convenience function to validate schema definition

    Args:
        schema: Schema definition to validate
        strict: Whether to apply strict validation rules

    Returns:
        SchemaValidationResult
    """
    validator = get_schema_validator()
    return validator.validate_schema(schema, strict)