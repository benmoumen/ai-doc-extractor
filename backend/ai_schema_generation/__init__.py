"""
AI-Powered Schema Generation Module

This module provides comprehensive AI-powered schema generation capabilities
for document data extraction, including:

- Automated schema generation from document analysis
- Field type inference and validation rule generation
- Confidence scoring and quality assessment
- Integration with existing schema management systems
- Performance monitoring and caching
- Comprehensive error handling and logging

Main Components:
- Core API (ai_schema_generation.core.api)
- UI Components (ai_schema_generation.ui)
- Integration Layer (ai_schema_generation.integration)
- Utilities (ai_schema_generation.utils)

Usage:
    from ai_schema_generation.core.api import AISchemaGenerationAPI

    api = AISchemaGenerationAPI()
    result = api.generate_schema_from_document(document_path, document_type)

For UI integration:
    from ai_schema_generation.integration.app_integration import integrate_with_main_app

    integrate_with_main_app()

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AI Document Extractor Team"

# Import only utilities that are implemented
from .utils import (
    get_data_validator, get_schema_validator, get_confidence_calculator,
    get_cache_manager, get_error_handler, get_performance_monitor,
    get_logger, get_backup_manager
)

# Core API and Integration will be imported when implemented
try:
    from .core.api import AISchemaGenerationAPI
    _HAS_CORE_API = True
except ImportError:
    _HAS_CORE_API = False

try:
    from .integration.app_integration import integrate_with_main_app
    _HAS_INTEGRATION = True
except ImportError:
    _HAS_INTEGRATION = False

# Dynamic __all__ based on what's available
__all__ = [
    # Always available utility functions
    'get_data_validator',
    'get_schema_validator',
    'get_confidence_calculator',
    'get_cache_manager',
    'get_error_handler',
    'get_performance_monitor',
    'get_logger',
    'get_backup_manager'
]

if _HAS_CORE_API:
    __all__.append('AISchemaGenerationAPI')

if _HAS_INTEGRATION:
    __all__.append('integrate_with_main_app')