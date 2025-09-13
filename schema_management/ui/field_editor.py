"""
Field editor component for schema management UI.
Handles individual field configuration: type, validation, dependencies, etc.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
import re

from ..models.field import Field, FieldType, FieldStatus
from ..models.validation_rule import ValidationRule, ValidationRuleType, ValidationSeverity
from ..services.field_service import FieldService
from ..services.validation_service import ValidationService


def render_field_editor(field_data: Dict[str, Any] = None, 
                       existing_fields: List[Dict[str, Any]] = None,
                       template_suggestions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Render field editor interface
    
    Args:
        field_data: Current field data (None for new field)
        existing_fields: List of existing fields in schema
        template_suggestions: List of suggested field templates
        
    Returns:
        Dictionary with updated field configuration
    """
    existing_fields = existing_fields or []
    template_suggestions = template_suggestions or []
    
    # Initialize defaults
    defaults = {
        "name": "",
        "display_name": "",
        "type": "text",
        "required": False,
        "description": "",
        "placeholder": "",
        "help_text": "",
        "examples": [],
        "validation_rules": [],
        "depends_on": None,
        "condition": None,
        "condition_value": None
    }
    
    # Use existing data if available
    if field_data:
        defaults.update({k: v for k, v in field_data.items() if k in defaults})
    
    st.subheader("⚙️ Field Configuration")
    
    # Template suggestions (if available)
    if template_suggestions:
        render_template_suggestions(template_suggestions)
    
    with st.container():
        # Basic field information
        render_basic_field_info(defaults, existing_fields)
        
        st.divider()
        
        # Field type and configuration
        field_type = render_field_type_selection(defaults["type"])
        
        st.divider()
        
        # Field properties
        field_props = render_field_properties(defaults)
        
        st.divider()
        
        # Examples
        examples = render_field_examples(defaults["examples"])
        
        st.divider()
        
        # Dependencies
        dependency_config = render_field_dependencies(defaults, existing_fields)
        
        st.divider()
        
        # Validation rules
        validation_rules = render_field_validation_preview(defaults.get("validation_rules", []))
    
    # Validation
    st.divider()
    render_field_validation_status(
        st.session_state.get("field_name", ""),
        st.session_state.get("field_display_name", ""),
        field_type,
        existing_fields
    )
    
    # Collect all field data
    field_result = {
        "name": st.session_state.get("field_name", ""),
        "display_name": st.session_state.get("field_display_name", ""),
        "type": field_type,
        "required": field_props["required"],
        "description": field_props["description"],
        "placeholder": field_props["placeholder"],
        "help_text": field_props["help_text"],
        "examples": examples,
        "validation_rules": validation_rules,
        "depends_on": dependency_config["depends_on"],
        "condition": dependency_config["condition"],
        "condition_value": dependency_config["condition_value"]
    }
    
    return field_result


def render_template_suggestions(suggestions: List[Dict[str, Any]]) -> None:
    """Render field template suggestions"""
    with st.expander("💡 Template Suggestions"):
        st.write("**Suggested templates based on your field:**")
        
        cols = st.columns(min(len(suggestions), 3))
        
        for i, suggestion in enumerate(suggestions[:3]):
            with cols[i]:
                if st.button(
                    f"📋 {suggestion['name']}", 
                    help=suggestion.get('description', ''),
                    key=f"template_suggestion_{i}"
                ):
                    # Apply template to current field
                    apply_template_to_field(suggestion)


def apply_template_to_field(template: Dict[str, Any]) -> None:
    """Apply template data to current field editor"""
    st.session_state.field_name = template.get("name", "")
    st.session_state.field_display_name = template.get("display_name", "")
    st.session_state.field_type = template.get("type", "text")
    st.session_state.field_required = template.get("required", False)
    st.session_state.field_description = template.get("description", "")
    st.session_state.field_placeholder = template.get("placeholder", "")
    st.session_state.field_help_text = template.get("help_text", "")
    
    st.success(f"Applied template: {template['name']}")
    st.rerun()


def render_basic_field_info(defaults: Dict[str, Any], existing_fields: List[Dict[str, Any]]) -> None:
    """Render basic field information inputs"""
    col1, col2 = st.columns(2)
    
    with col1:
        field_name = st.text_input(
            "Field Name *",
            value=defaults["name"],
            placeholder="e.g., customer_name, invoice_date",
            help="Internal field name (must be valid Python identifier)",
            key="field_name"
        )
        
        # Auto-generate display name from field name
        if field_name and not st.session_state.get("manual_display_name", False):
            auto_display_name = generate_display_name(field_name)
            if "field_display_name" not in st.session_state or st.session_state.get("auto_generated_display_name", True):
                st.session_state.field_display_name = auto_display_name
                st.session_state.auto_generated_display_name = True
    
    with col2:
        display_name = st.text_input(
            "Display Name *",
            value=st.session_state.get("field_display_name", defaults["display_name"]),
            placeholder="Human-readable name",
            help="Name shown to users in the interface",
            key="field_display_name_input"
        )
        
        manual_display = st.checkbox(
            "Manual Display Name",
            value=st.session_state.get("manual_display_name", False),
            help="Check to manually set the display name",
            key="manual_display_name"
        )
        
        if manual_display:
            st.session_state.auto_generated_display_name = False
        
        # Update session state
        if manual_display or display_name != st.session_state.get("field_display_name", ""):
            st.session_state.field_display_name = display_name


def generate_display_name(field_name: str) -> str:
    """Generate display name from field name"""
    if not field_name:
        return ""
    
    # Split on underscores and capitalize each word
    words = field_name.replace("_", " ").split()
    return " ".join(word.capitalize() for word in words)


def render_field_type_selection(current_type: str) -> str:
    """Render field type selection with type-specific options"""
    # Field type selection
    field_types = [ft.value for ft in FieldType]
    type_index = field_types.index(current_type) if current_type in field_types else 0
    
    field_type = st.selectbox(
        "Field Type *",
        options=field_types,
        index=type_index,
        help="The type of data this field will contain",
        key="field_type"
    )
    
    # Type-specific configuration
    render_type_specific_config(field_type)
    
    return field_type


def render_type_specific_config(field_type: str) -> None:
    """Render type-specific configuration options"""
    if field_type == "select":
        st.subheader("Select Options")
        render_select_options()
    
    elif field_type == "number":
        st.subheader("Number Configuration")
        render_number_config()
    
    elif field_type == "date":
        st.subheader("Date Configuration")
        render_date_config()
    
    elif field_type == "custom":
        st.subheader("Custom Type Configuration")
        render_custom_type_config()


def render_select_options() -> None:
    """Render select field options configuration"""
    st.write("**Available Options:**")
    
    # Get existing options from session state
    if "select_options" not in st.session_state:
        st.session_state.select_options = []
    
    # Add new option
    col1, col2 = st.columns([3, 1])
    with col1:
        new_option = st.text_input("Add Option", key="new_select_option")
    with col2:
        if st.button("Add", disabled=not new_option):
            if new_option not in st.session_state.select_options:
                st.session_state.select_options.append(new_option)
                st.session_state.new_select_option = ""
                st.rerun()
    
    # Display existing options
    for i, option in enumerate(st.session_state.select_options):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(f"Option {i+1}", value=option, disabled=True, key=f"option_{i}")
        with col2:
            if st.button("Remove", key=f"remove_option_{i}"):
                st.session_state.select_options.pop(i)
                st.rerun()


def render_number_config() -> None:
    """Render number field configuration"""
    col1, col2 = st.columns(2)
    
    with col1:
        decimal_places = st.number_input(
            "Decimal Places",
            min_value=0,
            max_value=10,
            value=2,
            help="Number of decimal places to display",
            key="number_decimal_places"
        )
    
    with col2:
        currency_format = st.checkbox(
            "Currency Format",
            help="Display as currency with appropriate symbols",
            key="number_currency_format"
        )


def render_date_config() -> None:
    """Render date field configuration"""
    date_format = st.selectbox(
        "Date Format",
        options=["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "DD-MM-YYYY"],
        help="Expected date format in documents",
        key="date_format"
    )
    
    allow_time = st.checkbox(
        "Include Time",
        help="Allow time component in addition to date",
        key="date_include_time"
    )


def render_custom_type_config() -> None:
    """Render custom type configuration"""
    custom_type_name = st.text_input(
        "Custom Type Name",
        placeholder="e.g., SSN, License Plate",
        help="Name for your custom field type",
        key="custom_type_name"
    )
    
    custom_validation_pattern = st.text_input(
        "Validation Pattern (Regex)",
        placeholder="e.g., \\d{3}-\\d{2}-\\d{4}",
        help="Regular expression pattern for validation",
        key="custom_validation_pattern"
    )


def render_field_properties(defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Render field properties section"""
    st.subheader("📝 Field Properties")
    
    # Required checkbox
    required = st.checkbox(
        "Required Field",
        value=defaults["required"],
        help="Whether this field must be filled",
        key="field_required"
    )
    
    # Description
    description = st.text_area(
        "Description",
        value=defaults["description"],
        placeholder="Explain what this field represents and how it should be filled",
        help="Detailed description for users and documentation",
        height=80,
        key="field_description"
    )
    
    # UI Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        placeholder = st.text_input(
            "Placeholder Text",
            value=defaults["placeholder"],
            placeholder="Text shown when field is empty",
            help="Placeholder text displayed in the input field",
            key="field_placeholder"
        )
    
    with col2:
        help_text = st.text_input(
            "Help Text",
            value=defaults["help_text"],
            placeholder="Additional guidance for users",
            help="Help text shown next to the field",
            key="field_help_text"
        )
    
    return {
        "required": required,
        "description": description,
        "placeholder": placeholder,
        "help_text": help_text
    }


def render_field_examples(current_examples: List[str]) -> List[str]:
    """Render field examples section"""
    st.subheader("💡 Examples")
    
    # Initialize session state for examples
    if "field_examples" not in st.session_state:
        st.session_state.field_examples = current_examples.copy()
    
    # Add new example
    col1, col2 = st.columns([3, 1])
    with col1:
        new_example = st.text_input("Add Example", key="new_field_example")
    with col2:
        if st.button("Add Example", disabled=not new_example):
            if new_example not in st.session_state.field_examples:
                st.session_state.field_examples.append(new_example)
                st.session_state.new_field_example = ""
                st.rerun()
    
    # Display existing examples
    for i, example in enumerate(st.session_state.field_examples):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(f"Example {i+1}", value=example, disabled=True, key=f"example_{i}")
        with col2:
            if st.button("Remove", key=f"remove_example_{i}"):
                st.session_state.field_examples.pop(i)
                st.rerun()
    
    return st.session_state.field_examples.copy()


def render_field_dependencies(defaults: Dict[str, Any], existing_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Render field dependencies section"""
    st.subheader("🔗 Field Dependencies")
    
    if not existing_fields:
        st.info("No other fields available for dependencies. Add more fields to create dependencies.")
        return {"depends_on": None, "condition": None, "condition_value": None}
    
    # Enable dependency
    enable_dependency = st.checkbox(
        "This field depends on another field",
        value=defaults["depends_on"] is not None,
        key="enable_field_dependency"
    )
    
    if not enable_dependency:
        return {"depends_on": None, "condition": None, "condition_value": None}
    
    # Dependency configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Field to depend on
        field_names = [f["name"] for f in existing_fields]
        depends_on_index = 0
        if defaults["depends_on"] and defaults["depends_on"] in field_names:
            depends_on_index = field_names.index(defaults["depends_on"])
        
        depends_on = st.selectbox(
            "Depends On Field",
            options=field_names,
            index=depends_on_index,
            key="field_depends_on"
        )
    
    with col2:
        # Condition
        conditions = ["==", "!=", ">", "<", ">=", "<=", "contains", "not_contains"]
        condition_index = 0
        if defaults["condition"] and defaults["condition"] in conditions:
            condition_index = conditions.index(defaults["condition"])
        
        condition = st.selectbox(
            "Condition",
            options=conditions,
            index=condition_index,
            key="field_condition"
        )
    
    with col3:
        # Condition value
        condition_value = st.text_input(
            "Value",
            value=str(defaults["condition_value"]) if defaults["condition_value"] is not None else "",
            key="field_condition_value"
        )
    
    # Dependency explanation
    if depends_on and condition and condition_value:
        st.info(f"💡 This field will be shown/required when '{depends_on}' {condition} '{condition_value}'")
    
    return {
        "depends_on": depends_on,
        "condition": condition,
        "condition_value": condition_value if condition_value else None
    }


def render_field_validation_preview(validation_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Render validation rules preview"""
    st.subheader("✅ Validation Rules")
    
    if not validation_rules:
        st.info("No validation rules configured. Add rules in the Validation tab.")
        return []
    
    # Display existing validation rules
    for i, rule in enumerate(validation_rules):
        with st.expander(f"Rule {i+1}: {rule.get('type', 'Unknown')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Type:**", rule.get("type", "Unknown"))
                st.write("**Message:**", rule.get("message", "No message"))
            
            with col2:
                if rule.get("parameters"):
                    st.write("**Parameters:**")
                    for key, value in rule["parameters"].items():
                        st.write(f"- {key}: {value}")
    
    return validation_rules


def render_field_validation_status(field_name: str, display_name: str, field_type: str, existing_fields: List[Dict[str, Any]]) -> None:
    """Render field validation status"""
    issues = validate_field_configuration(field_name, display_name, field_type, existing_fields)
    
    if issues:
        st.subheader("⚠️ Field Validation Issues")
        
        for issue in issues:
            if issue["severity"] == "error":
                st.error(f"**{issue['field']}**: {issue['message']}")
            elif issue["severity"] == "warning":
                st.warning(f"**{issue['field']}**: {issue['message']}")
            else:
                st.info(f"**{issue['field']}**: {issue['message']}")
    else:
        st.success("✅ Field configuration is valid")


def validate_field_configuration(field_name: str, display_name: str, field_type: str, existing_fields: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Validate field configuration"""
    issues = []
    
    # Validate field name
    if not field_name:
        issues.append({
            "field": "Name",
            "message": "Field name is required",
            "severity": "error"
        })
    elif not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field_name):
        issues.append({
            "field": "Name",
            "message": "Field name must be a valid Python identifier",
            "severity": "error"
        })
    elif len(field_name) < 2:
        issues.append({
            "field": "Name",
            "message": "Field name must be at least 2 characters",
            "severity": "error"
        })
    elif field_name in [f["name"] for f in existing_fields]:
        issues.append({
            "field": "Name",
            "message": "Field name already exists in this schema",
            "severity": "error"
        })
    
    # Validate display name
    if not display_name:
        issues.append({
            "field": "Display Name",
            "message": "Display name is required",
            "severity": "error"
        })
    elif len(display_name) < 2:
        issues.append({
            "field": "Display Name",
            "message": "Display name must be at least 2 characters",
            "severity": "error"
        })
    
    # Validate field type
    if not field_type:
        issues.append({
            "field": "Type",
            "message": "Field type is required",
            "severity": "error"
        })
    
    return issues


def render_field_editor_help() -> None:
    """Render help information for field editor"""
    with st.expander("ℹ️ Help: Field Editor"):
        st.markdown("""
        ### Field Configuration Guide
        
        **Field Name**: The internal identifier for the field. Must be a valid Python identifier (letters, numbers, underscores only, cannot start with number).
        
        **Display Name**: The user-friendly name shown in the interface. Can contain spaces and special characters.
        
        **Field Types**:
        - **Text**: General text input
        - **Number**: Numeric values (integer or decimal)
        - **Date**: Date values with format validation
        - **Email**: Email addresses with validation
        - **Phone**: Phone numbers with format checking
        - **Boolean**: True/false or yes/no values
        - **Select**: Dropdown with predefined options
        - **Currency**: Monetary amounts with currency formatting
        - **URL**: Web addresses with validation
        - **Custom**: Define your own type with custom validation
        
        **Required Fields**: Mark fields as required to ensure they are always filled during extraction.
        
        **Examples**: Provide sample values to help users understand the expected format.
        
        **Dependencies**: Make fields conditional based on values of other fields.
        
        **Validation Rules**: Add specific validation rules in the Validation tab to ensure data quality.
        """)


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