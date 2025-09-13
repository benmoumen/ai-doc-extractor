# Schema Management Module Documentation

## Overview

The Schema Management module provides a comprehensive system for creating, managing, and validating document schemas within the AI Document Data Extractor application. This module extends the core document extraction capabilities with structured schema definitions, field validation, and UI management components.

## Table of Contents

1. [Core Models](#core-models)
2. [Services](#services)
3. [UI Components](#ui-components)
4. [Storage System](#storage-system)
5. [Validation System](#validation-system)
6. [Import/Export](#importexport)
7. [Error Handling](#error-handling)
8. [Performance Considerations](#performance-considerations)
9. [API Reference](#api-reference)
10. [Usage Examples](#usage-examples)

## Core Models

### Schema Class

The `Schema` class represents a document schema with fields, validation rules, and metadata.

#### Class Definition

```python
class Schema:
    def __init__(self, schema_id: str, name: str, description: str = "", version: str = "1.0.0"):
        self.schema_id = schema_id
        self.name = name
        self.description = description
        self.version = version
        self.fields = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata = {}
```

#### Key Methods

- **`add_field(field: Field) -> None`**: Add a field to the schema
- **`remove_field(field_id: str) -> bool`**: Remove a field by ID
- **`get_field(field_id: str) -> Optional[Field]`**: Retrieve a field by ID
- **`reorder_fields(field_ids: List[str]) -> None`**: Reorder fields
- **`validate() -> ValidationResult`**: Validate the schema structure
- **`to_dict() -> dict`**: Serialize to dictionary
- **`from_dict(cls, data: dict) -> Schema`**: Deserialize from dictionary

#### Properties

- **`field_count: int`**: Number of fields in schema
- **`required_field_count: int`**: Number of required fields
- **`field_types: Dict[str, int]`**: Count of fields by type

### Field Class

The `Field` class represents individual schema fields with validation rules and UI properties.

#### Class Definition

```python
class Field:
    def __init__(self, field_id: str, name: str, field_type: str, 
                 required: bool = False, description: str = ""):
        self.field_id = field_id
        self.name = name
        self.field_type = field_type
        self.required = required
        self.description = description
        self.validation_rules = []
        self.options = []
        self.placeholder = ""
        self.help_text = ""
        self.default_value = None
```

#### Supported Field Types

- **`string`**: Text input with optional regex validation
- **`number`**: Numeric input with min/max constraints
- **`email`**: Email validation with format checking
- **`phone`**: Phone number with format validation
- **`date`**: Date picker with range constraints
- **`select`**: Single selection dropdown
- **`multiselect`**: Multiple selection dropdown
- **`boolean`**: Checkbox input
- **`url`**: URL validation with format checking

#### Key Methods

- **`add_validation_rule(rule: dict) -> None`**: Add validation rule
- **`remove_validation_rule(rule_id: str) -> bool`**: Remove validation rule
- **`validate_value(value: any) -> ValidationResult`**: Validate field value
- **`to_dict() -> dict`**: Serialize to dictionary
- **`from_dict(cls, data: dict) -> Field`**: Deserialize from dictionary

## Services

### StorageService Class

Handles persistence and retrieval of schemas from the storage backend.

#### Key Methods

```python
class StorageService:
    def save_schema(self, schema: Schema) -> bool
    def load_schema(self, schema_id: str) -> Optional[Schema]
    def list_schemas(self) -> List[Dict[str, str]]
    def delete_schema(self, schema_id: str) -> bool
    def schema_exists(self, schema_id: str) -> bool
    def get_schema_metadata(self, schema_id: str) -> Optional[Dict]
    def backup_schemas(self, backup_path: str) -> bool
    def restore_schemas(self, backup_path: str) -> bool
```

#### Storage Backends

- **File-based**: JSON files in `schemas/` directory
- **Database**: SQLite integration (optional)
- **Memory**: In-memory storage for testing

### ValidationService Class

Provides comprehensive validation for schemas and field values.

#### Key Methods

```python
class ValidationService:
    def validate_schema(self, schema: Schema) -> ValidationResult
    def validate_field(self, field: Field, value: any) -> ValidationResult
    def validate_cross_field(self, schema: Schema, data: dict) -> ValidationResult
    def validate_schema_integrity(self, schema: Schema) -> ValidationResult
```

#### Validation Types

- **Field-level**: Individual field validation
- **Schema-level**: Overall schema structure validation
- **Cross-field**: Dependencies between fields
- **Data integrity**: Consistency checks

## UI Components

### SchemaManagementInterface

Main UI component for schema management within Streamlit.

```python
class SchemaManagementInterface:
    def render(self) -> None
    def render_schema_list(self) -> None
    def render_schema_editor(self, schema: Schema) -> None
    def render_field_editor(self, field: Field) -> None
    def render_preview(self, schema: Schema) -> None
```

### FieldEditor

Specialized component for editing individual fields.

```python
class FieldEditor:
    def render_field_properties(self, field: Field) -> None
    def render_validation_rules(self, field: Field) -> None
    def render_options_manager(self, field: Field) -> None
    def render_field_preview(self, field: Field) -> None
```

### SchemaPreview

Component for previewing schemas in different formats.

```python
class SchemaPreview:
    def render_form_preview(self, schema: Schema) -> None
    def render_json_preview(self, schema: Schema) -> None
    def render_documentation_preview(self, schema: Schema) -> None
    def render_extraction_prompt_preview(self, schema: Schema) -> None
```

## Storage System

### File Structure

```
schemas/
├── metadata.json           # Schema registry
├── national_id.json       # Schema definition
├── passport.json          # Schema definition
└── backups/
    └── backup_20250913.zip
```

### Schema File Format

```json
{
  "schema_id": "national_id",
  "name": "National ID Card",
  "description": "Schema for national identification cards",
  "version": "1.0.0",
  "created_at": "2025-09-13T10:30:00Z",
  "updated_at": "2025-09-13T10:30:00Z",
  "fields": {
    "id_number": {
      "field_id": "id_number",
      "name": "ID Number",
      "field_type": "string",
      "required": true,
      "validation_rules": [
        {
          "type": "regex",
          "pattern": "^[0-9]{8}$",
          "message": "ID must be 8 digits"
        }
      ]
    }
  }
}
```

### Backup System

- **Automatic**: Daily backups of all schemas
- **Manual**: On-demand backup creation
- **Versioned**: Multiple backup versions
- **Compressed**: ZIP format for efficiency

## Validation System

### ValidationResult Class

```python
class ValidationResult:
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.field_results = {}
```

### Validation Rules

#### String Validation
- **Regex patterns**: Custom format validation
- **Length constraints**: Min/max character limits
- **Character sets**: Allowed character validation

#### Numeric Validation
- **Range constraints**: Min/max value limits
- **Precision**: Decimal place restrictions
- **Format**: Integer vs decimal validation

#### Email Validation
- **Format checking**: RFC-compliant email validation
- **Domain validation**: Whitelist/blacklist domains
- **Length limits**: Email address length constraints

#### Phone Validation
- **International formats**: E.164 format support
- **Regional formats**: Country-specific patterns
- **Extension support**: Phone extension handling

#### Date Validation
- **Date ranges**: Min/max date constraints
- **Format validation**: ISO date format checking
- **Business rules**: Working days, holidays

### Custom Validation Rules

```python
# Example custom validation rule
{
    "type": "custom",
    "function": "validate_tax_id",
    "parameters": {
        "country": "US",
        "format": "SSN"
    },
    "message": "Invalid US Social Security Number format"
}
```

## Import/Export

### Supported Formats

#### JSON Export
```python
def export_schema_json(schema: Schema) -> str:
    return json.dumps(schema.to_dict(), indent=2)
```

#### CSV Export
```python
def export_schema_csv(schemas: List[Schema]) -> str:
    # Exports schema metadata and field summaries
```

#### YAML Export
```python
def export_schema_yaml(schema: Schema) -> str:
    return yaml.dump(schema.to_dict(), default_flow_style=False)
```

### Import Validation

- **Format validation**: Ensures proper JSON/YAML structure
- **Schema validation**: Validates against schema definition
- **Conflict resolution**: Handles duplicate schema IDs
- **Data integrity**: Ensures field relationships are maintained

### Batch Operations

```python
class ImportExportManager:
    def export_multiple_schemas(self, schema_ids: List[str], format: str) -> str
    def import_schemas_from_file(self, file_path: str) -> ImportResult
    def create_schema_package(self, schema_ids: List[str]) -> bytes
    def extract_schema_package(self, package_data: bytes) -> ImportResult
```

## Error Handling

### Exception Hierarchy

```python
class SchemaError(Exception):
    """Base exception for schema-related errors"""

class ValidationError(SchemaError):
    """Raised when validation fails"""

class StorageError(SchemaError):
    """Raised when storage operations fail"""

class ImportExportError(SchemaError):
    """Raised during import/export operations"""
```

### Error Recovery Strategies

- **Graceful degradation**: Fallback to default schemas
- **User notification**: Clear error messages
- **Automatic retry**: For transient failures
- **Data preservation**: Prevent data loss during errors

### Error Context Management

```python
class ErrorHandler:
    def handle_validation_error(self, error: ValidationError) -> None
    def handle_storage_error(self, error: StorageError) -> None
    def create_error_report(self, error: Exception) -> Dict
    def log_error(self, error: Exception, context: Dict) -> None
```

## Performance Considerations

### Optimization Strategies

- **Lazy loading**: Load schemas on demand
- **Caching**: In-memory caching of frequently used schemas
- **Indexing**: Fast field lookup and search
- **Compression**: Efficient storage of large schemas

### Performance Metrics

- **Response times**: Target <500ms for UI operations
- **Memory usage**: Monitor memory consumption
- **Storage efficiency**: Optimize file sizes
- **Concurrent access**: Handle multiple user sessions

### Caching System

```python
class SchemaCache:
    def get_schema(self, schema_id: str) -> Optional[Schema]
    def cache_schema(self, schema: Schema) -> None
    def invalidate_cache(self, schema_id: str) -> None
    def clear_cache(self) -> None
    def get_cache_stats(self) -> Dict
```

## API Reference

### Core Functions

```python
# Schema Management
create_schema(name: str, description: str = "") -> Schema
load_schema(schema_id: str) -> Optional[Schema]
save_schema(schema: Schema) -> bool
delete_schema(schema_id: str) -> bool
list_schemas() -> List[Dict[str, str]]

# Field Management
create_field(name: str, field_type: str, required: bool = False) -> Field
add_field_to_schema(schema: Schema, field: Field) -> None
remove_field_from_schema(schema: Schema, field_id: str) -> bool
update_field_properties(field: Field, properties: Dict) -> None

# Validation
validate_schema(schema: Schema) -> ValidationResult
validate_field_value(field: Field, value: any) -> ValidationResult
validate_document_data(schema: Schema, data: Dict) -> ValidationResult

# Import/Export
export_schema(schema: Schema, format: str = "json") -> str
import_schema(data: str, format: str = "json") -> Schema
backup_schemas(backup_path: str) -> bool
restore_schemas(backup_path: str) -> bool
```

### Configuration Options

```python
# Schema Management Configuration
SCHEMA_CONFIG = {
    "storage_backend": "file",  # file, database, memory
    "cache_enabled": True,
    "cache_size": 100,
    "auto_backup": True,
    "backup_interval": "daily",
    "validation_mode": "strict",  # strict, permissive
    "max_fields_per_schema": 100,
    "max_schema_size": "10MB"
}
```

## Usage Examples

### Creating a New Schema

```python
# Create a new schema
schema = create_schema("driver_license", "Driver License Schema")

# Add fields
id_field = create_field("license_number", "string", required=True)
id_field.add_validation_rule({
    "type": "regex",
    "pattern": "^[A-Z]{1,2}[0-9]{6,8}$",
    "message": "Invalid license number format"
})

name_field = create_field("full_name", "string", required=True)
name_field.add_validation_rule({
    "type": "length",
    "min": 2,
    "max": 100,
    "message": "Name must be between 2 and 100 characters"
})

expiry_field = create_field("expiry_date", "date", required=True)
expiry_field.add_validation_rule({
    "type": "date_range",
    "min": "today",
    "max": "today+10years",
    "message": "Expiry date must be in the future"
})

# Add fields to schema
add_field_to_schema(schema, id_field)
add_field_to_schema(schema, name_field)
add_field_to_schema(schema, expiry_field)

# Validate and save
result = validate_schema(schema)
if result.is_valid:
    save_schema(schema)
else:
    print("Schema validation errors:", result.errors)
```

### Integrating with Document Extraction

```python
def extract_with_schema(document_path: str, schema_id: str) -> Dict:
    # Load schema
    schema = load_schema(schema_id)
    if not schema:
        raise ValueError(f"Schema {schema_id} not found")
    
    # Generate schema-aware prompt
    prompt = generate_extraction_prompt(schema)
    
    # Process document
    extracted_data = process_document(document_path, prompt)
    
    # Validate extracted data
    validation_result = validate_document_data(schema, extracted_data)
    
    return {
        "data": extracted_data,
        "validation": validation_result,
        "schema": schema.to_dict()
    }
```

### Custom Validation Rules

```python
def create_custom_field_with_validation():
    # Create field with custom validation
    ssn_field = create_field("ssn", "string", required=True)
    
    # Add multiple validation rules
    ssn_field.add_validation_rule({
        "type": "regex",
        "pattern": "^[0-9]{3}-[0-9]{2}-[0-9]{4}$",
        "message": "SSN must be in format XXX-XX-XXXX"
    })
    
    ssn_field.add_validation_rule({
        "type": "custom",
        "function": "validate_ssn_checksum",
        "message": "Invalid SSN checksum"
    })
    
    return ssn_field
```

### Batch Schema Operations

```python
def migrate_schemas_to_new_version():
    # Load all schemas
    schema_list = list_schemas()
    
    for schema_info in schema_list:
        schema = load_schema(schema_info["schema_id"])
        
        # Update schema version
        if schema.version == "1.0.0":
            # Apply migration logic
            schema.version = "2.0.0"
            schema.updated_at = datetime.now()
            
            # Add new required field
            if not schema.get_field("document_source"):
                source_field = create_field("document_source", "select", required=True)
                source_field.options = ["scan", "photo", "digital"]
                add_field_to_schema(schema, source_field)
            
            # Save updated schema
            save_schema(schema)
            print(f"Migrated schema: {schema.name}")
```

## Integration Points

### Streamlit Integration

The schema management system integrates seamlessly with the existing Streamlit application:

- **Session State**: Manages schema selection and editing state
- **UI Components**: Renders schema management interface in sidebar
- **Document Processing**: Enhances extraction with schema validation
- **Results Display**: Shows validation results alongside extracted data

### LiteLLM Integration

Schema-aware prompts are generated for the LiteLLM API:

- **Dynamic Prompts**: Generated based on schema fields
- **Validation Instructions**: Embedded in extraction prompts
- **Response Parsing**: Enhanced JSON parsing with schema validation
- **Error Handling**: Improved error reporting with field-level context

This comprehensive documentation provides developers with all necessary information to understand, use, and extend the Schema Management module within the AI Document Data Extractor application.