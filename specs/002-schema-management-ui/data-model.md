# Data Model: Schema Management UI Extension

## Core Entities

### Schema Entity

**Purpose**: Represents a complete document type schema with metadata and fields

**Storage**: Hybrid approach - JSON files for content, SQLite for metadata

```python
class Schema:
    """
    Complete document schema definition
    """
    id: str                    # Unique identifier (e.g., "national_id")
    name: str                  # Display name (e.g., "National ID Card")
    description: str           # Schema description
    category: str              # Category (Government, Business, Personal, Custom)
    version: str               # Semantic version (e.g., "v1.2.0")
    is_active: bool           # Whether schema is available for extraction
    
    # Content (stored in JSON)
    fields: Dict[str, Field]   # Field definitions keyed by field ID
    validation_rules: List[CrossFieldValidation]  # Cross-field validations
    
    # Metadata (stored in SQLite)
    created_date: datetime
    updated_date: datetime
    created_by: str           # User identifier
    usage_count: int          # Number of times used for extraction
    
    # Versioning
    migration_notes: str      # Changes in this version
    backward_compatible: bool # Whether compatible with previous version
```

**JSON File Structure** (`/data/schemas/{schema_id}_v{version}.json`):
```json
{
  "id": "national_id",
  "name": "National ID Card",
  "description": "Government-issued national identification document",
  "category": "Government",
  "version": "v1.2.0",
  "is_active": true,
  "fields": {
    "full_name": {
      "name": "full_name",
      "display_name": "Full Name",
      "type": "text",
      "required": true,
      "description": "Complete legal name as shown on document",
      "examples": ["John Smith", "María González"],
      "validation_rules": [
        {
          "type": "required",
          "message": "Full name is required"
        },
        {
          "type": "length",
          "min": 2,
          "max": 100,
          "message": "Name must be between 2 and 100 characters"
        }
      ]
    }
  },
  "validation_rules": [
    {
      "type": "date_range",
      "fields": ["birth_date", "issue_date"],
      "rule": "birth_date < issue_date",
      "message": "Issue date must be after birth date"
    }
  ],
  "created_date": "2025-09-12T10:30:00Z",
  "updated_date": "2025-09-12T15:45:00Z",
  "migration_notes": "Added optional email field",
  "backward_compatible": true
}
```

**SQLite Metadata Table**:
```sql
CREATE TABLE schema_metadata (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    version TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    usage_count INTEGER DEFAULT 0
);
```

### Field Entity

**Purpose**: Individual field definition within a schema

```python
class Field:
    """
    Individual field configuration
    """
    name: str                     # Field identifier (snake_case)
    display_name: str            # Human-readable name
    type: FieldType              # Field data type
    required: bool               # Whether field is mandatory
    description: str             # Field purpose and usage
    examples: List[str]          # Example values for AI guidance
    validation_rules: List[ValidationRule]  # Field-specific validations
    
    # UI Configuration
    placeholder: str             # Input placeholder text
    help_text: str              # Contextual help for users
    
    # Dependencies
    depends_on: Optional[str]    # Field that controls this field's visibility
    condition: Optional[str]     # Condition for dependency (e.g., "==", "!=")
    condition_value: Optional[Any]  # Value for dependency condition
```

**Field Types** (`FieldType` enum):
```python
class FieldType(Enum):
    TEXT = "text"               # General text input
    NUMBER = "number"           # Numeric values (int/float)
    DATE = "date"              # Date values with picker
    EMAIL = "email"            # Email address with validation
    PHONE = "phone"            # Phone number with formatting
    BOOLEAN = "boolean"        # True/false checkbox
    SELECT = "select"          # Dropdown with predefined options
    CURRENCY = "currency"      # Monetary values with formatting
    URL = "url"               # Web URLs with validation
    CUSTOM = "custom"         # Custom validation pattern
```

### ValidationRule Entity

**Purpose**: Individual validation rule for fields

```python
class ValidationRule:
    """
    Field validation rule definition
    """
    type: ValidationType         # Type of validation
    message: str                # Error message for validation failure
    
    # Type-specific parameters
    pattern: Optional[str]       # Regex pattern (for pattern validation)
    min_length: Optional[int]    # Minimum length (for length validation)
    max_length: Optional[int]    # Maximum length (for length validation)
    min_value: Optional[float]   # Minimum value (for range validation)
    max_value: Optional[float]   # Maximum value (for range validation)
    format: Optional[str]        # Format type (for format validation)
    options: Optional[List[str]] # Valid options (for select validation)
    custom_rule_id: Optional[str]  # Custom rule identifier
```

**Validation Types** (`ValidationType` enum):
```python
class ValidationType(Enum):
    REQUIRED = "required"       # Field must have value
    PATTERN = "pattern"         # Must match regex pattern
    LENGTH = "length"           # Text length constraints
    RANGE = "range"            # Numeric range constraints
    FORMAT = "format"          # Predefined format (email, phone, etc.)
    CUSTOM = "custom"          # Custom validation rule
```

### CrossFieldValidation Entity

**Purpose**: Validation rules that span multiple fields

```python
class CrossFieldValidation:
    """
    Multi-field validation rule
    """
    type: str                   # Validation type (date_range, conditional, etc.)
    fields: List[str]          # Field names involved in validation
    rule: str                  # Validation rule expression
    message: str               # Error message
    condition: Optional[str]   # Additional condition logic
```

### Template Entities

**Purpose**: Reusable components for rapid schema creation

```python
class FieldTemplate:
    """
    Reusable field configuration template
    """
    id: str                    # Template identifier
    name: str                  # Template display name
    category: str              # Template category
    description: str           # Template description
    field_config: Field        # Base field configuration
    usage_count: int          # Popularity tracking

class ValidationTemplate:
    """
    Reusable validation rule template
    """
    id: str                    # Template identifier
    name: str                  # Template display name
    description: str           # Template description
    rule_config: ValidationRule  # Base validation configuration
    applicable_types: List[FieldType]  # Field types this applies to
```

### Version Control Entities

**Purpose**: Track schema changes and support rollback

```python
class SchemaVersion:
    """
    Schema version tracking
    """
    schema_id: str             # Parent schema identifier
    version: str               # Version string
    changes: str               # JSON description of changes
    created_date: datetime     # Version creation timestamp
    created_by: str           # User who created version
    migration_notes: str       # Human-readable change description
    
class SchemaChange:
    """
    Individual change record
    """
    change_type: str          # "field_added", "field_removed", "field_modified"
    field_name: str           # Affected field name
    old_value: Optional[Any]  # Previous value (for modifications)
    new_value: Optional[Any]  # New value (for additions/modifications)
    timestamp: datetime       # When change was made
```

## Storage Architecture

### Hybrid Storage Strategy

**JSON Files** (`/data/schemas/`):
- Primary storage for schema content
- Human-readable and version control friendly
- Easy backup and restore
- File naming: `{schema_id}_v{version}.json`

**SQLite Database** (`/data/schema_metadata.db`):
- Metadata for fast queries and indexing
- Version tracking and change history
- Usage statistics and performance metrics
- Template storage and management

### Database Schema

```sql
-- Schema metadata
CREATE TABLE schema_metadata (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    version TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    usage_count INTEGER DEFAULT 0
);

-- Version tracking
CREATE TABLE schema_versions (
    schema_id TEXT,
    version TEXT,
    changes TEXT,  -- JSON blob
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    migration_notes TEXT,
    FOREIGN KEY (schema_id) REFERENCES schema_metadata (id),
    PRIMARY KEY (schema_id, version)
);

-- Field templates
CREATE TABLE field_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    field_config TEXT,  -- JSON blob
    usage_count INTEGER DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Validation templates  
CREATE TABLE validation_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    rule_config TEXT,  -- JSON blob
    applicable_types TEXT,  -- JSON array
    usage_count INTEGER DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usage tracking
CREATE TABLE extraction_usage (
    schema_id TEXT,
    used_date DATE,
    usage_count INTEGER DEFAULT 1,
    FOREIGN KEY (schema_id) REFERENCES schema_metadata (id),
    PRIMARY KEY (schema_id, used_date)
);
```

## State Transitions

### Schema Lifecycle

```
[Draft] → [Validated] → [Active] → [Deprecated] → [Archived]
   ↑          ↓            ↓           ↓
   ←─────── [Editing] ←────┘           ↓
                                   [Deleted]
```

**State Descriptions**:
- **Draft**: New schema being created, not yet validated
- **Validated**: Schema passes validation but not yet active
- **Active**: Schema available for document extraction
- **Editing**: Temporary state during modifications
- **Deprecated**: Schema marked for replacement but still functional
- **Archived**: Schema preserved for historical reference
- **Deleted**: Schema marked for removal (soft delete)

### Field State Management

```
[New] → [Configured] → [Validated] → [Active]
  ↑         ↓              ↓
  ←─── [Editing] ←─────────┘
```

## Data Validation Rules

### Schema Validation

1. **Uniqueness**: Schema IDs must be unique across all versions
2. **Naming**: Schema names must be unique within category
3. **Fields**: At least one field required per schema
4. **Version**: Must follow semantic versioning (MAJOR.MINOR.PATCH)
5. **Backward Compatibility**: Breaking changes require major version increment

### Field Validation

1. **Naming**: Field names must be valid Python identifiers
2. **Types**: Field types must be from allowed FieldType enum
3. **Required**: At least one required field per schema
4. **Dependencies**: Circular dependencies are forbidden
5. **Validation Rules**: Must be appropriate for field type

### Integration Points

**Existing System Integration**:
- Schema data must be compatible with existing `config.py` format
- New schemas automatically available in document type selector
- Validation rules integrated with AI prompt generation
- Performance tracking continues with new schemas

**API Compatibility**:
- Existing extraction API remains unchanged
- New schemas accessible through existing interfaces
- Backward compatibility maintained for all operations

This data model provides a robust foundation for schema management while maintaining compatibility with the existing document extraction system.