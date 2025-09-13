"""
Schema utilities for document data extraction.
Handles schema loading, validation, and prompt generation for AI processing.
"""
import json
import os
from typing import Dict, Any, List, Optional, Tuple
from config import DOCUMENT_SCHEMAS


def load_custom_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Load custom schemas from the schema management system.
    
    Returns:
        Dictionary of custom schemas with schema_id as key
    """
    custom_schemas = {}
    data_dir = "data"
    
    if not os.path.exists(data_dir):
        return custom_schemas
    
    # Load schemas from JSON files in data directory
    for filename in os.listdir(data_dir):
        if filename.endswith('.json') and filename.startswith('schema_'):
            schema_path = os.path.join(data_dir, filename)
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
                    
                # Convert custom schema format to extraction format
                if _is_valid_custom_schema(schema_data):
                    extraction_schema = _convert_custom_schema_to_extraction_format(schema_data)
                    custom_schemas[schema_data['id']] = extraction_schema
                    
            except (json.JSONDecodeError, IOError, KeyError) as e:
                # Skip invalid schema files
                continue
    
    return custom_schemas


def _is_valid_custom_schema(schema_data: Dict[str, Any]) -> bool:
    """
    Check if a loaded schema has the expected custom schema format.
    
    Args:
        schema_data: Schema data from JSON file
        
    Returns:
        True if valid custom schema format
    """
    required_fields = ['id', 'name', 'description', 'fields']
    return all(field in schema_data for field in required_fields)


def _convert_custom_schema_to_extraction_format(custom_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert custom schema format to the format expected by extraction workflow.
    
    Args:
        custom_schema: Schema in custom management format
        
    Returns:
        Schema in extraction format
    """
    # Convert field list to field dictionary
    fields_dict = {}
    
    for field_data in custom_schema.get('fields', []):
        field_name = field_data.get('name', '')
        if not field_name:
            continue
            
        # Convert field format
        extraction_field = {
            'name': field_name,
            'display_name': field_data.get('display_name', field_name),
            'type': field_data.get('type', 'string'),
            'required': field_data.get('required', False),
            'description': field_data.get('description', ''),
        }
        
        # Convert validation rules
        validation_rules = field_data.get('validation_rules', [])
        if validation_rules:
            converted_rules = []
            for rule in validation_rules:
                converted_rule = _convert_validation_rule_format(rule)
                if converted_rule:
                    converted_rules.append(converted_rule)
            extraction_field['validation_rules'] = converted_rules
        
        # Add examples if available
        if 'examples' in field_data:
            extraction_field['examples'] = field_data['examples']
            
        # Add options for select fields
        if field_data.get('type') in ['select', 'multiselect'] and 'options' in field_data:
            extraction_field['options'] = field_data['options']
        
        fields_dict[field_name] = extraction_field
    
    # Create extraction format schema
    extraction_schema = {
        'id': custom_schema['id'],
        'name': custom_schema['name'],
        'description': custom_schema['description'],
        'fields': fields_dict,
        'category': custom_schema.get('category', 'Custom'),
        'version': custom_schema.get('version', '1.0.0'),
        'custom': True  # Mark as custom schema
    }
    
    return extraction_schema


def _convert_validation_rule_format(rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convert validation rule from custom format to extraction format.
    
    Args:
        rule: Validation rule in custom format
        
    Returns:
        Validation rule in extraction format or None if invalid
    """
    rule_type = rule.get('rule_type')
    if not rule_type:
        return None
    
    # Map rule types from custom format to extraction format
    rule_type_mapping = {
        'required': 'required',
        'min_length': 'length',
        'max_length': 'length', 
        'regex': 'pattern',
        'min_value': 'range',
        'max_value': 'range',
        'email_format': 'format',
        'phone_format': 'format',
        'date_format': 'format'
    }
    
    mapped_type = rule_type_mapping.get(rule_type, rule_type)
    
    converted_rule = {
        'type': mapped_type,
        'message': rule.get('message', 'Validation failed'),
        'severity': rule.get('severity', 'error')
    }
    
    # Convert parameters based on rule type
    parameters = rule.get('parameters', {})
    
    if rule_type in ['min_length', 'max_length']:
        if 'length' in parameters:
            if rule_type == 'min_length':
                converted_rule['min'] = parameters['length']
            else:
                converted_rule['max'] = parameters['length']
    
    elif rule_type == 'regex':
        if 'pattern' in parameters:
            converted_rule['value'] = parameters['pattern']
    
    elif rule_type in ['min_value', 'max_value']:
        if 'value' in parameters:
            if rule_type == 'min_value':
                converted_rule['min'] = parameters['value']
            else:
                converted_rule['max'] = parameters['value']
    
    elif rule_type in ['email_format', 'phone_format', 'date_format']:
        format_mapping = {
            'email_format': 'email',
            'phone_format': 'phone', 
            'date_format': 'date'
        }
        converted_rule['value'] = format_mapping.get(rule_type, rule_type)
    
    return converted_rule


def get_all_available_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Get all available schemas (both predefined and custom).
    
    Returns:
        Dictionary of all schemas with schema_id as key
    """
    # Start with predefined schemas
    all_schemas = DOCUMENT_SCHEMAS.copy()
    
    # Add custom schemas
    custom_schemas = load_custom_schemas()
    all_schemas.update(custom_schemas)
    
    return all_schemas


def get_available_document_types() -> Dict[str, str]:
    """
    Get mapping of document type names to IDs (includes both predefined and custom schemas).
    
    Returns:
        dict: Mapping of display names to document type IDs
    """
    all_schemas = get_all_available_schemas()
    return {schema['name']: doc_id for doc_id, schema in all_schemas.items()}


def get_document_schema(document_type_id: str) -> Optional[Dict[str, Any]]:
    """
    Get schema for a specific document type (includes both predefined and custom schemas).
    
    Args:
        document_type_id: ID of the document type
        
    Returns:
        Schema dictionary or None if not found
    """
    # Handle invalid input types
    if not isinstance(document_type_id, str) or not document_type_id:
        return None
    
    all_schemas = get_all_available_schemas()
    return all_schemas.get(document_type_id)


def validate_schema_structure(schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that a schema has the required structure.
    
    Args:
        schema: Schema dictionary to validate
        
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required top-level fields
    required_fields = ['id', 'name', 'description', 'fields']
    for field in required_fields:
        if field not in schema:
            errors.append(f"Missing required field: {field}")
    
    # Check fields structure
    if 'fields' in schema:
        if not isinstance(schema['fields'], dict):
            errors.append("'fields' must be a dictionary")
        else:
            for field_name, field_def in schema['fields'].items():
                field_errors = _validate_field_definition(field_name, field_def)
                errors.extend(field_errors)
    
    return len(errors) == 0, errors


def _validate_field_definition(field_name: str, field_def: Dict[str, Any]) -> List[str]:
    """
    Validate individual field definition.
    
    Args:
        field_name: Name of the field
        field_def: Field definition dictionary
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Check required field properties
    required_props = ['name', 'display_name', 'type', 'required', 'description']
    for prop in required_props:
        if prop not in field_def:
            errors.append(f"Field '{field_name}' missing required property: {prop}")
    
    # Validate field type
    valid_types = ['string', 'number', 'date', 'boolean', 'email', 'phone']
    if 'type' in field_def and field_def['type'] not in valid_types:
        errors.append(f"Field '{field_name}' has invalid type: {field_def['type']}")
    
    # Validate validation rules if present
    if 'validation_rules' in field_def:
        if not isinstance(field_def['validation_rules'], list):
            errors.append(f"Field '{field_name}' validation_rules must be a list")
        else:
            for i, rule in enumerate(field_def['validation_rules']):
                rule_errors = _validate_validation_rule(field_name, i, rule)
                errors.extend(rule_errors)
    
    return errors


def _validate_validation_rule(field_name: str, rule_index: int, rule: Dict[str, Any]) -> List[str]:
    """
    Validate individual validation rule.
    
    Args:
        field_name: Name of the field
        rule_index: Index of the rule in the rules list
        rule: Validation rule dictionary
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Check required rule properties
    if 'type' not in rule:
        errors.append(f"Field '{field_name}' rule {rule_index} missing 'type'")
    
    if 'message' not in rule:
        errors.append(f"Field '{field_name}' rule {rule_index} missing 'message'")
    
    # Validate rule type
    valid_rule_types = ['required', 'pattern', 'length', 'range', 'format', 'custom']
    if 'type' in rule and rule['type'] not in valid_rule_types:
        errors.append(f"Field '{field_name}' rule {rule_index} has invalid type: {rule['type']}")
    
    # Validate severity if present
    if 'severity' in rule:
        valid_severities = ['error', 'warning', 'info']
        if rule['severity'] not in valid_severities:
            errors.append(f"Field '{field_name}' rule {rule_index} has invalid severity: {rule['severity']}")
    
    return errors


def create_schema_prompt(document_type_id: str) -> Optional[str]:
    """
    Generate schema-aware extraction prompt for AI processing.
    
    Args:
        document_type_id: ID of the document type
        
    Returns:
        Schema-aware prompt string or None if schema not found
    """
    schema = get_document_schema(document_type_id)
    if not schema:
        return None
    
    document_type_name = schema['name']
    fields_description = {}
    
    # Build field descriptions for the prompt
    for field_name, field_def in schema['fields'].items():
        field_info = {
            "display_name": field_def["display_name"],
            "type": field_def["type"],
            "required": field_def["required"],
            "description": field_def["description"]
        }
        
        # Add examples if available
        if "examples" in field_def:
            field_info["examples"] = field_def["examples"]
        
        # Add validation information
        if "validation_rules" in field_def:
            validation_info = []
            for rule in field_def["validation_rules"]:
                if rule["type"] == "pattern":
                    validation_info.append(f"Must match pattern: {rule['value']}")
                elif rule["type"] == "length":
                    if "min" in rule and "max" in rule:
                        validation_info.append(f"Length: {rule['min']}-{rule['max']} characters")
                    elif "min" in rule:
                        validation_info.append(f"Minimum length: {rule['min']} characters")
                    elif "max" in rule:
                        validation_info.append(f"Maximum length: {rule['max']} characters")
                elif rule["type"] == "range":
                    if "min" in rule and "max" in rule:
                        validation_info.append(f"Range: {rule['min']} to {rule['max']}")
                elif rule["type"] == "format":
                    validation_info.append(f"Format: {rule['value']}")
            
            if validation_info:
                field_info["validation"] = validation_info
        
        fields_description[field_name] = field_info
    
    # Generate the prompt
    prompt = f"""Analyze the {document_type_name} document in the provided image.

Extract data according to this exact schema:
{json.dumps(fields_description, indent=2, ensure_ascii=False)}

Return JSON in this EXACT format:
{{
    "extracted_data": {{
        {', '.join([f'"{field_name}": "extracted_value"' for field_name in schema['fields'].keys()])}
    }},
    "validation_results": {{
        {', '.join([f'"{field_name}": {{"status": "valid|invalid|warning|missing", "message": "detailed feedback", "extracted_value": "value", "confidence": 0.0-1.0}}' for field_name in schema['fields'].keys()])}
    }}
}}

CRITICAL REQUIREMENTS:
- Include validation_results for EVERY field in the schema, even if not found
- Use "missing" status if field is not visible or readable in the document
- Use "invalid" status if field doesn't meet the validation requirements
- Use "valid" status if field is found and meets requirements
- Use "warning" status for minor issues that don't prevent extraction
- Provide specific, helpful feedback in validation messages
- Include confidence score (0.0-1.0) based on text clarity and certainty
- Extract exactly what you see - do not infer or guess missing information
- For required fields that are missing, explain what you looked for
- For validation failures, explain what was expected vs what was found

The document type is: {document_type_name}
Expected purpose: {schema['description']}"""

    return prompt


def format_validation_results_for_display(validation_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format validation results for UI display.
    
    Args:
        validation_results: Raw validation results from AI
        
    Returns:
        List of formatted validation result entries
    """
    formatted_results = []
    
    for field_name, result in validation_results.items():
        status = result.get('status', 'unknown')
        message = result.get('message', 'No validation info')
        extracted_value = result.get('extracted_value', 'N/A')
        confidence = result.get('confidence', 0.0)
        
        # Status icons and colors
        status_config = {
            'valid': {'icon': '✅', 'color': 'green'},
            'invalid': {'icon': '❌', 'color': 'red'},
            'warning': {'icon': '⚠️', 'color': 'orange'},
            'missing': {'icon': '❓', 'color': 'gray'},
            'unknown': {'icon': '❔', 'color': 'gray'}
        }
        
        config = status_config.get(status, status_config['unknown'])
        
        formatted_results.append({
            'field_name': field_name,
            'status': status,
            'message': message,
            'extracted_value': extracted_value,
            'confidence': confidence,
            'icon': config['icon'],
            'color': config['color']
        })
    
    return formatted_results


def get_required_fields(document_type_id: str) -> List[str]:
    """
    Get list of required field names for a document type.
    
    Args:
        document_type_id: ID of the document type
        
    Returns:
        List of required field names
    """
    schema = get_document_schema(document_type_id)
    if not schema:
        return []
    
    return [
        field_name for field_name, field_def in schema['fields'].items()
        if field_def.get('required', False)
    ]


def validate_extracted_data_completeness(document_type_id: str, extracted_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that extracted data contains all required fields.
    
    Args:
        document_type_id: ID of the document type
        extracted_data: Data extracted from document
        
    Returns:
        tuple: (is_complete, list_of_missing_fields)
    """
    required_fields = get_required_fields(document_type_id)
    missing_fields = []
    
    for field_name in required_fields:
        if field_name not in extracted_data or not extracted_data[field_name]:
            missing_fields.append(field_name)
    
    return len(missing_fields) == 0, missing_fields