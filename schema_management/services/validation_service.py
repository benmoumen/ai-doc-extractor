"""
Validation service implementation.
Based on data-model.md specifications.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from urllib.parse import urlparse
import ipaddress

from ..models.field import Field, FieldType
from ..models.validation_rule import ValidationRule, ValidationRuleType, ValidationSeverity
from ..models.schema import Schema
from ..services.schema_service import SchemaService
from ..storage.schema_storage import SchemaStorage


logger = logging.getLogger(__name__)


class ValidationServiceError(Exception):
    """Custom exception for validation service operations"""
    pass


class ValidationResult:
    """
    Represents the result of a validation operation
    """
    
    def __init__(self, field_name: str, value: Any, field_type: str):
        self.field_name = field_name
        self.value = value
        self.field_type = field_type
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.info = []
        self.confidence = 1.0
        self.normalized_value = value
    
    def add_error(self, message: str, rule_type: str = None):
        """Add validation error"""
        self.is_valid = False
        self.errors.append({"message": message, "rule_type": rule_type})
    
    def add_warning(self, message: str, rule_type: str = None):
        """Add validation warning"""
        self.warnings.append({"message": message, "rule_type": rule_type})
    
    def add_info(self, message: str, rule_type: str = None):
        """Add validation info"""
        self.info.append({"message": message, "rule_type": rule_type})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "field_name": self.field_name,
            "value": self.value,
            "field_type": self.field_type,
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "confidence": self.confidence,
            "normalized_value": self.normalized_value
        }


class SchemaValidationResult:
    """
    Represents the result of schema-level validation
    """
    
    def __init__(self, schema_id: str):
        self.schema_id = schema_id
        self.is_valid = True
        self.field_results = {}
        self.schema_errors = []
        self.cross_field_errors = []
        self.overall_confidence = 1.0
        self.validation_timestamp = datetime.now()
    
    def add_field_result(self, field_name: str, result: ValidationResult):
        """Add field validation result"""
        self.field_results[field_name] = result
        if not result.is_valid:
            self.is_valid = False
    
    def add_schema_error(self, message: str):
        """Add schema-level error"""
        self.is_valid = False
        self.schema_errors.append(message)
    
    def add_cross_field_error(self, message: str, affected_fields: List[str] = None):
        """Add cross-field validation error"""
        self.is_valid = False
        self.cross_field_errors.append({
            "message": message,
            "affected_fields": affected_fields or []
        })
    
    def calculate_overall_confidence(self):
        """Calculate overall confidence based on field results"""
        if not self.field_results:
            self.overall_confidence = 1.0
            return
        
        confidences = [result.confidence for result in self.field_results.values()]
        self.overall_confidence = sum(confidences) / len(confidences)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "schema_id": self.schema_id,
            "is_valid": self.is_valid,
            "field_results": {name: result.to_dict() for name, result in self.field_results.items()},
            "schema_errors": self.schema_errors,
            "cross_field_errors": self.cross_field_errors,
            "overall_confidence": self.overall_confidence,
            "validation_timestamp": self.validation_timestamp.isoformat()
        }


class ValidationService:
    """
    Service layer for validation operations
    
    Provides comprehensive validation functionality for fields, schemas,
    and extracted data against schema definitions.
    """
    
    def __init__(self, storage: SchemaStorage = None, schema_service: SchemaService = None):
        """
        Initialize validation service
        
        Args:
            storage: Storage backend
            schema_service: Schema service for schema operations
        """
        self.storage = storage or SchemaStorage()
        self.schema_service = schema_service or SchemaService(self.storage)
        
        # Precompiled regex patterns for performance
        self._email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self._phone_pattern = re.compile(r'^[\+]?[1-9][\d]{0,15}$')
        self._uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.I)
    
    def validate_field_value(self, field: Field, value: Any, 
                           context_values: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate a single field value against its configuration
        
        Args:
            field: Field object with validation rules
            value: Value to validate
            context_values: Other field values for dependency validation
            
        Returns:
            ValidationResult object
        """
        result = ValidationResult(field.name, value, field.type)
        context_values = context_values or {}
        
        try:
            # Check if field is required
            if field.required and (value is None or value == ""):
                result.add_error("This field is required", "required")
                return result
            
            # Skip further validation if value is empty and field is not required
            if value is None or value == "":
                return result
            
            # Type-specific validation
            self._validate_field_type(field, value, result)
            
            # Apply validation rules
            applicable_rules = [
                rule for rule in field.validation_rules 
                if self._is_rule_applicable(rule, context_values)
            ]
            
            for rule_dict in applicable_rules:
                rule = ValidationRule.from_dict(rule_dict)
                self._apply_validation_rule(rule, value, result, context_values)
            
            # Calculate confidence based on validation results
            result.confidence = self._calculate_field_confidence(result)
            
        except Exception as e:
            logger.error(f"Error validating field {field.name}: {e}")
            result.add_error(f"Validation error: {str(e)}")
        
        return result
    
    def validate_extracted_data(self, schema_id: str, extracted_data: Dict[str, Any]) -> SchemaValidationResult:
        """
        Validate extracted data against a schema
        
        Args:
            schema_id: Schema identifier
            extracted_data: Dictionary of field names to values
            
        Returns:
            SchemaValidationResult object
        """
        result = SchemaValidationResult(schema_id)
        
        try:
            # Load schema
            schema = self.schema_service.get_schema(schema_id)
            if not schema:
                result.add_schema_error(f"Schema {schema_id} not found")
                return result
            
            # Validate each field
            for field_name, field_config in schema.fields.items():
                field = Field.from_dict(field_config)
                value = extracted_data.get(field_name)
                
                field_result = self.validate_field_value(field, value, extracted_data)
                result.add_field_result(field_name, field_result)
            
            # Check for unexpected fields
            schema_fields = set(schema.fields.keys())
            extracted_fields = set(extracted_data.keys())
            unexpected_fields = extracted_fields - schema_fields
            
            if unexpected_fields:
                result.add_schema_error(f"Unexpected fields found: {', '.join(unexpected_fields)}")
            
            # Apply schema-level validation rules
            self._apply_schema_validation_rules(schema, extracted_data, result)
            
            # Apply cross-field validation
            self._apply_cross_field_validation(schema, extracted_data, result)
            
            # Calculate overall confidence
            result.calculate_overall_confidence()
            
        except Exception as e:
            logger.error(f"Error validating extracted data for schema {schema_id}: {e}")
            result.add_schema_error(f"Validation error: {str(e)}")
        
        return result
    
    def validate_schema_structure(self, schema: Schema) -> List[Dict[str, str]]:
        """
        Validate schema structure and configuration
        
        Args:
            schema: Schema object to validate
            
        Returns:
            List of validation error dictionaries
        """
        errors = []
        
        try:
            # Use built-in schema validation
            schema_errors = schema.validate_structure()
            errors.extend(schema_errors)
            
            # Additional business logic validation
            errors.extend(self._validate_schema_business_rules(schema))
            
        except Exception as e:
            logger.error(f"Error validating schema structure: {e}")
            errors.append({"field": "general", "message": f"Validation error: {str(e)}"})
        
        return errors
    
    def validate_field_configuration(self, field: Field) -> List[str]:
        """
        Validate field configuration
        
        Args:
            field: Field object to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        try:
            # Use built-in field validation
            errors.extend(field.validate_structure())
            
            # Additional validation for field configuration
            errors.extend(self._validate_field_business_rules(field))
            
        except Exception as e:
            logger.error(f"Error validating field configuration: {e}")
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def validate_validation_rule(self, rule: ValidationRule, field_type: str = None) -> List[str]:
        """
        Validate validation rule configuration
        
        Args:
            rule: ValidationRule object to validate
            field_type: Field type for compatibility checking
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        try:
            # Use built-in rule validation
            errors.extend(rule.validate_structure())
            
            # Check rule compatibility with field type
            if field_type:
                compatibility_errors = self._check_rule_field_compatibility(rule, field_type)
                errors.extend(compatibility_errors)
            
        except Exception as e:
            logger.error(f"Error validating validation rule: {e}")
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def suggest_validation_rules(self, field: Field, sample_values: List[Any] = None) -> List[ValidationRule]:
        """
        Suggest validation rules based on field type and sample values
        
        Args:
            field: Field object
            sample_values: Sample values for analysis
            
        Returns:
            List of suggested ValidationRule objects
        """
        suggestions = []
        sample_values = sample_values or []
        
        try:
            # Always suggest required rule for required fields
            if field.required:
                suggestions.append(ValidationRule.create_required_rule())
            
            # Type-specific suggestions
            if field.type == "text":
                suggestions.extend(self._suggest_text_validation_rules(sample_values))
            elif field.type == "number":
                suggestions.extend(self._suggest_number_validation_rules(sample_values))
            elif field.type == "email":
                suggestions.append(ValidationRule.create_format_rule("email"))
            elif field.type == "phone":
                suggestions.append(ValidationRule.create_format_rule("phone"))
            elif field.type == "url":
                suggestions.append(ValidationRule.create_format_rule("url"))
            elif field.type == "date":
                suggestions.append(ValidationRule.create_format_rule("date"))
            
        except Exception as e:
            logger.error(f"Error suggesting validation rules: {e}")
        
        return suggestions
    
    def _validate_field_type(self, field: Field, value: Any, result: ValidationResult):
        """Validate value against field type"""
        field_type = field.type
        
        if field_type == "text":
            if not isinstance(value, str):
                result.add_error(f"Expected text, got {type(value).__name__}")
        
        elif field_type == "number":
            try:
                normalized = float(value)
                result.normalized_value = normalized
            except (ValueError, TypeError):
                result.add_error("Value is not a valid number")
        
        elif field_type == "date":
            if not self._is_valid_date_string(value):
                result.add_error("Value is not a valid date")
        
        elif field_type == "email":
            if not self._email_pattern.match(str(value)):
                result.add_error("Value is not a valid email address")
        
        elif field_type == "phone":
            cleaned_phone = re.sub(r'[^\d+]', '', str(value))
            if not self._phone_pattern.match(cleaned_phone):
                result.add_error("Value is not a valid phone number")
            else:
                result.normalized_value = cleaned_phone
        
        elif field_type == "url":
            if not self._is_valid_url(value):
                result.add_error("Value is not a valid URL")
        
        elif field_type == "boolean":
            if not self._is_valid_boolean(value):
                result.add_error("Value is not a valid boolean")
            else:
                result.normalized_value = self._normalize_boolean(value)
    
    def _apply_validation_rule(self, rule: ValidationRule, value: Any, 
                              result: ValidationResult, context_values: Dict[str, Any]):
        """Apply a specific validation rule"""
        try:
            if rule.type == "required":
                # Already handled in main validation
                pass
            
            elif rule.type == "length":
                self._validate_length_rule(rule, value, result)
            
            elif rule.type == "range":
                self._validate_range_rule(rule, value, result)
            
            elif rule.type == "pattern":
                self._validate_pattern_rule(rule, value, result)
            
            elif rule.type == "format":
                self._validate_format_rule(rule, value, result)
            
            elif rule.type == "options":
                self._validate_options_rule(rule, value, result)
            
            elif rule.type == "custom":
                self._validate_custom_rule(rule, value, result, context_values)
            
        except Exception as e:
            message = f"Error applying {rule.type} validation: {str(e)}"
            if rule.severity == ValidationSeverity.ERROR:
                result.add_error(message, rule.type)
            elif rule.severity == ValidationSeverity.WARNING:
                result.add_warning(message, rule.type)
            else:
                result.add_info(message, rule.type)
    
    def _validate_length_rule(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Validate length rule"""
        text_value = str(value)
        length = len(text_value)
        
        min_length = rule.get_parameter("min_length")
        max_length = rule.get_parameter("max_length")
        
        if min_length is not None and length < min_length:
            if rule.severity == ValidationSeverity.ERROR:
                result.add_error(rule.message, rule.type)
            elif rule.severity == ValidationSeverity.WARNING:
                result.add_warning(rule.message, rule.type)
            else:
                result.add_info(rule.message, rule.type)
        
        if max_length is not None and length > max_length:
            if rule.severity == ValidationSeverity.ERROR:
                result.add_error(rule.message, rule.type)
            elif rule.severity == ValidationSeverity.WARNING:
                result.add_warning(rule.message, rule.type)
            else:
                result.add_info(rule.message, rule.type)
    
    def _validate_range_rule(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Validate range rule"""
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            result.add_error("Cannot validate range for non-numeric value", rule.type)
            return
        
        min_value = rule.get_parameter("min_value")
        max_value = rule.get_parameter("max_value")
        
        if min_value is not None and numeric_value < min_value:
            if rule.severity == ValidationSeverity.ERROR:
                result.add_error(rule.message, rule.type)
            elif rule.severity == ValidationSeverity.WARNING:
                result.add_warning(rule.message, rule.type)
            else:
                result.add_info(rule.message, rule.type)
        
        if max_value is not None and numeric_value > max_value:
            if rule.severity == ValidationSeverity.ERROR:
                result.add_error(rule.message, rule.type)
            elif rule.severity == ValidationSeverity.WARNING:
                result.add_warning(rule.message, rule.type)
            else:
                result.add_info(rule.message, rule.type)
    
    def _validate_pattern_rule(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Validate pattern rule"""
        pattern = rule.get_parameter("pattern")
        if not pattern:
            result.add_error("Pattern validation rule missing pattern parameter", rule.type)
            return
        
        try:
            if not re.match(pattern, str(value)):
                if rule.severity == ValidationSeverity.ERROR:
                    result.add_error(rule.message, rule.type)
                elif rule.severity == ValidationSeverity.WARNING:
                    result.add_warning(rule.message, rule.type)
                else:
                    result.add_info(rule.message, rule.type)
        except re.error as e:
            result.add_error(f"Invalid regex pattern: {e}", rule.type)
    
    def _validate_format_rule(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Validate format rule"""
        format_type = rule.get_parameter("format")
        str_value = str(value)
        
        is_valid = False
        
        if format_type == "email":
            is_valid = self._email_pattern.match(str_value) is not None
        elif format_type == "phone":
            cleaned = re.sub(r'[^\d+]', '', str_value)
            is_valid = self._phone_pattern.match(cleaned) is not None
        elif format_type == "url":
            is_valid = self._is_valid_url(str_value)
        elif format_type == "date":
            is_valid = self._is_valid_date_string(str_value)
        elif format_type == "uuid":
            is_valid = self._uuid_pattern.match(str_value) is not None
        elif format_type == "ipv4":
            try:
                ipaddress.IPv4Address(str_value)
                is_valid = True
            except ipaddress.AddressValueError:
                is_valid = False
        elif format_type == "ipv6":
            try:
                ipaddress.IPv6Address(str_value)
                is_valid = True
            except ipaddress.AddressValueError:
                is_valid = False
        
        if not is_valid:
            if rule.severity == ValidationSeverity.ERROR:
                result.add_error(rule.message, rule.type)
            elif rule.severity == ValidationSeverity.WARNING:
                result.add_warning(rule.message, rule.type)
            else:
                result.add_info(rule.message, rule.type)
    
    def _validate_options_rule(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Validate options rule"""
        options = rule.get_parameter("options")
        if not options:
            result.add_error("Options validation rule missing options parameter", rule.type)
            return
        
        if value not in options:
            if rule.severity == ValidationSeverity.ERROR:
                result.add_error(rule.message, rule.type)
            elif rule.severity == ValidationSeverity.WARNING:
                result.add_warning(rule.message, rule.type)
            else:
                result.add_info(rule.message, rule.type)
    
    def _validate_custom_rule(self, rule: ValidationRule, value: Any, 
                             result: ValidationResult, context_values: Dict[str, Any]):
        """Validate custom rule (placeholder for custom validation logic)"""
        # Custom validation logic would be implemented here
        # This is a placeholder for extensibility
        pass
    
    def _apply_schema_validation_rules(self, schema: Schema, extracted_data: Dict[str, Any],
                                     result: SchemaValidationResult):
        """Apply schema-level validation rules"""
        for rule_dict in schema.validation_rules:
            try:
                # Schema-level validation rules would be applied here
                # This is a placeholder for schema-wide validation logic
                pass
            except Exception as e:
                result.add_schema_error(f"Schema validation rule error: {str(e)}")
    
    def _apply_cross_field_validation(self, schema: Schema, extracted_data: Dict[str, Any],
                                    result: SchemaValidationResult):
        """Apply cross-field validation"""
        # Check field dependencies
        for field_name, field_config in schema.fields.items():
            depends_on = field_config.get("depends_on")
            if depends_on:
                condition = field_config.get("condition")
                condition_value = field_config.get("condition_value")
                
                if depends_on in extracted_data:
                    dependency_value = extracted_data[depends_on]
                    field_value = extracted_data.get(field_name)
                    
                    # Simple condition checking
                    dependency_met = False
                    if condition == "==":
                        dependency_met = dependency_value == condition_value
                    elif condition == "!=":
                        dependency_met = dependency_value != condition_value
                    # Add more conditions as needed
                    
                    if dependency_met and (field_value is None or field_value == ""):
                        if field_config.get("required", False):
                            result.add_cross_field_error(
                                f"Field '{field_name}' is required when '{depends_on}' is '{condition_value}'",
                                [field_name, depends_on]
                            )
    
    def _is_rule_applicable(self, rule_dict: Dict[str, Any], context_values: Dict[str, Any]) -> bool:
        """Check if validation rule is applicable given context"""
        try:
            rule = ValidationRule.from_dict(rule_dict)
            return rule.is_applicable(context_values)
        except Exception as e:
            logger.error(f"Error checking rule applicability: {e}")
            return True  # Default to applicable if check fails
    
    def _calculate_field_confidence(self, result: ValidationResult) -> float:
        """Calculate confidence score for field validation"""
        if not result.is_valid:
            return 0.5  # Low confidence for invalid fields
        
        if result.warnings:
            return 0.8  # Reduced confidence for warnings
        
        return 1.0  # Full confidence for valid fields without warnings
    
    def _validate_schema_business_rules(self, schema: Schema) -> List[Dict[str, str]]:
        """Validate schema business rules"""
        errors = []
        
        # Check minimum number of fields
        if len(schema.fields) == 0:
            errors.append({"field": "fields", "message": "Schema must have at least one field"})
        
        # Check for at least one required field
        required_fields = [name for name, config in schema.fields.items() if config.get("required", False)]
        if not required_fields:
            errors.append({"field": "fields", "message": "Schema should have at least one required field"})
        
        return errors
    
    def _validate_field_business_rules(self, field: Field) -> List[str]:
        """Validate field business rules"""
        errors = []
        
        # Check validation rules are appropriate for field type
        for rule_dict in field.validation_rules:
            try:
                rule = ValidationRule.from_dict(rule_dict)
                compatibility_errors = self._check_rule_field_compatibility(rule, field.type)
                errors.extend(compatibility_errors)
            except Exception as e:
                errors.append(f"Invalid validation rule: {str(e)}")
        
        return errors
    
    def _check_rule_field_compatibility(self, rule: ValidationRule, field_type: str) -> List[str]:
        """Check if validation rule is compatible with field type"""
        errors = []
        
        # Length rules only applicable to text-like fields
        if rule.type == "length" and field_type not in ["text", "email", "phone", "url"]:
            errors.append(f"Length validation not applicable to {field_type} fields")
        
        # Range rules only applicable to numeric fields
        if rule.type == "range" and field_type != "number":
            errors.append(f"Range validation not applicable to {field_type} fields")
        
        # Format rules should match field type
        if rule.type == "format":
            format_type = rule.get_parameter("format")
            if format_type and format_type != field_type:
                errors.append(f"Format validation '{format_type}' doesn't match field type '{field_type}'")
        
        return errors
    
    def _suggest_text_validation_rules(self, sample_values: List[Any]) -> List[ValidationRule]:
        """Suggest validation rules for text fields"""
        suggestions = []
        
        if sample_values:
            # Analyze length patterns
            lengths = [len(str(val)) for val in sample_values if val is not None]
            if lengths:
                min_len = min(lengths)
                max_len = max(lengths)
                
                # Suggest length validation if there's a clear pattern
                if max_len - min_len <= 5:  # Similar lengths
                    suggestions.append(ValidationRule.create_length_rule(
                        min_length=max(1, min_len - 2),
                        max_length=max_len + 2
                    ))
        
        return suggestions
    
    def _suggest_number_validation_rules(self, sample_values: List[Any]) -> List[ValidationRule]:
        """Suggest validation rules for number fields"""
        suggestions = []
        
        if sample_values:
            # Analyze numeric patterns
            numeric_values = []
            for val in sample_values:
                try:
                    numeric_values.append(float(val))
                except (ValueError, TypeError):
                    continue
            
            if numeric_values:
                min_val = min(numeric_values)
                max_val = max(numeric_values)
                
                # Suggest range if values are positive
                if min_val >= 0:
                    suggestions.append(ValidationRule.create_range_rule(min_value=0))
                
                # Suggest specific range if values are in a tight range
                if max_val - min_val <= 1000:
                    suggestions.append(ValidationRule.create_range_rule(
                        min_value=min_val,
                        max_value=max_val
                    ))
        
        return suggestions
    
    def _is_valid_date_string(self, value: str) -> bool:
        """Check if string is a valid date"""
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # MM-DD-YYYY
        ]
        
        return any(re.match(pattern, str(value)) for pattern in date_patterns)
    
    def _is_valid_url(self, value: str) -> bool:
        """Check if string is a valid URL"""
        try:
            result = urlparse(str(value))
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _is_valid_boolean(self, value: Any) -> bool:
        """Check if value is a valid boolean"""
        if isinstance(value, bool):
            return True
        
        str_value = str(value).lower()
        return str_value in ['true', 'false', '1', '0', 'yes', 'no', 'on', 'off']
    
    def _normalize_boolean(self, value: Any) -> bool:
        """Normalize value to boolean"""
        if isinstance(value, bool):
            return value
        
        str_value = str(value).lower()
        return str_value in ['true', '1', 'yes', 'on']