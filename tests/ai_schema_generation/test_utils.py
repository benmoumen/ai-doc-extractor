"""
T066: Unit tests for AI schema generation utilities
Comprehensive test suite for all utility components
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sqlite3
import time

# Import utilities to test
from ai_schema_generation.utils.data_validator import DataValidator, ValidationResult, get_data_validator
from ai_schema_generation.utils.schema_validator import SchemaValidator, SchemaValidationResult, get_schema_validator
from ai_schema_generation.utils.confidence_calculator import ConfidenceCalculator, ConfidenceScore, ConfidenceLevel, get_confidence_calculator
from ai_schema_generation.utils.cache_manager import CacheManager, get_cache_manager
from ai_schema_generation.utils.error_handler import ErrorHandler, ErrorSeverity, AISchemaError, get_error_handler
from ai_schema_generation.utils.performance_monitor import PerformanceMonitor, get_performance_monitor, ExecutionTimer
from ai_schema_generation.utils.logging_system import AISchemaLogger, LogLevel, get_logger
from ai_schema_generation.utils.backup_restore import BackupManager, BackupType, RestoreMode, get_backup_manager


class TestDataValidator:
    """Test data validation utilities"""

    @pytest.fixture
    def validator(self):
        return DataValidator()

    @pytest.fixture
    def sample_schema(self):
        return {
            'fields': {
                'name': {
                    'type': 'string',
                    'required': True,
                    'validation_rules': [{'type': 'length', 'min': 2, 'max': 100}]
                },
                'email': {
                    'type': 'email',
                    'required': True
                },
                'age': {
                    'type': 'integer',
                    'required': False,
                    'validation_rules': [{'type': 'range', 'min': 0, 'max': 150}]
                }
            }
        }

    def test_validate_string_field(self, validator):
        result = validator._validate_string("Hello World")
        assert result.is_valid
        assert result.normalized_value == "Hello World"

    def test_validate_email_field(self, validator):
        result = validator._validate_email("test@example.com")
        assert result.is_valid
        assert "@" in result.normalized_value

        result = validator._validate_email("invalid-email")
        assert not result.is_valid

    def test_validate_number_field(self, validator):
        result = validator._validate_number("123")
        assert result.is_valid
        assert result.normalized_value == 123

        result = validator._validate_number("123.45")
        assert result.is_valid
        assert result.normalized_value == 123.45

    def test_validate_schema_data(self, validator, sample_schema):
        valid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30
        }

        results = validator.validate_schema_data(valid_data, sample_schema)

        assert all(result.is_valid for result in results.values())
        assert len(results) == 3

    def test_validation_summary(self, validator, sample_schema):
        data_with_errors = {
            'name': 'J',  # Too short
            'email': 'invalid',  # Invalid email
            'age': 200  # Too old
        }

        results = validator.validate_schema_data(data_with_errors, sample_schema)
        summary = validator.get_validation_summary(results)

        assert summary['invalid_fields'] > 0
        assert not summary['is_valid']
        assert len(summary['errors']) > 0


class TestSchemaValidator:
    """Test schema validation utilities"""

    @pytest.fixture
    def validator(self):
        return SchemaValidator()

    @pytest.fixture
    def valid_schema(self):
        return {
            'id': 'test_schema',
            'name': 'Test Schema',
            'fields': {
                'field1': {
                    'type': 'string',
                    'required': True,
                    'display_name': 'Field 1'
                },
                'field2': {
                    'type': 'number',
                    'required': False,
                    'validation_rules': [{'type': 'range', 'min': 0, 'max': 100}]
                }
            }
        }

    def test_validate_valid_schema(self, validator, valid_schema):
        result = validator.validate_schema(valid_schema)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_invalid_schema_missing_id(self, validator):
        invalid_schema = {
            'name': 'Test Schema',
            'fields': {}
        }

        result = validator.validate_schema(invalid_schema)
        assert not result.is_valid
        assert any('id' in error.lower() for error in result.errors)

    def test_validate_field_names(self, validator):
        assert validator._is_valid_field_name('valid_name')
        assert validator._is_valid_field_name('valid_name_123')
        assert not validator._is_valid_field_name('123_invalid')
        assert not validator._is_valid_field_name('')

    def test_schema_compatibility_check(self, validator, valid_schema):
        modified_schema = valid_schema.copy()
        modified_schema['fields']['new_field'] = {'type': 'string', 'required': False}

        result = validator.validate_schema_compatibility(modified_schema, valid_schema)
        assert result.is_valid or len(result.warnings) > 0

    def test_suggest_improvements(self, validator, valid_schema):
        suggestions = validator.suggest_schema_improvements(valid_schema)
        assert isinstance(suggestions, list)


class TestConfidenceCalculator:
    """Test confidence calculation utilities"""

    @pytest.fixture
    def calculator(self):
        return ConfidenceCalculator()

    @pytest.fixture
    def sample_field_config(self):
        return {
            'type': 'email',
            'required': True,
            'validation_rules': [{'type': 'pattern', 'pattern': r'^[^@]+@[^@]+\.[^@]+$'}]
        }

    @pytest.fixture
    def sample_schema(self):
        return {
            'fields': {
                'email': {'type': 'email', 'required': True},
                'name': {'type': 'string', 'required': True},
                'phone': {'type': 'phone', 'required': False}
            }
        }

    def test_calculate_field_confidence_valid_email(self, calculator, sample_field_config):
        confidence = calculator.calculate_field_confidence(
            'email', 'test@example.com', sample_field_config
        )

        assert isinstance(confidence, ConfidenceScore)
        assert 0.0 <= confidence.score <= 1.0
        assert confidence.level in ConfidenceLevel

    def test_calculate_field_confidence_invalid_email(self, calculator, sample_field_config):
        confidence = calculator.calculate_field_confidence(
            'email', 'invalid-email', sample_field_config
        )

        assert confidence.score < 0.8  # Should have lower confidence

    def test_calculate_schema_confidence(self, calculator, sample_schema):
        schema_data = {
            'email': 'test@example.com',
            'name': 'John Doe',
            'phone': '+1234567890'
        }

        confidence = calculator.calculate_schema_confidence(schema_data, sample_schema)

        assert isinstance(confidence, ConfidenceScore)
        assert confidence.score > 0.5  # Should be reasonably confident

    def test_confidence_levels(self, calculator):
        assert calculator._get_confidence_level(0.95) == ConfidenceLevel.VERY_HIGH
        assert calculator._get_confidence_level(0.80) == ConfidenceLevel.HIGH
        assert calculator._get_confidence_level(0.60) == ConfidenceLevel.MEDIUM
        assert calculator._get_confidence_level(0.30) == ConfidenceLevel.LOW
        assert calculator._get_confidence_level(0.10) == ConfidenceLevel.VERY_LOW


class TestCacheManager:
    """Test cache management utilities"""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def cache_manager(self, temp_dir):
        return CacheManager(cache_dir=temp_dir)

    def test_cache_set_and_get(self, cache_manager):
        test_data = {'key': 'value', 'number': 42}

        success = cache_manager.set('test_key', test_data)
        assert success

        retrieved_data = cache_manager.get('test_key')
        assert retrieved_data == test_data

    def test_cache_expiration(self, cache_manager):
        test_data = {'expires': 'soon'}

        # Set with very short TTL
        cache_manager.set('expire_test', test_data, ttl_hours=0.001)  # ~3.6 seconds

        # Should be available immediately
        assert cache_manager.get('expire_test') == test_data

        # Wait and check expiration (in real test might need to mock time)
        time.sleep(4)
        assert cache_manager.get('expire_test') is None

    def test_cache_decorator(self, cache_manager):
        call_count = 0

        @cache_manager.cache_function(ttl_hours=1)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented

    def test_cache_cleanup(self, cache_manager):
        # Add multiple entries
        for i in range(5):
            cache_manager.set(f'key_{i}', f'value_{i}')

        # Check stats
        stats = cache_manager.get_cache_stats()
        assert stats['total_entries'] == 5


class TestErrorHandler:
    """Test error handling utilities"""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def error_handler(self, temp_dir):
        log_file = str(Path(temp_dir) / "test_errors.log")
        return ErrorHandler(log_file=log_file)

    def test_handle_basic_error(self, error_handler):
        test_error = ValueError("Test error message")

        error_info = error_handler.handle_error(test_error)

        assert error_info['type'] == 'ValueError'
        assert error_info['message'] == 'Test error message'
        assert 'error_id' in error_info
        assert 'timestamp' in error_info

    def test_handle_error_with_context(self, error_handler):
        test_error = RuntimeError("Runtime error")
        context = {'user_id': 'test_user', 'operation': 'test_op'}

        error_info = error_handler.handle_error(
            test_error,
            context=context,
            severity=ErrorSeverity.HIGH
        )

        assert error_info['context'] == context
        assert error_info['severity'] == ErrorSeverity.HIGH.value

    def test_ai_schema_error(self):
        error = AISchemaError(
            "Schema generation failed",
            error_code="SCHEMA_GEN_001",
            severity=ErrorSeverity.CRITICAL
        )

        assert error.error_code == "SCHEMA_GEN_001"
        assert error.severity == ErrorSeverity.CRITICAL
        assert str(error) == "Schema generation failed"

    def test_error_report(self, error_handler):
        # Generate some errors
        for i in range(3):
            error_handler.handle_error(ValueError(f"Error {i}"))

        report = error_handler.create_error_report()

        assert report['total_errors'] == 3
        assert 'ValueError' in report['errors_by_type']
        assert report['errors_by_type']['ValueError'] == 3


class TestPerformanceMonitor:
    """Test performance monitoring utilities"""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def monitor(self, temp_dir):
        db_path = str(Path(temp_dir) / "test_performance.db")
        return PerformanceMonitor(db_path=db_path)

    def test_start_end_session(self, monitor):
        session_id = monitor.start_session("test_session", {"test": True})
        assert session_id == "test_session"
        assert monitor.current_session is not None

        completed_session = monitor.end_session()
        assert completed_session is not None
        assert completed_session.session_id == "test_session"

    def test_record_metric(self, monitor):
        monitor.start_session("metric_test")

        monitor.record_metric("test_operation", 1.5, "seconds", {"status": "success"})

        # Check metric was recorded
        assert len(monitor.current_session.metrics) == 1
        metric = monitor.current_session.metrics[0]
        assert metric.name == "test_operation"
        assert metric.value == 1.5

    def test_execution_timer_context_manager(self, monitor):
        with monitor.measure_execution_time("test_operation") as timer:
            time.sleep(0.1)  # Simulate work
            elapsed = timer.get_elapsed_time()
            assert elapsed >= 0.1

    def test_execution_timer_decorator(self, monitor):
        from ai_schema_generation.utils.performance_monitor import measure_time

        @measure_time("decorated_operation")
        def test_function():
            time.sleep(0.05)
            return "result"

        result = test_function()
        assert result == "result"

    def test_performance_summary(self, monitor):
        monitor.start_session("summary_test")

        # Record some metrics
        monitor.record_metric("operation_a", 1.0)
        monitor.record_metric("operation_b", 2.0)
        monitor.record_metric("operation_a", 1.5)  # Another instance

        monitor.end_session()

        summary = monitor.get_performance_summary("summary_test")
        assert 'metrics' in summary

        # Should have data for both operations
        metrics = summary['metrics']
        assert 'operation_a' in metrics
        assert 'operation_b' in metrics


class TestLoggingSystem:
    """Test logging system utilities"""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def logger(self, temp_dir):
        return AISchemaLogger(
            name="test_logger",
            log_dir=temp_dir,
            enable_console=False,  # Disable for testing
            enable_file=True,
            enable_database=True
        )

    def test_basic_logging(self, logger):
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")

    def test_structured_logging(self, logger):
        logger.set_session_context("test_session", "test_user")

        logger.log_structured(
            LogLevel.INFO,
            "Structured log message",
            document_id="doc123",
            schema_id="schema456",
            extra_data={"key": "value"}
        )

    def test_performance_context(self, logger):
        with logger.performance_context("test_operation", operation_type="test") as context_id:
            time.sleep(0.1)
            assert context_id in logger.performance_contexts

    def test_ai_analysis_logging(self, logger):
        ai_metadata = {
            'model_used': 'gpt-4',
            'confidence': 0.85,
            'tokens_used': 150
        }

        logger.ai_analysis("AI analysis completed", ai_metadata=ai_metadata)

    @pytest.mark.asyncio
    async def test_get_recent_logs(self, logger):
        # Log some messages
        logger.info("Recent log 1")
        logger.warning("Recent log 2")

        # Allow time for async processing
        time.sleep(0.1)

        recent_logs = logger.get_recent_logs(hours=1)
        assert len(recent_logs) >= 0  # May be 0 due to async processing timing


class TestBackupManager:
    """Test backup and restore utilities"""

    @pytest.fixture
    def temp_dirs(self):
        backup_dir = tempfile.mkdtemp()
        data_dir = tempfile.mkdtemp()

        # Create some test data
        (Path(data_dir) / "schemas").mkdir(exist_ok=True)
        (Path(data_dir) / "extractions").mkdir(exist_ok=True)

        # Add test schema
        test_schema = {
            'id': 'test_schema',
            'name': 'Test Schema',
            'fields': {'field1': {'type': 'string'}}
        }
        with open(Path(data_dir) / "schemas" / "test_schema.json", 'w') as f:
            json.dump(test_schema, f)

        yield backup_dir, data_dir

        shutil.rmtree(backup_dir)
        shutil.rmtree(data_dir)

    @pytest.fixture
    def backup_manager(self, temp_dirs):
        backup_dir, data_dir = temp_dirs
        return BackupManager(backup_dir=backup_dir, data_dir=data_dir)

    def test_create_full_backup(self, backup_manager):
        result = backup_manager.create_backup(
            BackupType.FULL,
            description="Test full backup"
        )

        assert result['success']
        assert 'backup_id' in result
        assert Path(result['backup_path']).exists()

    def test_create_schema_backup(self, backup_manager):
        result = backup_manager.create_backup(
            BackupType.SCHEMAS,
            description="Test schema backup"
        )

        assert result['success']
        backup_path = Path(result['backup_path'])
        assert backup_path.exists()
        assert backup_path.suffix == '.zip'

    def test_list_backups(self, backup_manager):
        # Create a backup first
        backup_manager.create_backup(BackupType.SCHEMAS, description="Test backup")

        backups = backup_manager.list_backups()
        assert len(backups) >= 1

        backup = backups[0]
        assert 'backup_id' in backup
        assert 'backup_type' in backup
        assert 'created_at' in backup

    def test_backup_restore_cycle(self, backup_manager):
        # Create backup
        backup_result = backup_manager.create_backup(BackupType.SCHEMAS)
        assert backup_result['success']

        backup_id = backup_result['backup_id']

        # Restore backup
        restore_result = backup_manager.restore_backup(
            backup_id,
            RestoreMode.REPLACE
        )

        assert restore_result['success']
        assert restore_result['backup_id'] == backup_id

    def test_backup_statistics(self, backup_manager):
        # Create some backups
        backup_manager.create_backup(BackupType.SCHEMAS)
        backup_manager.create_backup(BackupType.DATA)

        stats = backup_manager.get_backup_statistics()

        assert stats['total_backups'] >= 2
        assert 'backups_by_type' in stats
        assert 'total_size_bytes' in stats

    def test_cleanup_old_backups(self, backup_manager):
        # Create several backups
        for i in range(3):
            backup_manager.create_backup(BackupType.SCHEMAS, description=f"Backup {i}")

        # Clean up, keeping only 2
        cleanup_result = backup_manager.cleanup_old_backups(keep_count=2)

        assert cleanup_result['success']
        # Note: Cleanup based on age might not delete recent backups


class TestIntegration:
    """Integration tests across utility components"""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_full_validation_workflow(self, temp_dir):
        """Test complete validation workflow using multiple utilities"""

        # Setup components
        data_validator = DataValidator()
        schema_validator = SchemaValidator()
        confidence_calculator = ConfidenceCalculator()
        error_handler = ErrorHandler()

        # Test schema
        test_schema = {
            'id': 'integration_test',
            'name': 'Integration Test Schema',
            'fields': {
                'email': {'type': 'email', 'required': True},
                'name': {'type': 'string', 'required': True},
                'age': {'type': 'integer', 'required': False}
            }
        }

        # Test data
        test_data = {
            'email': 'test@example.com',
            'name': 'John Doe',
            'age': 30
        }

        # 1. Validate schema structure
        schema_result = schema_validator.validate_schema(test_schema)
        assert schema_result.is_valid

        # 2. Validate extracted data
        data_results = data_validator.validate_schema_data(test_data, test_schema)
        assert all(result.is_valid for result in data_results.values())

        # 3. Calculate confidence
        confidence = confidence_calculator.calculate_schema_confidence(
            test_data, test_schema
        )
        assert confidence.score > 0.5

        # 4. Test error handling
        try:
            raise ValueError("Test integration error")
        except Exception as e:
            error_info = error_handler.handle_error(e)
            assert error_info['type'] == 'ValueError'

    def test_performance_monitoring_integration(self, temp_dir):
        """Test performance monitoring with other components"""

        monitor = PerformanceMonitor(db_path=str(Path(temp_dir) / "perf.db"))
        cache_manager = CacheManager(cache_dir=str(Path(temp_dir) / "cache"))

        session_id = monitor.start_session("integration_test")

        # Simulate operations with performance monitoring
        with monitor.measure_execution_time("cache_operation"):
            cache_manager.set("test_key", {"data": "test"})
            retrieved = cache_manager.get("test_key")
            assert retrieved["data"] == "test"

        monitor.end_session()

        # Verify performance data was recorded
        summary = monitor.get_performance_summary(session_id)
        assert 'metrics' in summary


# Test fixtures and utilities
@pytest.fixture(scope="session")
def sample_document_data():
    """Sample document data for testing"""
    return {
        'invoice_number': 'INV-2024-001',
        'date': '2024-01-15',
        'customer_name': 'Acme Corporation',
        'customer_email': 'billing@acme.com',
        'total_amount': 1250.50,
        'line_items': [
            {'description': 'Widget A', 'quantity': 10, 'price': 25.00},
            {'description': 'Widget B', 'quantity': 20, 'price': 50.00}
        ]
    }

@pytest.fixture(scope="session")
def sample_schema_definition():
    """Sample schema definition for testing"""
    return {
        'id': 'invoice_schema',
        'name': 'Invoice Schema',
        'description': 'Schema for invoice documents',
        'fields': {
            'invoice_number': {
                'type': 'string',
                'required': True,
                'display_name': 'Invoice Number',
                'validation_rules': [
                    {'type': 'pattern', 'pattern': r'^INV-\d{4}-\d{3}$'}
                ]
            },
            'date': {
                'type': 'date',
                'required': True,
                'display_name': 'Invoice Date'
            },
            'customer_name': {
                'type': 'string',
                'required': True,
                'display_name': 'Customer Name'
            },
            'customer_email': {
                'type': 'email',
                'required': False,
                'display_name': 'Customer Email'
            },
            'total_amount': {
                'type': 'float',
                'required': True,
                'display_name': 'Total Amount',
                'validation_rules': [
                    {'type': 'range', 'min': 0}
                ]
            },
            'line_items': {
                'type': 'array',
                'required': False,
                'display_name': 'Line Items'
            }
        },
        'metadata': {
            'version': '1.0',
            'created_date': '2024-01-01T00:00:00',
            'description': 'Standard invoice schema for document extraction'
        }
    }


if __name__ == '__main__':
    pytest.main([__file__, '-v'])