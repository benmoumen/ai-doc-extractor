"""
Schema Compatibility Layer for Document Extraction Workflow

Ensures seamless integration between predefined and custom schemas,
providing fallback mechanisms and consistent data flow throughout
the extraction process.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime

from schema_utils import (
    get_all_available_schemas,
    get_document_schema,
    create_schema_prompt,
    validate_extracted_data_completeness,
    format_validation_results_for_display
)
from config import DOCUMENT_SCHEMAS


logger = logging.getLogger(__name__)


class SchemaCompatibilityError(Exception):
    """Exception raised for schema compatibility issues."""
    pass


class SchemaCompatibilityLayer:
    """
    Handles compatibility between different schema formats and versions.
    """
    
    def __init__(self):
        self._schema_cache = {}
        self._last_cache_update = None
        self._cache_ttl = 300  # 5 minutes
    
    def get_compatible_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """
        Get schema with compatibility layer applied.
        
        Args:
            schema_id: ID of the schema to retrieve
            
        Returns:
            Compatible schema or None if not found
        """
        # Check cache first
        if self._is_cache_valid() and schema_id in self._schema_cache:
            return self._schema_cache[schema_id]
        
        # Refresh cache if needed
        if not self._is_cache_valid():
            self._refresh_schema_cache()
        
        # Get schema and apply compatibility
        raw_schema = get_document_schema(schema_id)
        if not raw_schema:
            return None
        
        compatible_schema = self._apply_compatibility_layer(raw_schema)
        
        # Cache the result
        self._schema_cache[schema_id] = compatible_schema
        
        return compatible_schema
    
    def _is_cache_valid(self) -> bool:
        """Check if schema cache is still valid."""
        if not self._last_cache_update:
            return False
        
        time_diff = (datetime.now() - self._last_cache_update).total_seconds()
        return time_diff < self._cache_ttl
    
    def _refresh_schema_cache(self):
        """Refresh the schema cache."""
        self._schema_cache.clear()
        self._last_cache_update = datetime.now()
        logger.info("Schema cache refreshed")
    
    def _apply_compatibility_layer(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply compatibility transformations to a schema.
        
        Args:
            schema: Raw schema data
            
        Returns:
            Schema with compatibility layer applied
        """
        compatible_schema = schema.copy()
        
        # Ensure required fields exist
        compatible_schema = self._ensure_required_fields(compatible_schema)
        
        # Normalize field definitions
        compatible_schema = self._normalize_field_definitions(compatible_schema)
        
        # Add compatibility metadata
        compatible_schema['_compatibility'] = {
            'version': '1.0.0',
            'processed_at': datetime.now().isoformat(),
            'is_custom': compatible_schema.get('custom', False),
            'original_format': 'custom' if compatible_schema.get('custom') else 'predefined'
        }
        
        return compatible_schema
    
    def _ensure_required_fields(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure schema has all required fields with defaults."""
        schema = schema.copy()
        
        # Top-level required fields
        if 'id' not in schema:
            schema['id'] = f"unknown_{datetime.now().timestamp()}"
        
        if 'name' not in schema:
            schema['name'] = schema['id'].replace('_', ' ').title()
        
        if 'description' not in schema:
            schema['description'] = f"Schema for {schema['name']}"
        
        if 'version' not in schema:
            schema['version'] = '1.0.0'
        
        if 'category' not in schema:
            schema['category'] = 'General'
        
        if 'fields' not in schema:
            schema['fields'] = {}
        
        return schema
    
    def _normalize_field_definitions(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field definitions for consistency."""
        schema = schema.copy()
        
        normalized_fields = {}
        
        for field_name, field_def in schema.get('fields', {}).items():
            normalized_field = self._normalize_single_field(field_name, field_def)
            normalized_fields[field_name] = normalized_field
        
        schema['fields'] = normalized_fields
        return schema
    
    def _normalize_single_field(self, field_name: str, field_def: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single field definition."""
        normalized = field_def.copy()
        
        # Ensure required field properties
        if 'name' not in normalized:
            normalized['name'] = field_name
        
        if 'display_name' not in normalized:
            normalized['display_name'] = field_name.replace('_', ' ').title()
        
        if 'type' not in normalized:
            normalized['type'] = 'string'
        
        if 'required' not in normalized:
            normalized['required'] = False
        
        if 'description' not in normalized:
            normalized['description'] = f"Field for {normalized['display_name']}"
        
        # Normalize validation rules
        if 'validation_rules' in normalized:
            normalized['validation_rules'] = self._normalize_validation_rules(
                normalized['validation_rules']
            )
        
        # Add metadata
        normalized['_normalized'] = True
        normalized['_original_name'] = field_name
        
        return normalized
    
    def _normalize_validation_rules(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize validation rules."""
        normalized_rules = []
        
        for rule in rules:
            normalized_rule = rule.copy()
            
            # Ensure required rule properties
            if 'type' not in normalized_rule and 'rule_type' in normalized_rule:
                normalized_rule['type'] = normalized_rule['rule_type']
            
            if 'message' not in normalized_rule:
                rule_type = normalized_rule.get('type', 'validation')
                normalized_rule['message'] = f"{rule_type} validation failed"
            
            if 'severity' not in normalized_rule:
                normalized_rule['severity'] = 'error'
            
            normalized_rules.append(normalized_rule)
        
        return normalized_rules
    
    def validate_schema_compatibility(self, schema_id: str) -> Tuple[bool, List[str]]:
        """
        Validate that a schema is compatible with the extraction workflow.
        
        Args:
            schema_id: ID of the schema to validate
            
        Returns:
            Tuple of (is_compatible, list of issues)
        """
        issues = []
        
        schema = self.get_compatible_schema(schema_id)
        if not schema:
            return False, ["Schema not found"]
        
        # Check required top-level fields
        required_fields = ['id', 'name', 'fields']
        for field in required_fields:
            if field not in schema:
                issues.append(f"Missing required field: {field}")
        
        # Check field definitions
        if 'fields' in schema:
            for field_name, field_def in schema['fields'].items():
                field_issues = self._validate_field_compatibility(field_name, field_def)
                issues.extend(field_issues)
        
        # Check if schema can generate valid prompts
        try:
            prompt = create_schema_prompt(schema_id)
            if not prompt:
                issues.append("Schema cannot generate extraction prompts")
        except Exception as e:
            issues.append(f"Prompt generation error: {str(e)}")
        
        return len(issues) == 0, issues
    
    def _validate_field_compatibility(self, field_name: str, field_def: Dict[str, Any]) -> List[str]:
        """Validate field compatibility."""
        issues = []
        
        # Check required field properties
        required_props = ['name', 'type']
        for prop in required_props:
            if prop not in field_def:
                issues.append(f"Field '{field_name}' missing required property: {prop}")
        
        # Check field type validity
        valid_types = [
            'string', 'number', 'integer', 'boolean', 'date', 'datetime',
            'email', 'url', 'phone', 'select', 'multiselect', 'file'
        ]
        field_type = field_def.get('type')
        if field_type and field_type not in valid_types:
            issues.append(f"Field '{field_name}' has unsupported type: {field_type}")
        
        return issues
    
    def get_extraction_fallbacks(self, schema_id: str) -> Dict[str, Any]:
        """
        Get fallback configuration for extraction workflow.
        
        Args:
            schema_id: ID of the schema
            
        Returns:
            Fallback configuration
        """
        schema = self.get_compatible_schema(schema_id)
        
        fallbacks = {
            'use_generic_extraction': False,
            'required_fields': [],
            'optional_fields': [],
            'fallback_prompt': None,
            'validation_level': 'strict'  # strict, relaxed, permissive
        }
        
        if not schema:
            fallbacks['use_generic_extraction'] = True
            return fallbacks
        
        # Analyze schema to determine fallback strategy
        fields = schema.get('fields', {})
        
        for field_name, field_def in fields.items():
            if field_def.get('required', False):
                fallbacks['required_fields'].append(field_name)
            else:
                fallbacks['optional_fields'].append(field_name)
        
        # Set validation level based on schema complexity
        total_fields = len(fields)
        validation_rules_count = sum(
            len(field_def.get('validation_rules', []))
            for field_def in fields.values()
        )
        
        if validation_rules_count > total_fields * 2:
            fallbacks['validation_level'] = 'strict'
        elif validation_rules_count > total_fields:
            fallbacks['validation_level'] = 'relaxed'
        else:
            fallbacks['validation_level'] = 'permissive'
        
        return fallbacks


# Global compatibility layer instance
compatibility_layer = SchemaCompatibilityLayer()


def get_compatible_schema(schema_id: str) -> Optional[Dict[str, Any]]:
    """
    Get schema with compatibility layer applied.
    
    Args:
        schema_id: Schema ID
        
    Returns:
        Compatible schema or None
    """
    return compatibility_layer.get_compatible_schema(schema_id)


def validate_schema_for_extraction(schema_id: str) -> Tuple[bool, List[str]]:
    """
    Validate that a schema is compatible with extraction workflow.
    
    Args:
        schema_id: Schema ID
        
    Returns:
        Tuple of (is_valid, list of issues)
    """
    return compatibility_layer.validate_schema_compatibility(schema_id)


def get_extraction_configuration(schema_id: str) -> Dict[str, Any]:
    """
    Get extraction configuration with fallbacks for a schema.
    
    Args:
        schema_id: Schema ID
        
    Returns:
        Extraction configuration
    """
    fallbacks = compatibility_layer.get_extraction_fallbacks(schema_id)
    schema = get_compatible_schema(schema_id)
    
    config = {
        'schema': schema,
        'fallbacks': fallbacks,
        'temperature': 0.1 if schema else 0.7,
        'max_tokens': 1500 if schema else 1024,
        'use_schema_prompt': schema is not None,
        'validation_enabled': schema is not None,
        'custom_schema': schema.get('custom', False) if schema else False
    }
    
    return config


def handle_extraction_error(
    schema_id: Optional[str],
    error: Exception,
    fallback_to_generic: bool = True
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Handle extraction errors with schema compatibility fallbacks.
    
    Args:
        schema_id: Schema ID that caused error
        error: The exception that occurred
        fallback_to_generic: Whether to fallback to generic extraction
        
    Returns:
        Tuple of (should_retry, fallback_config)
    """
    logger.error(f"Extraction error with schema {schema_id}: {str(error)}")
    
    if not schema_id or not fallback_to_generic:
        return False, None
    
    # Create fallback configuration for generic extraction
    fallback_config = {
        'schema': None,
        'temperature': 0.7,
        'max_tokens': 1024,
        'use_schema_prompt': False,
        'validation_enabled': False,
        'custom_schema': False,
        'fallback_reason': f"Schema error: {str(error)}"
    }
    
    logger.info(f"Falling back to generic extraction for schema {schema_id}")
    return True, fallback_config


def get_schema_health_status() -> Dict[str, Any]:
    """
    Get overall health status of schema system.
    
    Returns:
        Health status information
    """
    all_schemas = get_all_available_schemas()
    
    health = {
        'total_schemas': len(all_schemas),
        'predefined_schemas': 0,
        'custom_schemas': 0,
        'compatible_schemas': 0,
        'incompatible_schemas': 0,
        'issues': []
    }
    
    for schema_id, schema in all_schemas.items():
        if schema.get('custom', False):
            health['custom_schemas'] += 1
        else:
            health['predefined_schemas'] += 1
        
        # Check compatibility
        is_compatible, issues = validate_schema_for_extraction(schema_id)
        if is_compatible:
            health['compatible_schemas'] += 1
        else:
            health['incompatible_schemas'] += 1
            health['issues'].extend([f"{schema_id}: {issue}" for issue in issues])
    
    health['health_score'] = (
        health['compatible_schemas'] / health['total_schemas'] * 100
        if health['total_schemas'] > 0 else 100
    )
    
    return health


def refresh_schema_cache():
    """Force refresh of schema compatibility cache."""
    compatibility_layer._refresh_schema_cache()


def get_schema_migration_plan(old_schema_id: str, new_schema_id: str) -> Dict[str, Any]:
    """
    Generate migration plan between two schemas.
    
    Args:
        old_schema_id: Source schema ID
        new_schema_id: Target schema ID
        
    Returns:
        Migration plan
    """
    old_schema = get_compatible_schema(old_schema_id)
    new_schema = get_compatible_schema(new_schema_id)
    
    if not old_schema or not new_schema:
        return {
            'can_migrate': False,
            'reason': 'One or both schemas not found',
            'plan': []
        }
    
    old_fields = set(old_schema.get('fields', {}).keys())
    new_fields = set(new_schema.get('fields', {}).keys())
    
    common_fields = old_fields.intersection(new_fields)
    removed_fields = old_fields - new_fields
    added_fields = new_fields - old_fields
    
    plan = {
        'can_migrate': True,
        'compatibility_score': len(common_fields) / len(old_fields) if old_fields else 1.0,
        'plan': [
            {
                'action': 'keep',
                'fields': list(common_fields),
                'count': len(common_fields)
            },
            {
                'action': 'remove',
                'fields': list(removed_fields),
                'count': len(removed_fields)
            },
            {
                'action': 'add',
                'fields': list(added_fields),
                'count': len(added_fields)
            }
        ],
        'warnings': [],
        'recommendations': []
    }
    
    # Add warnings and recommendations
    if removed_fields:
        plan['warnings'].append(f"Data for {len(removed_fields)} fields will be lost")
    
    if added_fields:
        plan['recommendations'].append(f"Consider providing default values for {len(added_fields)} new fields")
    
    if plan['compatibility_score'] < 0.5:
        plan['warnings'].append("Low compatibility score - consider manual review")
    
    return plan