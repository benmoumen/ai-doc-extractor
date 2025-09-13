"""
Field list component with drag-drop functionality for schema management UI.
Displays field list with reordering, editing, and management capabilities.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
import json

try:
    from streamlit_elements import elements, mui, html
    ELEMENTS_AVAILABLE = True
except ImportError:
    ELEMENTS_AVAILABLE = False
    st.warning("streamlit-elements not available. Drag-and-drop functionality will be limited.")

from ..models.field import Field, FieldType


def render_field_list(fields: List[Dict[str, Any]], 
                     editable: bool = True,
                     show_reorder: bool = True) -> Dict[str, Any]:
    """
    Render field list with drag-drop reordering
    
    Args:
        fields: List of field dictionaries
        editable: Whether fields can be edited/deleted
        show_reorder: Whether to show reordering controls
        
    Returns:
        Dictionary with action and field information
    """
    if not fields:
        render_empty_field_list()
        return {"action": None}
    
    st.subheader(f"📋 Schema Fields ({len(fields)})")
    
    # Field list controls
    if editable:
        render_field_list_controls()
    
    # Render based on available components
    if ELEMENTS_AVAILABLE and show_reorder:
        return render_draggable_field_list(fields, editable)
    else:
        return render_simple_field_list(fields, editable, show_reorder)


def render_empty_field_list() -> None:
    """Render empty field list with guidance"""
    st.info("🆕 No fields added yet. Start by adding your first field!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Add Field", type="primary"):
            st.session_state.action = "add_field"
    
    with col2:
        if st.button("📋 Use Template"):
            st.session_state.action = "use_template"
    
    with col3:
        if st.button("📥 Import Fields"):
            st.session_state.action = "import_fields"


def render_field_list_controls() -> None:
    """Render field list management controls"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Add Field", type="primary"):
            st.session_state.field_list_action = "add_field"
            st.session_state.selected_field_id = None
    
    with col2:
        if st.button("📋 Templates"):
            st.session_state.field_list_action = "show_templates"
    
    with col3:
        if st.button("📥 Import"):
            st.session_state.field_list_action = "import_fields"
    
    with col4:
        if st.button("🔄 Reset Order"):
            st.session_state.field_list_action = "reset_order"


def render_draggable_field_list(fields: List[Dict[str, Any]], editable: bool = True) -> Dict[str, Any]:
    """
    Render draggable field list using streamlit-elements
    
    Args:
        fields: List of field dictionaries
        editable: Whether fields can be edited
        
    Returns:
        Action dictionary
    """
    # Initialize drag state
    if "field_order" not in st.session_state:
        st.session_state.field_order = [f["name"] for f in fields]
    
    # Check for action in session state
    action_result = {"action": st.session_state.get("field_list_action")}
    if st.session_state.get("field_list_action"):
        action_result["field_id"] = st.session_state.get("selected_field_id")
        # Clear action after reading
        st.session_state.field_list_action = None
    
    with elements("field_list"):
        # Create sortable list
        field_items = []
        
        for field in fields:
            field_item = create_field_list_item(field, editable)
            field_items.append(field_item)
        
        # Render sortable container
        mui.Box(
            field_items,
            sx={
                "width": "100%",
                "bgcolor": "background.paper",
                "borderRadius": 1,
                "overflow": "hidden"
            }
        )
    
    return action_result


def render_simple_field_list(fields: List[Dict[str, Any]], 
                            editable: bool = True, 
                            show_reorder: bool = True) -> Dict[str, Any]:
    """
    Render simple field list without drag-drop
    
    Args:
        fields: List of field dictionaries
        editable: Whether fields can be edited
        show_reorder: Whether to show reorder buttons
        
    Returns:
        Action dictionary
    """
    action_result = {"action": None}
    
    for i, field in enumerate(fields):
        field_container = st.container()
        
        with field_container:
            # Field header with controls
            col1, col2, col3 = st.columns([6, 2, 2])
            
            with col1:
                # Field info
                field_icon = get_field_type_icon(field.get("type", "text"))
                required_badge = " 🔴" if field.get("required") else ""
                dependency_badge = " 🔗" if field.get("depends_on") else ""
                
                st.markdown(f"""
                **{field_icon} {field.get('display_name', field.get('name', 'Unnamed'))}**{required_badge}{dependency_badge}
                
                *{field.get('type', 'text')} • {field.get('name', 'unnamed')}*
                """)
                
                if field.get("description"):
                    st.caption(field["description"])
            
            with col2:
                # Reorder controls
                if show_reorder and editable:
                    if st.button("⬆️", key=f"up_{i}", disabled=i == 0):
                        action_result = {
                            "action": "move_field",
                            "field_id": field["name"],
                            "direction": "up",
                            "current_index": i
                        }
                    
                    if st.button("⬇️", key=f"down_{i}", disabled=i == len(fields) - 1):
                        action_result = {
                            "action": "move_field",
                            "field_id": field["name"],
                            "direction": "down",
                            "current_index": i
                        }
            
            with col3:
                # Action controls
                if editable:
                    if st.button("✏️", key=f"edit_{i}", help="Edit field"):
                        action_result = {
                            "action": "edit_field",
                            "field_id": field["name"],
                            "field_data": field
                        }
                    
                    if st.button("🗑️", key=f"delete_{i}", help="Delete field"):
                        action_result = {
                            "action": "delete_field",
                            "field_id": field["name"],
                            "field_name": field.get("display_name", field["name"])
                        }
        
        # Field details in expander
        with st.expander(f"📋 {field.get('display_name', field['name'])} Details"):
            render_field_details(field)
        
        st.divider()
    
    return action_result


def create_field_list_item(field: Dict[str, Any], editable: bool = True):
    """Create a single field list item for drag-drop interface"""
    field_icon = get_field_type_icon(field.get("type", "text"))
    required_badge = "🔴" if field.get("required") else ""
    dependency_badge = "🔗" if field.get("depends_on") else ""
    
    # Field content
    return mui.ListItem(
        mui.ListItemIcon(html.span(field_icon)),
        mui.ListItemText(
            primary=f"{field.get('display_name', field.get('name', 'Unnamed'))} {required_badge} {dependency_badge}",
            secondary=f"{field.get('type', 'text')} • {field.get('name', 'unnamed')}"
        ),
        mui.ListItemSecondaryAction(
            mui.ButtonGroup([
                mui.IconButton(
                    mui.Icon("edit"),
                    onClick=lambda: st.session_state.update({
                        "field_list_action": "edit_field",
                        "selected_field_id": field["name"]
                    })
                ) if editable else None,
                mui.IconButton(
                    mui.Icon("delete"),
                    onClick=lambda: st.session_state.update({
                        "field_list_action": "delete_field",
                        "selected_field_id": field["name"]
                    })
                ) if editable else None
            ].filter(None))
        ),
        sx={
            "bgcolor": "background.paper",
            "mb": 1,
            "borderRadius": 1,
            "border": "1px solid",
            "borderColor": "divider",
            "&:hover": {
                "bgcolor": "action.hover"
            }
        }
    )


def render_field_details(field: Dict[str, Any]) -> None:
    """Render detailed field information"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Type:**", field.get("type", "Unknown"))
        st.write("**Required:**", "Yes" if field.get("required") else "No")
        
        if field.get("placeholder"):
            st.write("**Placeholder:**", field["placeholder"])
        
        if field.get("help_text"):
            st.write("**Help Text:**", field["help_text"])
    
    with col2:
        if field.get("depends_on"):
            st.write("**Depends On:**", field["depends_on"])
            st.write("**Condition:**", f"{field.get('condition', '==')} {field.get('condition_value', '')}")
        
        if field.get("examples"):
            st.write("**Examples:**")
            for example in field["examples"][:3]:  # Show first 3 examples
                st.write(f"- {example}")
    
    # Validation rules
    if field.get("validation_rules"):
        st.write("**Validation Rules:**")
        for rule in field["validation_rules"]:
            rule_type = rule.get("type", "unknown")
            rule_message = rule.get("message", "No message")
            st.write(f"- {rule_type}: {rule_message}")


def render_field_statistics(fields: List[Dict[str, Any]]) -> None:
    """Render field statistics"""
    if not fields:
        return
    
    st.subheader("📊 Field Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Fields", len(fields))
    
    with col2:
        required_count = sum(1 for f in fields if f.get("required"))
        st.metric("Required Fields", required_count)
    
    with col3:
        with_validation = sum(1 for f in fields if f.get("validation_rules"))
        st.metric("With Validation", with_validation)
    
    with col4:
        with_dependencies = sum(1 for f in fields if f.get("depends_on"))
        st.metric("With Dependencies", with_dependencies)
    
    # Field type distribution
    type_counts = {}
    for field in fields:
        field_type = field.get("type", "unknown")
        type_counts[field_type] = type_counts.get(field_type, 0) + 1
    
    if type_counts:
        st.subheader("📈 Field Type Distribution")
        
        # Create columns for type distribution
        type_items = list(type_counts.items())
        cols = st.columns(min(len(type_items), 4))
        
        for i, (field_type, count) in enumerate(type_items):
            icon = get_field_type_icon(field_type)
            with cols[i % len(cols)]:
                st.metric(f"{icon} {field_type.title()}", count)


def render_field_search_and_filter(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Render search and filter controls for field list
    
    Args:
        fields: List of field dictionaries
        
    Returns:
        Filtered list of fields
    """
    if not fields:
        return fields
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input(
            "🔍 Search Fields",
            placeholder="Search by name or description...",
            key="field_search"
        )
    
    with col2:
        # Type filter
        field_types = sorted(set(f.get("type", "unknown") for f in fields))
        type_filter = st.selectbox(
            "Filter by Type",
            options=["All Types"] + field_types,
            key="field_type_filter"
        )
    
    with col3:
        # Status filter
        status_options = ["All Fields", "Required Only", "Optional Only", "With Dependencies", "With Validation"]
        status_filter = st.selectbox(
            "Filter by Status",
            options=status_options,
            key="field_status_filter"
        )
    
    # Apply filters
    filtered_fields = fields.copy()
    
    # Search filter
    if search_term:
        search_term = search_term.lower()
        filtered_fields = [
            f for f in filtered_fields
            if search_term in f.get("name", "").lower() or
               search_term in f.get("display_name", "").lower() or
               search_term in f.get("description", "").lower()
        ]
    
    # Type filter
    if type_filter != "All Types":
        filtered_fields = [f for f in filtered_fields if f.get("type") == type_filter]
    
    # Status filter
    if status_filter == "Required Only":
        filtered_fields = [f for f in filtered_fields if f.get("required")]
    elif status_filter == "Optional Only":
        filtered_fields = [f for f in filtered_fields if not f.get("required")]
    elif status_filter == "With Dependencies":
        filtered_fields = [f for f in filtered_fields if f.get("depends_on")]
    elif status_filter == "With Validation":
        filtered_fields = [f for f in filtered_fields if f.get("validation_rules")]
    
    # Show filter results
    if len(filtered_fields) != len(fields):
        st.info(f"Showing {len(filtered_fields)} of {len(fields)} fields")
    
    return filtered_fields


def render_bulk_field_operations(fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Render bulk operations interface for fields
    
    Args:
        fields: List of field dictionaries
        
    Returns:
        Bulk operation result
    """
    if not fields:
        return {"action": None}
    
    with st.expander("⚙️ Bulk Operations"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Select fields for bulk operations
            st.write("**Select Fields:**")
            selected_fields = []
            
            for field in fields:
                if st.checkbox(
                    f"{get_field_type_icon(field.get('type', 'text'))} {field.get('display_name', field['name'])}",
                    key=f"bulk_select_{field['name']}"
                ):
                    selected_fields.append(field["name"])
        
        with col2:
            if selected_fields:
                st.write(f"**Selected: {len(selected_fields)} fields**")
                
                # Bulk operations
                operation = st.selectbox(
                    "Bulk Operation",
                    options=[
                        "Make Required",
                        "Make Optional", 
                        "Add Validation Rule",
                        "Change Type",
                        "Delete Selected",
                        "Export Selected"
                    ],
                    key="bulk_operation"
                )
                
                if st.button("Apply Bulk Operation", type="primary"):
                    return {
                        "action": "bulk_operation",
                        "operation": operation,
                        "selected_fields": selected_fields
                    }
            else:
                st.info("Select fields to perform bulk operations")
    
    return {"action": None}


def get_field_type_icon(field_type: str) -> str:
    """Get icon for field type"""
    icons = {
        "text": "📝",
        "number": "🔢", 
        "date": "📅",
        "email": "📧",
        "phone": "📞",
        "boolean": "☑️",
        "select": "📋",
        "currency": "💰",
        "url": "🔗",
        "custom": "⚙️"
    }
    return icons.get(field_type, "❓")


def render_field_list_help() -> None:
    """Render help information for field list"""
    with st.expander("ℹ️ Help: Field List"):
        st.markdown("""
        ### Field List Management
        
        **Field Order**: 
        - Use drag & drop to reorder fields (if available)
        - Use ⬆️⬇️ buttons to move fields up/down
        - Field order affects the display order in forms
        
        **Field Status Indicators**:
        - 🔴 Required field
        - 🔗 Has dependencies on other fields
        - No indicator = optional field
        
        **Field Actions**:
        - ✏️ Edit field configuration
        - 🗑️ Delete field (with confirmation)
        - Click field name to expand details
        
        **Bulk Operations**:
        - Select multiple fields for batch operations
        - Change properties for multiple fields at once
        - Export selected fields for reuse
        
        **Search & Filter**:
        - Search by field name or description
        - Filter by field type or status
        - Combine filters for precise field selection
        """)


def export_fields_to_template(fields: List[Dict[str, Any]], template_name: str) -> Dict[str, Any]:
    """
    Export selected fields as a template
    
    Args:
        fields: List of field dictionaries to export
        template_name: Name for the template
        
    Returns:
        Template data dictionary
    """
    template_data = {
        "name": template_name,
        "description": f"Field template with {len(fields)} fields",
        "fields": fields,
        "created_date": st.session_state.get("current_timestamp"),
        "field_count": len(fields)
    }
    
    return template_data


def validate_field_order(fields: List[Dict[str, Any]]) -> List[str]:
    """
    Validate field ordering for dependencies
    
    Args:
        fields: List of field dictionaries in order
        
    Returns:
        List of validation warnings
    """
    warnings = []
    field_names = [f["name"] for f in fields]
    
    for i, field in enumerate(fields):
        if field.get("depends_on"):
            depends_on = field["depends_on"]
            
            # Check if dependency field comes after this field
            if depends_on in field_names:
                dependency_index = field_names.index(depends_on)
                if dependency_index > i:
                    warnings.append(
                        f"Field '{field['name']}' depends on '{depends_on}' which appears later in the list"
                    )
    
    return warnings