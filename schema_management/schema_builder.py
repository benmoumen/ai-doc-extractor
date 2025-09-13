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
from .ui.field_list import render_field_list, render_field_statistics
from .ui.validation_builder import render_validation_builder
from .ui.preview import render_schema_preview
from .ui.import_export import render_import_export_interface

# Services
from .services.schema_service import SchemaService
from .services.field_service import FieldService
from .services.validation_service import ValidationService
from .services.template_service import TemplateService

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
    template_service = TemplateService(storage, schema_service)
    
    # Sidebar navigation
    render_sidebar_navigation(schema_service)
    
    # Main content area
    action = st.session_state.get("schema_action", "builder")
    
    if action == "builder":
        render_schema_builder(schema_service, field_service, validation_service, template_service)
    elif action == "library":
        render_schema_library(schema_service)
    elif action == "templates":
        render_template_manager(template_service)
    elif action == "import_export":
        render_import_export_manager(schema_service)
    elif action == "settings":
        render_schema_settings()


def render_sidebar_navigation(schema_service: SchemaService):
    """Render sidebar navigation for schema management"""
    with st.sidebar:
        st.header("📋 Schema Management")
        
        # Main navigation
        st.subheader("Navigation")
        
        if st.button("🏗️ Schema Builder", use_container_width=True):
            st.session_state.schema_action = "builder"
            
        if st.button("📚 Schema Library", use_container_width=True):
            st.session_state.schema_action = "library"
            
        if st.button("📋 Templates", use_container_width=True):
            st.session_state.schema_action = "templates"
            
        if st.button("📁 Import/Export", use_container_width=True):
            st.session_state.schema_action = "import_export"
            
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.schema_action = "settings"
        
        st.divider()
        
        # Quick actions
        st.subheader("Quick Actions")
        
        if st.button("➕ New Schema", type="primary", use_container_width=True):
            clear_schema_builder_state()
            st.session_state.schema_action = "builder"
            st.rerun()
        
        # Schema selector
        st.subheader("Load Schema")
        
        schemas = schema_service.list_schemas()
        if schemas:
            schema_options = {s["id"]: s["name"] for s in schemas}
            selected_schema_id = st.selectbox(
                "Select Schema",
                options=list(schema_options.keys()),
                format_func=lambda x: schema_options[x]
            )
            
            if st.button("📂 Load Selected", use_container_width=True):
                load_schema_for_editing(selected_schema_id, schema_service)
        else:
            st.info("No schemas available")
        
        # Status indicator
        if has_unsaved_changes():
            st.warning("⚠️ Unsaved changes")


def render_schema_builder(schema_service: SchemaService, field_service: FieldService,
                          validation_service: ValidationService, template_service: TemplateService):
    """Render the main schema builder interface"""
    
    # Header with save controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        schema_name = st.session_state.get("schema_builder", {}).get("name", "New Schema")
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
        "👁️ Preview",
        "📁 Import/Export"
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
    
    # Import/Export Tab
    with tabs[4]:
        render_import_export_tab_content(schema_service)


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
    
    # Field statistics
    if fields:
        st.divider()
        render_field_statistics(fields)


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


def render_import_export_tab_content(schema_service: SchemaService):
    """Render import/export tab content"""
    current_schema = get_current_schema()
    
    action_result = render_import_export_interface(current_schema)
    
    if action_result and action_result.get("action"):
        handle_import_export_action(action_result, schema_service)


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


def render_template_manager(template_service: TemplateService):
    """Render template management interface"""
    st.subheader("📋 Template Management")
    
    tab1, tab2, tab3 = st.tabs(["Field Templates", "Schema Templates", "Create Template"])
    
    with tab1:
        render_field_templates(template_service)
    
    with tab2:
        render_schema_templates(template_service)
    
    with tab3:
        render_create_template(template_service)


def render_field_templates(template_service: TemplateService):
    """Render field templates"""
    st.write("**Available Field Templates**")
    
    templates = template_service.list_field_templates()
    
    if not templates:
        st.info("No field templates available")
        return
    
    for template in templates:
        with st.expander(f"📋 {template.name}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Type:** {template.field_type}")
                st.write(f"**Category:** {template.category}")
                if template.description:
                    st.write(f"**Description:** {template.description}")
                st.write(f"**Usage:** {template.usage_count} times")
            
            with col2:
                if st.button("Use", key=f"use_field_template_{template.id}"):
                    st.session_state.selected_field_template = template
                    st.info(f"Selected template: {template.name}")


def render_schema_templates(template_service: TemplateService):
    """Render schema templates"""
    st.write("**Available Schema Templates**")
    
    templates = template_service.list_schema_templates()
    
    if not templates:
        st.info("No schema templates available")
        return
    
    for template in templates:
        with st.expander(f"📋 {template.name}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Category:** {template.category.value if hasattr(template.category, 'value') else template.category}")
                if template.description:
                    st.write(f"**Description:** {template.description}")
                st.write(f"**Fields:** {len(template.field_templates)}")
                st.write(f"**Usage:** {template.usage_count} times")
            
            with col2:
                if st.button("Use", key=f"use_schema_template_{template.id}"):
                    apply_schema_template(template.id, template_service)


def render_create_template(template_service: TemplateService):
    """Render template creation interface"""
    st.write("**Create New Template**")
    
    template_type = st.selectbox(
        "Template Type",
        options=["Field Template", "Schema Template"]
    )
    
    if template_type == "Field Template":
        render_create_field_template(template_service)
    else:
        render_create_schema_template(template_service)


def render_create_field_template(template_service: TemplateService):
    """Render field template creation"""
    current_schema = get_current_schema()
    fields = current_schema.get("fields", {})
    
    if not fields:
        st.info("Create a schema with fields first to create templates")
        return
    
    field_names = list(fields.keys())
    selected_field = st.selectbox(
        "Create Template From Field",
        options=field_names,
        format_func=lambda x: fields[x].get("display_name", x)
    )
    
    template_name = st.text_input("Template Name")
    template_id = st.text_input("Template ID")
    
    if st.button("Create Field Template", type="primary"):
        if template_name and template_id and selected_field:
            success, message, template = template_service.create_template_from_field(
                current_schema["id"], selected_field, template_id, template_name
            )
            
            if success:
                st.success(message)
            else:
                st.error(message)


def render_create_schema_template(template_service: TemplateService):
    """Render schema template creation"""
    current_schema = get_current_schema()
    
    if not current_schema.get("id"):
        st.info("Save your schema first to create a template")
        return
    
    template_name = st.text_input("Template Name", value=f"{current_schema.get('name', '')} Template")
    template_id = st.text_input("Template ID", value=f"{current_schema.get('id', '')}_template")
    
    if st.button("Create Schema Template", type="primary"):
        if template_name and template_id:
            success, message, template = template_service.create_template_from_schema(
                current_schema["id"], template_id, template_name
            )
            
            if success:
                st.success(message)
            else:
                st.error(message)


def render_import_export_manager(schema_service: SchemaService):
    """Render import/export manager"""
    st.subheader("📁 Import & Export Manager")
    
    current_schema = get_current_schema()
    action_result = render_import_export_interface(current_schema)
    
    if action_result and action_result.get("action"):
        handle_import_export_action(action_result, schema_service)


def render_schema_settings():
    """Render schema settings"""
    st.subheader("⚙️ Schema Settings")
    
    st.info("Configure global schema management settings")
    
    # Settings sections
    with st.expander("Storage Settings"):
        st.write("**Data Directory:**", "data/")
        st.write("**Schema Directory:**", "data/schemas/")
        st.write("**Template Directory:**", "data/templates/")
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
        
        # Load into builder state
        st.session_state.schema_builder = schema_data
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


def apply_schema_template(template_id: str, template_service: TemplateService):
    """Apply schema template"""
    schema_id = f"schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    schema_name = f"New Schema from Template"
    
    success, message, schema = template_service.apply_schema_template(
        template_id, schema_id, schema_name
    )
    
    if success:
        st.success(message)
        # Load the new schema for editing
        if hasattr(schema, 'to_dict'):
            schema_data = schema.to_dict()
        else:
            schema_data = schema
        
        st.session_state.schema_builder = schema_data
        st.session_state.schema_action = "builder"
        mark_unsaved_changes(True)
        st.rerun()
    else:
        st.error(message)


def handle_import_export_action(action: Dict[str, Any], schema_service: SchemaService):
    """Handle import/export actions"""
    action_type = action.get("action")
    
    if action_type == "import_schema":
        handle_schema_import(action, schema_service)
    elif action_type == "create_backup":
        handle_backup_creation(action, schema_service)
    # Add more action handlers as needed


def handle_schema_import(action: Dict[str, Any], schema_service: SchemaService):
    """Handle schema import"""
    schema_data = action.get("data")
    new_id = action.get("new_id")
    mode = action.get("mode", "replace")
    
    if new_id:
        schema_data["id"] = new_id
    
    success, message, imported_schema = schema_service.import_schema(
        json.dumps(schema_data), "json"
    )
    
    if success:
        st.success(message)
        # Load imported schema for editing
        load_schema_for_editing(schema_data["id"], schema_service)
    else:
        st.error(message)


def handle_backup_creation(action: Dict[str, Any], schema_service: SchemaService):
    """Handle backup creation"""
    st.info("Backup creation is not yet implemented")
    # Implementation would create a backup file


def get_available_categories(schema_service: SchemaService) -> List[str]:
    """Get list of available categories"""
    schemas = schema_service.list_schemas({"active_only": False})
    categories = list(set(s.get("category", "Custom") for s in schemas))
    categories.sort()
    return categories


# Main entry point
if __name__ == "__main__":
    render_schema_management_page()