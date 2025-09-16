"""
Basic info tab component for schema management UI.
Handles schema metadata editing: name, description, category, etc.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
import re

from ..models.schema import Schema, SchemaStatus


def render_basic_info_tab(schema_data: Dict[str, Any] = None, 
                         available_categories: List[str] = None) -> Dict[str, Any]:
    """
    Render basic info tab for schema editing
    
    Args:
        schema_data: Current schema data (None for new schema)
        available_categories: List of available categories
        
    Returns:
        Dictionary with updated schema basic info
    """
    # Default categories if none provided
    if available_categories is None:
        available_categories = ["Custom", "Documents", "Forms", "Financial", "Legal", "Medical"]
    
    # Initialize default values
    defaults = {
        "name": "",
        "description": "",
        "category": "Custom",
        "id": "",
        "version": "v1.0.0",
        "status": SchemaStatus.DRAFT.value,
        "is_active": True
    }
    
    # Use existing data if available
    if schema_data:
        defaults.update({k: v for k, v in schema_data.items() if k in defaults})
    
    st.subheader("📋 Basic Information")
    
    with st.container():
        # Schema Name (required)
        name = st.text_input(
            "Schema Name *",
            value=defaults["name"],
            placeholder="Enter a descriptive name for your schema",
            help="This name will be displayed in the schema list and used for identification",
            key="schema_name"
        )
        
        # Auto-generate ID from name
        if name and not st.session_state.get("manual_id_override", False):
            auto_id = generate_schema_id_from_name(name)
            if "schema_id" not in st.session_state or st.session_state.get("auto_generated_id", True):
                st.session_state.schema_id = auto_id
                st.session_state.auto_generated_id = True
        
        # Schema ID with manual override option
        col1, col2 = st.columns([3, 1])
        
        with col1:
            schema_id = st.text_input(
                "Schema ID *",
                value=st.session_state.get("schema_id", defaults["id"]),
                placeholder="auto-generated from name",
                help="Unique identifier for the schema. Auto-generated from name unless manually overridden.",
                key="schema_id_input"
            )
        
        with col2:
            manual_override = st.checkbox(
                "Manual ID",
                value=st.session_state.get("manual_id_override", False),
                help="Check to manually set the schema ID",
                key="manual_id_override"
            )
            
            if manual_override:
                st.session_state.auto_generated_id = False
        
        # Update session state
        if manual_override or schema_id != st.session_state.get("schema_id", ""):
            st.session_state.schema_id = schema_id
        
        # Description
        description = st.text_area(
            "Description",
            value=defaults["description"],
            placeholder="Describe what this schema is used for and what types of documents it extracts data from",
            help="Provide a clear description to help users understand when to use this schema",
            height=100,
            key="schema_description"
        )
        
        # Category and Version in columns
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox(
                "Category",
                options=available_categories,
                index=available_categories.index(defaults["category"]) if defaults["category"] in available_categories else 0,
                help="Categorize your schema for better organization",
                key="schema_category"
            )
        
        with col2:
            version = st.text_input(
                "Version",
                value=defaults["version"],
                placeholder="v1.0.0",
                help="Semantic version for this schema",
                key="schema_version"
            )
        
        # Status and Active flag in columns
        col1, col2 = st.columns(2)
        
        with col1:
            status_options = [status.value for status in SchemaStatus]
            status_index = status_options.index(defaults["status"]) if defaults["status"] in status_options else 0
            status = st.selectbox(
                "Status",
                options=status_options,
                index=status_index,
                help="Current lifecycle status of the schema",
                key="schema_status"
            )
        
        with col2:
            is_active = st.checkbox(
                "Active Schema",
                value=defaults["is_active"],
                help="Whether this schema is active and available for use",
                key="schema_is_active"
            )
    
    # Validation section
    st.divider()
    render_basic_info_validation(name, schema_id, version)
    
    # Return collected data
    return {
        "name": name,
        "id": st.session_state.get("schema_id", schema_id),
        "description": description,
        "category": category,
        "version": version,
        "status": status,
        "is_active": is_active
    }


def render_basic_info_validation(name: str, schema_id: str, version: str) -> None:
    """
    Render validation feedback for basic info fields
    
    Args:
        name: Schema name
        schema_id: Schema ID
        version: Schema version
    """
    validation_issues = validate_basic_info(name, schema_id, version)
    
    if validation_issues:
        st.subheader("⚠️ Validation Issues")
        
        for issue in validation_issues:
            if issue["severity"] == "error":
                st.error(f"**{issue['field']}**: {issue['message']}")
            elif issue["severity"] == "warning":
                st.warning(f"**{issue['field']}**: {issue['message']}")
            else:
                st.info(f"**{issue['field']}**: {issue['message']}")
    else:
        st.success("✅ All basic information is valid")


def validate_basic_info(name: str, schema_id: str, version: str) -> List[Dict[str, str]]:
    """
    Validate basic schema information
    
    Args:
        name: Schema name
        schema_id: Schema ID
        version: Schema version
        
    Returns:
        List of validation issues
    """
    issues = []
    
    # Validate name
    if not name:
        issues.append({
            "field": "Name",
            "message": "Schema name is required",
            "severity": "error"
        })
    elif len(name) < 3:
        issues.append({
            "field": "Name",
            "message": "Schema name must be at least 3 characters long",
            "severity": "error"
        })
    elif len(name) > 100:
        issues.append({
            "field": "Name",
            "message": "Schema name must be less than 100 characters",
            "severity": "error"
        })
    
    # Validate ID
    if not schema_id:
        issues.append({
            "field": "ID",
            "message": "Schema ID is required",
            "severity": "error"
        })
    elif not re.match(r'^[a-zA-Z0-9_-]+$', schema_id):
        issues.append({
            "field": "ID",
            "message": "Schema ID can only contain letters, numbers, underscores, and hyphens",
            "severity": "error"
        })
    elif len(schema_id) < 3:
        issues.append({
            "field": "ID",
            "message": "Schema ID must be at least 3 characters long",
            "severity": "error"
        })
    elif len(schema_id) > 50:
        issues.append({
            "field": "ID",
            "message": "Schema ID must be less than 50 characters",
            "severity": "error"
        })
    
    # Validate version
    if not version:
        issues.append({
            "field": "Version",
            "message": "Version is required",
            "severity": "error"
        })
    elif not re.match(r'^v?\d+\.\d+\.\d+$', version):
        issues.append({
            "field": "Version",
            "message": "Version must follow semantic versioning format (e.g., v1.0.0 or 1.0.0)",
            "severity": "warning"
        })
    
    return issues


def generate_schema_id_from_name(name: str) -> str:
    """
    Generate a schema ID from the schema name
    
    Args:
        name: Schema name
        
    Returns:
        Generated schema ID
    """
    if not name:
        return ""
    
    # Convert to lowercase
    schema_id = name.lower()
    
    # Replace spaces and special characters with underscores
    schema_id = re.sub(r'[^a-z0-9]+', '_', schema_id)
    
    # Remove leading/trailing underscores
    schema_id = schema_id.strip('_')
    
    # Ensure it starts with a letter
    if schema_id and not schema_id[0].isalpha():
        schema_id = 'schema_' + schema_id
    
    return schema_id


def render_schema_metadata_display(schema: Schema) -> None:
    """
    Render read-only metadata display for existing schemas
    
    Args:
        schema: Schema object to display
    """
    st.subheader("📊 Schema Metadata")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Created",
            value=schema.created_date.strftime("%Y-%m-%d") if schema.created_date else "Unknown",
            help=f"Created by: {schema.created_by}"
        )
    
    with col2:
        st.metric(
            label="Last Modified",
            value=schema.updated_date.strftime("%Y-%m-%d") if schema.updated_date else "Unknown"
        )
    
    with col3:
        st.metric(
            label="Usage Count",
            value=schema.usage_count
        )
    
    # Additional metadata in expander
    with st.expander("📋 Additional Details"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Version:** ", schema.version)
            st.write("**Status:** ", schema.status.value if hasattr(schema.status, 'value') else schema.status)
            st.write("**Active:** ", "Yes" if schema.is_active else "No")
        
        with col2:
            st.write("**Category:** ", schema.category)
            st.write("**Fields Count:** ", len(schema.fields))
            st.write("**Backward Compatible:** ", "Yes" if schema.backward_compatible else "No")
        
        if schema.migration_notes:
            st.write("**Migration Notes:** ", schema.migration_notes)


def render_category_management() -> Optional[str]:
    """
    Render category management interface
    
    Returns:
        New category name if created, None otherwise
    """
    st.subheader("📁 Category Management")
    
    with st.expander("Add New Category"):
        new_category = st.text_input(
            "Category Name",
            placeholder="Enter new category name",
            help="Create a new category for organizing schemas"
        )
        
        if st.button("Add Category", disabled=not new_category):
            if new_category and len(new_category.strip()) > 0:
                # Validate category name
                if re.match(r'^[a-zA-Z0-9\s_-]+$', new_category):
                    st.success(f"Category '{new_category}' added successfully!")
                    return new_category.strip()
                else:
                    st.error("Category name can only contain letters, numbers, spaces, underscores, and hyphens")
            else:
                st.error("Please enter a valid category name")
    
    return None


def render_basic_info_help() -> None:
    """Render help information for basic info tab"""
    with st.expander("ℹ️ Help: Basic Information"):
        st.markdown("""
        ### Schema Basic Information
        
        **Schema Name**: A human-readable name that describes your schema. This will be displayed in lists and used for identification.
        
        **Schema ID**: A unique identifier used internally. Auto-generated from the name unless manually overridden. Must contain only letters, numbers, underscores, and hyphens.
        
        **Description**: A detailed explanation of what this schema does, what types of documents it's designed for, and any special considerations.
        
        **Category**: Helps organize schemas by type or use case. Choose from existing categories or create new ones.
        
        **Version**: Follows semantic versioning (major.minor.patch). Automatically incremented when making breaking changes.
        
        **Status**: 
        - **Draft**: Work in progress, not ready for use
        - **Validated**: Tested and validated, ready for activation
        - **Active**: Currently in use for document extraction
        - **Editing**: Temporarily locked while being modified
        - **Deprecated**: No longer recommended for new use
        - **Archived**: Stored for reference but not active
        - **Deleted**: Marked for deletion
        
        **Active Schema**: Whether this schema is available for selection in the document extraction workflow.
        """)


def get_schema_statistics(schemas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics about schemas for dashboard display
    
    Args:
        schemas: List of schema metadata dictionaries
        
    Returns:
        Statistics dictionary
    """
    if not schemas:
        return {
            "total_schemas": 0,
            "active_schemas": 0,
            "categories": {},
            "status_distribution": {},
            "total_usage": 0
        }
    
    stats = {
        "total_schemas": len(schemas),
        "active_schemas": sum(1 for s in schemas if s.get("is_active", False)),
        "categories": {},
        "status_distribution": {},
        "total_usage": sum(s.get("usage_count", 0) for s in schemas)
    }
    
    # Count by category
    for schema in schemas:
        category = schema.get("category", "Unknown")
        stats["categories"][category] = stats["categories"].get(category, 0) + 1
    
    # Count by status
    for schema in schemas:
        status = schema.get("status", "unknown")
        stats["status_distribution"][status] = stats["status_distribution"].get(status, 0) + 1
    
    return stats