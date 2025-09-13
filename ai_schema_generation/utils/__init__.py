"""
Utility functions for AI schema generation
"""

from .cache_manager import CacheManager, get_cache_manager, cached
from .error_handler import ErrorHandler, ErrorSeverity, AISchemaError, get_error_handler, safe_execute
from .performance_monitor import PerformanceMonitor, get_performance_monitor, measure_time, ExecutionTimer
from .data_validator import DataValidator, ValidationResult, get_data_validator, validate_extracted_data
from .schema_validator import SchemaValidator, SchemaValidationResult, get_schema_validator, validate_schema_definition
from .confidence_calculator import ConfidenceCalculator, ConfidenceScore, ConfidenceLevel, get_confidence_calculator, calculate_extraction_confidence
from .logging_system import AISchemaLogger, LogLevel, get_logger, setup_logging, log_performance
from .backup_restore import BackupManager, BackupType, RestoreMode, get_backup_manager, create_automated_backup

__all__ = [
    # Cache Management
    'CacheManager', 'get_cache_manager', 'cached',

    # Error Handling
    'ErrorHandler', 'ErrorSeverity', 'AISchemaError', 'get_error_handler', 'safe_execute',

    # Performance Monitoring
    'PerformanceMonitor', 'get_performance_monitor', 'measure_time', 'ExecutionTimer',

    # Data Validation
    'DataValidator', 'ValidationResult', 'get_data_validator', 'validate_extracted_data',

    # Schema Validation
    'SchemaValidator', 'SchemaValidationResult', 'get_schema_validator', 'validate_schema_definition',

    # Confidence Calculation
    'ConfidenceCalculator', 'ConfidenceScore', 'ConfidenceLevel', 'get_confidence_calculator', 'calculate_extraction_confidence',

    # Logging System
    'AISchemaLogger', 'LogLevel', 'get_logger', 'setup_logging', 'log_performance',

    # Backup & Restore
    'BackupManager', 'BackupType', 'RestoreMode', 'get_backup_manager', 'create_automated_backup'
]