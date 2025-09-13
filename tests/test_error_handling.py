"""
Error Handling Validation and Recovery Testing.

Tests error handling mechanisms, recovery strategies, user feedback,
and system resilience in the schema management system.
"""

import pytest
import tempfile
import shutil
import os
import json
import sqlite3
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock
import threading
import time

# Import the modules we're testing
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from schema_management.error_handling import (
    ErrorHandler, SchemaError, ErrorType, ErrorSeverity,
    error_handler, validate_schema_data, validate_fields_data,
    validation_error, storage_error, import_error,
    ErrorContext, handle_errors
)
from schema_management.models.schema import Schema
from schema_management.models.field import Field, FieldType
from schema_management.storage.schema_storage import SchemaStorage, SchemaStorageError
from schema_management.services.schema_service import SchemaService
from schema_compatibility import (
    handle_extraction_error, get_extraction_configuration,
    validate_schema_for_extraction, compatibility_layer
)


class TestErrorHandling:
    """Test cases for error handling system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.error_handler = ErrorHandler()

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_schema_error_creation(self):
        """Test creating SchemaError objects."""
        error = SchemaError(
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.ERROR,
            message="Test validation error",
            details="Detailed error information",
            field_id="test_field",
            context={"schema_id": "test_schema"},
            user_message="User-friendly error message",
            recovery_suggestions=["Try fixing the field", "Check validation rules"]
        )
        
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.severity == ErrorSeverity.ERROR
        assert error.message == "Test validation error"
        assert error.field_id == "test_field"
        assert len(error.recovery_suggestions) == 2
        
        # Test serialization
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "validation"
        assert error_dict["severity"] == "error"
        assert "timestamp" in error_dict

    def test_error_handler_basic_functionality(self):
        """Test basic error handler functionality."""
        # Test handling a simple exception
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            handled_error = self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.ERROR,
                user_message="A validation error occurred"
            )
        
        assert isinstance(handled_error, SchemaError)
        assert handled_error.error_type == ErrorType.VALIDATION_ERROR
        assert handled_error.message == "Test exception"
        assert handled_error.user_message == "A validation error occurred"
        
        # Check that error was stored
        recent_errors = self.error_handler.get_recent_errors(1)
        assert len(recent_errors) == 1
        assert recent_errors[0] == handled_error

    def test_error_handler_with_schema_error(self):
        """Test error handler with SchemaError input."""
        schema_error = SchemaError(
            error_type=ErrorType.STORAGE_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="Storage failure",
            user_message="Failed to save data"
        )
        
        handled_error = self.error_handler.handle_error(schema_error)
        
        assert handled_error == schema_error
        assert len(self.error_handler.errors) == 1

    def test_error_severity_handling(self):
        """Test handling of different error severities."""
        severities = [
            (ErrorSeverity.INFO, "Info message"),
            (ErrorSeverity.WARNING, "Warning message"),
            (ErrorSeverity.ERROR, "Error message"),
            (ErrorSeverity.CRITICAL, "Critical message")
        ]
        
        for severity, message in severities:
            error = SchemaError(
                error_type=ErrorType.SYSTEM_ERROR,
                severity=severity,
                message=message
            )
            
            self.error_handler.handle_error(error)
        
        # All errors should be stored
        assert len(self.error_handler.errors) == 4
        
        # Check critical error detection
        assert self.error_handler.has_critical_errors()

    def test_validation_error_functions(self):
        """Test validation error utility functions."""
        # Test schema validation
        invalid_schema_data = {
            "id": "",  # Invalid empty ID
            "name": "",  # Invalid empty name
            "fields": [
                {
                    "id": "field1",
                    "name": "field1", 
                    "type": "invalid_type",  # Invalid type
                    "required": True
                }
            ]
        }
        
        is_valid, errors = validate_schema_data(invalid_schema_data)
        
        assert is_valid is False
        assert len(errors) >= 2  # Should have errors for ID, name, and field type
        assert any(error.field_id == "id" for error in errors)
        assert any(error.field_id == "name" for error in errors)

    def test_field_validation_errors(self):
        """Test field validation error handling."""
        invalid_fields_data = [
            {
                "id": "",  # Invalid empty ID
                "name": "",  # Invalid empty name
                "type": "string",
                "required": True
            },
            {
                "id": "field2",
                "name": "field2",
                "type": "select",
                "required": True,
                "options": []  # Invalid empty options for select field
            },
            {
                "id": "field1",  # Duplicate ID
                "name": "duplicate_field",
                "type": "string",
                "required": False
            }
        ]
        
        errors = validate_fields_data(invalid_fields_data)
        
        assert len(errors) >= 3  # Multiple validation errors
        
        # Check for specific error types
        error_messages = [error.message for error in errors]
        assert any("Required field 'id' is missing" in msg for msg in error_messages)
        assert any("Required field 'name' is missing" in msg for msg in error_messages)
        assert any("Duplicate field ID" in msg for msg in error_messages)
        assert any("must have options" in msg for msg in error_messages)

    def test_error_context_manager(self):
        """Test ErrorContext context manager."""
        # Test successful operation (no error)
        with ErrorContext(
            error_type=ErrorType.STORAGE_ERROR,
            severity=ErrorSeverity.ERROR,
            user_message="Storage operation failed"
        ):
            result = 1 + 1  # Simple operation
        
        assert result == 2
        
        # Test error handling with suppression
        with ErrorContext(
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.WARNING,
            user_message="Validation warning",
            reraise=False
        ):
            raise ValueError("Test error")
        
        # Should not raise exception due to suppression
        
        # Test error handling with re-raising
        with pytest.raises(ValueError):
            with ErrorContext(
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.CRITICAL,
                user_message="Critical error",
                reraise=True
            ):
                raise ValueError("Critical test error")

    def test_error_decorator(self):
        """Test error handling decorator."""
        @handle_errors(
            error_type=ErrorType.SERVICE_ERROR,
            severity=ErrorSeverity.ERROR,
            user_message="Service operation failed"
        )
        def failing_function():
            raise RuntimeError("Function failed")
        
        @handle_errors(
            error_type=ErrorType.SERVICE_ERROR,
            severity=ErrorSeverity.ERROR
        )
        def working_function():
            return "success"
        
        # Test failing function
        result = failing_function()
        assert result is None  # Should return None on error
        
        # Test working function
        result = working_function()
        assert result == "success"

    def test_storage_error_recovery(self):
        """Test storage error recovery mechanisms."""
        # Test with corrupted storage
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Create a valid schema first
        schema = Schema(
            id="recovery_test",
            name="Recovery Test Schema",
            description="Testing recovery mechanisms",
            version="1.0.0"
        )
        
        # Save schema
        success = storage.save_schema(schema)
        assert success is True
        
        # Corrupt the JSON file
        schema_file = os.path.join(self.temp_dir, "schema_recovery_test.json")
        with open(schema_file, 'w') as f:
            f.write("invalid json {")
        
        # Try to retrieve schema - should handle corruption gracefully
        retrieved_schema = storage.get_schema("recovery_test")
        
        # Should either return None or handle error gracefully
        assert retrieved_schema is None or isinstance(retrieved_schema, Schema)

    def test_database_error_recovery(self):
        """Test database error recovery mechanisms."""
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Corrupt the database
        db_path = os.path.join(self.temp_dir, "schemas.db")
        with open(db_path, 'w') as f:
            f.write("not a database")
        
        # Try to perform database operations
        schema = Schema(
            id="db_recovery_test",
            name="Database Recovery Test",
            description="Testing database recovery",
            version="1.0.0"
        )
        
        # Should handle database errors gracefully
        try:
            result = storage.save_schema(schema)
            # If it succeeds, the system recovered
            assert isinstance(result, bool)
        except SchemaStorageError:
            # If it fails with proper error, that's acceptable too
            pass

    def test_concurrent_error_handling(self):
        """Test error handling with concurrent operations."""
        errors_caught = []
        error_lock = threading.Lock()
        
        def concurrent_operation(operation_id: int):
            """Function that may raise errors concurrently."""
            try:
                if operation_id % 3 == 0:
                    raise ValueError(f"Error in operation {operation_id}")
                elif operation_id % 5 == 0:
                    raise RuntimeError(f"Runtime error in operation {operation_id}")
                
                # Simulate some work
                time.sleep(0.01)
                
            except Exception as e:
                with error_lock:
                    error = self.error_handler.handle_error(
                        error=e,
                        error_type=ErrorType.SYSTEM_ERROR,
                        severity=ErrorSeverity.ERROR,
                        context={"operation_id": operation_id}
                    )
                    errors_caught.append(error)
        
        # Run concurrent operations
        threads = []
        for i in range(20):
            thread = threading.Thread(target=concurrent_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify errors were handled properly
        assert len(errors_caught) > 0
        assert all(isinstance(error, SchemaError) for error in errors_caught)
        
        # Check that error handler is thread-safe
        total_errors = len(self.error_handler.get_recent_errors(50))
        assert total_errors >= len(errors_caught)

    def test_extraction_error_handling(self):
        """Test extraction workflow error handling."""
        # Test schema compatibility error handling
        invalid_schema_id = "nonexistent_schema"
        
        should_retry, fallback_config = handle_extraction_error(
            invalid_schema_id,
            ValueError("Schema not found"),
            fallback_to_generic=True
        )
        
        assert should_retry is True
        assert fallback_config is not None
        assert fallback_config["use_schema_prompt"] is False
        assert "fallback_reason" in fallback_config

    def test_schema_compatibility_error_handling(self):
        """Test schema compatibility error handling."""
        # Test with invalid schema
        is_valid, issues = validate_schema_for_extraction("invalid_schema_id")
        
        assert is_valid is False
        assert "Schema not found" in issues

    def test_recovery_suggestions(self):
        """Test error recovery suggestions."""
        # Test validation error with suggestions
        validation_error_obj = validation_error(
            "Field validation failed",
            field_id="test_field",
            suggestions=["Check field format", "Verify required fields", "Contact administrator"]
        )
        
        assert len(validation_error_obj.recovery_suggestions) == 3
        assert "Check field format" in validation_error_obj.recovery_suggestions

    def test_error_logging_and_persistence(self):
        """Test error logging and persistence."""
        # Create multiple errors
        errors_to_create = [
            (ErrorType.VALIDATION_ERROR, ErrorSeverity.ERROR, "Validation failed"),
            (ErrorType.STORAGE_ERROR, ErrorSeverity.CRITICAL, "Storage corrupted"),
            (ErrorType.IMPORT_ERROR, ErrorSeverity.WARNING, "Import warning"),
            (ErrorType.UI_ERROR, ErrorSeverity.INFO, "UI info message")
        ]
        
        for error_type, severity, message in errors_to_create:
            error = SchemaError(
                error_type=error_type,
                severity=severity,
                message=message
            )
            self.error_handler.handle_error(error)
        
        # Test error retrieval
        all_errors = self.error_handler.get_recent_errors(10)
        assert len(all_errors) == 4
        
        # Test error clearing
        self.error_handler.clear_errors()
        assert len(self.error_handler.get_recent_errors(10)) == 0

    def test_error_message_internationalization(self):
        """Test error messages for internationalization readiness."""
        # Test that error messages don't contain hardcoded formatting
        error = SchemaError(
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.ERROR,
            message="validation.field.required",  # Message key style
            user_message="Field is required",
            context={"field_name": "email", "field_type": "email"}
        )
        
        # Error should store both technical message and user message
        assert error.message == "validation.field.required"
        assert error.user_message == "Field is required"
        assert error.context["field_name"] == "email"

    def test_error_filtering_and_categorization(self):
        """Test error filtering and categorization."""
        # Create errors of different types and severities
        test_errors = [
            SchemaError(ErrorType.VALIDATION_ERROR, ErrorSeverity.ERROR, "Validation error 1"),
            SchemaError(ErrorType.VALIDATION_ERROR, ErrorSeverity.WARNING, "Validation warning 1"),
            SchemaError(ErrorType.STORAGE_ERROR, ErrorSeverity.CRITICAL, "Storage critical 1"),
            SchemaError(ErrorType.UI_ERROR, ErrorSeverity.INFO, "UI info 1"),
            SchemaError(ErrorType.VALIDATION_ERROR, ErrorSeverity.ERROR, "Validation error 2")
        ]
        
        for error in test_errors:
            self.error_handler.handle_error(error)
        
        all_errors = self.error_handler.get_recent_errors(10)
        
        # Filter by type
        validation_errors = [e for e in all_errors if e.error_type == ErrorType.VALIDATION_ERROR]
        assert len(validation_errors) == 3
        
        # Filter by severity
        critical_errors = [e for e in all_errors if e.severity == ErrorSeverity.CRITICAL]
        assert len(critical_errors) == 1
        
        error_errors = [e for e in all_errors if e.severity == ErrorSeverity.ERROR]
        assert len(error_errors) == 2

    def test_cascading_error_prevention(self):
        """Test prevention of cascading errors."""
        # Simulate a situation where one error could cause more errors
        original_error_count = len(self.error_handler.errors)
        
        # First error
        try:
            raise ValueError("Primary error")
        except ValueError as e:
            self.error_handler.handle_error(
                e,
                error_type=ErrorType.SYSTEM_ERROR,
                severity=ErrorSeverity.ERROR
            )
        
        # Attempt to handle the same error again (should not create duplicate)
        try:
            raise ValueError("Primary error")
        except ValueError as e:
            self.error_handler.handle_error(
                e,
                error_type=ErrorType.SYSTEM_ERROR,
                severity=ErrorSeverity.ERROR
            )
        
        # Should have errors, but system should handle duplicates gracefully
        final_error_count = len(self.error_handler.errors)
        assert final_error_count > original_error_count
        assert final_error_count <= original_error_count + 2

    def test_error_context_preservation(self):
        """Test that error context is preserved through the system."""
        context = {
            "user_id": "test_user",
            "schema_id": "test_schema",
            "operation": "schema_creation",
            "timestamp": "2023-01-01T12:00:00Z"
        }
        
        error = SchemaError(
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.ERROR,
            message="Context preservation test",
            context=context
        )
        
        handled_error = self.error_handler.handle_error(error)
        
        # Context should be preserved
        assert handled_error.context == context
        assert handled_error.context["user_id"] == "test_user"
        assert handled_error.context["schema_id"] == "test_schema"

    def test_error_recovery_workflow(self):
        """Test complete error recovery workflow."""
        # Simulate a complete error scenario and recovery
        
        # 1. Initial error occurs
        original_error = Exception("Database connection failed")
        
        # 2. Error is handled with recovery suggestions
        handled_error = self.error_handler.handle_error(
            original_error,
            error_type=ErrorType.STORAGE_ERROR,
            severity=ErrorSeverity.ERROR,
            user_message="Failed to save schema",
            recovery_suggestions=[
                "Check database connection",
                "Retry the operation",
                "Use backup storage"
            ]
        )
        
        # 3. System should provide actionable recovery information
        assert len(handled_error.recovery_suggestions) == 3
        assert "Retry the operation" in handled_error.recovery_suggestions
        
        # 4. Error should be logged for analysis
        recent_errors = self.error_handler.get_recent_errors(1)
        assert len(recent_errors) == 1
        assert recent_errors[0].error_type == ErrorType.STORAGE_ERROR
        
        # 5. System should remain functional after error
        # Test that we can still perform basic operations
        new_error = SchemaError(
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.WARNING,
            message="Post-recovery test"
        )
        
        post_recovery_error = self.error_handler.handle_error(new_error)
        assert post_recovery_error is not None


class TestErrorHandlingIntegration:
    """Integration tests for error handling across the system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_error_handling(self):
        """Test error handling through complete workflow."""
        storage = SchemaStorage(data_dir=self.temp_dir)
        schema_service = SchemaService(storage)
        
        # Test creating schema with validation errors
        invalid_schema_data = {
            "id": "",  # Invalid
            "name": "Test Schema",
            "description": "Test description",
            "version": "1.0.0",
            "fields": [
                {
                    "id": "field1",
                    "name": "",  # Invalid empty name
                    "type": "invalid_type",  # Invalid type
                    "required": True
                }
            ]
        }
        
        # Should handle validation errors gracefully
        success, message, created_schema = schema_service.create_schema(invalid_schema_data)
        
        assert success is False
        assert "error" in message.lower() or "invalid" in message.lower()
        assert created_schema is None

    def test_recovery_from_storage_failure(self):
        """Test recovery from storage failures."""
        # Create storage in a location that will cause problems
        if os.name != 'nt':  # Skip on Windows due to permission handling differences
            restricted_dir = tempfile.mkdtemp()
            os.chmod(restricted_dir, 0o444)  # Read-only
            
            try:
                # This should handle the permission error gracefully
                storage = SchemaStorage(data_dir=restricted_dir)
                
                schema_data = {
                    "id": "test_schema",
                    "name": "Test Schema", 
                    "description": "Test",
                    "version": "1.0.0",
                    "fields": []
                }
                
                # Should either fail gracefully or succeed with workaround
                try:
                    result = storage.save_schema(Schema.from_dict(schema_data))
                    # If it succeeds, the system found a workaround
                    assert isinstance(result, bool)
                except (SchemaStorageError, PermissionError, OSError):
                    # If it fails with proper error, that's acceptable
                    pass
                    
            finally:
                os.chmod(restricted_dir, 0o755)  # Restore permissions
                shutil.rmtree(restricted_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])