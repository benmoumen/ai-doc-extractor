# Data Model: Schema-Driven Document Data Extraction

## Core Entities

### DocumentType
Represents a predefined category of documents that can be processed.

**Fields**:
- `id`: Unique identifier (string) - e.g., "national_id", "passport", "business_license"
- `name`: Human-readable name (string) - e.g., "National ID", "Passport", "Business License"
- `description`: Brief description of the document type (string)
- `schema`: Reference to associated Schema object
- `examples`: Optional list of field examples for UI guidance

**Example**:
```python
{
    "id": "national_id",
    "name": "National ID",
    "description": "Government-issued national identification document",
    "schema": {...},  # Schema object
    "examples": {
        "full_name": "John Smith",
        "id_number": "AB123456789"
    }
}
```

### Schema
Template defining the expected fields and validation rules for a document type.

**Fields**:
- `document_type_id`: Reference to parent DocumentType (string)
- `fields`: Dictionary of Field definitions (dict)
- `version`: Schema version for compatibility (string) - e.g., "1.0.0"
- `created_date`: Schema creation timestamp (datetime)
- `updated_date`: Last modification timestamp (datetime)

**Example**:
```python
{
    "document_type_id": "national_id",
    "fields": {
        "full_name": Field(...),
        "id_number": Field(...),
        "date_of_birth": Field(...)
    },
    "version": "1.0.0",
    "created_date": "2025-09-12T10:00:00Z",
    "updated_date": "2025-09-12T10:00:00Z"
}
```

### Field
Individual data element within a schema with validation rules.

**Fields**:
- `name`: Field identifier (string)
- `display_name`: Human-readable field name (string)
- `type`: Data type (enum) - "string", "number", "date", "boolean", "email", "phone"
- `required`: Whether field is mandatory (boolean)
- `validation_rules`: List of ValidationRule objects
- `description`: Field description for UI and prompts (string)
- `examples`: Sample values for guidance (list of strings)

**Example**:
```python
{
    "name": "id_number",
    "display_name": "ID Number",
    "type": "string",
    "required": True,
    "validation_rules": [
        {"type": "pattern", "value": "^[A-Z]{2}[0-9]{9}$", "message": "Must be 2 letters followed by 9 numbers"},
        {"type": "length", "min": 11, "max": 11, "message": "Must be exactly 11 characters"}
    ],
    "description": "Unique identification number on the document",
    "examples": ["AB123456789", "CD987654321"]
}
```

### ValidationRule
Constraint applied to field values during extraction.

**Fields**:
- `type`: Validation type (enum) - "required", "pattern", "length", "range", "format", "custom"
- `value`: Validation parameter (varies by type)
- `min`: Minimum value for range/length validations (optional)
- `max`: Maximum value for range/length validations (optional)
- `message`: Error message when validation fails (string)
- `severity`: Validation severity (enum) - "error", "warning", "info"

**Validation Types**:
- `required`: Field must have a value
- `pattern`: Must match regex pattern
- `length`: String length constraints
- `range`: Numeric range constraints
- `format`: Predefined formats (date, email, phone)
- `custom`: Custom validation logic identifier

### ExtractionResult
Complete output from AI processing containing extracted data and validation results.

**Fields**:
- `document_type_id`: Type of document processed (string)
- `extracted_data`: Raw extracted field values (dict)
- `validation_results`: Field-level validation outcomes (dict of ValidationResult)
- `processing_metadata`: AI model and processing info
- `confidence_scores`: Per-field confidence levels (dict, optional)
- `extraction_timestamp`: When processing occurred (datetime)

**Example**:
```python
{
    "document_type_id": "national_id",
    "extracted_data": {
        "full_name": "John Smith",
        "id_number": "AB123456789",
        "date_of_birth": "1985-03-15",
        "address": "123 Main St, City"
    },
    "validation_results": {
        "full_name": ValidationResult(...),
        "id_number": ValidationResult(...),
        "date_of_birth": ValidationResult(...),
        "address": ValidationResult(...)
    },
    "processing_metadata": {
        "model": "groq/meta-llama/llama-4-scout-17b-16e-instruct",
        "processing_time": 2.34,
        "tokens_used": {"input": 1250, "output": 380}
    },
    "extraction_timestamp": "2025-09-12T14:30:00Z"
}
```

### ValidationResult
Field-level validation feedback from AI processing.

**Fields**:
- `field_name`: Name of the field validated (string)
- `status`: Validation outcome (enum) - "valid", "invalid", "warning", "missing"
- `message`: Detailed validation feedback (string)
- `extracted_value`: The value that was extracted (any)
- `expected_format`: What format was expected (string, optional)
- `confidence`: AI confidence in the extraction (float 0-1, optional)

**Example**:
```python
{
    "field_name": "date_of_birth",
    "status": "valid",
    "message": "Date format is correct and value is reasonable",
    "extracted_value": "1985-03-15",
    "expected_format": "YYYY-MM-DD",
    "confidence": 0.95
}
```

## Entity Relationships

```
DocumentType (1) --> (1) Schema
Schema (1) --> (many) Field
Field (1) --> (many) ValidationRule
ExtractionResult (1) --> (many) ValidationResult
DocumentType (1) --> (many) ExtractionResult [via document_type_id]
```

## Data Flow

1. **Schema Definition**: DocumentType defines available document categories
2. **Field Specification**: Schema contains Field definitions with ValidationRules
3. **Document Processing**: User selects DocumentType and uploads document
4. **AI Extraction**: LLM processes document using schema-aware prompts
5. **Result Generation**: AI returns ExtractionResult with ValidationResults per field
6. **Display**: UI shows extracted data with validation feedback

## Implementation Notes

### Storage Strategy
Based on research findings, schemas will be stored as Python dictionaries in configuration files:

```python
# config.py extension
DOCUMENT_SCHEMAS = {
    "national_id": {
        "id": "national_id",
        "name": "National ID",
        "description": "Government-issued identification",
        "fields": {...}
    },
    # Additional document types...
}
```

### State Management
- Current document type selection stored in Streamlit session state
- Extraction results cached for download/review
- Schema definitions loaded at application startup

### Extensibility
- New document types added via configuration updates
- Field types extensible through type enumeration
- Validation rules support custom implementations
- Schema versioning enables backward compatibility