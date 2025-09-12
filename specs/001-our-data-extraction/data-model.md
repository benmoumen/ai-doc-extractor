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

## Schema Management UI Entities

### FieldTemplate
Reusable field configuration templates for common field types.

**Fields**:
- `id`: Unique template identifier (string) - e.g., "personal_name", "government_id"
- `name`: Display name for the template (string)
- `description`: Template description (string)
- `field_config`: Pre-configured Field object (dict)
- `category`: Template category (string) - e.g., "personal", "contact", "identification"
- `usage_count`: How often template is used (int, optional)

**Example**:
```python
{
    "id": "personal_name",
    "name": "Personal Name Field",
    "description": "Standard configuration for person's full name",
    "field_config": {
        "type": "string",
        "required": True,
        "validation_rules": [
            {"type": "required", "message": "Name is required"},
            {"type": "length", "min": 2, "max": 100, "message": "Name must be 2-100 characters"}
        ]
    },
    "category": "personal",
    "usage_count": 15
}
```

### ValidationTemplate
Common validation rule patterns for reuse across fields.

**Fields**:
- `id`: Unique template identifier (string)
- `name`: Display name (string)
- `description`: Template description (string)
- `validation_rules`: Array of pre-configured ValidationRule objects
- `applicable_types`: Field types this template applies to (array)
- `category`: Template category (string)

**Example**:
```python
{
    "id": "government_id_format",
    "name": "Government ID Format",
    "description": "Standard government ID validation (2 letters + 9 numbers)",
    "validation_rules": [
        {"type": "pattern", "value": "^[A-Z]{2}[0-9]{9}$", "message": "Must be 2 letters followed by 9 numbers"},
        {"type": "length", "min": 11, "max": 11, "message": "Must be exactly 11 characters"}
    ],
    "applicable_types": ["string"],
    "category": "identification"
}
```

### SchemaVersion
Version control for schema changes with audit trail.

**Fields**:
- `schema_id`: Reference to parent schema (string)
- `version`: Version identifier (string) - e.g., "v1.0", "v1.1", "v2.0"
- `changes`: Description of changes made (string)
- `created_date`: Version creation timestamp (datetime)
- `created_by`: User/system that created version (string)
- `is_active`: Whether this version is currently active (boolean)
- `migration_notes`: Notes for upgrading from previous version (string, optional)
- `schema_data`: Complete schema snapshot (dict)

**Example**:
```python
{
    "schema_id": "national_id",
    "version": "v1.1",
    "changes": "Added optional 'middle_name' field, updated ID number validation pattern",
    "created_date": "2025-09-12T15:30:00Z",
    "created_by": "admin_user",
    "is_active": True,
    "migration_notes": "Existing extractions will continue to work; new field is optional",
    "schema_data": {...}  # Complete schema at this version
}
```

### SchemaImportResult
Results and validation feedback from schema import operations.

**Fields**:
- `import_id`: Unique import operation identifier (string)
- `status`: Import status (enum) - "success", "partial", "failed"
- `imported_schemas`: List of successfully imported schema IDs (array)
- `failed_schemas`: List of schemas that failed import (array)
- `warnings`: Non-fatal issues encountered (array of strings)
- `errors`: Fatal errors that prevented import (array of strings)
- `import_timestamp`: When import was performed (datetime)
- `source_file`: Original import file name (string)
- `validation_details`: Detailed validation results per schema (dict)

**Example**:
```python
{
    "import_id": "import_20250912_153045",
    "status": "partial",
    "imported_schemas": ["custom_national_id", "custom_passport"],
    "failed_schemas": ["invalid_business_license"],
    "warnings": ["Field 'middle_name' in custom_national_id has no validation rules"],
    "errors": ["Schema 'invalid_business_license' missing required 'fields' property"],
    "import_timestamp": "2025-09-12T15:30:45Z",
    "source_file": "custom_schemas.json",
    "validation_details": {
        "custom_national_id": {"valid": True, "field_count": 5},
        "invalid_business_license": {"valid": False, "missing_fields": ["fields"]}
    }
}
```

### SchemaBuilder (UI State)
Transient state object for the schema building interface.

**Fields**:
- `current_schema`: Working schema being edited (Schema object)
- `active_tab`: Currently selected UI tab (string)
- `selected_field`: Currently selected field for editing (string, optional)
- `unsaved_changes`: Whether schema has unsaved modifications (boolean)
- `validation_errors`: Current form validation errors (array)
- `preview_mode`: Whether preview panel is active (boolean)
- `field_templates`: Available field templates (array of FieldTemplate)
- `validation_templates`: Available validation templates (array of ValidationTemplate)

## Extended Entity Relationships

```
DocumentType (1) --> (1) Schema
Schema (1) --> (many) Field
Schema (1) --> (many) SchemaVersion [version history]
Field (1) --> (many) ValidationRule
Field (many) --> (many) FieldTemplate [via templates]
ValidationRule (many) --> (many) ValidationTemplate [via templates]
SchemaImportResult (1) --> (many) Schema [import operations]
SchemaBuilder (1) --> (1) Schema [current editing session]
```

## Implementation Notes

### Storage Strategy
Based on research findings, the system will use a hybrid approach:

```python
# Static schemas remain in config.py (backward compatibility)
DOCUMENT_SCHEMAS = {...}

# Dynamic schemas stored in data/ directory
data/
├── schemas/              # User-created schemas (JSON files)
│   ├── custom_national_id_v1.json
│   └── custom_passport_v1.json
├── templates/           # Field and validation templates
│   ├── field_types.json
│   └── validation_presets.json
└── schema_metadata.db   # SQLite: versions, timestamps, usage stats
```

### Schema Loading Priority
1. Check for user-created schemas in `data/schemas/`
2. Fall back to static schemas in `config.py`
3. Merge templates from `data/templates/`

### State Management
- Current document type selection stored in Streamlit session state
- Schema builder state maintained during editing session
- Extraction results cached for download/review
- Schema definitions loaded dynamically (cached for performance)

### Dynamic Schema Management
- Schema CRUD operations through UI interface
- Real-time validation during schema building
- Version control with rollback capabilities
- Import/export functionality for schema sharing
- Template system for common field configurations

### UI Component Architecture
- Multi-tab schema builder interface
- Drag-drop field reordering (via streamlit-elements)
- Real-time preview with sample data
- Form validation with immediate feedback
- Template selection and customization

### Extensibility
- Plugin architecture for custom field types
- Template system for reusable configurations
- Custom validation rule definitions
- Schema versioning and migration support
- Import/export for schema portability