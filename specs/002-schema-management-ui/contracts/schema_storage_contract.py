"""
Schema Storage Contract Tests
These tests define the expected behavior of the SchemaStorage interface.
MUST FAIL initially - implementation comes after tests pass.
"""

import pytest
import tempfile
import json
from datetime import datetime
from pathlib import Path


class TestSchemaStorageContract:
    """Contract tests for SchemaStorage interface"""
    
    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        # Import will fail until implementation exists
        from schema_management.schema_storage import SchemaStorage
        self.storage = SchemaStorage(data_dir=self.test_dir)
    
    def test_save_new_schema_contract(self):
        """Contract: save_schema() creates new schema with metadata"""
        schema_data = {
            "id": "test_document",
            "name": "Test Document Type",
            "description": "Test schema for contract validation",
            "category": "Test",
            "version": "v1.0.0",
            "is_active": True,
            "fields": {
                "test_field": {
                    "name": "test_field",
                    "display_name": "Test Field",
                    "type": "text",
                    "required": True,
                    "description": "A test field",
                    "examples": ["Sample value"],
                    "validation_rules": []
                }
            },
            "validation_rules": []
        }
        
        # Contract: Should return True on successful save
        result = self.storage.save_schema("test_document", schema_data)
        assert result is True
        
        # Contract: JSON file should be created
        json_file = Path(self.test_dir) / "schemas" / "test_document_v1.0.0.json"
        assert json_file.exists()
        
        # Contract: Metadata should be stored in SQLite
        metadata = self.storage.get_schema_metadata("test_document")
        assert metadata is not None
        assert metadata["name"] == "Test Document Type"
        assert metadata["version"] == "v1.0.0"
    
    def test_load_existing_schema_contract(self):
        """Contract: load_schema() retrieves existing schema data"""
        # Setup: Create a schema first
        schema_data = {
            "id": "load_test",
            "name": "Load Test Schema",
            "version": "v1.0.0",
            "fields": {}
        }
        self.storage.save_schema("load_test", schema_data)
        
        # Contract: Should load the exact data that was saved
        loaded_schema = self.storage.load_schema("load_test")
        assert loaded_schema is not None
        assert loaded_schema["id"] == "load_test"
        assert loaded_schema["name"] == "Load Test Schema"
        assert loaded_schema["version"] == "v1.0.0"
    
    def test_load_nonexistent_schema_contract(self):
        """Contract: load_schema() returns None for nonexistent schemas"""
        result = self.storage.load_schema("nonexistent_schema")
        assert result is None
    
    def test_list_schemas_contract(self):
        """Contract: list_schemas() returns all active schemas with metadata"""
        # Setup: Create multiple schemas
        schemas = [
            {"id": "schema1", "name": "Schema One", "category": "Test"},
            {"id": "schema2", "name": "Schema Two", "category": "Test"},
            {"id": "schema3", "name": "Schema Three", "category": "Production"}
        ]
        
        for schema in schemas:
            self.storage.save_schema(schema["id"], schema)
        
        # Contract: Should return list of schema metadata
        schema_list = self.storage.list_schemas()
        assert len(schema_list) == 3
        
        # Contract: Each item should have required metadata fields
        for schema_meta in schema_list:
            assert "id" in schema_meta
            assert "name" in schema_meta
            assert "category" in schema_meta
            assert "version" in schema_meta
            assert "created_date" in schema_meta
    
    def test_delete_schema_contract(self):
        """Contract: delete_schema() marks schema as inactive"""
        # Setup: Create schema
        schema_data = {"id": "delete_test", "name": "Delete Test"}
        self.storage.save_schema("delete_test", schema_data)
        
        # Contract: Should mark as inactive, not physically delete
        result = self.storage.delete_schema("delete_test")
        assert result is True
        
        # Contract: Schema should not appear in active list
        active_schemas = self.storage.list_schemas()
        active_ids = [s["id"] for s in active_schemas]
        assert "delete_test" not in active_ids
        
        # Contract: Schema data should still be loadable (soft delete)
        deleted_schema = self.storage.load_schema("delete_test", include_inactive=True)
        assert deleted_schema is not None
    
    def test_version_management_contract(self):
        """Contract: Schema versioning creates new files, tracks history"""
        # Setup: Create initial version
        schema_v1 = {
            "id": "versioned_schema",
            "name": "Versioned Schema",
            "version": "v1.0.0",
            "fields": {"field1": {"name": "field1", "type": "text"}}
        }
        self.storage.save_schema("versioned_schema", schema_v1)
        
        # Contract: Update to new version
        schema_v2 = {
            "id": "versioned_schema", 
            "name": "Versioned Schema",
            "version": "v1.1.0",
            "fields": {
                "field1": {"name": "field1", "type": "text"},
                "field2": {"name": "field2", "type": "number"}
            }
        }
        self.storage.save_schema("versioned_schema", schema_v2)
        
        # Contract: Should load latest version by default
        current = self.storage.load_schema("versioned_schema")
        assert current["version"] == "v1.1.0"
        assert len(current["fields"]) == 2
        
        # Contract: Should load specific version when requested
        previous = self.storage.load_schema("versioned_schema", version="v1.0.0")
        assert previous["version"] == "v1.0.0"
        assert len(previous["fields"]) == 1
        
        # Contract: Should track version history
        versions = self.storage.get_schema_versions("versioned_schema")
        assert len(versions) == 2
        assert "v1.0.0" in [v["version"] for v in versions]
        assert "v1.1.0" in [v["version"] for v in versions]
    
    def test_usage_tracking_contract(self):
        """Contract: Usage statistics are tracked and retrievable"""
        # Setup: Create schema
        schema_data = {"id": "usage_test", "name": "Usage Test"}
        self.storage.save_schema("usage_test", schema_data)
        
        # Contract: Initial usage count should be 0
        metadata = self.storage.get_schema_metadata("usage_test")
        assert metadata["usage_count"] == 0
        
        # Contract: Record usage should increment counter
        self.storage.record_schema_usage("usage_test")
        metadata = self.storage.get_schema_metadata("usage_test")
        assert metadata["usage_count"] == 1
        
        # Contract: Multiple uses should accumulate
        self.storage.record_schema_usage("usage_test")
        self.storage.record_schema_usage("usage_test")
        metadata = self.storage.get_schema_metadata("usage_test")
        assert metadata["usage_count"] == 3
    
    def test_backup_restore_contract(self):
        """Contract: Schemas can be backed up and restored"""
        # Setup: Create schemas
        schemas = [
            {"id": "backup1", "name": "Backup Test 1"},
            {"id": "backup2", "name": "Backup Test 2"}
        ]
        
        for schema in schemas:
            self.storage.save_schema(schema["id"], schema)
        
        # Contract: Create backup should export all schemas
        backup_data = self.storage.create_backup()
        assert "schemas" in backup_data
        assert "metadata" in backup_data
        assert len(backup_data["schemas"]) == 2
        
        # Contract: Restore should recreate schemas
        self.storage.clear_all_schemas()  # Clear for restore test
        result = self.storage.restore_backup(backup_data)
        assert result is True
        
        # Contract: Restored schemas should match originals
        restored_list = self.storage.list_schemas()
        assert len(restored_list) == 2
        restored_ids = [s["id"] for s in restored_list]
        assert "backup1" in restored_ids
        assert "backup2" in restored_ids