"""
Unit tests for Field model.

Tests the Field data model including validation, serialization,
validation rules, and field-specific behavior.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List
import json

# Import the modules we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from schema_management.models.field import Field, FieldType, FieldValidationResult
from schema_management.models.validation_rule import ValidationRule, ValidationRuleType, ValidationSeverity


class TestFieldModel:
    """Test cases for Field model."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_validation_rules = [
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
            ),
            ValidationRule(
                rule_type=ValidationRuleType.REGEX,
                message="Must contain only letters",
                parameters={"pattern": "^[A-Za-z]+$"},
                severity=ValidationSeverity.WARNING
            )
        ]

        self.sample_field = Field(
            id="sample_field_001",
            name="full_name",
            display_name="Full Name",
            field_type=FieldType.STRING,
            required=True,
            description="Person's full legal name",
            validation_rules=self.sample_validation_rules,
            metadata={
                "placeholder": "Enter your full name",
                "help_text": "Include first and last name"
            }
        )

    def test_field_creation_basic(self):
        """Test basic field creation."""
        field = Field(
            id="basic_field",
            name="test_field",
            display_name="Test Field",
            field_type=FieldType.STRING
        )
        
        assert field.id == "basic_field"
        assert field.name == "test_field"
        assert field.display_name == "Test Field"
        assert field.field_type == FieldType.STRING
        assert field.required is False  # Default
        assert field.description == ""  # Default
        assert field.validation_rules == []  # Default
        assert field.metadata == {}  # Default
        assert field.options == []  # Default
        assert field.dependencies == []  # Default

    def test_field_creation_with_all_parameters(self):
        """Test field creation with all parameters."""
        field = self.sample_field
        
        assert field.id == "sample_field_001"
        assert field.name == "full_name"
        assert field.display_name == "Full Name"
        assert field.field_type == FieldType.STRING
        assert field.required is True
        assert field.description == "Person's full legal name"
        assert len(field.validation_rules) == 3
        assert len(field.metadata) == 2
        assert field.metadata["placeholder"] == "Enter your full name"

    def test_field_types(self):
        """Test all field types."""
        field_type_tests = [
            (FieldType.STRING, "string"),
            (FieldType.NUMBER, "number"), 
            (FieldType.INTEGER, "integer"),
            (FieldType.BOOLEAN, "boolean"),
            (FieldType.DATE, "date"),
            (FieldType.DATETIME, "datetime"),
            (FieldType.EMAIL, "email"),
            (FieldType.URL, "url"),
            (FieldType.PHONE, "phone"),
            (FieldType.SELECT, "select"),
            (FieldType.MULTISELECT, "multiselect"),
            (FieldType.FILE, "file")
        ]
        
        for field_type, expected_value in field_type_tests:
            field = Field(
                id=f"test_{expected_value}",
                name=f"test_{expected_value}",
                display_name=f"Test {expected_value.title()}",
                field_type=field_type
            )
            assert field.field_type == field_type
            assert field.field_type.value == expected_value

    def test_select_field_with_options(self):
        """Test select field with options."""
        field = Field(
            id="select_field",
            name="country",
            display_name="Country",
            field_type=FieldType.SELECT,
            options=["USA", "Canada", "UK", "Germany"],
            required=True
        )
        
        assert field.field_type == FieldType.SELECT
        assert len(field.options) == 4
        assert "USA" in field.options
        assert field.required is True

    def test_multiselect_field_with_options(self):
        """Test multiselect field with options."""
        field = Field(
            id="skills_field",
            name="skills",
            display_name="Skills",
            field_type=FieldType.MULTISELECT,
            options=["Python", "JavaScript", "Java", "C++", "Go"],
            required=False
        )
        
        assert field.field_type == FieldType.MULTISELECT
        assert len(field.options) == 5
        assert "Python" in field.options

    def test_field_with_dependencies(self):
        """Test field with dependencies."""
        field = Field(
            id="dependent_field",
            name="zip_code",
            display_name="ZIP Code",
            field_type=FieldType.STRING,
            dependencies=["country", "state"],
            required=True
        )
        
        assert len(field.dependencies) == 2
        assert "country" in field.dependencies
        assert "state" in field.dependencies

    def test_add_validation_rule(self):
        """Test adding validation rule to field."""
        field = Field(
            id="test_validation",
            name="test_field",
            display_name="Test Field",
            field_type=FieldType.STRING
        )
        
        assert len(field.validation_rules) == 0
        
        rule = ValidationRule(
            rule_type=ValidationRuleType.REQUIRED,
            message="This field is required",
            severity=ValidationSeverity.ERROR
        )
        
        field.add_validation_rule(rule)
        
        assert len(field.validation_rules) == 1
        assert field.validation_rules[0] == rule

    def test_remove_validation_rule(self):
        """Test removing validation rule from field."""
        field = self.sample_field.copy()
        original_count = len(field.validation_rules)
        
        # Remove the first rule
        removed_rule = field.remove_validation_rule(0)
        
        assert removed_rule is not None
        assert len(field.validation_rules) == original_count - 1

    def test_remove_validation_rule_invalid_index(self):
        """Test removing validation rule with invalid index."""
        field = self.sample_field
        
        # Try to remove rule at invalid index
        removed_rule = field.remove_validation_rule(999)
        
        assert removed_rule is None
        assert len(field.validation_rules) == 3  # Unchanged

    def test_update_validation_rule(self):
        """Test updating existing validation rule."""
        field = self.sample_field.copy()
        
        new_rule = ValidationRule(
            rule_type=ValidationRuleType.MIN_LENGTH,
            message="Updated: Must be at least 5 characters",
            parameters={"length": 5},
            severity=ValidationSeverity.WARNING
        )
        
        success = field.update_validation_rule(0, new_rule)
        
        assert success is True
        assert field.validation_rules[0].message == "Updated: Must be at least 5 characters"
        assert field.validation_rules[0].parameters["length"] == 5
        assert field.validation_rules[0].severity == ValidationSeverity.WARNING

    def test_validate_field_basic(self):
        """Test basic field validation."""
        field = Field(
            id="valid_field",
            name="valid_name",
            display_name="Valid Field",
            field_type=FieldType.STRING,
            required=True
        )
        
        result = field.validate()
        
        assert isinstance(result, FieldValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validate_field_missing_required_info(self):
        """Test validation with missing required information."""
        field = Field(
            id="",  # Empty ID
            name="",  # Empty name
            display_name="Valid Display Name",
            field_type=FieldType.STRING
        )
        
        result = field.validate()
        
        assert result.is_valid is False
        assert len(result.errors) >= 2
        
        error_messages = [error.message for error in result.errors]
        assert any("Field ID is required" in msg for msg in error_messages)
        assert any("Field name is required" in msg for msg in error_messages)

    def test_validate_select_field_without_options(self):
        """Test validation of select field without options."""
        field = Field(
            id="invalid_select",
            name="invalid_select",
            display_name="Invalid Select",
            field_type=FieldType.SELECT,
            options=[]  # Empty options for select field
        )
        
        result = field.validate()
        
        assert result.is_valid is False
        error_messages = [error.message for error in result.errors]
        assert any("options" in msg.lower() for msg in error_messages)

    def test_validate_multiselect_field_without_options(self):
        """Test validation of multiselect field without options."""
        field = Field(
            id="invalid_multiselect",
            name="invalid_multiselect", 
            display_name="Invalid Multiselect",
            field_type=FieldType.MULTISELECT,
            options=[]  # Empty options
        )
        
        result = field.validate()
        
        assert result.is_valid is False
        error_messages = [error.message for error in result.errors]
        assert any("options" in msg.lower() for msg in error_messages)

    def test_validate_field_with_invalid_validation_rules(self):
        """Test field validation with invalid validation rules."""
        invalid_rule = ValidationRule(
            rule_type=ValidationRuleType.MIN_LENGTH,
            message="",  # Empty message
            parameters={},  # Missing required parameters
            severity=ValidationSeverity.ERROR
        )
        
        field = Field(
            id="field_with_invalid_rule",
            name="test_field",
            display_name="Test Field",
            field_type=FieldType.STRING,
            validation_rules=[invalid_rule]
        )
        
        result = field.validate()
        
        # Should have errors about invalid validation rule
        assert len(result.errors) > 0 or len(result.warnings) > 0

    def test_validate_field_value_string(self):
        """Test validating a string value against field rules."""
        field = Field(
            id="string_validation_test",
            name="test_string",
            display_name="Test String",
            field_type=FieldType.STRING,
            required=True,
            validation_rules=[
                ValidationRule(
                    rule_type=ValidationRuleType.MIN_LENGTH,
                    message="Too short",
                    parameters={"length": 3}
                ),
                ValidationRule(
                    rule_type=ValidationRuleType.MAX_LENGTH,
                    message="Too long",
                    parameters={"length": 10}
                )
            ]
        )
        
        # Valid value
        result = field.validate_value("Hello")
        assert result.is_valid is True
        
        # Too short
        result = field.validate_value("Hi")
        assert result.is_valid is False
        
        # Too long
        result = field.validate_value("This is too long")
        assert result.is_valid is False
        
        # Empty value for required field
        result = field.validate_value("")
        assert result.is_valid is False

    def test_validate_field_value_number(self):
        """Test validating a number value against field rules."""
        field = Field(
            id="number_validation_test",
            name="test_number",
            display_name="Test Number",
            field_type=FieldType.NUMBER,
            required=True,
            validation_rules=[
                ValidationRule(
                    rule_type=ValidationRuleType.MIN_VALUE,
                    message="Too small",
                    parameters={"value": 0}
                ),
                ValidationRule(
                    rule_type=ValidationRuleType.MAX_VALUE,
                    message="Too large", 
                    parameters={"value": 100}
                )
            ]
        )
        
        # Valid value
        result = field.validate_value(50)
        assert result.is_valid is True
        
        # Also test string number
        result = field.validate_value("75")
        assert result.is_valid is True
        
        # Too small
        result = field.validate_value(-5)
        assert result.is_valid is False
        
        # Too large
        result = field.validate_value(150)
        assert result.is_valid is False
        
        # Invalid number format
        result = field.validate_value("not_a_number")
        assert result.is_valid is False

    def test_validate_field_value_email(self):
        """Test validating email values."""
        field = Field(
            id="email_test",
            name="email",
            display_name="Email",
            field_type=FieldType.EMAIL,
            required=True
        )
        
        # Valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        for email in valid_emails:
            result = field.validate_value(email)
            assert result.is_valid is True, f"Email {email} should be valid"
        
        # Invalid emails
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user name@example.com"  # Space in local part
        ]
        
        for email in invalid_emails:
            result = field.validate_value(email)
            assert result.is_valid is False, f"Email {email} should be invalid"

    def test_validate_field_value_select(self):
        """Test validating select field values."""
        field = Field(
            id="select_test",
            name="country",
            display_name="Country",
            field_type=FieldType.SELECT,
            options=["USA", "Canada", "UK"],
            required=True
        )
        
        # Valid selection
        result = field.validate_value("USA")
        assert result.is_valid is True
        
        # Invalid selection
        result = field.validate_value("France")
        assert result.is_valid is False
        
        # Empty selection for required field
        result = field.validate_value("")
        assert result.is_valid is False

    def test_validate_field_value_multiselect(self):
        """Test validating multiselect field values."""
        field = Field(
            id="multiselect_test",
            name="skills",
            display_name="Skills",
            field_type=FieldType.MULTISELECT,
            options=["Python", "JavaScript", "Java", "C++"],
            required=True
        )
        
        # Valid selections
        result = field.validate_value(["Python", "Java"])
        assert result.is_valid is True
        
        result = field.validate_value(["JavaScript"])  # Single selection
        assert result.is_valid is True
        
        # Invalid selection (not in options)
        result = field.validate_value(["Python", "Go"])
        assert result.is_valid is False
        
        # Empty selection for required field
        result = field.validate_value([])
        assert result.is_valid is False

    def test_to_dict(self):
        """Test converting field to dictionary."""
        field = self.sample_field
        
        field_dict = field.to_dict()
        
        assert isinstance(field_dict, dict)
        assert field_dict["id"] == field.id
        assert field_dict["name"] == field.name
        assert field_dict["display_name"] == field.display_name
        assert field_dict["type"] == field.field_type.value
        assert field_dict["required"] == field.required
        assert field_dict["description"] == field.description
        
        # Check validation rules serialization
        assert "validation_rules" in field_dict
        assert len(field_dict["validation_rules"]) == len(field.validation_rules)
        assert all(isinstance(rule, dict) for rule in field_dict["validation_rules"])
        
        # Check metadata
        assert field_dict["metadata"] == field.metadata

    def test_from_dict(self):
        """Test creating field from dictionary."""
        field_data = {
            "id": "from_dict_test",
            "name": "test_field",
            "display_name": "Test Field",
            "type": "string",
            "required": True,
            "description": "Test field from dict",
            "validation_rules": [
                {
                    "rule_type": "min_length",
                    "message": "Too short",
                    "parameters": {"length": 3},
                    "severity": "error"
                }
            ],
            "metadata": {
                "placeholder": "Enter value"
            },
            "options": [],
            "dependencies": ["other_field"]
        }
        
        field = Field.from_dict(field_data)
        
        assert field.id == "from_dict_test"
        assert field.name == "test_field"
        assert field.field_type == FieldType.STRING
        assert field.required is True
        assert len(field.validation_rules) == 1
        assert field.validation_rules[0].rule_type == ValidationRuleType.MIN_LENGTH
        assert field.metadata["placeholder"] == "Enter value"
        assert "other_field" in field.dependencies

    def test_copy_field(self):
        """Test copying a field."""
        original = self.sample_field
        
        # Test shallow copy
        copy_shallow = original.copy()
        
        assert copy_shallow.id == original.id
        assert copy_shallow.name == original.name
        assert len(copy_shallow.validation_rules) == len(original.validation_rules)
        assert copy_shallow is not original
        
        # Test deep copy with new ID
        copy_deep = original.copy(new_id="copied_field")
        
        assert copy_deep.id == "copied_field"
        assert copy_deep.name == original.name
        assert len(copy_deep.validation_rules) == len(original.validation_rules)
        
        # Modify original to ensure deep copy
        original.add_validation_rule(ValidationRule(
            rule_type=ValidationRuleType.REQUIRED,
            message="Required field"
        ))
        
        # Copy should not be affected
        assert len(copy_deep.validation_rules) != len(original.validation_rules)

    def test_field_json_serialization(self):
        """Test JSON serialization and deserialization."""
        field = self.sample_field
        
        # Serialize to JSON
        json_str = field.to_json()
        assert isinstance(json_str, str)
        
        # Ensure it's valid JSON
        json_data = json.loads(json_str)
        assert isinstance(json_data, dict)
        assert json_data["id"] == field.id
        
        # Deserialize from JSON
        deserialized = Field.from_json(json_str)
        
        assert deserialized.id == field.id
        assert deserialized.name == field.name
        assert deserialized.field_type == field.field_type
        assert len(deserialized.validation_rules) == len(field.validation_rules)
        
        # Ensure validation rule details are preserved
        assert deserialized.validation_rules[0].rule_type == field.validation_rules[0].rule_type
        assert deserialized.validation_rules[0].message == field.validation_rules[0].message

    def test_field_metadata_operations(self):
        """Test field metadata operations."""
        field = Field(
            id="metadata_test",
            name="test_field",
            display_name="Test Field",
            field_type=FieldType.STRING
        )
        
        # Set metadata
        field.set_metadata("placeholder", "Enter text")
        field.set_metadata("max_chars", 100)
        
        assert field.get_metadata("placeholder") == "Enter text"
        assert field.get_metadata("max_chars") == 100
        assert field.get_metadata("nonexistent") is None
        
        # Update metadata
        field.set_metadata("max_chars", 200)
        assert field.get_metadata("max_chars") == 200
        
        # Remove metadata
        field.remove_metadata("max_chars")
        assert field.get_metadata("max_chars") is None

    def test_field_with_complex_validation_rules(self):
        """Test field with complex validation rule combinations."""
        field = Field(
            id="complex_validation",
            name="password",
            display_name="Password",
            field_type=FieldType.STRING,
            required=True,
            validation_rules=[
                ValidationRule(
                    rule_type=ValidationRuleType.MIN_LENGTH,
                    message="Password must be at least 8 characters",
                    parameters={"length": 8}
                ),
                ValidationRule(
                    rule_type=ValidationRuleType.REGEX,
                    message="Password must contain uppercase letter",
                    parameters={"pattern": ".*[A-Z].*"}
                ),
                ValidationRule(
                    rule_type=ValidationRuleType.REGEX,
                    message="Password must contain lowercase letter",
                    parameters={"pattern": ".*[a-z].*"}
                ),
                ValidationRule(
                    rule_type=ValidationRuleType.REGEX,
                    message="Password must contain number",
                    parameters={"pattern": ".*[0-9].*"}
                )
            ]
        )
        
        # Test various password combinations
        test_cases = [
            ("Password123", True),   # Valid
            ("password123", False),  # No uppercase
            ("PASSWORD123", False),  # No lowercase
            ("Password", False),     # No number
            ("Pass1", False),        # Too short
            ("", False),             # Empty (required field)
        ]
        
        for password, expected_valid in test_cases:
            result = field.validate_value(password)
            assert result.is_valid == expected_valid, f"Password '{password}' validation result should be {expected_valid}"


class TestFieldEdgeCases:
    """Test edge cases and error conditions for Field model."""

    def test_field_with_empty_options_list(self):
        """Test non-select field with empty options list."""
        field = Field(
            id="empty_options",
            name="test_field",
            display_name="Test Field",
            field_type=FieldType.STRING,
            options=[]  # Empty options for non-select field
        )
        
        # Should not cause validation errors for non-select fields
        result = field.validate()
        assert result.is_valid is True

    def test_field_with_none_values(self):
        """Test field handling of None values."""
        field = Field(
            id="none_test",
            name="test_field",
            display_name="Test Field", 
            field_type=FieldType.STRING,
            description=None,  # None description
            metadata=None,     # None metadata
            options=None,      # None options
            dependencies=None  # None dependencies
        )
        
        assert field.description == ""  # Should default to empty string
        assert field.metadata == {}    # Should default to empty dict
        assert field.options == []     # Should default to empty list
        assert field.dependencies == [] # Should default to empty list

    def test_field_validation_with_circular_dependencies(self):
        """Test field validation with circular dependencies."""
        # This would typically be detected at schema level,
        # but field should handle gracefully
        field = Field(
            id="circular_test",
            name="field_a",
            display_name="Field A",
            field_type=FieldType.STRING,
            dependencies=["field_a"]  # Self-dependency
        )
        
        result = field.validate()
        
        # Should have a warning about self-dependency
        assert len(result.warnings) > 0 or len(result.errors) > 0

    def test_field_validation_performance(self):
        """Test field validation performance with many rules."""
        import time
        
        # Create field with many validation rules
        rules = []
        for i in range(100):
            rules.append(ValidationRule(
                rule_type=ValidationRuleType.REGEX,
                message=f"Rule {i}",
                parameters={"pattern": f".*{i}.*"}
            ))
        
        field = Field(
            id="performance_test",
            name="perf_field",
            display_name="Performance Field",
            field_type=FieldType.STRING,
            validation_rules=rules
        )
        
        # Test validation performance
        start_time = time.time()
        result = field.validate_value("test123value456")
        validation_time = time.time() - start_time
        
        # Should validate quickly even with many rules
        assert validation_time < 1.0  # Less than 1 second

    def test_field_with_invalid_field_type(self):
        """Test handling of invalid field type."""
        # This should be caught during creation or validation
        with pytest.raises((ValueError, TypeError)):
            Field(
                id="invalid_type",
                name="invalid",
                display_name="Invalid",
                field_type="invalid_type"  # Invalid type
            )

    def test_field_large_options_list(self):
        """Test field with very large options list."""
        large_options = [f"option_{i}" for i in range(10000)]
        
        field = Field(
            id="large_options",
            name="large_select",
            display_name="Large Select",
            field_type=FieldType.SELECT,
            options=large_options
        )
        
        assert len(field.options) == 10000
        
        # Validation should still work efficiently
        result = field.validate_value("option_5000")
        assert result.is_valid is True
        
        result = field.validate_value("nonexistent_option")
        assert result.is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])