"""
Validation builder component for schema management UI.
Handles creation and management of field validation rules.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
import re

from ..models.validation_rule import ValidationRule, ValidationRuleType, ValidationSeverity
from ..models.field import FieldType


def render_validation_builder(field_data: Dict[str, Any], 
                             existing_rules: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Render validation rule builder interface
    
    Args:
        field_data: Current field configuration
        existing_rules: List of existing validation rules
        
    Returns:
        Updated list of validation rules
    """
    existing_rules = existing_rules or []
    field_type = field_data.get("type", "text")
    field_name = field_data.get("name", "field")
    
    st.subheader("✅ Validation Rules")
    
    # Initialize session state for validation rules
    if "validation_rules" not in st.session_state:
        st.session_state.validation_rules = existing_rules.copy()
    
    # Display current rules
    render_existing_validation_rules()
    
    st.divider()
    
    # Add new validation rule
    render_add_validation_rule_interface(field_type, field_name)
    
    st.divider()
    
    # Validation suggestions
    render_validation_suggestions(field_type, field_data)
    
    return st.session_state.validation_rules.copy()


def render_existing_validation_rules() -> None:
    """Render list of existing validation rules with edit/delete options"""
    if not st.session_state.validation_rules:
        st.info("📝 No validation rules configured yet. Add rules below to ensure data quality.")
        return
    
    st.write(f"**Current Rules ({len(st.session_state.validation_rules)}):**")
    
    for i, rule in enumerate(st.session_state.validation_rules):
        with st.expander(f"Rule {i+1}: {rule.get('type', 'Unknown').title()}", expanded=False):
            render_validation_rule_editor(i, rule)


def render_validation_rule_editor(index: int, rule: Dict[str, Any]) -> None:
    """Render individual validation rule editor"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Rule details
        st.write("**Type:**", rule.get("type", "Unknown"))
        st.write("**Message:**", rule.get("message", "No message"))
        
        # Parameters
        if rule.get("parameters"):
            st.write("**Parameters:**")
            for key, value in rule["parameters"].items():
                st.write(f"- {key}: {value}")
        
        # Severity
        severity = rule.get("severity", "error")
        st.write("**Severity:**", severity.title())
        
        # Condition (if applicable)
        if rule.get("condition"):
            st.write("**Condition:**", rule["condition"])
    
    with col2:
        # Actions
        if st.button("✏️ Edit", key=f"edit_rule_{index}"):
            st.session_state.editing_rule_index = index
            st.session_state.show_rule_editor = True
            st.rerun()
        
        if st.button("🗑️ Delete", key=f"delete_rule_{index}"):
            st.session_state.validation_rules.pop(index)
            st.success(f"Deleted validation rule {index + 1}")
            st.rerun()
        
        if st.button("📋 Copy", key=f"copy_rule_{index}"):
            copied_rule = rule.copy()
            copied_rule["message"] = f"{copied_rule['message']} (Copy)"
            st.session_state.validation_rules.append(copied_rule)
            st.success("Validation rule copied!")
            st.rerun()


def render_add_validation_rule_interface(field_type: str, field_name: str) -> None:
    """Render interface for adding new validation rules"""
    st.subheader("➕ Add Validation Rule")
    
    # Rule type selection
    applicable_types = get_applicable_validation_types(field_type)
    
    col1, col2 = st.columns(2)
    
    with col1:
        rule_type = st.selectbox(
            "Rule Type",
            options=applicable_types,
            help="Select the type of validation to apply",
            key="new_rule_type"
        )
    
    with col2:
        severity = st.selectbox(
            "Severity",
            options=["error", "warning", "info"],
            help="How critical is this validation rule",
            key="new_rule_severity"
        )
    
    # Rule-specific configuration
    rule_config = render_rule_type_configuration(rule_type, field_type)
    
    # Add rule button
    if st.button("Add Validation Rule", type="primary"):
        if validate_rule_configuration(rule_type, rule_config):
            new_rule = create_validation_rule(rule_type, rule_config, severity)
            st.session_state.validation_rules.append(new_rule)
            st.success(f"Added {rule_type} validation rule!")
            
            # Clear form
            clear_validation_form()
            st.rerun()
        else:
            st.error("Please complete all required fields for this validation rule.")


def render_rule_type_configuration(rule_type: str, field_type: str) -> Dict[str, Any]:
    """Render configuration interface for specific rule type"""
    config = {}
    
    if rule_type == "required":
        config = render_required_rule_config()
    elif rule_type == "length":
        config = render_length_rule_config()
    elif rule_type == "range":
        config = render_range_rule_config()
    elif rule_type == "pattern":
        config = render_pattern_rule_config()
    elif rule_type == "format":
        config = render_format_rule_config(field_type)
    elif rule_type == "options":
        config = render_options_rule_config()
    elif rule_type == "custom":
        config = render_custom_rule_config()
    elif rule_type == "cross_field":
        config = render_cross_field_rule_config()
    elif rule_type == "conditional":
        config = render_conditional_rule_config()
    
    return config


def render_required_rule_config() -> Dict[str, Any]:
    """Render required rule configuration"""
    message = st.text_input(
        "Error Message",
        value="This field is required",
        key="required_message"
    )
    
    return {
        "message": message,
        "parameters": {}
    }


def render_length_rule_config() -> Dict[str, Any]:
    """Render length rule configuration"""
    col1, col2 = st.columns(2)
    
    with col1:
        min_length = st.number_input(
            "Minimum Length",
            min_value=0,
            value=None,
            help="Leave empty for no minimum",
            key="length_min"
        )
    
    with col2:
        max_length = st.number_input(
            "Maximum Length", 
            min_value=1,
            value=None,
            help="Leave empty for no maximum",
            key="length_max"
        )
    
    # Auto-generate message
    if min_length is not None and max_length is not None:
        default_message = f"Length must be between {min_length} and {max_length} characters"
    elif min_length is not None:
        default_message = f"Must be at least {min_length} characters"
    elif max_length is not None:
        default_message = f"Must be no more than {max_length} characters"
    else:
        default_message = "Invalid length"
    
    message = st.text_input(
        "Error Message",
        value=default_message,
        key="length_message"
    )
    
    parameters = {}
    if min_length is not None:
        parameters["min_length"] = min_length
    if max_length is not None:
        parameters["max_length"] = max_length
    
    return {
        "message": message,
        "parameters": parameters
    }


def render_range_rule_config() -> Dict[str, Any]:
    """Render range rule configuration"""
    col1, col2 = st.columns(2)
    
    with col1:
        min_value = st.number_input(
            "Minimum Value",
            value=None,
            help="Leave empty for no minimum",
            key="range_min"
        )
    
    with col2:
        max_value = st.number_input(
            "Maximum Value",
            value=None,
            help="Leave empty for no maximum", 
            key="range_max"
        )
    
    # Auto-generate message
    if min_value is not None and max_value is not None:
        default_message = f"Value must be between {min_value} and {max_value}"
    elif min_value is not None:
        default_message = f"Value must be at least {min_value}"
    elif max_value is not None:
        default_message = f"Value must be no more than {max_value}"
    else:
        default_message = "Invalid value"
    
    message = st.text_input(
        "Error Message",
        value=default_message,
        key="range_message"
    )
    
    parameters = {}
    if min_value is not None:
        parameters["min_value"] = min_value
    if max_value is not None:
        parameters["max_value"] = max_value
    
    return {
        "message": message,
        "parameters": parameters
    }


def render_pattern_rule_config() -> Dict[str, Any]:
    """Render pattern rule configuration"""
    pattern = st.text_input(
        "Regular Expression Pattern",
        placeholder="e.g., ^[A-Z]{2}\\d{6}$ for license plates",
        help="Enter a valid regular expression pattern",
        key="pattern_regex"
    )
    
    # Pattern examples
    with st.expander("📋 Common Patterns"):
        st.code("""
Phone: ^\\+?1?\\d{9,15}$
SSN: ^\\d{3}-\\d{2}-\\d{4}$
License Plate: ^[A-Z]{2}\\d{6}$
ZIP Code: ^\\d{5}(-\\d{4})?$
Credit Card: ^\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}$
        """)
    
    # Test pattern
    if pattern:
        test_value = st.text_input(
            "Test Value (optional)",
            placeholder="Test your pattern here",
            key="pattern_test"
        )
        
        if test_value:
            try:
                match = re.match(pattern, test_value)
                if match:
                    st.success("✅ Pattern matches!")
                else:
                    st.error("❌ Pattern does not match")
            except re.error as e:
                st.error(f"❌ Invalid regex: {e}")
    
    message = st.text_input(
        "Error Message",
        value=f"Value must match pattern: {pattern}" if pattern else "Invalid format",
        key="pattern_message"
    )
    
    return {
        "message": message,
        "parameters": {"pattern": pattern} if pattern else {}
    }


def render_format_rule_config(field_type: str) -> Dict[str, Any]:
    """Render format rule configuration"""
    format_options = {
        "email": "Email address format",
        "phone": "Phone number format", 
        "url": "URL format",
        "date": "Date format",
        "time": "Time format",
        "datetime": "Date and time format",
        "uuid": "UUID format",
        "ipv4": "IPv4 address format",
        "ipv6": "IPv6 address format"
    }
    
    # Pre-select format based on field type
    default_format = field_type if field_type in format_options else "email"
    
    format_type = st.selectbox(
        "Format Type",
        options=list(format_options.keys()),
        index=list(format_options.keys()).index(default_format),
        format_func=lambda x: f"{x} - {format_options[x]}",
        key="format_type"
    )
    
    message = st.text_input(
        "Error Message",
        value=f"Must be a valid {format_type}",
        key="format_message"
    )
    
    return {
        "message": message,
        "parameters": {"format": format_type}
    }


def render_options_rule_config() -> Dict[str, Any]:
    """Render options rule configuration"""
    st.write("**Define allowed values:**")
    
    # Initialize options in session state
    if "validation_options" not in st.session_state:
        st.session_state.validation_options = []
    
    # Add new option
    col1, col2 = st.columns([3, 1])
    with col1:
        new_option = st.text_input("Add Option", key="new_validation_option")
    with col2:
        if st.button("Add", disabled=not new_option):
            if new_option not in st.session_state.validation_options:
                st.session_state.validation_options.append(new_option)
                st.session_state.new_validation_option = ""
                st.rerun()
    
    # Display existing options
    for i, option in enumerate(st.session_state.validation_options):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(f"Option {i+1}", value=option, disabled=True, key=f"validation_option_{i}")
        with col2:
            if st.button("Remove", key=f"remove_validation_option_{i}"):
                st.session_state.validation_options.pop(i)
                st.rerun()
    
    message = st.text_input(
        "Error Message",
        value=f"Value must be one of: {', '.join(st.session_state.validation_options)}" if st.session_state.validation_options else "Invalid option",
        key="options_message"
    )
    
    return {
        "message": message,
        "parameters": {"options": st.session_state.validation_options.copy()}
    }


def render_custom_rule_config() -> Dict[str, Any]:
    """Render custom rule configuration"""
    st.warning("⚠️ Custom validation rules require implementation in the validation service.")
    
    rule_name = st.text_input(
        "Custom Rule Name",
        placeholder="e.g., check_credit_card_validity",
        key="custom_rule_name"
    )
    
    rule_description = st.text_area(
        "Rule Description",
        placeholder="Describe what this custom validation does",
        key="custom_rule_description"
    )
    
    custom_parameters = st.text_area(
        "Parameters (JSON)",
        placeholder='{"param1": "value1", "param2": "value2"}',
        help="Additional parameters for the custom rule in JSON format",
        key="custom_parameters"
    )
    
    message = st.text_input(
        "Error Message",
        value="Custom validation failed",
        key="custom_message"
    )
    
    parameters = {"rule_name": rule_name}
    if custom_parameters:
        try:
            import json
            additional_params = json.loads(custom_parameters)
            parameters.update(additional_params)
        except json.JSONDecodeError:
            st.error("Invalid JSON in parameters")
    
    return {
        "message": message,
        "parameters": parameters
    }


def render_cross_field_rule_config() -> Dict[str, Any]:
    """Render cross-field validation rule configuration"""
    st.info("🔗 Cross-field validation compares this field with other fields in the schema.")
    
    # This would need access to other fields in the schema
    target_field = st.text_input(
        "Target Field",
        placeholder="Name of field to compare with",
        key="cross_field_target"
    )
    
    comparison = st.selectbox(
        "Comparison",
        options=["equals", "not_equals", "greater_than", "less_than", "greater_equal", "less_equal"],
        key="cross_field_comparison"
    )
    
    message = st.text_input(
        "Error Message",
        value=f"This field must {comparison.replace('_', ' ')} {target_field}",
        key="cross_field_message"
    )
    
    return {
        "message": message,
        "parameters": {
            "target_field": target_field,
            "comparison": comparison
        }
    }


def render_conditional_rule_config() -> Dict[str, Any]:
    """Render conditional validation rule configuration"""
    st.info("🔀 Conditional validation only applies when certain conditions are met.")
    
    condition_field = st.text_input(
        "Condition Field",
        placeholder="Field name that determines if this validation applies",
        key="conditional_field"
    )
    
    condition_operator = st.selectbox(
        "Condition",
        options=["==", "!=", ">", "<", ">=", "<=", "contains", "not_contains"],
        key="conditional_operator"
    )
    
    condition_value = st.text_input(
        "Condition Value",
        placeholder="Value to compare against",
        key="conditional_value"
    )
    
    message = st.text_input(
        "Error Message",
        value="Conditional validation failed",
        key="conditional_message"
    )
    
    return {
        "message": message,
        "parameters": {
            "condition_field": condition_field,
            "condition_operator": condition_operator,
            "condition_value": condition_value
        }
    }


def get_applicable_validation_types(field_type: str) -> List[str]:
    """Get list of validation types applicable to field type"""
    base_types = ["required", "custom"]
    
    type_specific = {
        "text": ["length", "pattern", "format"],
        "number": ["range"],
        "email": ["format"],
        "phone": ["format", "pattern"],
        "url": ["format"],
        "date": ["format"],
        "boolean": [],
        "select": ["options"],
        "currency": ["range"],
        "custom": ["pattern", "format"]
    }
    
    applicable = base_types + type_specific.get(field_type, [])
    
    # Add cross-field and conditional for all types
    applicable.extend(["cross_field", "conditional"])
    
    return applicable


def create_validation_rule(rule_type: str, config: Dict[str, Any], severity: str) -> Dict[str, Any]:
    """Create validation rule dictionary from configuration"""
    return {
        "type": rule_type,
        "message": config.get("message", "Validation failed"),
        "parameters": config.get("parameters", {}),
        "severity": severity,
        "enabled": True,
        "created_date": st.session_state.get("current_timestamp")
    }


def validate_rule_configuration(rule_type: str, config: Dict[str, Any]) -> bool:
    """Validate rule configuration is complete"""
    if not config.get("message"):
        return False
    
    parameters = config.get("parameters", {})
    
    if rule_type == "length":
        return "min_length" in parameters or "max_length" in parameters
    elif rule_type == "range":
        return "min_value" in parameters or "max_value" in parameters
    elif rule_type == "pattern":
        return "pattern" in parameters and parameters["pattern"]
    elif rule_type == "format":
        return "format" in parameters and parameters["format"]
    elif rule_type == "options":
        return "options" in parameters and len(parameters["options"]) > 0
    elif rule_type == "custom":
        return "rule_name" in parameters and parameters["rule_name"]
    elif rule_type == "cross_field":
        return "target_field" in parameters and parameters["target_field"]
    elif rule_type == "conditional":
        return all(key in parameters for key in ["condition_field", "condition_operator", "condition_value"])
    
    return True


def clear_validation_form() -> None:
    """Clear validation form fields"""
    keys_to_clear = [
        "new_rule_type", "new_rule_severity", "required_message",
        "length_min", "length_max", "length_message",
        "range_min", "range_max", "range_message", 
        "pattern_regex", "pattern_message", "pattern_test",
        "format_type", "format_message",
        "options_message", "new_validation_option",
        "custom_rule_name", "custom_rule_description", "custom_parameters", "custom_message",
        "cross_field_target", "cross_field_comparison", "cross_field_message",
        "conditional_field", "conditional_operator", "conditional_value", "conditional_message"
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear validation options
    if "validation_options" in st.session_state:
        st.session_state.validation_options = []


def render_validation_suggestions(field_type: str, field_data: Dict[str, Any]) -> None:
    """Render validation rule suggestions"""
    with st.expander("💡 Validation Suggestions"):
        suggestions = get_validation_suggestions(field_type, field_data)
        
        if not suggestions:
            st.info("No specific suggestions for this field type.")
            return
        
        st.write("**Recommended validation rules for this field:**")
        
        for suggestion in suggestions:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{suggestion['type'].title()}**: {suggestion['description']}")
                if suggestion.get("example"):
                    st.caption(f"Example: {suggestion['example']}")
            
            with col2:
                if st.button(f"Add {suggestion['type']}", key=f"suggest_{suggestion['type']}"):
                    # Add suggested rule
                    suggested_rule = create_suggested_rule(suggestion)
                    st.session_state.validation_rules.append(suggested_rule)
                    st.success(f"Added {suggestion['type']} validation!")
                    st.rerun()


def get_validation_suggestions(field_type: str, field_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get validation suggestions for field type"""
    suggestions = []
    
    # Common suggestions
    if field_data.get("required"):
        suggestions.append({
            "type": "required",
            "description": "Ensure this field is always filled",
            "example": "This field is required"
        })
    
    # Type-specific suggestions
    if field_type == "text":
        suggestions.extend([
            {
                "type": "length",
                "description": "Limit text length to reasonable bounds",
                "example": "2-100 characters"
            },
            {
                "type": "pattern",
                "description": "Enforce specific text format",
                "example": "Letters and spaces only"
            }
        ])
    
    elif field_type == "number":
        suggestions.append({
            "type": "range",
            "description": "Ensure numbers are within valid range",
            "example": "Between 0 and 999,999"
        })
    
    elif field_type == "email":
        suggestions.append({
            "type": "format",
            "description": "Validate email address format",
            "example": "Must be valid email format"
        })
    
    elif field_type == "phone":
        suggestions.extend([
            {
                "type": "format",
                "description": "Validate phone number format",
                "example": "Must be valid phone format"
            },
            {
                "type": "pattern",
                "description": "Enforce specific phone format",
                "example": "(555) 123-4567"
            }
        ])
    
    elif field_type == "select":
        suggestions.append({
            "type": "options",
            "description": "Define allowed selection options",
            "example": "Option A, Option B, Option C"
        })
    
    return suggestions


def create_suggested_rule(suggestion: Dict[str, Any]) -> Dict[str, Any]:
    """Create validation rule from suggestion"""
    rule_type = suggestion["type"]
    
    base_rule = {
        "type": rule_type,
        "message": suggestion.get("example", "Validation failed"),
        "severity": "error",
        "enabled": True,
        "parameters": {}
    }
    
    # Add default parameters based on type
    if rule_type == "length":
        base_rule["parameters"] = {"min_length": 2, "max_length": 100}
    elif rule_type == "range":
        base_rule["parameters"] = {"min_value": 0}
    elif rule_type == "format":
        base_rule["parameters"] = {"format": "email"}  # Default, should be customized
    
    return base_rule


def render_validation_builder_help() -> None:
    """Render help information for validation builder"""
    with st.expander("ℹ️ Help: Validation Builder"):
        st.markdown("""
        ### Validation Rules Guide
        
        **Rule Types**:
        
        **Required**: Ensures field is not empty
        - Use for critical fields that must always have values
        
        **Length**: Controls text length
        - Set minimum/maximum character limits
        - Useful for names, descriptions, codes
        
        **Range**: Controls numeric values
        - Set minimum/maximum value limits
        - Perfect for amounts, quantities, percentages
        
        **Pattern**: Uses regular expressions
        - Enforce specific formats (phone, SSN, license plates)
        - Validate custom text patterns
        
        **Format**: Built-in format validation
        - Email, phone, URL, date formats
        - UUID, IP address validation
        
        **Options**: Dropdown/select validation
        - Define allowed values for selection fields
        - Ensures only valid options are chosen
        
        **Cross-field**: Compare with other fields
        - Ensure consistency between related fields
        - Date ranges, value relationships
        
        **Conditional**: Apply rules conditionally
        - Only validate when certain conditions are met
        - Dynamic validation based on other field values
        
        **Custom**: Implement your own validation
        - For complex business rules
        - Requires custom implementation
        
        **Severity Levels**:
        - **Error**: Prevents submission, must be fixed
        - **Warning**: Shows warning but allows submission
        - **Info**: Informational message only
        """)


def render_cross_field_validation(schema_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Render cross-field validation builder
    
    Args:
        schema_fields: List of all fields in schema
        
    Returns:
        List of cross-field validation rules
    """
    st.subheader("🔗 Cross-Field Validation")
    
    if len(schema_fields) < 2:
        st.info("Add more fields to create cross-field validation rules.")
        return []
    
    # Initialize cross-field rules in session state
    if "cross_field_rules" not in st.session_state:
        st.session_state.cross_field_rules = []
    
    # Display existing cross-field rules
    for i, rule in enumerate(st.session_state.cross_field_rules):
        with st.expander(f"Cross-field Rule {i+1}: {rule.get('description', 'Unnamed')}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write("**Fields:**", f"{rule['field1']} {rule['operator']} {rule['field2']}")
                st.write("**Message:**", rule['message'])
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_cross_rule_{i}"):
                    st.session_state.cross_field_rules.pop(i)
                    st.rerun()
    
    # Add new cross-field rule
    st.write("**Add Cross-Field Rule:**")
    
    col1, col2, col3 = st.columns(3)
    
    field_names = [f["name"] for f in schema_fields]
    
    with col1:
        field1 = st.selectbox("First Field", options=field_names, key="cross_field1")
    
    with col2:
        operator = st.selectbox(
            "Relationship",
            options=["must_equal", "must_not_equal", "must_be_greater", "must_be_less", "must_be_after", "must_be_before"],
            key="cross_operator"
        )
    
    with col3:
        field2 = st.selectbox("Second Field", options=field_names, key="cross_field2")
    
    message = st.text_input(
        "Error Message",
        value=f"{field1} {operator.replace('_', ' ')} {field2}",
        key="cross_message"
    )
    
    if st.button("Add Cross-Field Rule"):
        if field1 != field2:
            new_rule = {
                "field1": field1,
                "operator": operator,
                "field2": field2,
                "message": message,
                "description": f"{field1} {operator.replace('_', ' ')} {field2}"
            }
            st.session_state.cross_field_rules.append(new_rule)
            st.success("Cross-field rule added!")
            st.rerun()
        else:
            st.error("Please select different fields for comparison.")
    
    return st.session_state.cross_field_rules.copy()