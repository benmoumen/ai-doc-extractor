"""
Unit tests for Validation Service.

Tests the validation service including field validation, schema validation,
cross-field validation, and validation rule processing.
"""

import pytest
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import re

# Import the modules we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from schema_management.services.validation_service import ValidationService, ValidationResult, SchemaValidationResult
from schema_management.models.schema import Schema, SchemaStatus
from schema_management.models.field import Field, FieldType
from schema_management.models.validation_rule import ValidationRule, ValidationRuleType, ValidationSeverity
from schema_management.storage.schema_storage import SchemaStorage
from schema_management.services.schema_service import SchemaService
import tempfile
import shutil


class TestValidationService:
    """Test cases for ValidationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SchemaStorage(data_dir=self.temp_dir)
        self.schema_service = SchemaService(self.storage)
        self.validation_service = ValidationService(self.storage, self.schema_service)
        
        # Sample validation rules
        self.string_rules = [
            ValidationRule(
                rule_type=ValidationRuleType.MIN_LENGTH,
                message="Must be at least 2 characters",
                parameters={"length": 2},
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                rule_type=ValidationRuleType.MAX_LENGTH,
                message="Must not exceed 50 characters",
                parameters={"length": 50},
                severity=ValidationSeverity.ERROR
            )
        ]
        
        self.email_rules = [
            ValidationRule(
                rule_type=ValidationRuleType.EMAIL_FORMAT,
                message="Must be a valid email address",
                severity=ValidationSeverity.ERROR
            )
        ]
        
        self.number_rules = [
            ValidationRule(
                rule_type=ValidationRuleType.MIN_VALUE,
                message="Must be at least 0",
                parameters={"value": 0},
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                rule_type=ValidationRuleType.MAX_VALUE,
                message="Must not exceed 120",
                parameters={"value": 120},
                severity=ValidationSeverity.ERROR
            )
        ]
        
        # Sample schema
        self.sample_schema = Schema(
            id="validation_test_schema",
            name="Validation Test Schema",
            description="Schema for testing validation",
            version="1.0.0",
            fields=[
                Field(
                    id="name_field",
                    name="full_name",
                    display_name="Full Name",
                    field_type=FieldType.STRING,
                    required=True,
                    validation_rules=self.string_rules
                ),
                Field(
                    id="email_field",
                    name="email",
                    display_name="Email Address",
                    field_type=FieldType.EMAIL,
                    required=True,
                    validation_rules=self.email_rules
                ),
                Field(
                    id="age_field",
                    name="age",
                    display_name="Age",
                    field_type=FieldType.NUMBER,
                    required=False,
                    validation_rules=self.number_rules
                )
            ]
        )

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_string_field_valid(self):
        """Test validation of valid string values."""
        field = Field(
            id="string_test",
            name="test_string",
            display_name="Test String",
            field_type=FieldType.STRING,
            required=True,
            validation_rules=self.string_rules
        )
        
        valid_values = ["John", "Jane Doe", "A valid name with spaces", "X" * 25]
        
        for value in valid_values:
            result = self.validation_service.validate_field_value(field, value)
            assert result.is_valid is True, f"Value '{value}' should be valid"
            assert len(result.errors) == 0

    def test_validate_string_field_invalid(self):
        """Test validation of invalid string values."""
        field = Field(
            id="string_test",
            name="test_string",
            display_name="Test String",
            field_type=FieldType.STRING,
            required=True,
            validation_rules=self.string_rules
        )
        
        invalid_cases = [
            ("", "Empty string for required field"),
            ("X", "Too short (min 2 characters)"),
            ("X" * 51, "Too long (max 50 characters)")
        ]
        
        for value, reason in invalid_cases:
            result = self.validation_service.validate_field_value(field, value)
            assert result.is_valid is False, f"Value '{value}' should be invalid: {reason}"
            assert len(result.errors) > 0

    def test_validate_email_field(self):
        """Test email field validation."""
        field = Field(
            id="email_test",
            name="email",
            display_name="Email",
            field_type=FieldType.EMAIL,
            required=True,
            validation_rules=self.email_rules
        )
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "firstname.lastname@company-name.com"
        ]
        
        for email in valid_emails:
            result = self.validation_service.validate_field_value(field, email)
            assert result.is_valid is True, f"Email '{email}' should be valid"
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user name@example.com",  # Space in local part
            "user@domain",           # No TLD
            ""                       # Empty for required field
        ]
        
        for email in invalid_emails:
            result = self.validation_service.validate_field_value(field, email)
            assert result.is_valid is False, f"Email '{email}' should be invalid"

    def test_validate_number_field(self):
        """Test number field validation."""
        field = Field(
            id="number_test",
            name="age",
            display_name="Age",
            field_type=FieldType.NUMBER,
            required=True,
            validation_rules=self.number_rules
        )
        
        valid_numbers = [0, 25, 50, 120, "30", "75.5"]
        
        for number in valid_numbers:
            result = self.validation_service.validate_field_value(field, number)
            assert result.is_valid is True, f"Number '{number}' should be valid"
        
        invalid_numbers = [-1, 121, 200, "not_a_number", ""]
        
        for number in invalid_numbers:
            result = self.validation_service.validate_field_value(field, number)
            assert result.is_valid is False, f"Number '{number}' should be invalid"

    def test_validate_boolean_field(self):
        """Test boolean field validation."""
        field = Field(
            id="boolean_test",
            name="active",
            display_name="Active",
            field_type=FieldType.BOOLEAN,
            required=True
        )
        
        valid_booleans = [True, False, "true", "false", "1", "0", 1, 0]
        
        for value in valid_booleans:
            result = self.validation_service.validate_field_value(field, value)
            assert result.is_valid is True, f"Boolean '{value}' should be valid"
        
        invalid_booleans = ["maybe", "yes", "no", 2, -1]
        
        for value in invalid_booleans:
            result = self.validation_service.validate_field_value(field, value)
            assert result.is_valid is False, f"Boolean '{value}' should be invalid"

    def test_validate_date_field(self):
        """Test date field validation."""
        field = Field(
            id="date_test",
            name="birth_date",
            display_name="Birth Date",
            field_type=FieldType.DATE,
            required=True
        )
        
        valid_dates = [
            "2023-12-25",
            "1990-01-01",
            date(2023, 12, 25),
            datetime(2023, 12, 25)
        ]
        
        for date_value in valid_dates:
            result = self.validation_service.validate_field_value(field, date_value)
            assert result.is_valid is True, f"Date '{date_value}' should be valid"
        
        invalid_dates = [
            "invalid-date",
            "2023-13-01",  # Invalid month
            "2023-02-30",  # Invalid day
            "not a date",
            ""
        ]
        
        for date_value in invalid_dates:
            result = self.validation_service.validate_field_value(field, date_value)
            assert result.is_valid is False, f"Date '{date_value}' should be invalid"

    def test_validate_select_field(self):
        """Test select field validation."""
        field = Field(
            id="select_test",
            name="country",
            display_name="Country",
            field_type=FieldType.SELECT,
            required=True,
            options=["USA", "Canada", "UK", "Germany"]
        )
        
        # Valid selections
        for option in field.options:
            result = self.validation_service.validate_field_value(field, option)
            assert result.is_valid is True, f"Option '{option}' should be valid"
        
        # Invalid selections
        invalid_options = ["France", "Japan", "", "Invalid Option"]
        
        for option in invalid_options:
            result = self.validation_service.validate_field_value(field, option)
            assert result.is_valid is False, f"Option '{option}' should be invalid"

    def test_validate_multiselect_field(self):
        """Test multiselect field validation."""
        field = Field(
            id="multiselect_test",
            name="skills",
            display_name="Skills",
            field_type=FieldType.MULTISELECT,
            required=True,
            options=["Python", "JavaScript", "Java", "C++", "Go"]
        )
        
        # Valid selections
        valid_selections = [
            ["Python"],
            ["Python", "JavaScript"],
            ["Python", "Java", "C++"],
            field.options  # All options
        ]
        
        for selection in valid_selections:
            result = self.validation_service.validate_field_value(field, selection)
            assert result.is_valid is True, f"Selection {selection} should be valid"
        
        # Invalid selections
        invalid_selections = [
            ["Python", "Ruby"],  # Ruby not in options
            ["Invalid"],         # Not in options
            [],                  # Empty for required field
            ""                   # Wrong type
        ]
        
        for selection in invalid_selections:
            result = self.validation_service.validate_field_value(field, selection)
            assert result.is_valid is False, f"Selection {selection} should be invalid"

    def test_validate_regex_rule(self):
        """Test regex validation rule."""
        regex_rule = ValidationRule(
            rule_type=ValidationRuleType.REGEX,
            message="Must contain only letters and spaces",
            parameters={"pattern": "^[A-Za-z ]+$"},
            severity=ValidationSeverity.ERROR
        )
        
        field = Field(
            id="regex_test",
            name="name",
            display_name="Name",
            field_type=FieldType.STRING,
            validation_rules=[regex_rule]
        )
        
        valid_values = ["John Doe", "Mary Jane", "A B C", "SingleName"]
        
        for value in valid_values:
            result = self.validation_service.validate_field_value(field, value)
            assert result.is_valid is True, f"Value '{value}' should match regex"
        
        invalid_values = ["John123", "Name!", "Test@Value", "Name-Hyphen"]
        
        for value in invalid_values:
            result = self.validation_service.validate_field_value(field, value)
            assert result.is_valid is False, f"Value '{value}' should not match regex"

    def test_validate_phone_field(self):
        """Test phone field validation."""
        field = Field(
            id="phone_test",
            name="phone",
            display_name="Phone Number",
            field_type=FieldType.PHONE,
            required=True
        )
        
        valid_phones = [
            "+1234567890",
            "1234567890",
            "+12345678901234",  # Long international
            "555-123-4567"      # With dashes
        ]
        
        for phone in valid_phones:
            result = self.validation_service.validate_field_value(field, phone)
            assert result.is_valid is True, f"Phone '{phone}' should be valid"
        
        invalid_phones = [
            "123",              # Too short
            "abcdefghij",       # Non-numeric
            "",                 # Empty for required field
            "123 456 7890 123"  # Too long
        ]
        
        for phone in invalid_phones:
            result = self.validation_service.validate_field_value(field, phone)
            assert result.is_valid is False, f"Phone '{phone}' should be invalid"

    def test_validate_url_field(self):
        """Test URL field validation."""
        field = Field(
            id="url_test",
            name="website",
            display_name="Website",
            field_type=FieldType.URL,
            required=True
        )
        
        valid_urls = [
            "https://example.com",
            "http://test.org",
            "https://subdomain.example.com/path?query=value",
            "ftp://files.example.com"
        ]
        
        for url in valid_urls:
            result = self.validation_service.validate_field_value(field, url)
            assert result.is_valid is True, f"URL '{url}' should be valid"
        
        invalid_urls = [
            "not-a-url",
            "example.com",      # Missing protocol
            "http://",          # Incomplete
            "",                 # Empty for required field
            "javascript:alert(1)"  # Potentially dangerous
        ]
        
        for url in invalid_urls:
            result = self.validation_service.validate_field_value(field, url)
            assert result.is_valid is False, f"URL '{url}' should be invalid"

    def test_validate_optional_field(self):
        """Test validation of optional fields."""
        field = Field(
            id="optional_test",
            name="optional_field",
            display_name="Optional Field",
            field_type=FieldType.STRING,
            required=False,
            validation_rules=self.string_rules
        )
        
        # Empty value should be valid for optional field
        result = self.validation_service.validate_field_value(field, "")
        assert result.is_valid is True
        
        # None value should be valid for optional field
        result = self.validation_service.validate_field_value(field, None)
        assert result.is_valid is True
        
        # Valid non-empty value should be valid
        result = self.validation_service.validate_field_value(field, "Valid Value")
        assert result.is_valid is True
        
        # Invalid non-empty value should be invalid
        result = self.validation_service.validate_field_value(field, "X")  # Too short
        assert result.is_valid is False

    def test_validate_data_against_schema(self):
        """Test validating complete data against a schema."""
        # Save schema first
        self.schema_service.create_schema(self.sample_schema.to_dict())
        
        valid_data = {
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30
        }
        
        result = self.validation_service.validate_data_against_schema(
            self.sample_schema.id,
            valid_data
        )
        
        assert result.is_valid is True
        assert len(result.field_results) == 3
        assert all(fr.is_valid for fr in result.field_results.values())

    def test_validate_data_with_missing_required_fields(self):
        """Test validation with missing required fields."""
        # Save schema first
        self.schema_service.create_schema(self.sample_schema.to_dict())
        
        incomplete_data = {
            "full_name": "John Doe",
            # Missing required email field
            "age": 30
        }
        
        result = self.validation_service.validate_data_against_schema(
            self.sample_schema.id,
            incomplete_data
        )
        
        assert result.is_valid is False
        assert "email" in result.field_results
        assert not result.field_results["email"].is_valid

    def test_validate_data_with_invalid_values(self):
        """Test validation with invalid field values."""
        # Save schema first
        self.schema_service.create_schema(self.sample_schema.to_dict())
        
        invalid_data = {
            "full_name": "X",  # Too short
            "email": "invalid-email",  # Invalid format
            "age": -5  # Below minimum
        }
        
        result = self.validation_service.validate_data_against_schema(
            self.sample_schema.id,
            invalid_data
        )
        
        assert result.is_valid is False
        assert not result.field_results["full_name"].is_valid
        assert not result.field_results["email"].is_valid
        assert not result.field_results["age"].is_valid

    def test_validate_data_with_extra_fields(self):
        """Test validation with extra fields not in schema."""
        # Save schema first
        self.schema_service.create_schema(self.sample_schema.to_dict())
        
        data_with_extra = {
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30,
            "extra_field": "This field is not in the schema"
        }
        
        result = self.validation_service.validate_data_against_schema(
            self.sample_schema.id,
            data_with_extra
        )
        
        # Should still be valid (extra fields are typically ignored)
        assert result.is_valid is True
        # But might include warnings about extra fields
        assert len(result.warnings) >= 0

    def test_validate_cross_field_dependencies(self):
        """Test cross-field validation dependencies."""
        # Create schema with field dependencies
        dependent_schema = Schema(
            id="dependent_schema",
            name="Dependent Schema",
            description="Schema with field dependencies",
            version="1.0.0",
            fields=[
                Field(
                    id="country_field",
                    name="country",
                    display_name="Country",
                    field_type=FieldType.SELECT,
                    required=True,
                    options=["USA", "Canada"]
                ),
                Field(
                    id="state_field",
                    name="state",
                    display_name="State/Province",
                    field_type=FieldType.STRING,
                    required=True,
                    dependencies=["country"]  # Depends on country
                )
            ]
        )
        
        self.schema_service.create_schema(dependent_schema.to_dict())
        
        # Test with valid dependencies
        valid_data = {
            "country": "USA",
            "state": "California"
        }
        
        result = self.validation_service.validate_data_against_schema(
            dependent_schema.id,
            valid_data
        )
        
        assert result.is_valid is True

    def test_validate_schema_definition(self):
        """Test validation of schema definition itself."""
        # Valid schema
        valid_schema = Schema(
            id="valid_schema",
            name="Valid Schema",
            description="A valid schema",
            version="1.0.0",
            fields=[
                Field(
                    id="valid_field",
                    name="valid_field",
                    display_name="Valid Field",
                    field_type=FieldType.STRING,
                    required=True
                )
            ]
        )
        
        result = self.validation_service.validate_schema_definition(valid_schema.to_dict())
        assert result.is_valid is True
        
        # Invalid schema - missing required field
        invalid_schema_data = {
            "id": "",  # Empty ID
            "name": "Invalid Schema",
            "description": "Missing required ID",
            "version": "1.0.0",
            "fields": []
        }
        
        result = self.validation_service.validate_schema_definition(invalid_schema_data)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_field_definition(self):
        """Test validation of field definition."""
        # Valid field
        valid_field_data = {
            "id": "valid_field",
            "name": "valid_field",
            "display_name": "Valid Field",
            "type": "string",
            "required": True,
            "description": "A valid field"
        }
        
        result = self.validation_service.validate_field_definition(valid_field_data)
        assert result.is_valid is True
        
        # Invalid field - missing required properties
        invalid_field_data = {
            "id": "",  # Empty ID
            "name": "",  # Empty name
            "type": "invalid_type",  # Invalid type
            "required": True
        }
        
        result = self.validation_service.validate_field_definition(invalid_field_data)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_custom_validation_rules(self):
        """Test validation of custom validation rules."""
        custom_rule = ValidationRule(
            rule_type="custom_rule",  # Custom rule type
            message="Custom validation failed",
            parameters={"custom_param": "value"},
            severity=ValidationSeverity.WARNING
        )
        
        field = Field(
            id="custom_test",
            name="custom_field",
            display_name="Custom Field",
            field_type=FieldType.STRING,
            validation_rules=[custom_rule]
        )
        
        # Should handle custom rules gracefully
        result = self.validation_service.validate_field_value(field, "test_value")
        
        # Custom rules might be skipped or cause warnings
        assert isinstance(result, ValidationResult)

    def test_validation_performance_with_many_rules(self):
        """Test validation performance with many validation rules."""
        import time
        
        # Create field with many validation rules
        many_rules = []
        for i in range(100):
            rule = ValidationRule(
                rule_type=ValidationRuleType.REGEX,
                message=f"Rule {i}",
                parameters={"pattern": f".*{i}.*"},
                severity=ValidationSeverity.WARNING
            )
            many_rules.append(rule)
        
        field = Field(
            id="performance_test",
            name="perf_field",
            display_name="Performance Field",
            field_type=FieldType.STRING,
            validation_rules=many_rules
        )
        
        # Test validation performance
        start_time = time.time()
        result = self.validation_service.validate_field_value(field, "test_value_50")
        validation_time = time.time() - start_time
        
        # Should validate efficiently
        assert validation_time < 1.0  # Less than 1 second
        assert isinstance(result, ValidationResult)

    def test_validation_with_null_and_undefined_values(self):
        """Test validation with null and undefined values."""
        field = Field(
            id="null_test",
            name="null_field",
            display_name="Null Field",
            field_type=FieldType.STRING,
            required=False
        )
        
        # Test various "empty" values
        empty_values = [None, "", " ", "\t", "\n"]
        
        for value in empty_values:
            result = self.validation_service.validate_field_value(field, value)
            # For optional fields, empty values should generally be valid
            assert result.is_valid is True, f"Empty value '{repr(value)}' should be valid for optional field"

    def test_validation_error_messages(self):
        """Test that validation error messages are informative."""
        field = Field(
            id="error_message_test",
            name="test_field",
            display_name="Test Field",
            field_type=FieldType.STRING,
            required=True,
            validation_rules=[
                ValidationRule(
                    rule_type=ValidationRuleType.MIN_LENGTH,
                    message="Custom error: Field must be at least 5 characters long",
                    parameters={"length": 5},
                    severity=ValidationSeverity.ERROR
                )
            ]
        )
        
        result = self.validation_service.validate_field_value(field, "abc")  # Too short
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Check that custom error message is used
        error_messages = [error.message for error in result.errors]
        assert any("Custom error" in msg for msg in error_messages)

    def test_validation_severity_levels(self):
        """Test different validation severity levels."""
        field = Field(
            id="severity_test",
            name="severity_field",
            display_name="Severity Field",
            field_type=FieldType.STRING,
            required=True,
            validation_rules=[
                ValidationRule(
                    rule_type=ValidationRuleType.MIN_LENGTH,
                    message="Error level validation",
                    parameters={"length": 5},
                    severity=ValidationSeverity.ERROR
                ),
                ValidationRule(
                    rule_type=ValidationRuleType.REGEX,
                    message="Warning level validation",
                    parameters={"pattern": "^[A-Z].*"},  # Must start with uppercase
                    severity=ValidationSeverity.WARNING
                )
            ]
        )
        
        # Test value that triggers warning but not error
        result = self.validation_service.validate_field_value(field, "lowercase")  # 9 chars, starts lowercase
        
        # Should have warnings but still be considered valid for some purposes
        assert len(result.warnings) > 0
        
        # Test value that triggers error
        result = self.validation_service.validate_field_value(field, "abc")  # Too short
        
        assert result.is_valid is False
        assert len(result.errors) > 0


class TestValidationServiceEdgeCases:
    """Test edge cases and error conditions for ValidationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SchemaStorage(data_dir=self.temp_dir)
        self.schema_service = SchemaService(self.storage)
        self.validation_service = ValidationService(self.storage, self.schema_service)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_against_nonexistent_schema(self):
        """Test validation against a schema that doesn't exist."""
        data = {"field1": "value1"}
        
        result = self.validation_service.validate_data_against_schema(
            "nonexistent_schema",
            data
        )
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        error_messages = [error.message for error in result.errors]
        assert any("schema" in msg.lower() for msg in error_messages)

    def test_validate_with_malformed_validation_rules(self):
        """Test validation with malformed validation rules."""
        # Create rule with missing parameters
        malformed_rule = ValidationRule(
            rule_type=ValidationRuleType.MIN_LENGTH,
            message="Malformed rule",
            parameters={},  # Missing required 'length' parameter
            severity=ValidationSeverity.ERROR
        )
        
        field = Field(
            id="malformed_test",
            name="malformed_field",
            display_name="Malformed Field",
            field_type=FieldType.STRING,
            validation_rules=[malformed_rule]
        )
        
        # Should handle gracefully
        result = self.validation_service.validate_field_value(field, "test_value")
        
        # Should not crash, might skip the malformed rule
        assert isinstance(result, ValidationResult)

    def test_validate_with_circular_regex(self):
        """Test validation with potentially problematic regex patterns."""
        # Regex that could cause catastrophic backtracking
        problematic_regex = ValidationRule(
            rule_type=ValidationRuleType.REGEX,
            message="Problematic regex",
            parameters={"pattern": "(a+)+$"},  # Potentially problematic pattern
            severity=ValidationSeverity.ERROR
        )
        
        field = Field(
            id="regex_problem_test",
            name="regex_field",
            display_name="Regex Field",
            field_type=FieldType.STRING,
            validation_rules=[problematic_regex]
        )
        
        # Test with value that could trigger backtracking
        result = self.validation_service.validate_field_value(field, "a" * 20 + "b")
        
        # Should complete in reasonable time and not crash
        assert isinstance(result, ValidationResult)

    def test_validate_extremely_large_values(self):
        """Test validation with extremely large values."""
        field = Field(
            id="large_value_test",
            name="large_field",
            display_name="Large Field",
            field_type=FieldType.STRING,
            required=True
        )
        
        # Very large string (1MB)
        large_value = "x" * 1000000
        
        result = self.validation_service.validate_field_value(field, large_value)
        
        # Should handle gracefully
        assert isinstance(result, ValidationResult)

    def test_validate_with_unicode_characters(self):
        """Test validation with unicode characters."""
        field = Field(
            id="unicode_test",
            name="unicode_field",
            display_name="Unicode Field",
            field_type=FieldType.STRING,
            required=True,
            validation_rules=[
                ValidationRule(
                    rule_type=ValidationRuleType.MIN_LENGTH,
                    message="Must be at least 2 characters",
                    parameters={"length": 2},
                    severity=ValidationSeverity.ERROR
                )
            ]
        )
        
        unicode_values = [
            "café",           # Accented characters
            "北京",           # Chinese characters
            "🎉🎊",           # Emojis
            "مرحبا",          # Arabic
            "Здравствуйте"   # Cyrillic
        ]
        
        for value in unicode_values:
            result = self.validation_service.validate_field_value(field, value)
            assert isinstance(result, ValidationResult)
            # Most should be valid (length >= 2)
            if len(value) >= 2:
                assert result.is_valid is True, f"Unicode value '{value}' should be valid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])