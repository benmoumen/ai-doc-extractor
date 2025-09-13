"""
Unit tests for Schema model.

Tests the Schema data model including validation, serialization,
field management, and business logic.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List
import json

# Import the modules we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from schema_management.models.schema import Schema, SchemaStatus, SchemaValidationResult
from schema_management.models.field import Field, FieldType
from schema_management.models.validation_rule import ValidationRule, ValidationRuleType, ValidationSeverity


class TestSchemaModel:
    """Test cases for Schema model."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_fields = [
            Field(
                id="field_1",
                name="first_name",
                display_name="First Name",
                field_type=FieldType.STRING,
                required=True,
                description="Person's first name"
            ),
            Field(
                id="field_2", 
                name="email",
                display_name="Email Address",
                field_type=FieldType.EMAIL,
                required=True,
                description="Contact email address",
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.EMAIL_FORMAT,
                        message="Must be a valid email address",
                        severity=ValidationSeverity.ERROR
                    )
                ]
            ),
            Field(
                id="field_3",
                name="age",
                display_name="Age",
                field_type=FieldType.NUMBER,
                required=False,
                description="Person's age",
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MIN_VALUE,
                        message="Age must be at least 0",
                        parameters={"value": 0},
                        severity=ValidationSeverity.ERROR
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_VALUE,
                        message="Age must be less than 150",
                        parameters={"value": 150},
                        severity=ValidationSeverity.ERROR
                    )
                ]
            )
        ]

        self.sample_schema = Schema(
            id="test_schema_001",
            name="Person Information",
            description="Schema for capturing person information",
            version="1.0.0",
            category="Personal",
            fields=self.sample_fields,
            metadata={
                "created_by": "test_user",
                "tags": ["personal", "contact"]
            }
        )

    def test_schema_creation(self):
        """Test basic schema creation."""
        schema = Schema(
            id="simple_schema",
            name="Simple Schema",
            description="A simple test schema",
            version="1.0.0"
        )
        
        assert schema.id == "simple_schema"
        assert schema.name == "Simple Schema"
        assert schema.description == "A simple test schema"
        assert schema.version == "1.0.0"
        assert schema.status == SchemaStatus.DRAFT
        assert schema.fields == []
        assert schema.metadata == {}
        assert isinstance(schema.created_at, datetime)
        assert isinstance(schema.updated_at, datetime)

    def test_schema_with_fields(self):
        """Test schema creation with fields."""
        schema = self.sample_schema
        
        assert len(schema.fields) == 3
        assert schema.get_field_count() == 3
        assert schema.get_required_field_count() == 2
        
        # Test field retrieval
        first_name_field = schema.get_field("field_1")
        assert first_name_field is not None
        assert first_name_field.name == "first_name"
        assert first_name_field.required is True

    def test_add_field(self):
        """Test adding a field to schema."""
        schema = Schema(
            id="test_add_field",
            name="Test Schema",
            description="Testing field addition"
        )
        
        new_field = Field(
            id="new_field",
            name="test_field",
            display_name="Test Field",
            field_type=FieldType.STRING
        )
        
        schema.add_field(new_field)
        
        assert len(schema.fields) == 1
        assert schema.get_field("new_field") == new_field
        assert schema.updated_at > schema.created_at

    def test_add_duplicate_field_id(self):
        """Test that adding a field with duplicate ID raises error."""
        schema = self.sample_schema
        
        duplicate_field = Field(
            id="field_1",  # Duplicate ID
            name="duplicate",
            display_name="Duplicate",
            field_type=FieldType.STRING
        )
        
        with pytest.raises(ValueError, match="Field with ID 'field_1' already exists"):
            schema.add_field(duplicate_field)

    def test_remove_field(self):
        """Test removing a field from schema."""
        schema = self.sample_schema.copy()
        original_count = len(schema.fields)
        
        removed_field = schema.remove_field("field_2")
        
        assert removed_field is not None
        assert removed_field.name == "email"
        assert len(schema.fields) == original_count - 1
        assert schema.get_field("field_2") is None

    def test_remove_nonexistent_field(self):
        """Test removing a field that doesn't exist."""
        schema = self.sample_schema
        
        removed_field = schema.remove_field("nonexistent")
        
        assert removed_field is None

    def test_update_field(self):
        """Test updating an existing field."""
        schema = self.sample_schema.copy()
        
        updated_field = Field(
            id="field_1",
            name="first_name_updated",
            display_name="Updated First Name",
            field_type=FieldType.STRING,
            required=False,  # Changed from True
            description="Updated description"
        )
        
        success = schema.update_field("field_1", updated_field)
        
        assert success is True
        field = schema.get_field("field_1")
        assert field.name == "first_name_updated"
        assert field.required is False
        assert field.description == "Updated description"

    def test_update_nonexistent_field(self):
        """Test updating a field that doesn't exist."""
        schema = self.sample_schema
        
        new_field = Field(
            id="nonexistent",
            name="test",
            display_name="Test",
            field_type=FieldType.STRING
        )
        
        success = schema.update_field("nonexistent", new_field)
        
        assert success is False

    def test_reorder_fields(self):
        """Test reordering fields in schema."""
        schema = self.sample_schema.copy()
        original_order = [f.id for f in schema.fields]
        
        new_order = ["field_2", "field_3", "field_1"]
        success = schema.reorder_fields(new_order)
        
        assert success is True
        reordered_ids = [f.id for f in schema.fields]
        assert reordered_ids == new_order
        assert reordered_ids != original_order

    def test_reorder_fields_invalid_ids(self):
        """Test reordering with invalid field IDs."""
        schema = self.sample_schema
        
        # Missing one field ID
        incomplete_order = ["field_1", "field_2"]
        success = schema.reorder_fields(incomplete_order)
        assert success is False
        
        # Extra field ID
        extra_order = ["field_1", "field_2", "field_3", "field_4"]
        success = schema.reorder_fields(extra_order)
        assert success is False

    def test_get_field_names(self):
        """Test getting list of field names."""
        schema = self.sample_schema
        
        field_names = schema.get_field_names()
        expected_names = ["first_name", "email", "age"]
        
        assert field_names == expected_names

    def test_get_required_fields(self):
        """Test getting list of required fields."""
        schema = self.sample_schema
        
        required_fields = schema.get_required_fields()
        required_names = [f.name for f in required_fields]
        
        assert len(required_fields) == 2
        assert "first_name" in required_names
        assert "email" in required_names
        assert "age" not in required_names

    def test_validate_schema_basic(self):
        """Test basic schema validation."""
        schema = self.sample_schema
        
        result = schema.validate()
        
        assert isinstance(result, SchemaValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validate_schema_missing_required_fields(self):
        """Test validation with missing required information."""
        schema = Schema(
            id="",  # Empty ID should cause validation error
            name="",  # Empty name should cause validation error
            description="Valid description"
        )
        
        result = schema.validate()
        
        assert result.is_valid is False
        assert len(result.errors) >= 2
        
        error_messages = [error.message for error in result.errors]
        assert any("Schema ID is required" in msg for msg in error_messages)
        assert any("Schema name is required" in msg for msg in error_messages)

    def test_validate_schema_invalid_version(self):
        """Test validation with invalid version format."""
        schema = Schema(
            id="test_id",
            name="Test Name",
            description="Test description",
            version="invalid_version"  # Should follow semantic versioning
        )
        
        result = schema.validate()
        
        # Should have a warning about version format
        assert len(result.warnings) > 0
        warning_messages = [warning.message for warning in result.warnings]
        assert any("version" in msg.lower() for msg in warning_messages)

    def test_to_dict(self):
        """Test converting schema to dictionary."""
        schema = self.sample_schema
        
        schema_dict = schema.to_dict()
        
        assert isinstance(schema_dict, dict)
        assert schema_dict["id"] == schema.id
        assert schema_dict["name"] == schema.name
        assert schema_dict["description"] == schema.description
        assert schema_dict["version"] == schema.version
        assert schema_dict["status"] == schema.status.value
        assert schema_dict["category"] == schema.category
        
        # Check fields serialization
        assert "fields" in schema_dict
        assert len(schema_dict["fields"]) == len(schema.fields)
        assert all(isinstance(field, dict) for field in schema_dict["fields"])
        
        # Check metadata
        assert schema_dict["metadata"] == schema.metadata

    def test_from_dict(self):
        """Test creating schema from dictionary."""
        schema_data = {
            "id": "from_dict_test",
            "name": "From Dict Test",
            "description": "Testing from_dict method",
            "version": "2.0.0",
            "status": "active",
            "category": "Test",
            "fields": [
                {
                    "id": "test_field",
                    "name": "test_name",
                    "display_name": "Test Name",
                    "type": "string",
                    "required": True,
                    "description": "Test field"
                }
            ],
            "metadata": {
                "created_by": "from_dict_test",
                "tags": ["test"]
            }
        }
        
        schema = Schema.from_dict(schema_data)
        
        assert schema.id == "from_dict_test"
        assert schema.name == "From Dict Test"
        assert schema.version == "2.0.0"
        assert schema.status == SchemaStatus.ACTIVE
        assert len(schema.fields) == 1
        assert schema.fields[0].name == "test_name"
        assert schema.metadata["created_by"] == "from_dict_test"

    def test_copy_schema(self):
        """Test copying a schema."""
        original = self.sample_schema
        
        # Test shallow copy
        copy_shallow = original.copy()
        
        assert copy_shallow.id == original.id
        assert copy_shallow.name == original.name
        assert len(copy_shallow.fields) == len(original.fields)
        assert copy_shallow is not original
        
        # Test deep copy with new ID
        copy_deep = original.copy(new_id="copied_schema")
        
        assert copy_deep.id == "copied_schema"
        assert copy_deep.name == original.name
        assert len(copy_deep.fields) == len(original.fields)
        
        # Modify original to ensure deep copy
        original.add_field(Field(
            id="new_field",
            name="new",
            display_name="New",
            field_type=FieldType.STRING
        ))
        
        # Copy should not be affected
        assert len(copy_deep.fields) != len(original.fields)

    def test_schema_status_transitions(self):
        """Test valid status transitions."""
        schema = Schema(
            id="status_test",
            name="Status Test",
            description="Testing status transitions"
        )
        
        # Draft -> Active
        assert schema.status == SchemaStatus.DRAFT
        schema.set_status(SchemaStatus.ACTIVE)
        assert schema.status == SchemaStatus.ACTIVE
        
        # Active -> Deprecated
        schema.set_status(SchemaStatus.DEPRECATED)
        assert schema.status == SchemaStatus.DEPRECATED
        
        # Deprecated -> Archived
        schema.set_status(SchemaStatus.ARCHIVED)
        assert schema.status == SchemaStatus.ARCHIVED

    def test_schema_metadata_management(self):
        """Test metadata operations."""
        schema = Schema(
            id="metadata_test",
            name="Metadata Test",
            description="Testing metadata operations"
        )
        
        # Add metadata
        schema.set_metadata("author", "test_user")
        schema.set_metadata("priority", "high")
        
        assert schema.get_metadata("author") == "test_user"
        assert schema.get_metadata("priority") == "high"
        assert schema.get_metadata("nonexistent") is None
        
        # Update metadata
        schema.set_metadata("priority", "medium")
        assert schema.get_metadata("priority") == "medium"
        
        # Remove metadata
        schema.remove_metadata("priority")
        assert schema.get_metadata("priority") is None

    def test_schema_field_statistics(self):
        """Test field statistics methods."""
        schema = self.sample_schema
        
        stats = schema.get_field_statistics()
        
        assert stats["total_fields"] == 3
        assert stats["required_fields"] == 2
        assert stats["optional_fields"] == 1
        
        # Check field type distribution
        type_stats = stats["field_types"]
        assert type_stats[FieldType.STRING.value] == 1
        assert type_stats[FieldType.EMAIL.value] == 1
        assert type_stats[FieldType.NUMBER.value] == 1

    def test_schema_json_serialization(self):
        """Test JSON serialization and deserialization."""
        schema = self.sample_schema
        
        # Serialize to JSON
        json_str = schema.to_json()
        assert isinstance(json_str, str)
        
        # Ensure it's valid JSON
        json_data = json.loads(json_str)
        assert isinstance(json_data, dict)
        assert json_data["id"] == schema.id
        
        # Deserialize from JSON
        deserialized = Schema.from_json(json_str)
        
        assert deserialized.id == schema.id
        assert deserialized.name == schema.name
        assert len(deserialized.fields) == len(schema.fields)
        
        # Ensure field details are preserved
        original_field = schema.get_field("field_2")
        deserialized_field = deserialized.get_field("field_2")
        
        assert original_field.name == deserialized_field.name
        assert original_field.field_type == deserialized_field.field_type
        assert len(original_field.validation_rules) == len(deserialized_field.validation_rules)

    def test_schema_versioning(self):
        """Test schema versioning functionality."""
        schema = Schema(
            id="version_test",
            name="Version Test",
            description="Testing versioning",
            version="1.0.0"
        )
        
        # Test version increment
        schema.increment_version("minor")
        assert schema.version == "1.1.0"
        
        schema.increment_version("patch")
        assert schema.version == "1.1.1"
        
        schema.increment_version("major")
        assert schema.version == "2.0.0"

    def test_schema_field_dependencies(self):
        """Test field dependency tracking."""
        # Create fields with dependencies
        name_field = Field(
            id="name_field",
            name="full_name",
            display_name="Full Name",
            field_type=FieldType.STRING,
            required=True
        )
        
        first_name_field = Field(
            id="first_name_field",
            name="first_name",
            display_name="First Name",
            field_type=FieldType.STRING,
            dependencies=["full_name"]  # Depends on full_name field
        )
        
        schema = Schema(
            id="dependency_test",
            name="Dependency Test",
            description="Testing field dependencies",
            fields=[name_field, first_name_field]
        )
        
        # Test dependency checking
        dependencies = schema.get_field_dependencies("first_name_field")
        assert "full_name" in dependencies
        
        # Test circular dependency detection
        name_field.dependencies = ["first_name"]  # Create circular dependency
        
        has_circular = schema.has_circular_dependencies()
        assert has_circular is True


class TestSchemaEdgeCases:
    """Test edge cases and error conditions."""

    def test_schema_with_empty_fields_list(self):
        """Test schema behavior with empty fields list."""
        schema = Schema(
            id="empty_fields",
            name="Empty Fields",
            description="Schema with no fields",
            fields=[]
        )
        
        assert schema.get_field_count() == 0
        assert schema.get_required_field_count() == 0
        assert schema.get_field_names() == []
        assert schema.get_required_fields() == []

    def test_schema_with_none_values(self):
        """Test schema handling of None values."""
        schema = Schema(
            id="none_test",
            name="None Test",
            description=None,  # None description
            category=None,     # None category
            metadata=None      # None metadata
        )
        
        assert schema.description is None
        assert schema.category is None
        assert schema.metadata == {}  # Should default to empty dict

    def test_schema_validation_with_invalid_field_types(self):
        """Test validation with invalid field types."""
        # This would typically be caught at field level,
        # but test schema-level validation
        invalid_field_data = {
            "id": "invalid_field",
            "name": "invalid",
            "display_name": "Invalid",
            "type": "invalid_type",  # Invalid field type
            "required": True
        }
        
        # This should be handled gracefully
        with pytest.raises((ValueError, KeyError)):
            Field.from_dict(invalid_field_data)

    def test_large_schema_performance(self):
        """Test performance with large number of fields."""
        import time
        
        # Create schema with many fields
        fields = []
        for i in range(1000):
            field = Field(
                id=f"field_{i}",
                name=f"field_{i}",
                display_name=f"Field {i}",
                field_type=FieldType.STRING,
                required=(i % 2 == 0)  # Every other field required
            )
            fields.append(field)
        
        start_time = time.time()
        schema = Schema(
            id="large_schema",
            name="Large Schema",
            description="Schema with many fields",
            fields=fields
        )
        creation_time = time.time() - start_time
        
        # Should create quickly (less than 1 second)
        assert creation_time < 1.0
        
        # Test operations on large schema
        start_time = time.time()
        field_count = schema.get_field_count()
        required_count = schema.get_required_field_count()
        stats = schema.get_field_statistics()
        operation_time = time.time() - start_time
        
        assert field_count == 1000
        assert required_count == 500  # Half are required
        assert operation_time < 0.1  # Should be very fast


if __name__ == "__main__":
    pytest.main([__file__, "-v"])