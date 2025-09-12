"""
Test schema loading and validation functionality.
These tests MUST FAIL initially (TDD requirement) before implementation.
"""
import pytest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema_utils import (
    get_available_document_types,
    get_document_schema,
    validate_schema_structure,
    get_required_fields,
    validate_extracted_data_completeness
)
from config import DOCUMENT_SCHEMAS


class TestSchemaLoading:
    """Test schema loading functionality."""
    
    def test_get_available_document_types_returns_dict(self):
        """Test that get_available_document_types returns a dictionary of name->id mappings."""
        document_types = get_available_document_types()
        
        assert isinstance(document_types, dict), "Should return a dictionary"
        assert len(document_types) > 0, "Should return at least one document type"
        assert "National ID" in document_types, "Should include National ID document type"
        assert "Passport" in document_types, "Should include Passport document type"
        assert document_types["National ID"] == "national_id", "Should map to correct ID"
        assert document_types["Passport"] == "passport", "Should map to correct ID"

    def test_get_document_schema_valid_id(self):
        """Test getting schema for valid document type ID."""
        schema = get_document_schema("national_id")
        
        assert schema is not None, "Should return schema for valid ID"
        assert schema["id"] == "national_id", "Should return correct schema"
        assert schema["name"] == "National ID", "Should have correct name"
        assert "fields" in schema, "Should contain fields definition"
        assert len(schema["fields"]) > 0, "Should have at least one field"

    def test_get_document_schema_invalid_id(self):
        """Test getting schema for invalid document type ID."""
        schema = get_document_schema("invalid_document_type")
        
        assert schema is None, "Should return None for invalid ID"

    def test_get_document_schema_contains_required_fields(self):
        """Test that schema contains all required field definitions."""
        schema = get_document_schema("national_id")
        
        assert "full_name" in schema["fields"], "Should contain full_name field"
        assert "id_number" in schema["fields"], "Should contain id_number field"
        assert "date_of_birth" in schema["fields"], "Should contain date_of_birth field"
        
        # Test field structure
        full_name_field = schema["fields"]["full_name"]
        assert full_name_field["required"] is True, "Full name should be required"
        assert full_name_field["type"] == "string", "Full name should be string type"
        assert "validation_rules" in full_name_field, "Should have validation rules"


class TestSchemaValidation:
    """Test schema structure validation."""
    
    def test_validate_schema_structure_valid_schema(self):
        """Test validation of a valid schema structure."""
        valid_schema = {
            "id": "test_doc",
            "name": "Test Document",
            "description": "A test document",
            "fields": {
                "test_field": {
                    "name": "test_field",
                    "display_name": "Test Field",
                    "type": "string",
                    "required": True,
                    "description": "A test field",
                    "validation_rules": [
                        {
                            "type": "required",
                            "message": "Field is required",
                            "severity": "error"
                        }
                    ]
                }
            }
        }
        
        is_valid, errors = validate_schema_structure(valid_schema)
        
        assert is_valid is True, f"Valid schema should pass validation, got errors: {errors}"
        assert len(errors) == 0, "Valid schema should have no errors"

    def test_validate_schema_structure_missing_required_fields(self):
        """Test validation fails for schema missing required fields."""
        invalid_schema = {
            "id": "test_doc",
            "name": "Test Document"
            # Missing 'description' and 'fields'
        }
        
        is_valid, errors = validate_schema_structure(invalid_schema)
        
        assert is_valid is False, "Schema missing required fields should fail validation"
        assert len(errors) > 0, "Should return validation errors"
        assert any("description" in error for error in errors), "Should report missing description"
        assert any("fields" in error for error in errors), "Should report missing fields"

    def test_validate_schema_structure_invalid_field_type(self):
        """Test validation fails for fields with invalid types."""
        invalid_schema = {
            "id": "test_doc",
            "name": "Test Document", 
            "description": "A test document",
            "fields": {
                "invalid_field": {
                    "name": "invalid_field",
                    "display_name": "Invalid Field",
                    "type": "invalid_type",  # Invalid type
                    "required": True,
                    "description": "A field with invalid type"
                }
            }
        }
        
        is_valid, errors = validate_schema_structure(invalid_schema)
        
        assert is_valid is False, "Schema with invalid field type should fail validation"
        assert any("invalid type" in error.lower() for error in errors), "Should report invalid type"

    def test_validate_existing_schemas(self):
        """Test that all existing schemas in config are valid."""
        for doc_type_id, schema in DOCUMENT_SCHEMAS.items():
            is_valid, errors = validate_schema_structure(schema)
            
            assert is_valid is True, f"Schema '{doc_type_id}' should be valid, got errors: {errors}"
            assert len(errors) == 0, f"Schema '{doc_type_id}' should have no validation errors"


class TestRequiredFields:
    """Test required fields functionality."""
    
    def test_get_required_fields_national_id(self):
        """Test getting required fields for national ID."""
        required_fields = get_required_fields("national_id")
        
        assert isinstance(required_fields, list), "Should return a list"
        assert "full_name" in required_fields, "Full name should be required"
        assert "id_number" in required_fields, "ID number should be required"
        assert "date_of_birth" in required_fields, "Date of birth should be required"
        # Address should not be required
        assert "address" not in required_fields, "Address should not be required"

    def test_get_required_fields_invalid_document_type(self):
        """Test getting required fields for invalid document type."""
        required_fields = get_required_fields("invalid_type")
        
        assert isinstance(required_fields, list), "Should return a list"
        assert len(required_fields) == 0, "Should return empty list for invalid type"

    def test_validate_extracted_data_completeness_complete_data(self):
        """Test validation of complete extracted data."""
        complete_data = {
            "full_name": "John Smith",
            "id_number": "AB123456789",
            "date_of_birth": "1985-03-15",
            "address": "123 Main St"
        }
        
        is_complete, missing_fields = validate_extracted_data_completeness("national_id", complete_data)
        
        assert is_complete is True, "Complete data should validate successfully"
        assert len(missing_fields) == 0, "Complete data should have no missing fields"

    def test_validate_extracted_data_completeness_missing_required(self):
        """Test validation of incomplete extracted data."""
        incomplete_data = {
            "full_name": "John Smith",
            # Missing required fields: id_number, date_of_birth
            "address": "123 Main St"
        }
        
        is_complete, missing_fields = validate_extracted_data_completeness("national_id", incomplete_data)
        
        assert is_complete is False, "Incomplete data should fail validation"
        assert len(missing_fields) > 0, "Should report missing fields"
        assert "id_number" in missing_fields, "Should report missing ID number"
        assert "date_of_birth" in missing_fields, "Should report missing date of birth"
        assert "address" not in missing_fields, "Should not report missing optional fields"

    def test_validate_extracted_data_completeness_empty_values(self):
        """Test validation treats empty values as missing."""
        data_with_empty_values = {
            "full_name": "",  # Empty string should be treated as missing
            "id_number": "AB123456789",
            "date_of_birth": None,  # None should be treated as missing
            "address": "123 Main St"
        }
        
        is_complete, missing_fields = validate_extracted_data_completeness("national_id", data_with_empty_values)
        
        assert is_complete is False, "Data with empty required fields should fail validation"
        assert "full_name" in missing_fields, "Should report empty string as missing"
        assert "date_of_birth" in missing_fields, "Should report None as missing"


if __name__ == "__main__":
    # Run tests to verify they fail initially (TDD requirement)
    pytest.main([__file__, "-v"])