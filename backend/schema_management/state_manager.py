"""
Session State Management for Schema Builder

Centralizes Streamlit session state operations for the schema management interface.
Provides consistent state initialization, updates, and cleanup operations.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import uuid

from .models.schema import Schema
from .models.field import Field
from .models.validation_rule import ValidationRule


class SchemaBuilderState:
    """
    Constants and helper methods for schema builder session state management.
    """
    
    # Session state keys
    CURRENT_SCHEMA_ID = "schema_builder_current_schema_id"
    CURRENT_SCHEMA_DATA = "schema_builder_current_schema_data"
    UNSAVED_CHANGES = "schema_builder_unsaved_changes"
    EDITING_FIELD_ID = "schema_builder_editing_field_id"
    FIELD_EDITOR_DATA = "schema_builder_field_editor_data"
    SELECTED_TAB = "schema_builder_selected_tab"
    PREVIEW_MODE = "schema_builder_preview_mode"
    IMPORT_MODE = "schema_builder_import_mode"
    EXPORT_FORMAT = "schema_builder_export_format"
    VALIDATION_ERRORS = "schema_builder_validation_errors"
    LAST_SAVED = "schema_builder_last_saved"
    AUTO_SAVE_ENABLED = "schema_builder_auto_save_enabled"
    MODIFIED_FIELDS = "schema_builder_modified_fields"
    FIELD_ORDER_CHANGED = "schema_builder_field_order_changed"
    
    # Default values
    DEFAULT_SCHEMA_DATA = {
        "id": "",
        "name": "",
        "description": "",
        "version": "1.0.0",
        "category": "General",
        "fields": [],
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "created_by": "user",
            "tags": []
        }
    }
    
    DEFAULT_FIELD_DATA = {
        "id": "",
        "name": "",
        "display_name": "",
        "type": "string",
        "required": False,
        "description": "",
        "validation_rules": [],
        "metadata": {}
    }


def initialize_schema_builder_state() -> None:
    """
    Initialize all schema builder session state variables with default values.
    Should be called at the start of the schema management page.
    """
    # Current schema being edited
    if SchemaBuilderState.CURRENT_SCHEMA_ID not in st.session_state:
        st.session_state[SchemaBuilderState.CURRENT_SCHEMA_ID] = None
    
    if SchemaBuilderState.CURRENT_SCHEMA_DATA not in st.session_state:
        st.session_state[SchemaBuilderState.CURRENT_SCHEMA_DATA] = SchemaBuilderState.DEFAULT_SCHEMA_DATA.copy()
    
    # Change tracking
    if SchemaBuilderState.UNSAVED_CHANGES not in st.session_state:
        st.session_state[SchemaBuilderState.UNSAVED_CHANGES] = False
    
    if SchemaBuilderState.MODIFIED_FIELDS not in st.session_state:
        st.session_state[SchemaBuilderState.MODIFIED_FIELDS] = set()
    
    if SchemaBuilderState.FIELD_ORDER_CHANGED not in st.session_state:
        st.session_state[SchemaBuilderState.FIELD_ORDER_CHANGED] = False
    
    # Field editing state
    if SchemaBuilderState.EDITING_FIELD_ID not in st.session_state:
        st.session_state[SchemaBuilderState.EDITING_FIELD_ID] = None
    
    if SchemaBuilderState.FIELD_EDITOR_DATA not in st.session_state:
        st.session_state[SchemaBuilderState.FIELD_EDITOR_DATA] = SchemaBuilderState.DEFAULT_FIELD_DATA.copy()
    
    # UI state
    if SchemaBuilderState.SELECTED_TAB not in st.session_state:
        st.session_state[SchemaBuilderState.SELECTED_TAB] = 0
    
    if SchemaBuilderState.PREVIEW_MODE not in st.session_state:
        st.session_state[SchemaBuilderState.PREVIEW_MODE] = "form"
    
    if SchemaBuilderState.IMPORT_MODE not in st.session_state:
        st.session_state[SchemaBuilderState.IMPORT_MODE] = "json"
    
    if SchemaBuilderState.EXPORT_FORMAT not in st.session_state:
        st.session_state[SchemaBuilderState.EXPORT_FORMAT] = "json"
    
    # Validation and errors
    if SchemaBuilderState.VALIDATION_ERRORS not in st.session_state:
        st.session_state[SchemaBuilderState.VALIDATION_ERRORS] = {}
    
    # Save tracking
    if SchemaBuilderState.LAST_SAVED not in st.session_state:
        st.session_state[SchemaBuilderState.LAST_SAVED] = None
    
    if SchemaBuilderState.AUTO_SAVE_ENABLED not in st.session_state:
        st.session_state[SchemaBuilderState.AUTO_SAVE_ENABLED] = False


def get_current_schema() -> Optional[Dict[str, Any]]:
    """
    Get the current schema data from session state.
    
    Returns:
        Current schema data or None if no schema is loaded
    """
    return st.session_state.get(SchemaBuilderState.CURRENT_SCHEMA_DATA)


def get_current_schema_id() -> Optional[str]:
    """
    Get the current schema ID from session state.
    
    Returns:
        Current schema ID or None if no schema is loaded
    """
    return st.session_state.get(SchemaBuilderState.CURRENT_SCHEMA_ID)


def update_current_schema(schema_data: Dict[str, Any], schema_id: Optional[str] = None) -> None:
    """
    Update the current schema data in session state.
    
    Args:
        schema_data: Updated schema data
        schema_id: Optional schema ID (if different from current)
    """
    if isinstance(schema_data, dict):
        st.session_state[SchemaBuilderState.CURRENT_SCHEMA_DATA] = schema_data.copy()
    else:
        st.session_state[SchemaBuilderState.CURRENT_SCHEMA_DATA] = schema_data
    
    if schema_id is not None:
        st.session_state[SchemaBuilderState.CURRENT_SCHEMA_ID] = schema_id
    
    mark_unsaved_changes()


def update_current_schema_field(field_key: str, field_value: Any) -> None:
    """
    Update a single field in the current schema data.
    
    Args:
        field_key: The field key to update
        field_value: The new value for the field
    """
    current_schema = get_current_schema()
    if current_schema is None:
        current_schema = {}
    
    current_schema[field_key] = field_value
    st.session_state[SchemaBuilderState.CURRENT_SCHEMA_DATA] = current_schema
    mark_unsaved_changes()


def load_schema_into_state(schema: Schema) -> None:
    """
    Load a schema object into session state for editing.
    
    Args:
        schema: Schema object to load
    """
    schema_data = {
        "id": schema.id,
        "name": schema.name,
        "description": schema.description,
        "version": schema.version,
        "category": schema.category,
        "fields": [field.to_dict() for field in schema.fields],
        "metadata": schema.metadata
    }
    
    st.session_state[SchemaBuilderState.CURRENT_SCHEMA_ID] = schema.id
    st.session_state[SchemaBuilderState.CURRENT_SCHEMA_DATA] = schema_data
    st.session_state[SchemaBuilderState.UNSAVED_CHANGES] = False
    st.session_state[SchemaBuilderState.MODIFIED_FIELDS] = set()
    st.session_state[SchemaBuilderState.FIELD_ORDER_CHANGED] = False
    st.session_state[SchemaBuilderState.LAST_SAVED] = datetime.now().isoformat()
    
    # Clear field editor state
    st.session_state[SchemaBuilderState.EDITING_FIELD_ID] = None
    st.session_state[SchemaBuilderState.FIELD_EDITOR_DATA] = SchemaBuilderState.DEFAULT_FIELD_DATA.copy()
    
    # Clear validation errors
    st.session_state[SchemaBuilderState.VALIDATION_ERRORS] = {}


def create_new_schema_in_state(name: str = "", category: str = "General") -> None:
    """
    Initialize state for creating a new schema.
    
    Args:
        name: Initial schema name
        category: Schema category
    """
    new_id = f"schema_{uuid.uuid4().hex[:8]}"
    
    schema_data = SchemaBuilderState.DEFAULT_SCHEMA_DATA.copy()
    schema_data.update({
        "id": new_id,
        "name": name,
        "category": category,
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "created_by": "user",
            "tags": []
        }
    })
    
    st.session_state[SchemaBuilderState.CURRENT_SCHEMA_ID] = None  # Not saved yet
    st.session_state[SchemaBuilderState.CURRENT_SCHEMA_DATA] = schema_data
    st.session_state[SchemaBuilderState.UNSAVED_CHANGES] = True
    st.session_state[SchemaBuilderState.MODIFIED_FIELDS] = set()
    st.session_state[SchemaBuilderState.FIELD_ORDER_CHANGED] = False
    st.session_state[SchemaBuilderState.LAST_SAVED] = None
    
    # Clear field editor state
    st.session_state[SchemaBuilderState.EDITING_FIELD_ID] = None
    st.session_state[SchemaBuilderState.FIELD_EDITOR_DATA] = SchemaBuilderState.DEFAULT_FIELD_DATA.copy()
    
    # Clear validation errors
    st.session_state[SchemaBuilderState.VALIDATION_ERRORS] = {}


def mark_unsaved_changes(field_id: Optional[str] = None) -> None:
    """
    Mark that there are unsaved changes in the current schema.
    
    Args:
        field_id: Optional field ID that was modified
    """
    st.session_state[SchemaBuilderState.UNSAVED_CHANGES] = True
    
    if field_id:
        modified_fields: Set[str] = st.session_state.get(SchemaBuilderState.MODIFIED_FIELDS, set())
        modified_fields.add(field_id)
        st.session_state[SchemaBuilderState.MODIFIED_FIELDS] = modified_fields


def mark_field_order_changed() -> None:
    """Mark that field order has been changed."""
    st.session_state[SchemaBuilderState.FIELD_ORDER_CHANGED] = True
    mark_unsaved_changes()


def has_unsaved_changes() -> bool:
    """
    Check if there are unsaved changes in the current schema.
    
    Returns:
        True if there are unsaved changes, False otherwise
    """
    return st.session_state.get(SchemaBuilderState.UNSAVED_CHANGES, False)


def get_modified_fields() -> Set[str]:
    """
    Get the set of field IDs that have been modified.
    
    Returns:
        Set of modified field IDs
    """
    return st.session_state.get(SchemaBuilderState.MODIFIED_FIELDS, set())


def mark_saved() -> None:
    """Mark the current schema as saved (clear unsaved changes)."""
    st.session_state[SchemaBuilderState.UNSAVED_CHANGES] = False
    st.session_state[SchemaBuilderState.MODIFIED_FIELDS] = set()
    st.session_state[SchemaBuilderState.FIELD_ORDER_CHANGED] = False
    st.session_state[SchemaBuilderState.LAST_SAVED] = datetime.now().isoformat()


def clear_schema_builder_state() -> None:
    """Clear all schema builder session state."""
    keys_to_clear = [
        SchemaBuilderState.CURRENT_SCHEMA_ID,
        SchemaBuilderState.CURRENT_SCHEMA_DATA,
        SchemaBuilderState.UNSAVED_CHANGES,
        SchemaBuilderState.EDITING_FIELD_ID,
        SchemaBuilderState.FIELD_EDITOR_DATA,
        SchemaBuilderState.SELECTED_TAB,
        SchemaBuilderState.PREVIEW_MODE,
        SchemaBuilderState.IMPORT_MODE,
        SchemaBuilderState.EXPORT_FORMAT,
        SchemaBuilderState.VALIDATION_ERRORS,
        SchemaBuilderState.LAST_SAVED,
        SchemaBuilderState.MODIFIED_FIELDS,
        SchemaBuilderState.FIELD_ORDER_CHANGED
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


# Field Editor State Management

def start_editing_field(field_id: str, field_data: Dict[str, Any]) -> None:
    """
    Start editing a field by loading it into the field editor state.
    
    Args:
        field_id: ID of the field to edit
        field_data: Current field data
    """
    st.session_state[SchemaBuilderState.EDITING_FIELD_ID] = field_id
    st.session_state[SchemaBuilderState.FIELD_EDITOR_DATA] = field_data.copy()


def stop_editing_field() -> None:
    """Stop editing the current field and clear editor state."""
    st.session_state[SchemaBuilderState.EDITING_FIELD_ID] = None
    st.session_state[SchemaBuilderState.FIELD_EDITOR_DATA] = SchemaBuilderState.DEFAULT_FIELD_DATA.copy()


def get_editing_field_id() -> Optional[str]:
    """
    Get the ID of the field currently being edited.
    
    Returns:
        Field ID being edited or None
    """
    return st.session_state.get(SchemaBuilderState.EDITING_FIELD_ID)


def get_field_editor_data() -> Dict[str, Any]:
    """
    Get the current field editor data.
    
    Returns:
        Current field editor data
    """
    return st.session_state.get(SchemaBuilderState.FIELD_EDITOR_DATA, SchemaBuilderState.DEFAULT_FIELD_DATA.copy())


def update_field_editor_data(field_data: Dict[str, Any]) -> None:
    """
    Update the field editor data.
    
    Args:
        field_data: Updated field data
    """
    st.session_state[SchemaBuilderState.FIELD_EDITOR_DATA] = field_data.copy()


# UI State Management

def set_selected_tab(tab_index: int) -> None:
    """
    Set the currently selected tab.
    
    Args:
        tab_index: Index of the selected tab
    """
    st.session_state[SchemaBuilderState.SELECTED_TAB] = tab_index


def get_selected_tab() -> int:
    """
    Get the currently selected tab index.
    
    Returns:
        Selected tab index
    """
    return st.session_state.get(SchemaBuilderState.SELECTED_TAB, 0)


def set_preview_mode(mode: str) -> None:
    """
    Set the preview mode.
    
    Args:
        mode: Preview mode (form, json, table, docs, extraction)
    """
    st.session_state[SchemaBuilderState.PREVIEW_MODE] = mode


def get_preview_mode() -> str:
    """
    Get the current preview mode.
    
    Returns:
        Current preview mode
    """
    return st.session_state.get(SchemaBuilderState.PREVIEW_MODE, "form")


# Validation State Management

def set_validation_errors(errors: Dict[str, List[str]]) -> None:
    """
    Set validation errors for the current schema.
    
    Args:
        errors: Dictionary mapping field names to lists of error messages
    """
    st.session_state[SchemaBuilderState.VALIDATION_ERRORS] = errors.copy()


def get_validation_errors() -> Dict[str, List[str]]:
    """
    Get current validation errors.
    
    Returns:
        Dictionary of validation errors
    """
    return st.session_state.get(SchemaBuilderState.VALIDATION_ERRORS, {})


def add_validation_error(field_name: str, error_message: str) -> None:
    """
    Add a validation error for a specific field.
    
    Args:
        field_name: Name of the field with the error
        error_message: Error message
    """
    errors = get_validation_errors()
    if field_name not in errors:
        errors[field_name] = []
    errors[field_name].append(error_message)
    set_validation_errors(errors)


def clear_validation_errors(field_name: Optional[str] = None) -> None:
    """
    Clear validation errors.
    
    Args:
        field_name: Optional field name to clear errors for (clears all if None)
    """
    if field_name is None:
        st.session_state[SchemaBuilderState.VALIDATION_ERRORS] = {}
    else:
        errors = get_validation_errors()
        if field_name in errors:
            del errors[field_name]
        set_validation_errors(errors)


# Auto-save Management

def enable_auto_save() -> None:
    """Enable auto-save functionality."""
    st.session_state[SchemaBuilderState.AUTO_SAVE_ENABLED] = True


def disable_auto_save() -> None:
    """Disable auto-save functionality."""
    st.session_state[SchemaBuilderState.AUTO_SAVE_ENABLED] = False


def is_auto_save_enabled() -> bool:
    """
    Check if auto-save is enabled.
    
    Returns:
        True if auto-save is enabled, False otherwise
    """
    return st.session_state.get(SchemaBuilderState.AUTO_SAVE_ENABLED, False)


def get_last_saved_time() -> Optional[str]:
    """
    Get the timestamp of the last save operation.
    
    Returns:
        ISO timestamp string or None if never saved
    """
    return st.session_state.get(SchemaBuilderState.LAST_SAVED)


# Utility Functions

def get_schema_summary() -> Dict[str, Any]:
    """
    Get a summary of the current schema state.
    
    Returns:
        Dictionary with schema state summary
    """
    schema_data = get_current_schema()
    if not schema_data:
        return {"loaded": False}
    
    return {
        "loaded": True,
        "schema_id": get_current_schema_id(),
        "name": schema_data.get("name", ""),
        "field_count": len(schema_data.get("fields", [])),
        "has_unsaved_changes": has_unsaved_changes(),
        "modified_fields_count": len(get_modified_fields()),
        "last_saved": get_last_saved_time(),
        "validation_errors_count": sum(len(errors) for errors in get_validation_errors().values())
    }


def reset_to_clean_state() -> None:
    """Reset the schema builder to a clean state (no schema loaded)."""
    clear_schema_builder_state()
    initialize_schema_builder_state()