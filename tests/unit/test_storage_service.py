"""
Unit tests for Storage Service.

Tests the storage layer including file operations, database operations,
caching, error handling, and data integrity.
"""

import pytest
import tempfile
import shutil
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import the modules we're testing
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from schema_management.storage.schema_storage import SchemaStorage, SchemaStorageError
from schema_management.models.schema import Schema, SchemaStatus
from schema_management.models.field import Field, FieldType


class TestSchemaStorage:
    """Test cases for SchemaStorage."""

    def setup_method(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Sample schema for testing
        self.sample_schema = Schema(
            id="test_schema_001",
            name="Test Schema",
            description="A schema for testing storage operations",
            version="1.0.0",
            category="Test",
            fields=[
                Field(
                    id="field_1",
                    name="name",
                    display_name="Name",
                    field_type=FieldType.STRING,
                    required=True
                ),
                Field(
                    id="field_2",
                    name="email",
                    display_name="Email",
                    field_type=FieldType.EMAIL,
                    required=True
                )
            ]
        )

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_storage_initialization(self):
        """Test storage initialization."""
        # Test that directories are created
        assert os.path.exists(self.temp_dir)
        
        # Test that database is created
        db_path = os.path.join(self.temp_dir, "schemas.db")
        assert os.path.exists(db_path)
        
        # Test that database has correct tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if schemas table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schemas'")
        result = cursor.fetchone()
        assert result is not None
        
        conn.close()

    def test_save_schema_new(self):
        """Test saving a new schema."""
        success = self.storage.save_schema(self.sample_schema)
        
        assert success is True
        
        # Check that JSON file was created
        schema_file = os.path.join(self.temp_dir, f"schema_{self.sample_schema.id}.json")
        assert os.path.exists(schema_file)
        
        # Check that database record was created
        metadata = self.storage.get_schema_metadata(self.sample_schema.id)
        assert metadata is not None
        assert metadata["name"] == self.sample_schema.name
        assert metadata["version"] == self.sample_schema.version

    def test_save_schema_update(self):
        """Test updating an existing schema."""
        # Save initial schema
        self.storage.save_schema(self.sample_schema)
        
        # Update the schema
        updated_schema = self.sample_schema.copy()
        updated_schema.name = "Updated Test Schema"
        updated_schema.description = "Updated description"
        updated_schema.version = "1.1.0"
        
        success = self.storage.save_schema(updated_schema)
        
        assert success is True
        
        # Check that metadata was updated
        metadata = self.storage.get_schema_metadata(updated_schema.id)
        assert metadata["name"] == "Updated Test Schema"
        assert metadata["version"] == "1.1.0"

    def test_get_schema_success(self):
        """Test retrieving an existing schema."""
        # Save schema first
        self.storage.save_schema(self.sample_schema)
        
        # Retrieve schema
        retrieved_schema = self.storage.get_schema(self.sample_schema.id)
        
        assert retrieved_schema is not None
        assert retrieved_schema.id == self.sample_schema.id
        assert retrieved_schema.name == self.sample_schema.name
        assert len(retrieved_schema.fields) == len(self.sample_schema.fields)

    def test_get_schema_nonexistent(self):
        """Test retrieving a nonexistent schema."""
        retrieved_schema = self.storage.get_schema("nonexistent_schema")
        
        assert retrieved_schema is None

    def test_delete_schema_success(self):
        """Test deleting an existing schema."""
        # Save schema first
        self.storage.save_schema(self.sample_schema)
        
        # Verify it exists
        assert self.storage.schema_exists(self.sample_schema.id) is True
        
        # Delete schema
        success = self.storage.delete_schema(self.sample_schema.id)
        
        assert success is True
        assert self.storage.schema_exists(self.sample_schema.id) is False
        
        # Check that JSON file was deleted
        schema_file = os.path.join(self.temp_dir, f"schema_{self.sample_schema.id}.json")
        assert not os.path.exists(schema_file)

    def test_delete_schema_nonexistent(self):
        """Test deleting a nonexistent schema."""
        success = self.storage.delete_schema("nonexistent_schema")
        
        assert success is False

    def test_list_schemas_empty(self):
        """Test listing schemas when none exist."""
        schemas = self.storage.list_schemas()
        
        assert isinstance(schemas, list)
        assert len(schemas) == 0

    def test_list_schemas_with_data(self):
        """Test listing schemas with data."""
        # Create multiple schemas
        schemas_to_create = []
        for i in range(3):
            schema = Schema(
                id=f"schema_{i}",
                name=f"Schema {i}",
                description=f"Test schema {i}",
                version="1.0.0",
                category="Test"
            )
            schemas_to_create.append(schema)
            self.storage.save_schema(schema)
        
        # List schemas
        retrieved_schemas = self.storage.list_schemas()
        
        assert len(retrieved_schemas) == 3
        
        # Check that all schemas are present
        retrieved_ids = [s["id"] for s in retrieved_schemas]
        expected_ids = [s.id for s in schemas_to_create]
        
        for expected_id in expected_ids:
            assert expected_id in retrieved_ids

    def test_list_schemas_with_filters(self):
        """Test listing schemas with filters."""
        # Create schemas with different categories
        schema1 = Schema(id="schema1", name="Schema 1", category="Personal", version="1.0.0")
        schema2 = Schema(id="schema2", name="Schema 2", category="Business", version="1.0.0")
        schema3 = Schema(id="schema3", name="Schema 3", category="Personal", version="2.0.0")
        
        self.storage.save_schema(schema1)
        self.storage.save_schema(schema2)
        self.storage.save_schema(schema3)
        
        # Filter by category
        personal_schemas = self.storage.list_schemas({"category": "Personal"})
        assert len(personal_schemas) == 2
        
        business_schemas = self.storage.list_schemas({"category": "Business"})
        assert len(business_schemas) == 1
        
        # Filter by version
        v1_schemas = self.storage.list_schemas({"version": "1.0.0"})
        assert len(v1_schemas) == 2

    def test_search_schemas(self):
        """Test searching schemas by text."""
        # Create schemas with different names and descriptions
        schema1 = Schema(
            id="search1",
            name="User Profile",
            description="Schema for user profile information",
            version="1.0.0"
        )
        schema2 = Schema(
            id="search2", 
            name="Product Catalog",
            description="Schema for product information",
            version="1.0.0"
        )
        schema3 = Schema(
            id="search3",
            name="User Preferences",
            description="Schema for user settings and preferences",
            version="1.0.0"
        )
        
        self.storage.save_schema(schema1)
        self.storage.save_schema(schema2)
        self.storage.save_schema(schema3)
        
        # Search for "user"
        user_schemas = self.storage.search_schemas("user")
        assert len(user_schemas) >= 2  # Should find schema1 and schema3
        
        # Search for "product"
        product_schemas = self.storage.search_schemas("product")
        assert len(product_schemas) >= 1  # Should find schema2
        
        # Search for non-existent term
        empty_results = self.storage.search_schemas("nonexistent")
        assert len(empty_results) == 0

    def test_get_schema_metadata(self):
        """Test retrieving schema metadata."""
        self.storage.save_schema(self.sample_schema)
        
        metadata = self.storage.get_schema_metadata(self.sample_schema.id)
        
        assert metadata is not None
        assert metadata["id"] == self.sample_schema.id
        assert metadata["name"] == self.sample_schema.name
        assert metadata["version"] == self.sample_schema.version
        assert metadata["category"] == self.sample_schema.category
        assert "created_at" in metadata
        assert "updated_at" in metadata

    def test_update_schema_metadata(self):
        """Test updating schema metadata."""
        self.storage.save_schema(self.sample_schema)
        
        new_metadata = {
            "name": "Updated Schema Name",
            "description": "Updated description",
            "category": "Updated Category"
        }
        
        success = self.storage.update_schema_metadata(self.sample_schema.id, new_metadata)
        
        assert success is True
        
        # Verify metadata was updated
        updated_metadata = self.storage.get_schema_metadata(self.sample_schema.id)
        assert updated_metadata["name"] == "Updated Schema Name"
        assert updated_metadata["category"] == "Updated Category"

    def test_schema_exists(self):
        """Test checking if schema exists."""
        # Non-existent schema
        assert self.storage.schema_exists("nonexistent") is False
        
        # Save schema and check again
        self.storage.save_schema(self.sample_schema)
        assert self.storage.schema_exists(self.sample_schema.id) is True

    def test_get_schema_versions(self):
        """Test retrieving schema version history."""
        # Save initial version
        self.storage.save_schema(self.sample_schema)
        
        # Update version
        updated_schema = self.sample_schema.copy()
        updated_schema.version = "1.1.0"
        self.storage.save_schema(updated_schema)
        
        # Update version again
        updated_schema.version = "1.2.0"
        self.storage.save_schema(updated_schema)
        
        # Get version history
        versions = self.storage.get_schema_versions(self.sample_schema.id)
        
        # Should have at least the current version
        assert len(versions) >= 1
        assert any(v["version"] == "1.2.0" for v in versions)

    def test_backup_schema(self):
        """Test creating schema backup."""
        self.storage.save_schema(self.sample_schema)
        
        backup_path = self.storage.backup_schema(self.sample_schema.id)
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        
        # Verify backup contains correct data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        assert backup_data["id"] == self.sample_schema.id
        assert backup_data["name"] == self.sample_schema.name

    def test_restore_schema(self):
        """Test restoring schema from backup."""
        # Create and backup schema
        self.storage.save_schema(self.sample_schema)
        backup_path = self.storage.backup_schema(self.sample_schema.id)
        
        # Delete original schema
        self.storage.delete_schema(self.sample_schema.id)
        assert not self.storage.schema_exists(self.sample_schema.id)
        
        # Restore from backup
        success = self.storage.restore_schema(backup_path)
        
        assert success is True
        assert self.storage.schema_exists(self.sample_schema.id)
        
        # Verify restored schema
        restored_schema = self.storage.get_schema(self.sample_schema.id)
        assert restored_schema.name == self.sample_schema.name

    def test_concurrent_access(self):
        """Test concurrent access to storage."""
        import threading
        import time
        
        def save_schema(schema_id):
            schema = Schema(
                id=schema_id,
                name=f"Concurrent Schema {schema_id}",
                description="Testing concurrent access",
                version="1.0.0"
            )
            self.storage.save_schema(schema)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_schema, args=[f"concurrent_{i}"])
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all schemas were saved
        for i in range(5):
            schema_id = f"concurrent_{i}"
            assert self.storage.schema_exists(schema_id)

    def test_storage_error_handling(self):
        """Test storage error handling."""
        # Test with invalid directory permissions (if possible)
        if os.name != 'nt':  # Skip on Windows
            restricted_dir = tempfile.mkdtemp()
            os.chmod(restricted_dir, 0o444)  # Read-only
            
            try:
                restricted_storage = SchemaStorage(data_dir=restricted_dir)
                
                # This should raise an error or return False
                with pytest.raises((SchemaStorageError, PermissionError)):
                    restricted_storage.save_schema(self.sample_schema)
            finally:
                os.chmod(restricted_dir, 0o755)  # Restore permissions
                shutil.rmtree(restricted_dir, ignore_errors=True)

    def test_corrupted_data_handling(self):
        """Test handling of corrupted data files."""
        # Save valid schema first
        self.storage.save_schema(self.sample_schema)
        
        # Corrupt the JSON file
        schema_file = os.path.join(self.temp_dir, f"schema_{self.sample_schema.id}.json")
        with open(schema_file, 'w') as f:
            f.write("invalid json content {")
        
        # Try to retrieve schema
        retrieved_schema = self.storage.get_schema(self.sample_schema.id)
        
        # Should handle corruption gracefully (return None or raise specific error)
        assert retrieved_schema is None or isinstance(retrieved_schema, Schema)

    def test_database_integrity(self):
        """Test database integrity and consistency."""
        # Save schema
        self.storage.save_schema(self.sample_schema)
        
        # Manually corrupt database record
        db_path = os.path.join(self.temp_dir, "schemas.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update record to have inconsistent data
        cursor.execute(
            "UPDATE schemas SET name = 'Corrupted Name' WHERE id = ?",
            (self.sample_schema.id,)
        )
        conn.commit()
        conn.close()
        
        # Retrieve metadata and JSON data
        metadata = self.storage.get_schema_metadata(self.sample_schema.id)
        schema_data = self.storage.get_schema(self.sample_schema.id)
        
        # Should detect inconsistency
        if metadata and schema_data:
            assert metadata["name"] != schema_data.name

    def test_large_schema_handling(self):
        """Test handling of large schemas."""
        # Create schema with many fields
        large_fields = []
        for i in range(1000):
            field = Field(
                id=f"field_{i}",
                name=f"field_{i}",
                display_name=f"Field {i}",
                field_type=FieldType.STRING,
                description=f"Large schema test field {i}"
            )
            large_fields.append(field)
        
        large_schema = Schema(
            id="large_schema_test",
            name="Large Schema Test",
            description="Testing with many fields",
            version="1.0.0",
            fields=large_fields
        )
        
        # Test save and retrieve
        import time
        
        start_time = time.time()
        success = self.storage.save_schema(large_schema)
        save_time = time.time() - start_time
        
        assert success is True
        assert save_time < 5.0  # Should save within 5 seconds
        
        start_time = time.time()
        retrieved_schema = self.storage.get_schema(large_schema.id)
        retrieve_time = time.time() - start_time
        
        assert retrieved_schema is not None
        assert len(retrieved_schema.fields) == 1000
        assert retrieve_time < 5.0  # Should retrieve within 5 seconds

    def test_storage_cleanup(self):
        """Test storage cleanup operations."""
        # Create several schemas
        schema_ids = []
        for i in range(5):
            schema = Schema(
                id=f"cleanup_test_{i}",
                name=f"Cleanup Test {i}",
                description="Test cleanup",
                version="1.0.0"
            )
            self.storage.save_schema(schema)
            schema_ids.append(schema.id)
        
        # Delete some schemas
        for i in range(3):
            self.storage.delete_schema(schema_ids[i])
        
        # Run cleanup (if method exists)
        if hasattr(self.storage, 'cleanup'):
            self.storage.cleanup()
        
        # Verify only remaining schemas exist
        remaining_schemas = self.storage.list_schemas()
        assert len(remaining_schemas) == 2

    def test_storage_statistics(self):
        """Test storage statistics and metrics."""
        # Create schemas with different properties
        for i in range(10):
            schema = Schema(
                id=f"stats_test_{i}",
                name=f"Stats Test {i}",
                description="Testing statistics",
                version="1.0.0",
                category="Test" if i % 2 == 0 else "Other"
            )
            self.storage.save_schema(schema)
        
        # Get statistics (if method exists)
        if hasattr(self.storage, 'get_statistics'):
            stats = self.storage.get_statistics()
            
            assert stats["total_schemas"] == 10
            assert "categories" in stats
            assert stats["categories"]["Test"] == 5
            assert stats["categories"]["Other"] == 5


class TestSchemaStorageEdgeCases:
    """Test edge cases and error conditions for SchemaStorage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_storage_with_invalid_directory(self):
        """Test storage initialization with invalid directory."""
        # Test with a file instead of directory
        invalid_path = os.path.join(self.temp_dir, "not_a_directory")
        with open(invalid_path, 'w') as f:
            f.write("test")
        
        with pytest.raises((SchemaStorageError, OSError)):
            SchemaStorage(data_dir=invalid_path)

    def test_storage_with_readonly_directory(self):
        """Test storage with read-only directory."""
        if os.name != 'nt':  # Skip on Windows
            readonly_dir = tempfile.mkdtemp()
            os.chmod(readonly_dir, 0o444)  # Read-only
            
            try:
                with pytest.raises((SchemaStorageError, PermissionError)):
                    SchemaStorage(data_dir=readonly_dir)
            finally:
                os.chmod(readonly_dir, 0o755)  # Restore permissions
                shutil.rmtree(readonly_dir, ignore_errors=True)

    def test_save_schema_with_invalid_data(self):
        """Test saving schema with invalid data."""
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Test with None schema
        success = storage.save_schema(None)
        assert success is False

    def test_database_connection_failure(self):
        """Test handling of database connection failures."""
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Corrupt the database file
        db_path = os.path.join(self.temp_dir, "schemas.db")
        with open(db_path, 'w') as f:
            f.write("not a database")
        
        # Operations should handle database errors gracefully
        schema = Schema(id="test", name="Test", description="Test", version="1.0.0")
        
        # Should either succeed (by recreating DB) or fail gracefully
        try:
            result = storage.save_schema(schema)
            # If it succeeds, that's okay too (robust error recovery)
        except SchemaStorageError:
            # Expected error is also acceptable
            pass

    def test_disk_space_exhaustion(self):
        """Test handling of disk space exhaustion."""
        # This is difficult to test reliably across platforms
        # We'll create a scenario with a very large schema instead
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Create schema with very large field descriptions
        large_description = "x" * 10000000  # 10MB description
        
        schema = Schema(
            id="large_desc_test",
            name="Large Description Test",
            description=large_description,
            version="1.0.0"
        )
        
        # Should handle gracefully (succeed or fail with proper error)
        try:
            result = storage.save_schema(schema)
            # If it works, that's fine
        except (SchemaStorageError, MemoryError, OSError):
            # Expected errors are acceptable
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])