"""
Dynamic structured output schemas for LiteLLM JSON Mode.
Generates Pydantic models dynamically from user-defined schemas.
"""
import json
from typing import Dict, List, Optional, Any, Type
from pydantic import BaseModel, Field, create_model, ConfigDict
from enum import Enum


class ValidationStatus(str, Enum):
    """Validation status for extracted fields."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    MISSING = "missing"


class FieldValidation(BaseModel):
    """Validation result for a single field."""
    status: ValidationStatus
    message: str
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")


def python_type_from_schema_type(field_type: str) -> Type:
    """
    Convert schema field type string to Python type.

    Args:
        field_type: Schema field type (string, number, date, boolean, array, object)

    Returns:
        Python type for Pydantic model
    """
    type_mapping = {
        "string": str,
        "number": float,
        "integer": int,
        "date": str,  # ISO format date string
        "datetime": str,  # ISO format datetime string
        "boolean": bool,
        "array": List[Any],
        "object": Dict[str, Any]
    }
    return type_mapping.get(field_type, str)


def create_pydantic_field(field_config: dict) -> tuple:
    """
    Create a Pydantic field from schema field configuration.

    Args:
        field_config: Field configuration from schema

    Returns:
        Tuple of (type, Field) for Pydantic model
    """
    field_type = field_config.get("type", "string")
    python_type = python_type_from_schema_type(field_type)

    # Handle arrays with item types
    if field_type == "array" and "items" in field_config:
        item_type = field_config["items"].get("type", "string")
        python_type = List[python_type_from_schema_type(item_type)]

    # Make field optional if not required
    is_required = field_config.get("required", False)
    if not is_required:
        python_type = Optional[python_type]

    # Create field with metadata
    field = Field(
        default=None if not is_required else ...,
        description=field_config.get("description", ""),
        examples=field_config.get("examples", [])
    )

    return python_type, field


def create_dynamic_data_model(schema: dict) -> Type[BaseModel]:
    """
    Create a dynamic Pydantic model from user-defined schema.

    Args:
        schema: User-defined document schema

    Returns:
        Dynamically created Pydantic model class
    """
    fields = {}
    schema_fields = schema.get("fields", {})

    for field_name, field_config in schema_fields.items():
        # Convert field name to valid Python identifier
        safe_field_name = field_name.replace(" ", "_").replace("-", "_").lower()
        field_type, field_def = create_pydantic_field(field_config)
        fields[safe_field_name] = (field_type, field_def)

    # Create dynamic model with fields
    model_name = f"{schema.get('name', 'Document').replace(' ', '')}Data"
    return create_model(
        model_name,
        **fields,
        __config__=ConfigDict(extra='allow')
    )


def create_extraction_model(schema: dict) -> Type[BaseModel]:
    """
    Create a complete extraction model with data and validation.

    Args:
        schema: User-defined document schema

    Returns:
        Dynamically created extraction model class
    """
    # Create the data model
    data_model = create_dynamic_data_model(schema)

    # Create extraction wrapper model
    extraction_fields = {
        "data": (data_model, Field(description="Extracted document data")),
        "validation_results": (
            Dict[str, FieldValidation],
            Field(default_factory=dict, description="Validation results for each field")
        ),
        "document_confidence": (
            float,
            Field(ge=0.0, le=1.0, description="Overall extraction confidence")
        ),
        "processing_notes": (
            Optional[str],
            Field(None, description="Additional processing notes")
        )
    }

    model_name = f"{schema.get('name', 'Document').replace(' ', '')}Extraction"
    return create_model(
        model_name,
        **extraction_fields,
        __config__=ConfigDict(extra='allow')
    )


def get_schema_from_storage(document_type: str) -> Optional[dict]:
    """
    Retrieve schema from storage system.

    Args:
        document_type: Document type ID

    Returns:
        Schema dictionary or None if not found
    """
    try:
        from schema_utils import get_document_schema
        schema = get_document_schema(document_type)
        return schema
    except:
        # Fallback to trying schema management
        try:
            from schema_management.services.storage import SchemaStorageService
            storage = SchemaStorageService()
            schema = storage.get_schema(document_type)
            return schema
        except:
            return None


def create_response_format_from_schema(schema: dict, schema_name: Optional[str] = None, provider: Optional[str] = None) -> dict:
    """
    Create response_format parameter for LiteLLM from user schema.

    Args:
        schema: User-defined document schema
        schema_name: Optional custom schema name
        provider: Optional provider name for provider-specific formatting

    Returns:
        Dictionary with response_format configuration for LiteLLM
    """
    # Create dynamic Pydantic model
    model_class = create_extraction_model(schema)

    # Get JSON schema from Pydantic model
    json_schema = model_class.model_json_schema()

    # For Mistral and Groq, only use basic JSON mode
    # They don't support schema in response_format yet
    if provider and provider.lower() in ['mistral', 'groq']:
        return {"type": "json_object"}

    # For OpenAI and compatible providers, include schema
    return {
        "type": "json_object",
        "response_schema": json_schema,
        "name": schema_name or f"{schema.get('name', 'document')}_extraction"
    }


def create_response_format_for_document(document_type: str, provider: Optional[str] = None) -> Optional[dict]:
    """
    Create response_format for a document type from stored schema.

    Args:
        document_type: Document type ID
        provider: Optional provider name for provider-specific formatting

    Returns:
        Response format configuration or None if schema not found
    """
    schema = get_schema_from_storage(document_type)
    if not schema:
        return None

    return create_response_format_from_schema(schema, document_type, provider)


def validate_extraction_with_schema(schema: dict, result: dict) -> tuple[bool, Any, List[str]]:
    """
    Validate extraction result against dynamic schema.

    Args:
        schema: User-defined document schema
        result: Extraction result dictionary

    Returns:
        Tuple of (is_valid, parsed_model, validation_errors)
    """
    model_class = create_extraction_model(schema)

    try:
        parsed = model_class.model_validate(result)
        return True, parsed, []
    except Exception as e:
        errors = str(e).split('\n')
        return False, None, errors


def generate_simplified_prompt(schema: dict, provider: Optional[str] = None) -> str:
    """
    Generate a simplified prompt for structured output extraction.

    Args:
        schema: User-defined document schema
        provider: Optional provider name for provider-specific prompts

    Returns:
        Prompt string optimized for structured output
    """
    doc_type = schema.get('name', 'document')
    fields = schema.get('fields', {})

    # Build field list
    field_descriptions = []
    for field_name, field_config in fields.items():
        field_type = field_config.get('type', 'string')
        required = "required" if field_config.get('required', False) else "optional"
        description = field_config.get('description', '')
        field_descriptions.append(f"- {field_name} ({field_type}, {required}): {description}")

    # For Mistral/Groq, include detailed JSON structure since they don't support schema
    if provider and provider.lower() in ['mistral', 'groq']:
        # Create example JSON structure
        example_data = {}
        for field_name, field_config in fields.items():
            field_type = field_config.get('type', 'string')
            if field_type == 'string':
                example_data[field_name] = "extracted_text_here"
            elif field_type in ['number', 'integer']:
                example_data[field_name] = 0
            elif field_type == 'boolean':
                example_data[field_name] = True
            elif field_type == 'array':
                example_data[field_name] = []
            elif field_type == 'object':
                example_data[field_name] = {}
            else:
                example_data[field_name] = None

        prompt = f"""Extract information from this {doc_type} image.

Fields to extract:
{chr(10).join(field_descriptions)}

Return a JSON object with EXACTLY this structure:
{{
  "data": {json.dumps(example_data, indent=2)},
  "validation_results": {{
    "field_name": {{
      "status": "valid|invalid|warning|missing",
      "message": "validation message",
      "confidence": 0.95
    }}
  }},
  "document_confidence": 0.9,
  "processing_notes": "optional notes"
}}

Replace the example values with actual extracted data. Use null for missing optional fields."""
    else:
        # For providers with schema support, use simpler prompt
        prompt = f"""Extract information from this {doc_type} image.

Extract these fields:
{chr(10).join(field_descriptions)}

Return structured JSON with:
1. "data" object containing extracted field values
2. "validation_results" with status, message, and confidence for each field
3. "document_confidence" score (0-1)
4. "processing_notes" if applicable

Use null for missing optional fields."""

    return prompt

def validate_extraction_result(document_type: str, result: dict) -> tuple[bool, Any, List[str]]:
    """
    Validate extraction result against schema.
    This is a compatibility wrapper.

    Args:
        document_type: Type of document extracted
        result: Extraction result dictionary

    Returns:
        Tuple of (is_valid, parsed_model, validation_errors)
    """
    schema = get_schema_from_storage(document_type)
    if not schema:
        return False, None, ["Schema not found for document type"]

    return validate_extraction_with_schema(schema, result)