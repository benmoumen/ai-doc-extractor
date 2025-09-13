"""
Modern Schema utilities using Schema Manager directly.
Clean, unified interface for document schema operations.
"""
import json
from typing import Dict, Any, List, Optional, Tuple

from schema_management.services.schema_service import SchemaService


# Global Schema Service instance
schema_service = SchemaService()


def get_all_available_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Get all available schemas from Schema Manager.

    Returns:
        Dictionary of all schemas with schema_id as key
    """
    schemas = schema_service.list_schemas()
    return {schema['id']: schema for schema in schemas if schema.get('is_active', True)}


def get_available_document_types() -> Dict[str, str]:
    """
    Get mapping of document type names to IDs.

    Returns:
        dict: Mapping of display names to document type IDs
    """
    schemas = get_all_available_schemas()
    return {schema['name']: schema_id for schema_id, schema in schemas.items()}


def get_document_schema(document_type_id: str) -> Optional[Dict[str, Any]]:
    """
    Get schema for a specific document type.

    Args:
        document_type_id: ID of the document type

    Returns:
        Schema dictionary or None if not found
    """
    if not isinstance(document_type_id, str) or not document_type_id:
        return None

    try:
        schema = schema_service.get_schema(document_type_id)
        return schema.to_dict() if schema else None
    except Exception:
        return None


def create_schema_prompt(schema_id: str, document_type_name: str = None) -> Optional[str]:
    """
    Generate schema-aware extraction prompt for AI processing.

    Args:
        schema_id: ID of the document type
        document_type_name: Optional override for document name

    Returns:
        Schema-aware prompt string or None if schema not found
    """
    schema_dict = get_document_schema(schema_id)
    if not schema_dict:
        return None

    document_name = document_type_name or schema_dict['name']
    fields_description = {}

    # Build field descriptions for the prompt
    for field_name, field_def in schema_dict['fields'].items():
        field_info = {
            "display_name": field_def.get("display_name", field_name),
            "type": field_def.get("type", "text"),
            "required": field_def.get("required", False),
            "description": field_def.get("description", "")
        }

        # Add examples if available
        if "examples" in field_def:
            field_info["examples"] = field_def["examples"]

        fields_description[field_name] = field_info

    # Generate the prompt
    prompt = f"""Analyze the {document_name} document in the provided image.

Extract data according to this exact schema:
{json.dumps(fields_description, indent=2, ensure_ascii=False)}

Return JSON in this EXACT format:
{{
    "extracted_data": {{
        {', '.join([f'"{field_name}": "extracted_value"' for field_name in schema_dict['fields'].keys()])}
    }},
    "validation_results": {{
        {', '.join([f'"{field_name}": {{"status": "valid|invalid|warning|missing", "message": "detailed feedback", "extracted_value": "value", "confidence": 0.0-1.0}}' for field_name in schema_dict['fields'].keys()])}
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

The document type is: {document_name}
Expected purpose: {schema_dict.get('description', '')}"""

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