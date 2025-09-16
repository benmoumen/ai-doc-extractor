"""
T059: Enhanced error handling utilities
Comprehensive error handling and logging system
"""

import logging
import traceback
import sys
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum
import json


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AISchemaError(Exception):
    """Base exception for AI schema generation errors"""

    def __init__(self, message: str, error_code: str = None, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.severity = severity
        self.context = context or {}
        self.timestamp = datetime.now()


class ErrorHandler:
    """Comprehensive error handling system"""

    def __init__(self, log_file: str = "logs/ai_schema_errors.log"):
        """Initialize error handler"""
        self.log_file = log_file
        self.error_count = 0
        self.errors_by_type = {}
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        import os
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('ai_schema_generation')

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Dict[str, Any]:
        """Handle and log error with context"""
        self.error_count += 1

        error_info = {
            'error_id': f"ERR_{self.error_count:06d}",
            'type': type(error).__name__,
            'message': str(error),
            'severity': severity.value,
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
            'traceback': traceback.format_exc()
        }

        # Track error types
        error_type = type(error).__name__
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR: {error_info}")
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(f"HIGH SEVERITY: {error_info}")
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"MEDIUM SEVERITY: {error_info}")
        else:
            self.logger.info(f"LOW SEVERITY: {error_info}")

        return error_info

    def create_error_report(self) -> Dict[str, Any]:
        """Create comprehensive error report"""
        return {
            'total_errors': self.error_count,
            'errors_by_type': self.errors_by_type,
            'report_timestamp': datetime.now().isoformat(),
            'recommendations': self._get_error_recommendations()
        }

    def _get_error_recommendations(self) -> List[str]:
        """Get error handling recommendations"""
        recommendations = []

        if self.errors_by_type.get('DocumentProcessingError', 0) > 5:
            recommendations.append("High document processing errors - check document quality and formats")

        if self.errors_by_type.get('AIAnalysisError', 0) > 3:
            recommendations.append("AI analysis failures - verify API keys and model availability")

        if self.error_count > 20:
            recommendations.append("High error count - consider system health check")

        return recommendations


def safe_execute(func: Callable, *args, error_handler: Optional[ErrorHandler] = None, **kwargs) -> Dict[str, Any]:
    """Safely execute function with error handling"""
    try:
        result = func(*args, **kwargs)
        return {'success': True, 'result': result}
    except Exception as e:
        if error_handler:
            error_info = error_handler.handle_error(e)
        else:
            error_info = {'error': str(e), 'type': type(e).__name__}

        return {'success': False, 'error': error_info}


# Global error handler
_error_handler = ErrorHandler()

def get_error_handler() -> ErrorHandler:
    """Get global error handler"""
    return _error_handler