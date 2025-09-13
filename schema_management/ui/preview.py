"""
Schema preview component for schema management UI.
Shows schema structure, generates example forms, and provides export previews.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime

from ..models.schema import Schema, SchemaStatus
from ..models.field import Field, FieldType


def render_schema_preview(schema_data: Dict[str, Any], 
                         preview_mode: str = "form") -> None:
    """
    Render schema preview in different modes
    
    Args:
        schema_data: Complete schema data dictionary
        preview_mode: Preview mode ('form', 'json', 'table', 'docs')
    """
    if not schema_data:
        st.info("📝 Configure schema details and add fields to see preview")
        return
    
    st.subheader("👁️ Schema Preview")
    
    # Preview mode selector
    preview_modes = {
        "form": "📝 Form Preview",
        "json": "🔧 JSON Structure", 
        "table": "📊 Field Table",
        "docs": "📖 Documentation",
        "extraction": "🤖 Extraction Preview"
    }
    
    selected_mode = st.selectbox(
        "Preview Mode",
        options=list(preview_modes.keys()),
        format_func=lambda x: preview_modes[x],
        index=0,
        key="preview_mode"
    )
    
    # Render based on selected mode
    if selected_mode == "form":
        render_form_preview(schema_data)
    elif selected_mode == "json":
        render_json_preview(schema_data)
    elif selected_mode == "table":
        render_table_preview(schema_data)
    elif selected_mode == "docs":
        render_documentation_preview(schema_data)
    elif selected_mode == "extraction":
        render_extraction_preview(schema_data)


def render_form_preview(schema_data: Dict[str, Any]) -> None:
    """Render interactive form preview of the schema"""
    st.subheader("📝 Form Preview")
    st.info("💡 This shows how the schema will appear as a data entry form")
    
    fields = schema_data.get("fields", {})
    
    if not fields:
        st.warning("No fields configured yet. Add fields to see form preview.")
        return
    
    # Schema header
    with st.container():
        st.markdown(f"### {schema_data.get('name', 'Unnamed Schema')}")
        if schema_data.get("description"):
            st.caption(schema_data["description"])
        
        st.divider()
    
    # Render form fields
    form_data = {}
    
    # Sort fields by order if available
    sorted_fields = sort_fields_by_order(fields)
    
    for field_name, field_config in sorted_fields:
        form_data[field_name] = render_form_field_preview(field_name, field_config)
    
    # Form actions preview
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.button("💾 Save", disabled=True, help="Preview only - not functional")
    
    with col2:
        st.button("🔄 Reset", disabled=True, help="Preview only - not functional")
    
    with col3:
        st.button("✅ Validate", disabled=True, help="Preview only - not functional")
    
    # Show collected form data
    if any(form_data.values()):
        with st.expander("📊 Form Data Preview"):
            st.json(form_data)


def render_form_field_preview(field_name: str, field_config: Dict[str, Any]) -> Any:
    """Render individual form field preview"""
    field_type = field_config.get("type", "text")
    display_name = field_config.get("display_name", field_name)
    required = field_config.get("required", False)
    description = field_config.get("description", "")
    placeholder = field_config.get("placeholder", "")
    help_text = field_config.get("help_text", "")
    examples = field_config.get("examples", [])
    
    # Create label with required indicator
    label = f"{display_name} {'*' if required else ''}"
    
    # Create help text with examples
    help_content = help_text
    if examples:
        help_content += f"\n\nExamples: {', '.join(examples[:3])}"
    if description:
        help_content = f"{description}\n\n{help_content}" if help_content else description
    
    # Render based on field type
    if field_type == "text":
        return st.text_input(
            label,
            placeholder=placeholder or f"Enter {display_name.lower()}",
            help=help_content,
            key=f"preview_{field_name}",
            disabled=True
        )
    
    elif field_type == "number":
        return st.number_input(
            label,
            help=help_content,
            key=f"preview_{field_name}",
            disabled=True
        )
    
    elif field_type == "date":
        return st.date_input(
            label,
            help=help_content,
            key=f"preview_{field_name}",
            disabled=True
        )
    
    elif field_type == "email":
        return st.text_input(
            label,
            placeholder=placeholder or "example@email.com",
            help=help_content,
            key=f"preview_{field_name}",
            disabled=True
        )
    
    elif field_type == "phone":
        return st.text_input(
            label,
            placeholder=placeholder or "(555) 123-4567",
            help=help_content,
            key=f"preview_{field_name}",
            disabled=True
        )
    
    elif field_type == "boolean":
        return st.checkbox(
            label,
            help=help_content,
            key=f"preview_{field_name}",
            disabled=True
        )
    
    elif field_type == "select":
        options = ["Option 1", "Option 2", "Option 3"]  # Default options for preview
        return st.selectbox(
            label,
            options=options,
            help=help_content,
            key=f"preview_{field_name}",
            disabled=True
        )
    
    elif field_type == "currency":
        return st.number_input(
            label,
            format="%.2f",
            help=help_content,
            key=f"preview_{field_name}",
            disabled=True
        )
    
    elif field_type == "url":
        return st.text_input(
            label,
            placeholder=placeholder or "https://example.com",
            help=help_content,
            key=f"preview_{field_name}",
            disabled=True
        )
    
    else:  # custom or unknown type
        return st.text_input(
            label,
            placeholder=placeholder or f"Enter {display_name.lower()}",
            help=help_content,
            key=f"preview_{field_name}",
            disabled=True
        )


def render_json_preview(schema_data: Dict[str, Any]) -> None:
    """Render JSON structure preview"""
    st.subheader("🔧 JSON Structure")
    st.info("💡 This shows the schema as it will be stored and used by the system")
    
    # Clean up schema data for preview
    clean_schema = prepare_schema_for_export(schema_data)
    
    # JSON preview with syntax highlighting
    st.code(json.dumps(clean_schema, indent=2, ensure_ascii=False), language="json")
    
    # Schema statistics
    render_json_statistics(clean_schema)
    
    # Download button
    json_str = json.dumps(clean_schema, indent=2, ensure_ascii=False)
    st.download_button(
        label="📥 Download JSON",
        data=json_str,
        file_name=f"{schema_data.get('id', 'schema')}.json",
        mime="application/json"
    )


def render_json_statistics(schema_data: Dict[str, Any]) -> None:
    """Render JSON schema statistics"""
    with st.expander("📊 Schema Statistics"):
        col1, col2, col3, col4 = st.columns(4)
        
        fields = schema_data.get("fields", {})
        
        with col1:
            st.metric("Total Fields", len(fields))
        
        with col2:
            required_count = sum(1 for f in fields.values() if f.get("required"))
            st.metric("Required Fields", required_count)
        
        with col3:
            validation_count = sum(1 for f in fields.values() if f.get("validation_rules"))
            st.metric("With Validation", validation_count)
        
        with col4:
            json_size = len(json.dumps(schema_data))
            st.metric("JSON Size", f"{json_size} chars")


def render_table_preview(schema_data: Dict[str, Any]) -> None:
    """Render tabular field overview"""
    st.subheader("📊 Field Table")
    st.info("💡 Structured overview of all schema fields")
    
    fields = schema_data.get("fields", {})
    
    if not fields:
        st.warning("No fields configured yet.")
        return
    
    # Prepare table data
    table_data = []
    
    for field_name, field_config in fields.items():
        row = {
            "Field Name": field_name,
            "Display Name": field_config.get("display_name", ""),
            "Type": field_config.get("type", "").title(),
            "Required": "✅" if field_config.get("required") else "❌",
            "Validation": "✅" if field_config.get("validation_rules") else "❌",
            "Dependencies": "✅" if field_config.get("depends_on") else "❌",
            "Examples": len(field_config.get("examples", [])),
            "Description": field_config.get("description", "")[:50] + "..." if len(field_config.get("description", "")) > 50 else field_config.get("description", "")
        }
        table_data.append(row)
    
    # Display table
    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True
    )
    
    # Export table data
    if st.button("📊 Export as CSV"):
        import pandas as pd
        df = pd.DataFrame(table_data)
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{schema_data.get('id', 'schema')}_fields.csv",
            mime="text/csv"
        )


def render_documentation_preview(schema_data: Dict[str, Any]) -> None:
    """Render documentation preview"""
    st.subheader("📖 Documentation Preview")
    st.info("💡 Human-readable documentation for this schema")
    
    # Generate documentation
    doc_content = generate_schema_documentation(schema_data)
    
    # Display documentation
    st.markdown(doc_content)
    
    # Download documentation
    if st.button("📝 Export Documentation"):
        st.download_button(
            label="📥 Download Markdown",
            data=doc_content,
            file_name=f"{schema_data.get('id', 'schema')}_documentation.md",
            mime="text/markdown"
        )


def render_extraction_preview(schema_data: Dict[str, Any]) -> None:
    """Render extraction workflow preview"""
    st.subheader("🤖 Extraction Preview")
    st.info("💡 Shows how this schema will be used for document data extraction")
    
    fields = schema_data.get("fields", {})
    
    if not fields:
        st.warning("No fields configured yet.")
        return
    
    # Extraction prompt preview
    with st.expander("📝 Extraction Prompt Preview"):
        prompt = generate_extraction_prompt(schema_data)
        st.code(prompt, language="text")
    
    # Expected output structure
    with st.expander("📊 Expected Output Structure"):
        output_structure = generate_output_structure(schema_data)
        st.code(json.dumps(output_structure, indent=2), language="json")
    
    # Validation workflow
    with st.expander("✅ Validation Workflow"):
        render_validation_workflow_preview(schema_data)


def generate_extraction_prompt(schema_data: Dict[str, Any]) -> str:
    """Generate extraction prompt for the schema"""
    schema_name = schema_data.get("name", "Document")
    schema_description = schema_data.get("description", "")
    fields = schema_data.get("fields", {})
    
    prompt = f"""Extract structured data from {schema_name} documents.

{f"Description: {schema_description}" if schema_description else ""}

Extract the following fields:

"""
    
    for field_name, field_config in fields.items():
        display_name = field_config.get("display_name", field_name)
        field_type = field_config.get("type", "text")
        required = field_config.get("required", False)
        description = field_config.get("description", "")
        examples = field_config.get("examples", [])
        
        prompt += f"- {display_name} ({field_name}): {field_type}"
        if required:
            prompt += " [REQUIRED]"
        if description:
            prompt += f" - {description}"
        if examples:
            prompt += f" (Examples: {', '.join(examples[:2])})"
        prompt += "\n"
    
    prompt += """
Return the extracted data as valid JSON with field names as keys.
Include validation_results for each field with confidence scores.
"""
    
    return prompt


def generate_output_structure(schema_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate expected output structure"""
    fields = schema_data.get("fields", {})
    
    output = {}
    validation_results = {}
    
    for field_name, field_config in fields.items():
        field_type = field_config.get("type", "text")
        examples = field_config.get("examples", [])
        
        # Generate example value based on type
        if field_type == "text":
            output[field_name] = examples[0] if examples else "Sample text"
        elif field_type == "number":
            output[field_name] = float(examples[0]) if examples else 123.45
        elif field_type == "date":
            output[field_name] = examples[0] if examples else "2024-01-01"
        elif field_type == "email":
            output[field_name] = examples[0] if examples else "user@example.com"
        elif field_type == "phone":
            output[field_name] = examples[0] if examples else "(555) 123-4567"
        elif field_type == "boolean":
            output[field_name] = True
        elif field_type == "currency":
            output[field_name] = float(examples[0]) if examples else 99.99
        elif field_type == "url":
            output[field_name] = examples[0] if examples else "https://example.com"
        else:
            output[field_name] = examples[0] if examples else "sample_value"
        
        # Add validation result
        validation_results[field_name] = {
            "valid": True,
            "confidence": 0.95,
            "issues": []
        }
    
    return {
        **output,
        "validation_results": validation_results
    }


def render_validation_workflow_preview(schema_data: Dict[str, Any]) -> None:
    """Render validation workflow preview"""
    fields = schema_data.get("fields", {})
    
    st.write("**Validation Steps:**")
    
    step = 1
    
    # Required field validation
    required_fields = [name for name, config in fields.items() if config.get("required")]
    if required_fields:
        st.write(f"{step}. Check required fields: {', '.join(required_fields)}")
        step += 1
    
    # Type validation
    st.write(f"{step}. Validate field types")
    step += 1
    
    # Custom validation rules
    fields_with_validation = [name for name, config in fields.items() if config.get("validation_rules")]
    if fields_with_validation:
        st.write(f"{step}. Apply custom validation rules for: {', '.join(fields_with_validation)}")
        step += 1
    
    # Dependency validation
    fields_with_deps = [name for name, config in fields.items() if config.get("depends_on")]
    if fields_with_deps:
        st.write(f"{step}. Check field dependencies for: {', '.join(fields_with_deps)}")
        step += 1
    
    # Cross-field validation
    schema_validation_rules = schema_data.get("validation_rules", [])
    if schema_validation_rules:
        st.write(f"{step}. Apply schema-level validation rules")
        step += 1
    
    st.write(f"{step}. Generate validation report")


def generate_schema_documentation(schema_data: Dict[str, Any]) -> str:
    """Generate markdown documentation for schema"""
    schema_name = schema_data.get("name", "Unnamed Schema")
    schema_id = schema_data.get("id", "")
    description = schema_data.get("description", "")
    category = schema_data.get("category", "")
    version = schema_data.get("version", "")
    fields = schema_data.get("fields", {})
    
    doc = f"# {schema_name}\n\n"
    
    if description:
        doc += f"{description}\n\n"
    
    doc += "## Schema Information\n\n"
    doc += f"- **ID**: `{schema_id}`\n"
    doc += f"- **Category**: {category}\n"
    doc += f"- **Version**: {version}\n"
    doc += f"- **Fields**: {len(fields)}\n\n"
    
    if fields:
        doc += "## Fields\n\n"
        
        for field_name, field_config in fields.items():
            display_name = field_config.get("display_name", field_name)
            field_type = field_config.get("type", "text")
            required = field_config.get("required", False)
            description = field_config.get("description", "")
            examples = field_config.get("examples", [])
            validation_rules = field_config.get("validation_rules", [])
            
            doc += f"### {display_name}\n\n"
            doc += f"- **Field Name**: `{field_name}`\n"
            doc += f"- **Type**: {field_type}\n"
            doc += f"- **Required**: {'Yes' if required else 'No'}\n"
            
            if description:
                doc += f"- **Description**: {description}\n"
            
            if examples:
                doc += f"- **Examples**: {', '.join(examples)}\n"
            
            if validation_rules:
                doc += f"- **Validation Rules**: {len(validation_rules)} configured\n"
            
            doc += "\n"
    
    doc += "## Usage\n\n"
    doc += f"This schema is used to extract structured data from {schema_name.lower()} documents. "
    doc += "Fields marked as required must be present in the extracted data.\n\n"
    
    if any(field.get("validation_rules") for field in fields.values()):
        doc += "## Validation\n\n"
        doc += "This schema includes custom validation rules to ensure data quality. "
        doc += "All extracted data will be validated against these rules before acceptance.\n\n"
    
    doc += f"---\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    return doc


def prepare_schema_for_export(schema_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare schema data for clean export"""
    clean_schema = schema_data.copy()
    
    # Remove UI-specific keys
    ui_keys = ["editing", "unsaved_changes", "selected_field"]
    for key in ui_keys:
        clean_schema.pop(key, None)
    
    # Ensure proper structure
    if "fields" not in clean_schema:
        clean_schema["fields"] = {}
    
    if "validation_rules" not in clean_schema:
        clean_schema["validation_rules"] = []
    
    # Add metadata
    clean_schema.setdefault("created_date", datetime.now().isoformat())
    clean_schema.setdefault("updated_date", datetime.now().isoformat())
    clean_schema.setdefault("created_by", "schema_builder")
    clean_schema.setdefault("usage_count", 0)
    
    return clean_schema


def sort_fields_by_order(fields: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """Sort fields by order property or alphabetically"""
    field_items = list(fields.items())
    
    # Try to sort by order property if available
    try:
        return sorted(field_items, key=lambda x: x[1].get("order", 999))
    except (TypeError, KeyError):
        # Fallback to alphabetical sorting
        return sorted(field_items, key=lambda x: x[0])


def render_preview_controls() -> Dict[str, Any]:
    """Render preview control options"""
    with st.sidebar:
        st.subheader("🎛️ Preview Controls")
        
        # Preview options
        show_validation_indicators = st.checkbox(
            "Show Validation Indicators",
            value=True,
            help="Display validation status for each field"
        )
        
        show_field_descriptions = st.checkbox(
            "Show Field Descriptions", 
            value=True,
            help="Display field descriptions in preview"
        )
        
        show_examples = st.checkbox(
            "Show Examples",
            value=True,
            help="Display example values in preview"
        )
        
        # Form preview options
        st.subheader("📝 Form Options")
        
        form_layout = st.selectbox(
            "Layout",
            options=["single_column", "two_column", "compact"],
            format_func=lambda x: x.replace("_", " ").title()
        )
        
        show_field_numbers = st.checkbox(
            "Number Fields",
            value=False,
            help="Show field numbers in form"
        )
        
        return {
            "show_validation_indicators": show_validation_indicators,
            "show_field_descriptions": show_field_descriptions,
            "show_examples": show_examples,
            "form_layout": form_layout,
            "show_field_numbers": show_field_numbers
        }


def render_preview_help() -> None:
    """Render help information for schema preview"""
    with st.expander("ℹ️ Help: Schema Preview"):
        st.markdown("""
        ### Preview Modes
        
        **📝 Form Preview**: See how your schema will appear as a data entry form
        - Interactive form fields based on your configuration
        - Shows required field indicators and help text
        - Demonstrates field types and validation
        
        **🔧 JSON Structure**: View the technical schema structure
        - Complete JSON representation of your schema
        - Includes all fields, validation rules, and metadata
        - Can be exported and imported
        
        **📊 Field Table**: Tabular overview of all fields
        - Structured view of field properties
        - Easy to scan and compare fields
        - Exportable as CSV
        
        **📖 Documentation**: Human-readable documentation
        - Automatically generated documentation
        - Includes field descriptions and usage notes
        - Exportable as Markdown
        
        **🤖 Extraction Preview**: Shows AI extraction workflow
        - Preview of extraction prompts
        - Expected output structure
        - Validation workflow steps
        
        ### Using Previews
        
        - Use Form Preview to test user experience
        - Use JSON Structure for technical validation
        - Use Documentation for sharing with team
        - Use Extraction Preview to understand AI workflow
        """)


def validate_schema_completeness(schema_data: Dict[str, Any]) -> List[str]:
    """Validate schema is complete for preview"""
    issues = []
    
    if not schema_data.get("name"):
        issues.append("Schema name is required")
    
    if not schema_data.get("id"):
        issues.append("Schema ID is required")
    
    fields = schema_data.get("fields", {})
    if not fields:
        issues.append("At least one field is required")
    
    # Check field completeness
    for field_name, field_config in fields.items():
        if not field_config.get("display_name"):
            issues.append(f"Field '{field_name}' missing display name")
        
        if not field_config.get("type"):
            issues.append(f"Field '{field_name}' missing type")
    
    return issues