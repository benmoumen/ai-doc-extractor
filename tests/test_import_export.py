"""
Schema Import/Export Functionality Validation Tests.

Tests the import/export functionality including JSON, CSV, YAML formats,
templates, backup/restore, and data integrity validation.
"""

import pytest
import tempfile
import shutil
import os
import json
import csv
import yaml
from typing import Dict, Any, List
from io import StringIO
import zipfile

# Import the modules we're testing
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from schema_management.models.schema import Schema, SchemaStatus
from schema_management.models.field import Field, FieldType
from schema_management.models.validation_rule import ValidationRule, ValidationRuleType, ValidationSeverity
from schema_management.storage.schema_storage import SchemaStorage
from schema_management.services.schema_service import SchemaService
from schema_management.ui.import_export import (
    export_schema_to_json, export_schema_to_csv, export_schema_to_yaml,
    import_schema_from_json, import_schema_from_csv, import_schema_from_yaml,
    export_multiple_schemas, import_multiple_schemas,
    create_schema_backup, restore_schema_from_backup,
    validate_import_data, ImportExportResult
)


class TestSchemaImportExport:
    """Test cases for schema import/export functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SchemaStorage(data_dir=self.temp_dir)
        self.schema_service = SchemaService(self.storage)
        
        # Create comprehensive test schema
        self.test_schema = Schema(
            id="import_export_test",
            name="Import Export Test Schema",
            description="Comprehensive schema for testing import/export functionality",
            version="1.2.3",
            category="Testing",
            status=SchemaStatus.ACTIVE,
            fields=[
                Field(
                    id="string_field",
                    name="full_name",
                    display_name="Full Name",
                    field_type=FieldType.STRING,
                    required=True,
                    description="Person's full legal name",
                    validation_rules=[
                        ValidationRule(
                            rule_type=ValidationRuleType.MIN_LENGTH,
                            message="Name must be at least 2 characters",
                            parameters={"length": 2},
                            severity=ValidationSeverity.ERROR
                        ),
                        ValidationRule(
                            rule_type=ValidationRuleType.MAX_LENGTH,
                            message="Name must not exceed 100 characters",
                            parameters={"length": 100},
                            severity=ValidationSeverity.ERROR
                        )
                    ],
                    metadata={"placeholder": "Enter full name"}
                ),
                Field(
                    id="email_field",
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
                    id="select_field",
                    name="country",
                    display_name="Country",
                    field_type=FieldType.SELECT,
                    required=False,
                    description="Country of residence",
                    options=["USA", "Canada", "UK", "Germany", "France"],
                    metadata={"default": "USA"}
                ),
                Field(
                    id="number_field",
                    name="age",
                    display_name="Age",
                    field_type=FieldType.NUMBER,
                    required=False,
                    description="Person's age in years",
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
                            severity=ValidationSeverity.WARNING
                        )
                    ]
                ),
                Field(
                    id="multiselect_field",
                    name="skills",
                    display_name="Skills",
                    field_type=FieldType.MULTISELECT,
                    required=False,
                    description="Technical skills",
                    options=["Python", "JavaScript", "Java", "C++", "Go", "Rust"],
                    dependencies=["country"]
                )
            ],
            metadata={
                "created_by": "test_user",
                "tags": ["testing", "import", "export"],
                "version_notes": "Test schema for import/export validation"
            }
        )

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_schema_to_json(self):
        """Test exporting schema to JSON format."""
        # Save schema first
        self.schema_service.create_schema(self.test_schema.to_dict())
        
        # Export to JSON
        result = export_schema_to_json(self.test_schema.id, self.schema_service)
        
        assert result.success is True
        assert result.data is not None
        assert result.format == "json"
        
        # Validate JSON structure
        json_data = json.loads(result.data)
        assert json_data["id"] == self.test_schema.id
        assert json_data["name"] == self.test_schema.name
        assert json_data["version"] == self.test_schema.version
        assert len(json_data["fields"]) == len(self.test_schema.fields)
        
        # Check field details
        field_data = json_data["fields"][0]
        assert "id" in field_data
        assert "name" in field_data
        assert "type" in field_data
        assert "validation_rules" in field_data
        
        # Validate that complex data is preserved
        assert json_data["metadata"]["tags"] == ["testing", "import", "export"]

    def test_import_schema_from_json(self):
        """Test importing schema from JSON format."""
        # Export schema first
        self.schema_service.create_schema(self.test_schema.to_dict())
        export_result = export_schema_to_json(self.test_schema.id, self.schema_service)
        
        # Modify the JSON to create a new schema
        json_data = json.loads(export_result.data)
        json_data["id"] = "imported_json_schema"
        json_data["name"] = "Imported JSON Schema"
        modified_json = json.dumps(json_data, indent=2)
        
        # Import the modified schema
        import_result = import_schema_from_json(modified_json, self.schema_service)
        
        assert import_result.success is True
        assert import_result.schema_id == "imported_json_schema"
        
        # Verify imported schema
        imported_schema = self.schema_service.get_schema("imported_json_schema")
        assert imported_schema is not None
        assert imported_schema.name == "Imported JSON Schema"
        assert len(imported_schema.fields) == len(self.test_schema.fields)
        
        # Verify field details are preserved
        email_field = imported_schema.get_field("email_field")
        assert email_field is not None
        assert email_field.field_type == FieldType.EMAIL
        assert len(email_field.validation_rules) > 0

    def test_export_schema_to_csv(self):
        """Test exporting schema to CSV format."""
        # Save schema first
        self.schema_service.create_schema(self.test_schema.to_dict())
        
        # Export to CSV
        result = export_schema_to_csv(self.test_schema.id, self.schema_service)
        
        assert result.success is True
        assert result.data is not None
        assert result.format == "csv"
        
        # Parse CSV data
        csv_reader = csv.DictReader(StringIO(result.data))
        rows = list(csv_reader)
        
        # Should have one row per field
        assert len(rows) == len(self.test_schema.fields)
        
        # Check CSV structure
        expected_columns = [
            "field_id", "name", "display_name", "type", "required", 
            "description", "options", "validation_rules", "metadata"
        ]
        
        for col in expected_columns:
            assert col in csv_reader.fieldnames
        
        # Check field data
        first_row = rows[0]
        assert first_row["field_id"] == "string_field"
        assert first_row["name"] == "full_name"
        assert first_row["type"] == "string"
        assert first_row["required"] == "True"

    def test_import_schema_from_csv(self):
        """Test importing schema from CSV format."""
        # Create CSV data
        csv_data = """schema_id,schema_name,schema_description,schema_version,field_id,name,display_name,type,required,description,options,validation_rules
csv_import_test,CSV Import Test,Imported from CSV,2.0.0,name_field,person_name,Person Name,string,True,Full name of person,,min_length:2;max_length:50
csv_import_test,CSV Import Test,Imported from CSV,2.0.0,email_field,email_address,Email,email,True,Email address,,email_format
csv_import_test,CSV Import Test,Imported from CSV,2.0.0,country_field,country,Country,select,False,Country of residence,USA;Canada;UK,"""
        
        # Import from CSV
        import_result = import_schema_from_csv(csv_data, self.schema_service)
        
        assert import_result.success is True
        assert import_result.schema_id == "csv_import_test"
        
        # Verify imported schema
        imported_schema = self.schema_service.get_schema("csv_import_test")
        assert imported_schema is not None
        assert imported_schema.name == "CSV Import Test"
        assert imported_schema.version == "2.0.0"
        assert len(imported_schema.fields) == 3
        
        # Check specific field
        country_field = imported_schema.get_field("country_field")
        assert country_field is not None
        assert country_field.field_type == FieldType.SELECT
        assert "USA" in country_field.options
        assert len(country_field.options) == 3

    def test_export_schema_to_yaml(self):
        """Test exporting schema to YAML format."""
        # Save schema first
        self.schema_service.create_schema(self.test_schema.to_dict())
        
        # Export to YAML
        result = export_schema_to_yaml(self.test_schema.id, self.schema_service)
        
        assert result.success is True
        assert result.data is not None
        assert result.format == "yaml"
        
        # Parse YAML data
        yaml_data = yaml.safe_load(result.data)
        
        assert yaml_data["id"] == self.test_schema.id
        assert yaml_data["name"] == self.test_schema.name
        assert isinstance(yaml_data["fields"], list)
        assert len(yaml_data["fields"]) == len(self.test_schema.fields)
        
        # Check YAML structure preserves complex data
        field = yaml_data["fields"][0]
        assert isinstance(field["validation_rules"], list)
        if field["validation_rules"]:
            assert "rule_type" in field["validation_rules"][0]
            assert "parameters" in field["validation_rules"][0]

    def test_import_schema_from_yaml(self):
        """Test importing schema from YAML format."""
        # Create YAML data
        yaml_data = {
            "id": "yaml_import_test",
            "name": "YAML Import Test",
            "description": "Schema imported from YAML",
            "version": "3.0.0",
            "category": "Testing",
            "fields": [
                {
                    "id": "title_field",
                    "name": "title",
                    "display_name": "Title",
                    "type": "string",
                    "required": True,
                    "description": "Document title",
                    "validation_rules": [
                        {
                            "rule_type": "min_length",
                            "message": "Title too short",
                            "parameters": {"length": 5},
                            "severity": "error"
                        }
                    ]
                },
                {
                    "id": "status_field", 
                    "name": "status",
                    "display_name": "Status",
                    "type": "select",
                    "required": True,
                    "description": "Document status",
                    "options": ["draft", "review", "published", "archived"]
                }
            ],
            "metadata": {
                "imported_from": "yaml",
                "test_field": True
            }
        }
        
        yaml_string = yaml.dump(yaml_data, default_flow_style=False)
        
        # Import from YAML
        import_result = import_schema_from_yaml(yaml_string, self.schema_service)
        
        assert import_result.success is True
        assert import_result.schema_id == "yaml_import_test"
        
        # Verify imported schema
        imported_schema = self.schema_service.get_schema("yaml_import_test")
        assert imported_schema is not None
        assert imported_schema.name == "YAML Import Test"
        assert imported_schema.version == "3.0.0"
        assert len(imported_schema.fields) == 2
        
        # Check field with validation rules
        title_field = imported_schema.get_field("title_field")
        assert title_field is not None
        assert len(title_field.validation_rules) == 1
        assert title_field.validation_rules[0].rule_type == ValidationRuleType.MIN_LENGTH

    def test_export_multiple_schemas(self):
        """Test exporting multiple schemas."""
        # Create multiple schemas
        schemas = []
        for i in range(3):
            schema = Schema(
                id=f"multi_export_test_{i}",
                name=f"Multi Export Test {i}",
                description=f"Schema {i} for multi-export testing",
                version="1.0.0",
                fields=[
                    Field(
                        id=f"field_{i}",
                        name=f"field_{i}",
                        display_name=f"Field {i}",
                        field_type=FieldType.STRING,
                        required=True
                    )
                ]
            )
            schemas.append(schema)
            self.schema_service.create_schema(schema.to_dict())
        
        # Export multiple schemas
        schema_ids = [s.id for s in schemas]
        result = export_multiple_schemas(schema_ids, self.schema_service, format="json")
        
        assert result.success is True
        assert result.format == "json"
        assert result.data is not None
        
        # Parse exported data
        export_data = json.loads(result.data)
        assert "schemas" in export_data
        assert len(export_data["schemas"]) == 3
        assert "export_metadata" in export_data
        
        # Check individual schemas
        for i, schema_data in enumerate(export_data["schemas"]):
            assert schema_data["id"] == f"multi_export_test_{i}"
            assert len(schema_data["fields"]) == 1

    def test_import_multiple_schemas(self):
        """Test importing multiple schemas."""
        # Create export data for multiple schemas
        export_data = {
            "export_metadata": {
                "format_version": "1.0",
                "export_date": "2023-01-01T12:00:00Z",
                "schema_count": 2
            },
            "schemas": [
                {
                    "id": "multi_import_1",
                    "name": "Multi Import Schema 1",
                    "description": "First schema",
                    "version": "1.0.0",
                    "fields": [
                        {
                            "id": "field1",
                            "name": "field1",
                            "display_name": "Field 1",
                            "type": "string",
                            "required": True
                        }
                    ]
                },
                {
                    "id": "multi_import_2",
                    "name": "Multi Import Schema 2", 
                    "description": "Second schema",
                    "version": "1.0.0",
                    "fields": [
                        {
                            "id": "field2",
                            "name": "field2",
                            "display_name": "Field 2",
                            "type": "number",
                            "required": False
                        }
                    ]
                }
            ]
        }
        
        export_json = json.dumps(export_data, indent=2)
        
        # Import multiple schemas
        result = import_multiple_schemas(export_json, self.schema_service)
        
        assert result.success is True
        assert len(result.imported_schema_ids) == 2
        assert "multi_import_1" in result.imported_schema_ids
        assert "multi_import_2" in result.imported_schema_ids
        
        # Verify imported schemas
        schema1 = self.schema_service.get_schema("multi_import_1")
        schema2 = self.schema_service.get_schema("multi_import_2")
        
        assert schema1 is not None
        assert schema2 is not None
        assert schema1.name == "Multi Import Schema 1"
        assert schema2.name == "Multi Import Schema 2"

    def test_create_schema_backup(self):
        """Test creating schema backup."""
        # Save schema first
        self.schema_service.create_schema(self.test_schema.to_dict())
        
        # Create backup
        backup_path = create_schema_backup(self.test_schema.id, self.schema_service)
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.endswith('.zip')
        
        # Verify backup contents
        with zipfile.ZipFile(backup_path, 'r') as zip_file:
            file_list = zip_file.namelist()
            
            # Should contain schema JSON and metadata
            assert any(f.endswith('.json') for f in file_list)
            assert 'backup_metadata.json' in file_list
            
            # Read schema data from backup
            schema_file = [f for f in file_list if f.endswith('.json') and f != 'backup_metadata.json'][0]
            with zip_file.open(schema_file) as f:
                schema_data = json.load(f)
                assert schema_data["id"] == self.test_schema.id
                assert schema_data["name"] == self.test_schema.name

    def test_restore_schema_from_backup(self):
        """Test restoring schema from backup."""
        # Create and backup schema
        self.schema_service.create_schema(self.test_schema.to_dict())
        backup_path = create_schema_backup(self.test_schema.id, self.schema_service)
        
        # Delete original schema
        self.schema_service.delete_schema(self.test_schema.id)
        assert self.schema_service.get_schema(self.test_schema.id) is None
        
        # Restore from backup
        restore_result = restore_schema_from_backup(backup_path, self.schema_service)
        
        assert restore_result.success is True
        assert restore_result.schema_id == self.test_schema.id
        
        # Verify restored schema
        restored_schema = self.schema_service.get_schema(self.test_schema.id)
        assert restored_schema is not None
        assert restored_schema.name == self.test_schema.name
        assert len(restored_schema.fields) == len(self.test_schema.fields)
        
        # Verify complex data is preserved
        email_field = restored_schema.get_field("email_field")
        assert email_field is not None
        assert len(email_field.validation_rules) > 0

    def test_import_data_validation(self):
        """Test validation of import data."""
        # Test valid data
        valid_data = {
            "id": "valid_import",
            "name": "Valid Import Schema",
            "description": "Valid schema for import",
            "version": "1.0.0",
            "fields": [
                {
                    "id": "valid_field",
                    "name": "valid_field",
                    "display_name": "Valid Field",
                    "type": "string",
                    "required": True
                }
            ]
        }
        
        is_valid, errors = validate_import_data(valid_data)
        assert is_valid is True
        assert len(errors) == 0
        
        # Test invalid data
        invalid_data = {
            "id": "",  # Invalid empty ID
            "name": "",  # Invalid empty name
            "fields": [
                {
                    "id": "invalid_field",
                    "name": "",  # Invalid empty name
                    "type": "invalid_type",  # Invalid type
                    "required": True
                }
            ]
        }
        
        is_valid, errors = validate_import_data(invalid_data)
        assert is_valid is False
        assert len(errors) > 0
        
        # Check specific error types
        error_messages = [error.message for error in errors]
        assert any("Schema ID" in msg for msg in error_messages)
        assert any("Schema name" in msg for msg in error_messages)

    def test_import_export_data_integrity(self):
        """Test data integrity through export/import cycle."""
        # Save original schema
        self.schema_service.create_schema(self.test_schema.to_dict())
        
        # Export to JSON
        export_result = export_schema_to_json(self.test_schema.id, self.schema_service)
        
        # Import as new schema
        import_data = json.loads(export_result.data)
        import_data["id"] = "integrity_test_copy"
        import_data["name"] = "Integrity Test Copy"
        
        import_result = import_schema_from_json(
            json.dumps(import_data), 
            self.schema_service
        )
        
        # Compare original and imported schemas
        original = self.schema_service.get_schema(self.test_schema.id)
        imported = self.schema_service.get_schema("integrity_test_copy")
        
        assert original is not None
        assert imported is not None
        
        # Compare field by field
        assert len(original.fields) == len(imported.fields)
        
        for orig_field, imp_field in zip(original.fields, imported.fields):
            # IDs will be different, but other properties should match
            assert orig_field.name == imp_field.name
            assert orig_field.field_type == imp_field.field_type
            assert orig_field.required == imp_field.required
            assert orig_field.description == imp_field.description
            assert len(orig_field.validation_rules) == len(imp_field.validation_rules)
            assert orig_field.options == imp_field.options

    def test_import_with_conflicts(self):
        """Test importing schema that conflicts with existing schema."""
        # Create original schema
        self.schema_service.create_schema(self.test_schema.to_dict())
        
        # Try to import schema with same ID
        conflicting_data = {
            "id": self.test_schema.id,  # Same ID as existing
            "name": "Conflicting Schema",
            "description": "This should cause a conflict",
            "version": "2.0.0",
            "fields": [
                {
                    "id": "conflict_field",
                    "name": "conflict_field",
                    "display_name": "Conflict Field",
                    "type": "string",
                    "required": True
                }
            ]
        }
        
        # Import should handle conflict gracefully
        import_result = import_schema_from_json(
            json.dumps(conflicting_data),
            self.schema_service,
            handle_conflicts="rename"  # or "overwrite", "skip"
        )
        
        # Should either rename, overwrite, or skip based on conflict handling
        if import_result.success:
            # If successful, should have handled conflict appropriately
            assert import_result.schema_id is not None
        else:
            # If failed, should have informative error message
            assert "conflict" in import_result.message.lower()

    def test_export_with_custom_formatting(self):
        """Test export with custom formatting options."""
        # Save schema first
        self.schema_service.create_schema(self.test_schema.to_dict())
        
        # Export with custom options
        result = export_schema_to_json(
            self.test_schema.id, 
            self.schema_service,
            options={
                "include_metadata": True,
                "include_validation_rules": True,
                "pretty_print": True,
                "include_field_statistics": True
            }
        )
        
        assert result.success is True
        
        # Parse and verify custom formatting
        json_data = json.loads(result.data)
        
        # Should include all requested information
        assert "metadata" in json_data
        assert json_data["fields"][0]["validation_rules"] is not None
        
        # Check for additional statistics if included
        if "field_statistics" in json_data:
            assert "total_fields" in json_data["field_statistics"]
            assert "required_fields" in json_data["field_statistics"]

    def test_import_error_handling(self):
        """Test error handling during import operations."""
        # Test malformed JSON
        malformed_json = '{"id": "test", "name": incomplete json'
        
        result = import_schema_from_json(malformed_json, self.schema_service)
        assert result.success is False
        assert "json" in result.message.lower() or "format" in result.message.lower()
        
        # Test invalid schema structure
        invalid_schema = json.dumps({
            "not_a_schema": "invalid structure"
        })
        
        result = import_schema_from_json(invalid_schema, self.schema_service)
        assert result.success is False
        assert len(result.errors) > 0

    def test_bulk_export_performance(self):
        """Test performance of bulk export operations."""
        import time
        
        # Create many schemas
        schema_ids = []
        for i in range(50):
            schema = Schema(
                id=f"bulk_test_{i}",
                name=f"Bulk Test Schema {i}",
                description=f"Schema {i} for bulk testing",
                version="1.0.0",
                fields=[
                    Field(
                        id=f"field_{i}",
                        name=f"field_{i}",
                        display_name=f"Field {i}",
                        field_type=FieldType.STRING,
                        required=True
                    )
                ]
            )
            self.schema_service.create_schema(schema.to_dict())
            schema_ids.append(schema.id)
        
        # Test bulk export performance
        start_time = time.time()
        result = export_multiple_schemas(schema_ids, self.schema_service)
        export_time = time.time() - start_time
        
        assert result.success is True
        assert export_time < 10.0  # Should complete within 10 seconds
        
        # Verify all schemas were exported
        export_data = json.loads(result.data)
        assert len(export_data["schemas"]) == 50

    def test_template_export_import(self):
        """Test exporting and importing schema templates."""
        # Create schema template
        template_data = {
            "id": "person_template",
            "name": "Person Information Template",
            "description": "Template for person information schemas",
            "version": "1.0.0",
            "category": "Templates",
            "template": True,  # Mark as template
            "fields": [
                {
                    "id": "name_template_field",
                    "name": "name",
                    "display_name": "Name",
                    "type": "string",
                    "required": True,
                    "description": "Person's name",
                    "template_field": True
                },
                {
                    "id": "email_template_field",
                    "name": "email",
                    "display_name": "Email",
                    "type": "email",
                    "required": True,
                    "description": "Email address",
                    "template_field": True
                }
            ]
        }
        
        # Export template
        template_json = json.dumps(template_data, indent=2)
        result = import_schema_from_json(template_json, self.schema_service)
        
        assert result.success is True
        
        # Verify template
        template = self.schema_service.get_schema("person_template")
        assert template is not None
        assert template.metadata.get("template") is True


class TestImportExportEdgeCases:
    """Test edge cases and error conditions for import/export."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SchemaStorage(data_dir=self.temp_dir)
        self.schema_service = SchemaService(self.storage)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_nonexistent_schema(self):
        """Test exporting a schema that doesn't exist."""
        result = export_schema_to_json("nonexistent_schema", self.schema_service)
        
        assert result.success is False
        assert "not found" in result.message.lower()

    def test_import_extremely_large_schema(self):
        """Test importing a very large schema."""
        # Create schema with many fields
        large_schema_data = {
            "id": "large_schema_test",
            "name": "Large Schema Test",
            "description": "Schema with many fields",
            "version": "1.0.0",
            "fields": []
        }
        
        # Add 1000 fields
        for i in range(1000):
            field = {
                "id": f"large_field_{i}",
                "name": f"field_{i}",
                "display_name": f"Large Field {i}",
                "type": "string",
                "required": False,
                "description": f"Auto-generated field {i}"
            }
            large_schema_data["fields"].append(field)
        
        # Import large schema
        large_json = json.dumps(large_schema_data)
        result = import_schema_from_json(large_json, self.schema_service)
        
        # Should handle large schemas gracefully
        if result.success:
            # If successful, verify schema was created
            imported = self.schema_service.get_schema("large_schema_test")
            assert imported is not None
            assert len(imported.fields) == 1000
        else:
            # If failed, should have informative error
            assert "size" in result.message.lower() or "large" in result.message.lower()

    def test_import_with_unicode_content(self):
        """Test importing schema with unicode characters."""
        unicode_schema = {
            "id": "unicode_test",
            "name": "Unicode Test Schema 测试",
            "description": "Schema with unicode: café, 北京, مرحبا, Здравствуйте",
            "version": "1.0.0",
            "fields": [
                {
                    "id": "unicode_field",
                    "name": "unicode_name",
                    "display_name": "Unicode Display: 🌟",
                    "type": "string",
                    "required": True,
                    "description": "Field with unicode: café ☕"
                }
            ],
            "metadata": {
                "unicode_tag": "测试标签",
                "emoji": "🚀🎉"
            }
        }
        
        unicode_json = json.dumps(unicode_schema, ensure_ascii=False, indent=2)
        result = import_schema_from_json(unicode_json, self.schema_service)
        
        assert result.success is True
        
        # Verify unicode content is preserved
        imported = self.schema_service.get_schema("unicode_test")
        assert imported is not None
        assert "测试" in imported.name
        assert "☕" in imported.fields[0].description
        assert imported.metadata["emoji"] == "🚀🎉"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])