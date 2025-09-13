# UI Contracts: Schema Management Interface

## Overview
This document defines the interface contracts for the rich UI schema management system. These contracts specify the expected behavior, inputs, outputs, and interactions for each UI component.

## Schema Management Page

### Route/Navigation
- **Access**: New page/tab in Streamlit application
- **URL State**: Maintains current schema ID and active tab in URL parameters
- **Navigation**: Accessible from main sidebar or dedicated "Manage Schemas" button

### Main Interface Contract

```python
def render_schema_management_page():
    """
    Main schema management interface controller
    
    Returns:
        None (renders Streamlit components)
        
    Session State Dependencies:
        - current_schema_id: Currently selected schema (optional)
        - active_tab: Currently selected tab ("basic"|"fields"|"validation"|"preview")
        - unsaved_changes: Boolean indicating unsaved modifications
    """
```

## Tab 1: Basic Schema Information

### Basic Info Form Contract

```python
def render_basic_info_tab(schema: Dict) -> Dict:
    """
    Renders basic schema information form
    
    Args:
        schema: Current schema object (or empty dict for new schema)
        
    Returns:
        Dict with updated schema basic info:
        {
            "id": str,           # Schema identifier (auto-generated if new)
            "name": str,         # Display name
            "description": str,  # Schema description
            "category": str,     # Schema category
            "is_active": bool    # Whether schema is active
        }
        
    UI Components:
        - Text input for schema name (required, max 50 chars)
        - Text area for description (optional, max 200 chars)
        - Select box for category (predefined options + custom)
        - Checkbox for active status
        - Save/Cancel buttons
        
    Validation:
        - Schema name must be unique
        - Schema ID generated from name (sanitized)
        - All fields validated on blur
    """
```

## Tab 2: Field Management

### Field List Component Contract

```python
def render_field_list(fields: List[Dict]) -> List[Dict]:
    """
    Renders drag-droppable field list with reordering
    
    Args:
        fields: List of field objects
        
    Returns:
        List[Dict]: Reordered field list
        
    UI Components:
        - Drag-drop enabled list (via streamlit-elements)
        - Field preview cards showing type, required status
        - Delete field buttons with confirmation
        - Add field button (floating action)
        
    Interactions:
        - Drag to reorder fields
        - Click to select/edit field
        - Delete with confirmation dialog
    """
```

### Field Editor Contract

```python
def render_field_editor(field: Dict, field_templates: List[Dict]) -> Dict:
    """
    Field configuration editor interface
    
    Args:
        field: Current field object (or empty for new field)
        field_templates: Available field templates
        
    Returns:
        Dict: Updated field configuration
        {
            "name": str,              # Field identifier
            "display_name": str,      # Human-readable name
            "type": str,              # Field type (dropdown)
            "required": bool,         # Required status
            "description": str,       # Field description
            "examples": List[str],    # Example values
            "validation_rules": List[Dict]  # Validation rules
        }
        
    UI Components:
        - Field name input (auto-generates ID)
        - Display name input
        - Type selector dropdown
        - Required checkbox
        - Description text area
        - Examples list editor
        - Template selector (quick-fill)
        
    Validation:
        - Field names must be unique within schema
        - Field types must be valid
        - Examples must match field type
    """
```

### Add Field Interface Contract

```python
def render_add_field_interface(field_templates: List[Dict]) -> Dict:
    """
    Interface for adding new fields with templates
    
    Args:
        field_templates: Available field templates by category
        
    Returns:
        Dict: New field configuration or None if cancelled
        
    UI Components:
        - Template category selector
        - Template grid/list with previews
        - Quick field type buttons (common types)
        - "Start from scratch" option
        - Preview panel for selected template
    """
```

## Tab 3: Validation Rules Builder

### Validation Rule Builder Contract

```python
def render_validation_builder(field: Dict, validation_templates: List[Dict]) -> List[Dict]:
    """
    Visual validation rule builder interface
    
    Args:
        field: Field object to build validations for
        validation_templates: Available validation templates
        
    Returns:
        List[Dict]: List of validation rule objects
        
    UI Components:
        - Rule type selector (required, pattern, length, etc.)
        - Dynamic parameter inputs based on rule type
        - Template selector for common patterns
        - Rule preview with examples
        - Add/remove rule buttons
        
    Rule Types Supported:
        - required: No additional parameters
        - pattern: Regex pattern input with tester
        - length: Min/max length inputs
        - range: Min/max value inputs (numbers)
        - format: Format type selector (email, phone, etc.)
        - custom: Custom rule identifier input
    """
```

### Cross-Field Validation Contract

```python
def render_cross_field_validation(schema: Dict) -> List[Dict]:
    """
    Builder for validation rules that span multiple fields
    
    Args:
        schema: Complete schema object with all fields
        
    Returns:
        List[Dict]: Cross-field validation rules
        
    Examples:
        - Date range validation (start_date < end_date)
        - Conditional requirements (if field A then field B required)
        - Format consistency (phone + country code)
    """
```

## Tab 4: Preview & Testing

### Schema Preview Contract

```python
def render_schema_preview(schema: Dict) -> None:
    """
    Real-time schema preview with sample data visualization
    
    Args:
        schema: Complete schema object
        
    UI Components:
        - JSON schema display (formatted, collapsible)
        - Form preview (how fields will appear to users)
        - Sample data table with validation status
        - Prompt preview (AI prompt that will be generated)
        
    Features:
        - Syntax highlighting for JSON
        - Expandable/collapsible sections
        - Copy to clipboard functionality
        - Download schema as JSON
    """
```

### Schema Testing Interface Contract

```python
def render_schema_test_interface(schema: Dict) -> Dict:
    """
    Interface for testing schema with sample documents
    
    Args:
        schema: Schema to test
        
    Returns:
        Dict: Test results with validation feedback
        
    UI Components:
        - Sample document uploader
        - Test extraction button
        - Results display (extracted data + validation)
        - Comparison with expected results
        
    Features:
        - Test with multiple document samples
        - Save test cases for regression testing
        - Performance metrics (extraction time)
    """
```

## Schema Import/Export Interface

### Import Schema Contract

```python
def render_import_interface() -> SchemaImportResult:
    """
    Schema import interface with validation
    
    Returns:
        SchemaImportResult: Import operation results
        
    UI Components:
        - File uploader (JSON files)
        - Import options (overwrite, merge, validate-only)
        - Validation results display
        - Confirmation dialog for conflicts
        
    Import Process:
        1. File upload and parsing
        2. Schema validation
        3. Conflict detection
        4. User confirmation
        5. Import execution
        6. Results summary
    """
```

### Export Schema Contract

```python
def render_export_interface(schema_ids: List[str]) -> None:
    """
    Schema export interface with options
    
    Args:
        schema_ids: List of schema IDs to export
        
    UI Components:
        - Schema selector (multi-select)
        - Export format options (JSON, with/without metadata)
        - Include options (templates, versions, test cases)
        - Download button
        
    Export Formats:
        - JSON schema only
        - JSON with metadata and versions
        - Complete export with templates and test cases
    """
```

## Common UI Components

### Field Type Selector Contract

```python
def render_field_type_selector(current_type: str) -> str:
    """
    Field type selection component
    
    Args:
        current_type: Currently selected type
        
    Returns:
        str: Selected field type
        
    Field Types:
        - text: General text input
        - number: Numeric values
        - date: Date values with picker
        - email: Email address with validation
        - phone: Phone number with formatting
        - boolean: True/false checkbox
        - select: Dropdown with predefined options
        - custom: Custom field type
    """
```

### Validation Rule Editor Contract

```python
def render_validation_rule_editor(rule: Dict, field_type: str) -> Dict:
    """
    Individual validation rule editor
    
    Args:
        rule: Current validation rule object
        field_type: Field type for context-specific options
        
    Returns:
        Dict: Updated validation rule
        
    Dynamic UI based on rule type:
        - required: Just message input
        - pattern: Regex input + pattern tester
        - length: Min/max inputs with preview
        - range: Min/max inputs for numbers
        - format: Format selector dropdown
    """
```

## State Management Contracts

### Session State Schema

```python
# Streamlit session state keys for schema management
SCHEMA_MANAGEMENT_STATE = {
    "current_schema_id": Optional[str],      # Currently editing schema
    "active_tab": str,                       # Current tab ("basic"|"fields"|"validation"|"preview")
    "unsaved_changes": bool,                 # Has unsaved modifications
    "selected_field_id": Optional[str],      # Currently selected field
    "field_templates": List[Dict],           # Loaded field templates
    "validation_templates": List[Dict],      # Loaded validation templates
    "schema_builder": Dict,                  # Current editing session state
    "import_result": Optional[Dict],         # Last import operation result
    "preview_mode": bool                     # Whether preview is active
}
```

### Navigation State Contract

```python
def update_navigation_state(schema_id: str, tab: str) -> None:
    """
    Updates URL parameters and session state for navigation
    
    Args:
        schema_id: Schema ID to navigate to
        tab: Tab to activate
        
    Side Effects:
        - Updates session state
        - Updates URL parameters
        - Triggers component re-renders
    """
```

## Error Handling Contracts

### Validation Error Display

```python
def render_validation_errors(errors: List[Dict]) -> None:
    """
    Displays validation errors with appropriate severity styling
    
    Args:
        errors: List of error objects with severity levels
        
    Error Levels:
        - error: Red styling, blocks save operation
        - warning: Orange styling, allows save with confirmation
        - info: Blue styling, informational only
    """
```

### Conflict Resolution Interface

```python
def render_conflict_resolution(conflicts: List[Dict]) -> Dict:
    """
    Interface for resolving schema conflicts during import/save
    
    Args:
        conflicts: List of conflict objects
        
    Returns:
        Dict: Resolution decisions
        
    Conflict Types:
        - name_collision: Schema name already exists
        - field_collision: Field name conflicts
        - validation_mismatch: Incompatible validation rules
    """
```

## Performance Contracts

### Loading States

```python
def render_loading_state(operation: str, progress: Optional[float] = None) -> None:
    """
    Displays loading indicators for long-running operations
    
    Args:
        operation: Description of current operation
        progress: Optional progress percentage (0-100)
        
    Operations:
        - "Loading schema..."
        - "Saving changes..."
        - "Importing schemas..."
        - "Testing extraction..."
    """
```

### Debounced Updates

```python
def debounced_schema_update(schema: Dict, delay_ms: int = 300) -> None:
    """
    Debounced schema updates to prevent excessive re-renders
    
    Args:
        schema: Updated schema object
        delay_ms: Delay before update processing
        
    Used for:
        - Real-time preview updates
        - Auto-save functionality
        - Validation feedback
    """
```

## Integration Contracts

### Existing System Integration

```python
def integrate_with_extraction_workflow(schema_id: str) -> None:
    """
    Integrates new/updated schema with existing extraction workflow
    
    Args:
        schema_id: ID of schema to integrate
        
    Integration Points:
        - Updates document type selector
        - Refreshes schema cache
        - Validates prompt generation
        - Tests extraction pipeline
    """
```

These contracts define the expected behavior and interfaces for the schema management UI system. Each component should implement these contracts to ensure consistent behavior and proper integration with the existing document extraction workflow.