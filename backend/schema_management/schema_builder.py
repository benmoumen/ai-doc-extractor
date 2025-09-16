"""
Main schema management page for the UI.
Coordinates all UI components and handles the schema building workflow.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# UI Components
from .ui.basic_info import render_basic_info_tab
from .ui.field_editor import render_field_editor
from .ui.field_list import render_field_list
from .ui.validation_builder import render_validation_builder
from .ui.preview import render_schema_preview

# Services
from .services.schema_service import SchemaService
from .services.field_service import FieldService
from .services.validation_service import ValidationService

# Models
from .models.schema import Schema, SchemaStatus
from .models.field import Field

# Storage
from .storage.schema_storage import SchemaStorage

# State Management
from .state_manager import (
    initialize_schema_builder_state,
    get_current_schema,
    update_current_schema,
    update_current_schema_field,
    mark_unsaved_changes,
    has_unsaved_changes,
    clear_schema_builder_state
)

# Performance Optimization
from .performance_optimizer import (
    performance_optimizer,
    PerformanceMonitor,
    debounced_update,
    optimize_large_schema_rendering,
    preload_common_data,
    get_optimization_status
)


def render_schema_management_page():
    """
    Main entry point for schema management interface with performance optimizations
    """
    # Preload common data asynchronously
    preload_common_data()
    
    # Performance monitoring
    with PerformanceMonitor("schema_management_page_render"):
        st.title("📋 Schema Management")
        
        # Show performance metrics in debug mode
        if st.secrets.get("DEBUG_MODE", False):
            with st.expander("🔧 Performance Metrics", expanded=False):
                metrics = get_optimization_status()
                st.json(metrics)
    # Initialize state
    initialize_schema_builder_state()
    
    # Initialize services
    storage = SchemaStorage()
    schema_service = SchemaService(storage)
    field_service = FieldService(storage, schema_service)
    validation_service = ValidationService(storage, schema_service)
    
    # Sidebar navigation
    render_sidebar_navigation(schema_service)
    
    # Main content area
    action = st.session_state.get("schema_action", "builder")
    
    if action == "builder":
        render_schema_builder(schema_service, field_service, validation_service)
    elif action == "library":
        render_schema_library(schema_service)
    elif action == "settings":
        render_schema_settings()


def render_sidebar_navigation(schema_service: SchemaService):
    """Render sidebar navigation for schema management"""
    with st.sidebar:
        if st.button("🏗️ Schema Builder", use_container_width=True):
            st.session_state.schema_action = "builder"

        if st.button("📚 Schema Library", use_container_width=True):
            st.session_state.schema_action = "library"

        if st.button("➕ New Schema", type="primary", use_container_width=True):
            clear_schema_builder_state()
            st.session_state.schema_action = "builder"
            st.rerun()

        st.divider()

        # Schema selector
        schemas = schema_service.list_schemas()
        if schemas:
            schema_options = {s["id"]: s["name"] for s in schemas}
            selected_schema_id = st.selectbox(
                "Load Existing Schema",
                options=list(schema_options.keys()),
                format_func=lambda x: schema_options[x]
            )

            if st.button("📂 Load", use_container_width=True):
                load_schema_for_editing(selected_schema_id, schema_service)

        # Status indicator
        if has_unsaved_changes():
            st.warning("⚠️ Unsaved changes")


def render_schema_builder(schema_service: SchemaService, field_service: FieldService,
                          validation_service: ValidationService):
    """Render the main schema builder interface"""
    
    # Header with save controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        current_schema = get_current_schema() or {}
        schema_name = current_schema.get("name", "New Schema")
        st.subheader(f"🏗️ {schema_name}")
    
    with col2:
        if st.button("💾 Save", type="primary", disabled=not has_unsaved_changes()):
            save_current_schema(schema_service)
    
    with col3:
        if st.button("🔄 Reset", disabled=not has_unsaved_changes()):
            if st.session_state.get("confirm_reset"):
                clear_schema_builder_state()
                st.success("Schema reset")
                st.rerun()
            else:
                st.session_state.confirm_reset = True
                st.warning("Click again to confirm reset")
    
    with col4:
        if st.button("❌ Close"):
            st.session_state.schema_action = "library"
            st.rerun()
    
    # Main tabs
    tabs = st.tabs([
        "📋 Basic Info",
        "📝 Fields",
        "✅ Validation",
        "👁️ Preview"
    ])
    
    # Basic Info Tab
    with tabs[0]:
        render_basic_info_tab_content(schema_service)
    
    # Fields Tab
    with tabs[1]:
        render_fields_tab_content(field_service)
    
    # Validation Tab
    with tabs[2]:
        render_validation_tab_content(validation_service)
    
    # Preview Tab
    with tabs[3]:
        render_preview_tab_content()
    


def render_basic_info_tab_content(schema_service: SchemaService):
    """Render basic info tab content"""
    current_schema = get_current_schema()
    
    # Get available categories
    all_schemas = schema_service.list_schemas({"active_only": False})
    categories = list(set(s.get("category", "Custom") for s in all_schemas))
    if "Custom" not in categories:
        categories.append("Custom")
    categories.sort()
    
    # Render basic info form
    basic_info = render_basic_info_tab(current_schema, categories)
    
    # Update schema builder state
    if basic_info:
        for key, value in basic_info.items():
            if current_schema.get(key) != value:
                update_current_schema_field(key, value)
                mark_unsaved_changes(True)


def render_fields_tab_content(field_service: FieldService):
    """Render fields tab content"""
    current_schema = get_current_schema()
    schema_fields = current_schema.get("fields", {})
    if isinstance(schema_fields, dict):
        fields = list(schema_fields.values())
    elif isinstance(schema_fields, list):
        fields = schema_fields
    else:
        fields = []
    
    # Field management interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Field list
        field_action = render_field_list(fields, editable=True, show_reorder=True)
        
        # Handle field list actions
        if field_action and field_action.get("action"):
            handle_field_action(field_action, field_service)
    
    with col2:
        # Field editor panel
        if st.session_state.get("editing_field"):
            render_field_editor_panel(field_service)
        else:
            st.info("Select a field to edit or add a new field")
            
            if st.button("➕ Add Field", type="primary", use_container_width=True):
                st.session_state.editing_field = True
                st.session_state.editing_field_data = {}
                st.rerun()
    


def render_field_editor_panel(field_service: FieldService):
    """Render field editor panel"""
    st.subheader("⚙️ Field Editor")
    
    current_schema = get_current_schema()
    existing_fields = list(current_schema.get("fields", {}).values())
    editing_field_data = st.session_state.get("editing_field_data", {})
    
    # Render field editor
    field_data = render_field_editor(
        field_data=editing_field_data,
        existing_fields=existing_fields
    )
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Save Field", type="primary", use_container_width=True):
            if save_field(field_data, field_service):
                st.session_state.editing_field = False
                st.session_state.editing_field_data = {}
                st.rerun()
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.editing_field = False
            st.session_state.editing_field_data = {}
            st.rerun()


def render_validation_tab_content(validation_service: ValidationService):
    """Render validation tab content"""
    current_schema = get_current_schema()
    
    # Field selector for validation
    fields = current_schema.get("fields", {})
    
    if not fields:
        st.info("Add fields first to configure validation rules")
        return
    
    field_names = list(fields.keys())
    selected_field_name = st.selectbox(
        "Select Field for Validation",
        options=field_names,
        format_func=lambda x: fields[x].get("display_name", x)
    )
    
    if selected_field_name:
        field_data = fields[selected_field_name]
        existing_rules = field_data.get("validation_rules", [])
        
        # Render validation builder
        updated_rules = render_validation_builder(field_data, existing_rules)
        
        # Update field if rules changed
        if updated_rules != existing_rules:
            field_data["validation_rules"] = updated_rules
            current_schema["fields"][selected_field_name] = field_data
            update_current_schema("fields", current_schema["fields"])
            mark_unsaved_changes(True)
    
    # Schema-level validation
    st.divider()
    st.subheader("📊 Schema-Level Validation")
    st.info("Configure validation rules that apply across multiple fields")
    
    # This would render cross-field validation interface
    # Implementation depends on specific requirements


def render_preview_tab_content():
    """Render preview tab content"""
    current_schema = get_current_schema()
    
    if not current_schema.get("id") or not current_schema.get("fields"):
        st.info("Configure basic info and add fields to see preview")
        return
    
    render_schema_preview(current_schema)



def render_schema_library(schema_service: SchemaService):
    """Render schema library view with performance optimizations"""
    with PerformanceMonitor("schema_library_render"):
        st.subheader("📚 Schema Library")
        
        # Try to get cached schema list
        cached_schemas = performance_optimizer.get_cached_schema_list()
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input("🔍 Search", placeholder="Search schemas...")
    
    with col2:
        category_filter = st.selectbox(
            "Category",
            options=["All"] + get_available_categories(schema_service)
        )
    
    with col3:
        status_filter = st.selectbox(
            "Status",
            options=["All", "Active", "Draft", "Deprecated", "Archived"]
        )
    
    with col4:
        sort_by = st.selectbox(
            "Sort By",
            options=["Updated", "Name", "Usage", "Created"]
        )
    
    # Apply filters
    filters = {}
    if search_term:
        filters["search_term"] = search_term
    if category_filter != "All":
        filters["category"] = category_filter
    if status_filter != "All":
        filters["status"] = status_filter.lower()
    filters["sort_by"] = {
        "Updated": "updated_date",
        "Name": "name",
        "Usage": "usage_count",
        "Created": "created_date"
    }[sort_by]
    
    # Get schemas with caching
    if cached_schemas and not any(filters.values()):
        # Use cached results for unfiltered view
        schemas = cached_schemas
    else:
        # Load schemas and cache if no filters
        schemas = schema_service.list_schemas(filters)
        if not any(filters.values()):
            performance_optimizer.cache_schema_list(schemas)
    
    if not schemas:
        st.info("No schemas found matching your criteria")
        return

    # Optimize rendering for large numbers of schemas
    optimization_config = optimize_large_schema_rendering({'fields': schemas})

    if optimization_config['strategy'] == 'paginated':
        # Use pagination for medium number of schemas
        pagination = optimization_config['pagination']
        visible_schemas = pagination['visible_fields']  # Reusing field pagination logic

        # Show pagination info
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.write(f"Showing {pagination['start_idx']}-{pagination['end_idx']} of {pagination['total_fields']} schemas")

        # Pagination controls
        col1, col2, col3, col4, col5 = st.columns(5)
        with col2:
            if st.button("⬅️ Previous", disabled=pagination['current_page'] == 1):
                st.session_state['schema_list_page'] = pagination['current_page'] - 1
                st.rerun()

        with col4:
            if st.button("Next ➡️", disabled=pagination['current_page'] == pagination['total_pages']):
                st.session_state['schema_list_page'] = pagination['current_page'] + 1
                st.rerun()

        schemas_to_display = visible_schemas
    else:
        schemas_to_display = schemas

    # Display schemas
    for schema in schemas_to_display:
        with st.expander(f"📋 {schema['name']}"):
            render_schema_card(schema, schema_service)


def render_schema_card(schema: Dict[str, Any], schema_service: SchemaService):
    """Render individual schema card"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(f"**ID:** `{schema['id']}`")
        st.write(f"**Category:** {schema.get('category', 'Unknown')}")
        st.write(f"**Version:** {schema.get('version', 'Unknown')}")
        if schema.get('description'):
            st.write(f"**Description:** {schema['description']}")
    
    with col2:
        st.metric("Fields", schema.get('field_count', 0))
        st.metric("Usage", schema.get('usage_count', 0))
    
    with col3:
        if st.button("✏️ Edit", key=f"edit_{schema['id']}"):
            load_schema_for_editing(schema['id'], schema_service)
        
        if st.button("📋 Clone", key=f"clone_{schema['id']}"):
            clone_schema(schema['id'], schema_service)
        
        if st.button("🗑️ Delete", key=f"delete_{schema['id']}"):
            if st.session_state.get(f"confirm_delete_{schema['id']}"):
                delete_schema(schema['id'], schema_service)
            else:
                st.session_state[f"confirm_delete_{schema['id']}"] = True
                st.warning("Click again to confirm deletion")






def render_schema_settings():
    """Render schema settings"""
    st.subheader("⚙️ Schema Settings")
    
    st.info("Configure global schema management settings")
    
    # Settings sections
    with st.expander("Storage Settings"):
        st.write("**Data Directory:**", "data/")
        st.write("**Schema Directory:**", "data/schemas/")
        st.write("**Database:**", "data/db/schema_metadata.db")
    
    with st.expander("Validation Settings"):
        st.checkbox("Enable strict validation", value=True)
        st.checkbox("Validate on save", value=True)
        st.checkbox("Show validation warnings", value=True)
    
    with st.expander("UI Settings"):
        st.checkbox("Enable drag-and-drop", value=True)
        st.checkbox("Show field previews", value=True)
        st.checkbox("Auto-save drafts", value=False)
    
    if st.button("Save Settings"):
        st.success("Settings saved successfully")


# Helper functions

def load_schema_for_editing(schema_id: str, schema_service: SchemaService):
    """Load schema for editing"""
    schema = schema_service.get_schema(schema_id)
    
    if schema:
        # Convert to dict if needed
        if hasattr(schema, 'to_dict'):
            schema_data = schema.to_dict()
        else:
            schema_data = schema
        
        # Load into builder state using proper state manager
        from .state_manager import update_current_schema
        update_current_schema(schema_data, schema_data.get('id'))
        st.session_state.schema_action = "builder"
        mark_unsaved_changes(False)
        st.success(f"Loaded schema: {schema_data.get('name', 'Unknown')}")
        st.rerun()
    else:
        st.error(f"Failed to load schema: {schema_id}")


def save_current_schema(schema_service: SchemaService):
    """Save current schema with performance optimization"""
    with PerformanceMonitor("schema_save"):
        current_schema = get_current_schema()
        
        if not current_schema.get("id"):
            st.error("Schema ID is required")
            return
        
        if not current_schema.get("name"):
            st.error("Schema name is required")
            return
        
        # Check if schema exists
        existing = schema_service.get_schema(current_schema["id"])
        
        if existing:
            # Update existing schema
            success, message, _ = schema_service.update_schema(
                current_schema["id"],
                current_schema
            )
        else:
            # Create new schema
            success, message, _ = schema_service.create_schema(current_schema)
        
        if success:
            st.success(message)
            mark_unsaved_changes(False)
            # Clear cache to force refresh
            performance_optimizer.clear_caches()
        else:
            st.error(message)


@debounced_update(delay=3.0, key="auto_save_schema")
def auto_save_current_schema(schema_service: SchemaService):
    """Auto-save current schema with debouncing"""
    current_schema = get_current_schema()
    
    # Only auto-save if basic info is complete
    if (current_schema.get("id") and 
        current_schema.get("name") and 
        current_schema.get("fields")):
        
        save_current_schema(schema_service)


def clone_schema(schema_id: str, schema_service: SchemaService):
    """Clone a schema"""
    new_id = f"{schema_id}_copy"
    new_name = f"Copy of {schema_id}"
    
    success, message, cloned_schema = schema_service.clone_schema(
        schema_id, new_id, new_name
    )
    
    if success:
        st.success(message)
        load_schema_for_editing(new_id, schema_service)
    else:
        st.error(message)


def delete_schema(schema_id: str, schema_service: SchemaService):
    """Delete a schema"""
    success, message = schema_service.delete_schema(schema_id)
    
    if success:
        st.success(message)
        st.rerun()
    else:
        st.error(message)


def handle_field_action(action: Dict[str, Any], field_service: FieldService):
    """Handle field list actions"""
    action_type = action.get("action")
    
    if action_type == "add_field":
        st.session_state.editing_field = True
        st.session_state.editing_field_data = {}
        st.rerun()
    
    elif action_type == "edit_field":
        field_data = action.get("field_data", {})
        st.session_state.editing_field = True
        st.session_state.editing_field_data = field_data
        st.rerun()
    
    elif action_type == "delete_field":
        field_id = action.get("field_id")
        if field_id:
            delete_field(field_id)
    
    elif action_type == "move_field":
        handle_field_reorder(action)


def save_field(field_data: Dict[str, Any], field_service: FieldService) -> bool:
    """Save field to current schema"""
    current_schema = get_current_schema()
    
    if not field_data.get("name"):
        st.error("Field name is required")
        return False
    
    if not field_data.get("display_name"):
        st.error("Field display name is required")
        return False
    
    # Update fields
    if "fields" not in current_schema:
        current_schema["fields"] = {}
    
    current_schema["fields"][field_data["name"]] = field_data
    update_current_schema("fields", current_schema["fields"])
    mark_unsaved_changes(True)
    
    st.success(f"Field '{field_data['display_name']}' saved")
    return True


def delete_field(field_name: str):
    """Delete field from current schema"""
    current_schema = get_current_schema()
    
    if field_name in current_schema.get("fields", {}):
        del current_schema["fields"][field_name]
        update_current_schema("fields", current_schema["fields"])
        mark_unsaved_changes(True)
        st.success(f"Field '{field_name}' deleted")
        st.rerun()


def handle_field_reorder(action: Dict[str, Any]):
    """Handle field reordering"""
    current_schema = get_current_schema()
    fields = current_schema.get("fields", {})
    field_id = action.get("field_id")
    direction = action.get("direction")
    current_index = action.get("current_index", 0)
    
    # Convert fields dict to list for reordering
    field_items = list(fields.items())
    
    if direction == "up" and current_index > 0:
        # Swap with previous item
        field_items[current_index], field_items[current_index - 1] = \
            field_items[current_index - 1], field_items[current_index]
    elif direction == "down" and current_index < len(field_items) - 1:
        # Swap with next item
        field_items[current_index], field_items[current_index + 1] = \
            field_items[current_index + 1], field_items[current_index]
    
    # Convert back to dict
    current_schema["fields"] = dict(field_items)
    update_current_schema("fields", current_schema["fields"])
    mark_unsaved_changes(True)
    st.rerun()






def get_available_categories(schema_service: SchemaService) -> List[str]:
    """Get list of available categories"""
    schemas = schema_service.list_schemas({"active_only": False})
    categories = list(set(s.get("category", "Custom") for s in schemas))
    categories.sort()
    return categories


# Main entry point
if __name__ == "__main__":
    render_schema_management_page()