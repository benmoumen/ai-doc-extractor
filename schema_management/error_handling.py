"""
Error Handling and Validation System for Schema Management

Provides comprehensive error handling, validation, and user feedback mechanisms
for the schema management interface. Includes error logging, user notifications,
and recovery strategies.
"""

import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from datetime import datetime
from enum import Enum
import streamlit as st
from dataclasses import dataclass, field

from .models.schema import Schema, Field
from .models.validation_rule import ValidationRule, ValidationRuleType, ValidationSeverity


class ErrorType(Enum):
    """Types of errors that can occur in the schema management system."""
    VALIDATION_ERROR = "validation"
    STORAGE_ERROR = "storage" 
    IMPORT_ERROR = "import"
    EXPORT_ERROR = "export"
    UI_ERROR = "ui"
    SERVICE_ERROR = "service"
    SYSTEM_ERROR = "system"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SchemaError:
    """
    Represents an error in the schema management system.
    """
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    field_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    traceback_info: Optional[str] = None
    user_message: Optional[str] = None
    recovery_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "field_id": self.field_id,
            "context": self.context,
            "timestamp": self.timestamp,
            "traceback_info": self.traceback_info,
            "user_message": self.user_message,
            "recovery_suggestions": self.recovery_suggestions
        }


class ErrorHandler:
    """
    Central error handling system for schema management.
    """
    
    def __init__(self):
        self.errors: List[SchemaError] = []
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the error handler."""
        logger = logging.getLogger("schema_management.error_handler")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def handle_error(
        self,
        error: Union[Exception, SchemaError],
        error_type: ErrorType = ErrorType.SYSTEM_ERROR,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict[str, Any]] = None,
        field_id: Optional[str] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None
    ) -> SchemaError:
        """
        Handle an error and create a structured error object.
        
        Args:
            error: Exception or SchemaError object
            error_type: Type of error
            severity: Severity level
            context: Additional context information
            field_id: Related field ID if applicable
            user_message: User-friendly error message
            recovery_suggestions: List of recovery suggestions
            
        Returns:
            SchemaError object
        """
        if isinstance(error, SchemaError):
            schema_error = error
        else:
            schema_error = SchemaError(
                error_type=error_type,
                severity=severity,
                message=str(error),
                details=getattr(error, 'details', None),
                field_id=field_id,
                context=context or {},
                traceback_info=traceback.format_exc() if error else None,
                user_message=user_message,
                recovery_suggestions=recovery_suggestions or []
            )
        
        # Log the error
        self._log_error(schema_error)
        
        # Store error for tracking
        self.errors.append(schema_error)
        
        # Show user notification if appropriate
        if schema_error.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            self._show_user_notification(schema_error)
        
        return schema_error
    
    def _log_error(self, error: SchemaError) -> None:
        """Log an error with appropriate level."""
        log_message = f"[{error.error_type.value}] {error.message}"
        if error.details:
            log_message += f" - {error.details}"
        if error.context:
            log_message += f" - Context: {error.context}"
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Log traceback for exceptions
        if error.traceback_info and error.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            self.logger.error(f"Traceback: {error.traceback_info}")
    
    def _show_user_notification(self, error: SchemaError) -> None:
        """Show error notification to user via Streamlit."""
        user_msg = error.user_message or error.message
        
        if error.severity == ErrorSeverity.CRITICAL:
            st.error(f"🚨 Critical Error: {user_msg}")
        elif error.severity == ErrorSeverity.ERROR:
            st.error(f"❌ Error: {user_msg}")
        elif error.severity == ErrorSeverity.WARNING:
            st.warning(f"⚠️ Warning: {user_msg}")
        else:
            st.info(f"ℹ️ Info: {user_msg}")
        
        # Show recovery suggestions
        if error.recovery_suggestions:
            with st.expander("💡 Suggested Actions"):
                for suggestion in error.recovery_suggestions:
                    st.write(f"• {suggestion}")
    
    def get_recent_errors(self, limit: int = 10) -> List[SchemaError]:
        """Get recent errors."""
        return self.errors[-limit:] if self.errors else []
    
    def clear_errors(self) -> None:
        """Clear stored errors."""
        self.errors.clear()
    
    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors."""
        return any(error.severity == ErrorSeverity.CRITICAL for error in self.errors)


# Global error handler instance
error_handler = ErrorHandler()


# Validation Functions

def validate_schema_data(schema_data: Dict[str, Any]) -> Tuple[bool, List[SchemaError]]:
    """
    Validate schema data structure and content.
    
    Args:
        schema_data: Schema data to validate
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    # Required fields validation
    required_fields = ['id', 'name', 'version', 'fields']
    for field_name in required_fields:
        if field_name not in schema_data or not schema_data[field_name]:
            errors.append(SchemaError(
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.ERROR,
                message=f"Required field '{field_name}' is missing or empty",
                field_id=field_name,
                user_message=f"Schema must have a {field_name.replace('_', ' ')}",
                recovery_suggestions=[f"Please provide a value for {field_name}"]
            ))
    
    # Name validation
    if 'name' in schema_data:
        name = schema_data['name']
        if len(name) < 2:
            errors.append(SchemaError(
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.ERROR,
                message="Schema name must be at least 2 characters long",
                field_id='name',
                user_message="Schema name is too short",
                recovery_suggestions=["Enter a name with at least 2 characters"]
            ))
        elif len(name) > 100:
            errors.append(SchemaError(
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.ERROR,
                message="Schema name must not exceed 100 characters",
                field_id='name',
                user_message="Schema name is too long",
                recovery_suggestions=["Shorten the schema name to 100 characters or less"]
            ))
    
    # Version validation
    if 'version' in schema_data:
        version = schema_data['version']
        if not _is_valid_version(version):
            errors.append(SchemaError(
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.WARNING,
                message=f"Invalid version format: {version}",
                field_id='version',
                user_message="Version should follow semantic versioning (e.g., 1.0.0)",
                recovery_suggestions=["Use semantic versioning format like 1.0.0"]
            ))
    
    # Fields validation
    if 'fields' in schema_data:
        field_errors = validate_fields_data(schema_data['fields'])
        errors.extend(field_errors)
    
    return len(errors) == 0, errors


def validate_fields_data(fields_data: List[Dict[str, Any]]) -> List[SchemaError]:
    """
    Validate fields data.
    
    Args:
        fields_data: List of field data dictionaries
        
    Returns:
        List of validation errors
    """
    errors = []
    field_names = set()
    field_ids = set()
    
    for i, field_data in enumerate(fields_data):
        field_context = {"field_index": i}
        
        # Required field validation
        required_fields = ['id', 'name', 'type']
        for field_name in required_fields:
            if field_name not in field_data or not field_data[field_name]:
                errors.append(SchemaError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    severity=ErrorSeverity.ERROR,
                    message=f"Field {i+1}: Required field '{field_name}' is missing or empty",
                    field_id=field_data.get('id', f'field_{i}'),
                    context=field_context,
                    user_message=f"Field {i+1} is missing required {field_name}",
                    recovery_suggestions=[f"Provide a {field_name} for field {i+1}"]
                ))
        
        # Unique ID validation
        field_id = field_data.get('id')
        if field_id:
            if field_id in field_ids:
                errors.append(SchemaError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    severity=ErrorSeverity.ERROR,
                    message=f"Duplicate field ID: {field_id}",
                    field_id=field_id,
                    context=field_context,
                    user_message=f"Field ID '{field_id}' is used more than once",
                    recovery_suggestions=["Use unique IDs for each field"]
                ))
            field_ids.add(field_id)
        
        # Unique name validation
        field_name = field_data.get('name')
        if field_name:
            if field_name in field_names:
                errors.append(SchemaError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    severity=ErrorSeverity.ERROR,
                    message=f"Duplicate field name: {field_name}",
                    field_id=field_data.get('id', f'field_{i}'),
                    context=field_context,
                    user_message=f"Field name '{field_name}' is used more than once",
                    recovery_suggestions=["Use unique names for each field"]
                ))
            field_names.add(field_name)
        
        # Field type validation
        field_type = field_data.get('type')
        valid_types = ['string', 'number', 'integer', 'boolean', 'date', 'datetime', 'email', 'url', 'select', 'multiselect', 'file']
        if field_type and field_type not in valid_types:
            errors.append(SchemaError(
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.ERROR,
                message=f"Invalid field type: {field_type}",
                field_id=field_data.get('id', f'field_{i}'),
                context=field_context,
                user_message=f"Field type '{field_type}' is not supported",
                recovery_suggestions=[f"Use one of: {', '.join(valid_types)}"]
            ))
        
        # Select field options validation
        if field_type in ['select', 'multiselect']:
            options = field_data.get('options', [])
            if not options:
                errors.append(SchemaError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    severity=ErrorSeverity.ERROR,
                    message=f"Select field '{field_name}' must have options",
                    field_id=field_data.get('id', f'field_{i}'),
                    context=field_context,
                    user_message=f"Select field '{field_name}' needs options",
                    recovery_suggestions=["Add at least one option to the select field"]
                ))
        
        # Validation rules validation
        validation_rules = field_data.get('validation_rules', [])
        if validation_rules:
            rule_errors = validate_validation_rules(validation_rules, field_data.get('id', f'field_{i}'))
            errors.extend(rule_errors)
    
    return errors


def validate_validation_rules(rules_data: List[Dict[str, Any]], field_id: str) -> List[SchemaError]:
    """
    Validate validation rules data.
    
    Args:
        rules_data: List of validation rule data dictionaries
        field_id: ID of the field these rules belong to
        
    Returns:
        List of validation errors
    """
    errors = []
    
    for i, rule_data in enumerate(rules_data):
        rule_context = {"rule_index": i, "field_id": field_id}
        
        # Required fields
        if 'rule_type' not in rule_data:
            errors.append(SchemaError(
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.ERROR,
                message=f"Validation rule {i+1} missing rule_type",
                field_id=field_id,
                context=rule_context,
                user_message=f"Validation rule {i+1} needs a type",
                recovery_suggestions=["Select a validation rule type"]
            ))
        
        if 'message' not in rule_data or not rule_data['message']:
            errors.append(SchemaError(
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.WARNING,
                message=f"Validation rule {i+1} missing error message",
                field_id=field_id,
                context=rule_context,
                user_message=f"Validation rule {i+1} should have an error message",
                recovery_suggestions=["Add a descriptive error message"]
            ))
        
        # Rule-specific validation
        rule_type = rule_data.get('rule_type')
        parameters = rule_data.get('parameters', {})
        
        if rule_type == 'min_length' or rule_type == 'max_length':
            if 'length' not in parameters or not isinstance(parameters['length'], int):
                errors.append(SchemaError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    severity=ErrorSeverity.ERROR,
                    message=f"Length rule must have integer 'length' parameter",
                    field_id=field_id,
                    context=rule_context,
                    user_message="Length validation needs a number",
                    recovery_suggestions=["Enter a valid length number"]
                ))
        
        elif rule_type == 'regex':
            if 'pattern' not in parameters or not parameters['pattern']:
                errors.append(SchemaError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    severity=ErrorSeverity.ERROR,
                    message=f"Regex rule must have 'pattern' parameter",
                    field_id=field_id,
                    context=rule_context,
                    user_message="Regex validation needs a pattern",
                    recovery_suggestions=["Enter a valid regular expression pattern"]
                ))
    
    return errors


def _is_valid_version(version: str) -> bool:
    """Check if version string follows semantic versioning."""
    import re
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$'
    return bool(re.match(pattern, version))


# Decorator for error handling

def handle_errors(
    error_type: ErrorType = ErrorType.SYSTEM_ERROR,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    user_message: Optional[str] = None,
    recovery_suggestions: Optional[List[str]] = None
):
    """
    Decorator to handle errors in functions.
    
    Args:
        error_type: Type of error
        severity: Error severity
        user_message: User-friendly error message
        recovery_suggestions: Recovery suggestions
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    error=e,
                    error_type=error_type,
                    severity=severity,
                    context={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)},
                    user_message=user_message,
                    recovery_suggestions=recovery_suggestions
                )
                # Re-raise for critical errors
                if severity == ErrorSeverity.CRITICAL:
                    raise
                return None
        return wrapper
    return decorator


# Context manager for error handling

class ErrorContext:
    """Context manager for handling errors in code blocks."""
    
    def __init__(
        self,
        error_type: ErrorType = ErrorType.SYSTEM_ERROR,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None,
        reraise: bool = False
    ):
        self.error_type = error_type
        self.severity = severity
        self.user_message = user_message
        self.recovery_suggestions = recovery_suggestions
        self.reraise = reraise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback_obj):
        if exc_type is not None:
            error_handler.handle_error(
                error=exc_value,
                error_type=self.error_type,
                severity=self.severity,
                user_message=self.user_message,
                recovery_suggestions=self.recovery_suggestions
            )
            
            if self.reraise or self.severity == ErrorSeverity.CRITICAL:
                return False  # Re-raise the exception
            return True  # Suppress the exception


# Utility functions for UI

def show_error_summary():
    """Show a summary of recent errors in the UI."""
    recent_errors = error_handler.get_recent_errors()
    
    if not recent_errors:
        st.success("✅ No recent errors")
        return
    
    st.subheader("🔍 Error Summary")
    
    error_counts = {}
    for error in recent_errors:
        severity = error.severity.value
        error_counts[severity] = error_counts.get(severity, 0) + 1
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Critical", error_counts.get('critical', 0))
    with col2:
        st.metric("Errors", error_counts.get('error', 0))
    with col3:
        st.metric("Warnings", error_counts.get('warning', 0))
    with col4:
        st.metric("Info", error_counts.get('info', 0))
    
    if st.checkbox("Show Error Details"):
        for error in reversed(recent_errors):  # Most recent first
            severity_icon = {
                'critical': '🚨',
                'error': '❌',
                'warning': '⚠️',
                'info': 'ℹ️'
            }.get(error.severity.value, '❓')
            
            with st.expander(f"{severity_icon} {error.message}"):
                st.write(f"**Type:** {error.error_type.value}")
                st.write(f"**Time:** {error.timestamp}")
                if error.field_id:
                    st.write(f"**Field:** {error.field_id}")
                if error.details:
                    st.write(f"**Details:** {error.details}")
                if error.recovery_suggestions:
                    st.write("**Suggestions:**")
                    for suggestion in error.recovery_suggestions:
                        st.write(f"• {suggestion}")


def clear_error_history():
    """Clear error history (for UI button)."""
    error_handler.clear_errors()
    st.success("Error history cleared")


# Pre-configured error types for common scenarios

def validation_error(message: str, field_id: Optional[str] = None, suggestions: Optional[List[str]] = None) -> SchemaError:
    """Create a validation error."""
    return error_handler.handle_error(
        error=Exception(message),
        error_type=ErrorType.VALIDATION_ERROR,
        severity=ErrorSeverity.ERROR,
        field_id=field_id,
        user_message=message,
        recovery_suggestions=suggestions or []
    )


def storage_error(message: str, details: Optional[str] = None) -> SchemaError:
    """Create a storage error."""
    return error_handler.handle_error(
        error=Exception(message),
        error_type=ErrorType.STORAGE_ERROR,
        severity=ErrorSeverity.ERROR,
        user_message="Failed to save or load data",
        recovery_suggestions=["Check file permissions", "Try again", "Contact administrator"]
    )


def import_error(message: str, suggestions: Optional[List[str]] = None) -> SchemaError:
    """Create an import error."""
    return error_handler.handle_error(
        error=Exception(message),
        error_type=ErrorType.IMPORT_ERROR,
        severity=ErrorSeverity.ERROR,
        user_message="Failed to import schema",
        recovery_suggestions=suggestions or ["Check file format", "Verify file content", "Try a different file"]
    )