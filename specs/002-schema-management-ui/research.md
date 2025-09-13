# Research: Schema Management UI Extension

## Streamlit-Elements for Drag-Drop Schema Builder

**Decision**: Use streamlit-elements with Material-UI components for advanced UI interactions

**Rationale**: 
- streamlit-elements provides React-like components within Streamlit
- Material-UI integration offers professional drag-drop components
- Built-in state management through element callbacks
- Maintains Streamlit's declarative programming model

**Alternatives Considered**:
- Pure Streamlit components: Limited drag-drop capabilities
- Custom HTML/JS injection: Too complex, breaks Streamlit paradigm
- External iframe: Poor integration with existing app

**Implementation Approach**:
```python
from streamlit_elements import elements, mui, html
from streamlit_elements.core.drag import DragProvider

# Drag-drop field list
with elements("schema_builder"):
    with DragProvider():
        mui.List([
            mui.ListItem(field_data, draggable=True) 
            for field_data in schema_fields
        ])
```

## SQLite + JSON Hybrid Storage

**Decision**: SQLite for metadata/indexing, JSON files for schema content

**Rationale**:
- JSON files: Human-readable, version control friendly, easy backup
- SQLite: Fast queries, indexing, transactional metadata operations
- Hybrid approach: Best of both worlds for different access patterns
- Aligns with existing file-based schema storage approach

**Alternatives Considered**:
- Pure JSON: Poor query performance, no transactions
- Pure SQLite: Binary format, harder to version control
- Document database: Additional dependency complexity

**Storage Strategy**:
```python
# JSON: Schema content (human-readable)
# /data/schemas/national_id_v1.json
{
  "id": "national_id",
  "fields": {...},
  "validation_rules": {...}
}

# SQLite: Metadata and indexing
# /data/schema_metadata.db
CREATE TABLE schema_metadata (
    id TEXT PRIMARY KEY,
    version TEXT,
    created_date TIMESTAMP,
    usage_count INTEGER
);
```

## Schema Versioning Patterns

**Decision**: Semantic versioning with parallel storage and migration support

**Rationale**:
- MAJOR.MINOR.PATCH format provides clear change communication
- Parallel file storage allows rollback and comparison
- Migration scripts handle breaking changes gracefully
- Backward compatibility maintained for extraction workflow

**Alternatives Considered**:
- Git-based versioning: Too complex for end users
- Single file with history: Poor performance, complex merging
- No versioning: Risky for production schemas

**Versioning Strategy**:
```python
# File naming: {schema_id}_v{version}.json
national_id_v1.0.0.json  # Initial version
national_id_v1.1.0.json  # Minor update (new field)
national_id_v2.0.0.json  # Major update (breaking change)

# Migration tracking
{
  "migration_notes": "Added optional email field",
  "backward_compatible": true,
  "migration_script": "add_email_field.py"
}
```

## Real-Time Preview Patterns

**Decision**: Debounced updates with optimistic UI rendering

**Rationale**:
- 300ms debounce prevents excessive re-renders during typing
- Optimistic updates provide immediate feedback
- Background validation ensures data integrity
- Efficient for complex schemas with many fields

**Alternatives Considered**:
- Immediate updates: Too many re-renders, poor performance
- Manual refresh: Poor user experience
- Server-side rendering: Unnecessary complexity for this use case

**Preview Implementation**:
```python
import streamlit as st
from time import time

# Debounced update pattern
def debounced_preview_update(schema_data, delay=0.3):
    current_time = time()
    if 'last_update' not in st.session_state:
        st.session_state.last_update = 0
    
    if current_time - st.session_state.last_update > delay:
        # Update preview
        render_schema_preview(schema_data)
        st.session_state.last_update = current_time
```

## UI State Management

**Decision**: Streamlit session state with structured state objects

**Rationale**:
- Leverages built-in Streamlit state management
- Structured approach prevents state corruption
- Easy to debug and reason about
- Integrates naturally with form components

**State Structure**:
```python
# Session state schema
st.session_state.schema_builder = {
    "current_schema": {...},
    "active_tab": "basic",
    "selected_field": None,
    "unsaved_changes": False,
    "validation_errors": []
}
```

## Performance Optimizations

**Decision**: Lazy loading with caching for large schemas

**Rationale**:
- Only load schema content when needed
- Cache frequently accessed templates
- Minimize re-renders through selective updates
- Handle 100+ field schemas efficiently

**Optimization Patterns**:
```python
@st.cache_data
def load_field_templates():
    """Cache field templates for session"""
    return load_templates_from_disk()

@st.cache_data
def validate_schema(schema_json):
    """Cache validation results"""
    return jsonschema.validate(schema_json)
```

## Integration Strategy

**Decision**: Extend existing app.py with navigation tabs

**Rationale**:
- Maintains single application deployment
- Preserves existing user workflows
- Shares session state and configuration
- Minimal architectural changes required

**Integration Approach**:
```python
# app.py navigation
page = st.sidebar.selectbox(
    "Navigate",
    ["📊 Document Extraction", "🏗️ Schema Management"]
)

if page == "🏗️ Schema Management":
    from schema_management import render_schema_management_page
    render_schema_management_page()
else:
    # Existing extraction interface
    render_extraction_interface()
```

## Technology Stack Summary

**Core Dependencies**:
- `streamlit-elements>=0.1.0`: Advanced UI components
- `python-jsonschema>=4.0.0`: Schema validation
- `sqlite3`: Built-in Python, metadata storage

**Development Approach**:
- Test-driven development with pytest
- Modular architecture in schema_management/ package
- Progressive enhancement of existing features
- Backward compatibility maintenance

This research provides the foundation for implementing a robust, user-friendly schema management interface while maintaining the simplicity and reliability of the existing document extraction system.