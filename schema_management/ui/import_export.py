"""
Import/export interface for schema management UI.
Handles schema import/export, template management, and data migration.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
import json
import csv
import io
from datetime import datetime
import zipfile
import tempfile

from ..models.schema import Schema, SchemaStatus
from ..models.field import Field
from ..models.templates import FieldTemplate, SchemaTemplate
from ..services.schema_service import SchemaService
from ..services.template_service import TemplateService


def render_import_export_interface(current_schema: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Render import/export interface
    
    Args:
        current_schema: Current schema data for export
        
    Returns:
        Action result dictionary
    """
    st.subheader("📁 Import & Export")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Import", 
        "📤 Export", 
        "📋 Templates", 
        "🔄 Migration"
    ])
    
    with tab1:
        return render_import_interface()
    
    with tab2:
        return render_export_interface(current_schema)
    
    with tab3:
        return render_template_interface()
    
    with tab4:
        return render_migration_interface()


def render_import_interface() -> Dict[str, Any]:
    """Render schema import interface"""
    st.subheader("📥 Import Schema")
    
    import_type = st.selectbox(
        "Import Source",
        options=["json_file", "json_text", "csv_fields", "template", "url"],
        format_func=lambda x: {
            "json_file": "JSON File",
            "json_text": "JSON Text",
            "csv_fields": "CSV Fields",
            "template": "Schema Template", 
            "url": "URL/API"
        }[x]
    )
    
    if import_type == "json_file":
        return render_json_file_import()
    elif import_type == "json_text":
        return render_json_text_import()
    elif import_type == "csv_fields":
        return render_csv_fields_import()
    elif import_type == "template":
        return render_template_import()
    elif import_type == "url":
        return render_url_import()
    
    return {"action": None}


def render_json_file_import() -> Dict[str, Any]:
    """Render JSON file import interface"""
    st.write("**Upload JSON Schema File**")
    
    uploaded_file = st.file_uploader(
        "Choose JSON file",
        type=['json'],
        help="Upload a JSON schema file exported from this system or compatible format"
    )
    
    if uploaded_file is not None:
        try:
            # Read and parse JSON
            content = uploaded_file.read().decode('utf-8')
            schema_data = json.loads(content)
            
            # Validate schema structure
            validation_issues = validate_imported_schema(schema_data)
            
            if validation_issues:
                st.error("⚠️ Schema validation issues found:")
                for issue in validation_issues:
                    st.write(f"- {issue}")
                
                fix_issues = st.checkbox("Attempt to fix issues automatically")
                if fix_issues:
                    schema_data = fix_schema_issues(schema_data, validation_issues)
                    st.success("✅ Issues automatically fixed")
            
            # Preview imported schema
            with st.expander("👁️ Preview Imported Schema"):
                render_import_preview(schema_data)
            
            # Import options
            col1, col2 = st.columns(2)
            
            with col1:
                new_id = st.text_input(
                    "New Schema ID (optional)",
                    placeholder="Leave empty to use original ID",
                    help="Specify new ID to avoid conflicts"
                )
            
            with col2:
                import_mode = st.selectbox(
                    "Import Mode",
                    options=["replace", "merge", "new_version"],
                    format_func=lambda x: {
                        "replace": "Replace if exists",
                        "merge": "Merge with existing",
                        "new_version": "Create new version"
                    }[x]
                )
            
            if st.button("📥 Import Schema", type="primary"):
                return {
                    "action": "import_schema",
                    "source": "json_file",
                    "data": schema_data,
                    "new_id": new_id,
                    "mode": import_mode,
                    "filename": uploaded_file.name
                }
        
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON file: {e}")
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
    
    return {"action": None}


def render_json_text_import() -> Dict[str, Any]:
    """Render JSON text import interface"""
    st.write("**Paste JSON Schema**")
    
    json_text = st.text_area(
        "JSON Schema Content",
        height=300,
        placeholder="Paste your JSON schema here...",
        help="Paste JSON schema content directly"
    )
    
    if json_text:
        try:
            schema_data = json.loads(json_text)
            
            # Validate and preview
            validation_issues = validate_imported_schema(schema_data)
            
            if validation_issues:
                st.warning("⚠️ Validation issues found - see preview for details")
            
            with st.expander("👁️ Preview Schema"):
                render_import_preview(schema_data)
            
            if st.button("📥 Import from Text", type="primary"):
                return {
                    "action": "import_schema",
                    "source": "json_text", 
                    "data": schema_data
                }
        
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {e}")
    
    return {"action": None}


def render_csv_fields_import() -> Dict[str, Any]:
    """Render CSV fields import interface"""
    st.write("**Import Fields from CSV**")
    st.info("💡 Use this to bulk import field definitions from a spreadsheet")
    
    # CSV template download
    if st.button("📄 Download CSV Template"):
        template_csv = generate_csv_template()
        st.download_button(
            label="📥 Download Template",
            data=template_csv,
            file_name="field_template.csv",
            mime="text/csv"
        )
    
    # CSV file upload
    uploaded_csv = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="Upload CSV file with field definitions"
    )
    
    if uploaded_csv is not None:
        try:
            # Read CSV
            content = uploaded_csv.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content))
            fields_data = list(csv_reader)
            
            # Preview fields
            st.write(f"**Found {len(fields_data)} fields:**")
            
            preview_data = []
            for field_data in fields_data[:5]:  # Show first 5
                preview_data.append({
                    "Name": field_data.get("name", ""),
                    "Display Name": field_data.get("display_name", ""),
                    "Type": field_data.get("type", ""),
                    "Required": field_data.get("required", "")
                })
            
            st.dataframe(preview_data, use_container_width=True)
            
            if len(fields_data) > 5:
                st.caption(f"... and {len(fields_data) - 5} more fields")
            
            # Schema info for fields
            schema_name = st.text_input("Schema Name", value="Imported Schema")
            schema_id = st.text_input("Schema ID", value="imported_schema")
            
            if st.button("📥 Import Fields", type="primary"):
                return {
                    "action": "import_fields",
                    "source": "csv",
                    "fields_data": fields_data,
                    "schema_name": schema_name,
                    "schema_id": schema_id
                }
        
        except Exception as e:
            st.error(f"❌ Error reading CSV: {e}")
    
    return {"action": None}


def render_template_import() -> Dict[str, Any]:
    """Render template-based import interface"""
    st.write("**Import from Template**")
    st.info("💡 Use predefined templates to quickly create schemas")
    
    # Template categories
    template_categories = [
        "Government Documents",
        "Business Documents", 
        "Financial Documents",
        "Healthcare Documents",
        "Educational Documents",
        "Custom Templates"
    ]
    
    selected_category = st.selectbox("Template Category", template_categories)
    
    # Mock templates for demo (in real implementation, load from template service)
    templates = get_templates_by_category(selected_category)
    
    if templates:
        selected_template = st.selectbox(
            "Available Templates",
            options=templates,
            format_func=lambda x: f"{x['name']} - {x['description']}"
        )
        
        if selected_template:
            # Template preview
            with st.expander("👁️ Template Preview"):
                st.write(f"**{selected_template['name']}**")
                st.write(selected_template['description'])
                st.write(f"**Fields:** {len(selected_template['fields'])}")
                
                for field in selected_template['fields'][:3]:
                    st.write(f"- {field['display_name']} ({field['type']})")
                
                if len(selected_template['fields']) > 3:
                    st.write(f"... and {len(selected_template['fields']) - 3} more fields")
            
            # Customization options
            customize_template = st.checkbox("Customize template before import")
            
            if customize_template:
                new_name = st.text_input("Schema Name", value=selected_template['name'])
                new_id = st.text_input("Schema ID", value=selected_template.get('id', ''))
                new_description = st.text_area("Description", value=selected_template.get('description', ''))
            
            if st.button("📥 Import Template", type="primary"):
                template_data = selected_template.copy()
                
                if customize_template:
                    template_data.update({
                        "name": new_name,
                        "id": new_id,
                        "description": new_description
                    })
                
                return {
                    "action": "import_template",
                    "template_data": template_data,
                    "category": selected_category
                }
    else:
        st.info(f"No templates available for {selected_category}")
    
    return {"action": None}


def render_url_import() -> Dict[str, Any]:
    """Render URL/API import interface"""
    st.write("**Import from URL or API**")
    st.warning("⚠️ Only import from trusted sources")
    
    url = st.text_input(
        "Schema URL",
        placeholder="https://example.com/schema.json",
        help="URL to a JSON schema file"
    )
    
    # Authentication options
    with st.expander("🔐 Authentication (if required)"):
        auth_type = st.selectbox(
            "Authentication Type",
            options=["none", "bearer_token", "api_key", "basic_auth"]
        )
        
        if auth_type == "bearer_token":
            token = st.text_input("Bearer Token", type="password")
        elif auth_type == "api_key":
            api_key = st.text_input("API Key", type="password")
            header_name = st.text_input("Header Name", value="X-API-Key")
        elif auth_type == "basic_auth":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
    
    if url and st.button("🌐 Import from URL"):
        return {
            "action": "import_url",
            "url": url,
            "auth_type": auth_type
        }
    
    return {"action": None}


def render_export_interface(current_schema: Dict[str, Any] = None) -> Dict[str, Any]:
    """Render schema export interface"""
    st.subheader("📤 Export Schema")
    
    if not current_schema:
        st.info("💡 Configure and save a schema to enable export options")
        return {"action": None}
    
    export_format = st.selectbox(
        "Export Format",
        options=["json", "csv", "yaml", "documentation", "template", "backup"],
        format_func=lambda x: {
            "json": "JSON Schema",
            "csv": "CSV Fields List",
            "yaml": "YAML Format",
            "documentation": "Documentation (Markdown)",
            "template": "Reusable Template",
            "backup": "Complete Backup (ZIP)"
        }[x]
    )
    
    # Export options
    with st.expander("⚙️ Export Options"):
        include_metadata = st.checkbox("Include metadata", value=True)
        include_examples = st.checkbox("Include field examples", value=True)
        include_validation = st.checkbox("Include validation rules", value=True)
        minify_json = st.checkbox("Minify JSON", value=False) if export_format == "json" else False
    
    export_options = {
        "include_metadata": include_metadata,
        "include_examples": include_examples,
        "include_validation": include_validation,
        "minify_json": minify_json
    }
    
    # Generate export preview
    export_data = generate_export_data(current_schema, export_format, export_options)
    
    # Preview
    with st.expander("👁️ Export Preview"):
        if export_format == "json":
            st.code(export_data, language="json")
        elif export_format == "yaml":
            st.code(export_data, language="yaml")
        elif export_format == "documentation":
            st.markdown(export_data)
        elif export_format == "csv":
            st.text(export_data)
        else:
            st.text(str(export_data)[:1000] + "..." if len(str(export_data)) > 1000 else str(export_data))
    
    # Export button
    file_extension = {
        "json": "json",
        "csv": "csv", 
        "yaml": "yaml",
        "documentation": "md",
        "template": "json",
        "backup": "zip"
    }[export_format]
    
    filename = f"{current_schema.get('id', 'schema')}.{file_extension}"
    
    if export_format == "backup":
        # Special handling for backup
        if st.button("📦 Create Backup", type="primary"):
            return {
                "action": "create_backup",
                "schema": current_schema,
                "options": export_options
            }
    else:
        st.download_button(
            label=f"📥 Download {export_format.upper()}",
            data=export_data,
            file_name=filename,
            mime=get_mime_type(export_format),
            type="primary"
        )
    
    return {"action": None}


def render_template_interface() -> Dict[str, Any]:
    """Render template management interface"""
    st.subheader("📋 Template Management")
    
    template_action = st.selectbox(
        "Template Action",
        options=["browse", "create", "export", "import"],
        format_func=lambda x: {
            "browse": "Browse Templates",
            "create": "Create Template",
            "export": "Export Templates", 
            "import": "Import Templates"
        }[x]
    )
    
    if template_action == "browse":
        return render_template_browser()
    elif template_action == "create":
        return render_template_creator()
    elif template_action == "export":
        return render_template_exporter()
    elif template_action == "import":
        return render_template_importer()
    
    return {"action": None}


def render_template_browser() -> Dict[str, Any]:
    """Render template browser"""
    st.write("**Available Templates**")
    
    # Mock template data
    templates = [
        {
            "id": "invoice_template",
            "name": "Standard Invoice",
            "category": "Business",
            "fields": 8,
            "usage_count": 25,
            "description": "Standard business invoice template"
        },
        {
            "id": "id_card_template", 
            "name": "ID Card",
            "category": "Government",
            "fields": 6,
            "usage_count": 12,
            "description": "Government-issued ID card template"
        }
    ]
    
    for template in templates:
        with st.expander(f"📋 {template['name']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Category:** {template['category']}")
                st.write(f"**Fields:** {template['fields']}")
                st.write(f"**Usage:** {template['usage_count']} times")
            
            with col2:
                if st.button(f"Use Template", key=f"use_{template['id']}"):
                    return {
                        "action": "use_template",
                        "template_id": template['id']
                    }
            
            st.write(template['description'])
    
    return {"action": None}


def render_template_creator() -> Dict[str, Any]:
    """Render template creation interface"""
    st.write("**Create New Template**")
    st.info("💡 Create reusable templates from your schemas")
    
    template_name = st.text_input("Template Name")
    template_description = st.text_area("Description")
    template_category = st.selectbox(
        "Category",
        options=["Business", "Government", "Healthcare", "Education", "Custom"]
    )
    
    # Template source
    source_type = st.selectbox(
        "Create From",
        options=["current_schema", "blank", "existing_template"],
        format_func=lambda x: {
            "current_schema": "Current Schema",
            "blank": "Blank Template",
            "existing_template": "Copy Existing Template"
        }[x]
    )
    
    if st.button("🏗️ Create Template", type="primary"):
        return {
            "action": "create_template",
            "name": template_name,
            "description": template_description,
            "category": template_category,
            "source_type": source_type
        }
    
    return {"action": None}


def render_template_exporter() -> Dict[str, Any]:
    """Render template export interface"""
    st.write("**Export Templates**")
    
    # Template selection
    available_templates = ["Template 1", "Template 2", "Template 3"]  # Mock data
    selected_templates = st.multiselect("Select Templates", available_templates)
    
    if selected_templates:
        export_format = st.selectbox(
            "Export Format",
            options=["json", "zip", "yaml"]
        )
        
        if st.button("📤 Export Selected"):
            return {
                "action": "export_templates",
                "templates": selected_templates,
                "format": export_format
            }
    
    return {"action": None}


def render_template_importer() -> Dict[str, Any]:
    """Render template import interface"""
    st.write("**Import Templates**")
    
    uploaded_file = st.file_uploader(
        "Choose template file",
        type=['json', 'zip', 'yaml']
    )
    
    if uploaded_file and st.button("📥 Import Templates"):
        return {
            "action": "import_templates",
            "file": uploaded_file
        }
    
    return {"action": None}


def render_migration_interface() -> Dict[str, Any]:
    """Render data migration interface"""
    st.subheader("🔄 Data Migration")
    
    migration_type = st.selectbox(
        "Migration Type",
        options=["version_upgrade", "format_conversion", "system_migration", "backup_restore"],
        format_func=lambda x: {
            "version_upgrade": "Version Upgrade",
            "format_conversion": "Format Conversion",
            "system_migration": "System Migration",
            "backup_restore": "Backup & Restore"
        }[x]
    )
    
    if migration_type == "version_upgrade":
        return render_version_upgrade_interface()
    elif migration_type == "format_conversion":
        return render_format_conversion_interface()
    elif migration_type == "system_migration":
        return render_system_migration_interface()
    elif migration_type == "backup_restore":
        return render_backup_restore_interface()
    
    return {"action": None}


def render_version_upgrade_interface() -> Dict[str, Any]:
    """Render version upgrade interface"""
    st.write("**Schema Version Upgrade**")
    st.info("💡 Upgrade schemas to newer versions while maintaining compatibility")
    
    # Source version
    source_version = st.selectbox("From Version", ["v1.0.0", "v1.1.0", "v2.0.0"])
    target_version = st.selectbox("To Version", ["v2.0.0", "v2.1.0", "v3.0.0"])
    
    # Migration options
    preserve_data = st.checkbox("Preserve existing data", value=True)
    create_backup = st.checkbox("Create backup before upgrade", value=True)
    
    if st.button("🚀 Start Upgrade"):
        return {
            "action": "version_upgrade",
            "source_version": source_version,
            "target_version": target_version,
            "preserve_data": preserve_data,
            "create_backup": create_backup
        }
    
    return {"action": None}


def render_format_conversion_interface() -> Dict[str, Any]:
    """Render format conversion interface"""
    st.write("**Format Conversion**")
    st.info("💡 Convert schemas between different formats")
    
    input_format = st.selectbox("Input Format", ["JSON", "YAML", "XML", "CSV"])
    output_format = st.selectbox("Output Format", ["JSON", "YAML", "XML", "CSV"])
    
    uploaded_file = st.file_uploader("Choose file to convert")
    
    if uploaded_file and st.button("🔄 Convert"):
        return {
            "action": "format_conversion",
            "input_format": input_format,
            "output_format": output_format,
            "file": uploaded_file
        }
    
    return {"action": None}


def render_system_migration_interface() -> Dict[str, Any]:
    """Render system migration interface"""
    st.write("**System Migration**")
    st.warning("⚠️ Advanced feature - use with caution")
    
    migration_source = st.selectbox(
        "Migration Source",
        options=["json_export", "database_dump", "api_endpoint"],
        format_func=lambda x: {
            "json_export": "JSON Export",
            "database_dump": "Database Dump",
            "api_endpoint": "API Endpoint"
        }[x]
    )
    
    if migration_source == "api_endpoint":
        api_url = st.text_input("API URL")
        api_key = st.text_input("API Key", type="password")
    
    if st.button("🔄 Start Migration"):
        return {
            "action": "system_migration",
            "source": migration_source
        }
    
    return {"action": None}


def render_backup_restore_interface() -> Dict[str, Any]:
    """Render backup and restore interface"""
    st.write("**Backup & Restore**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💾 Create Backup")
        
        backup_scope = st.selectbox(
            "Backup Scope",
            options=["current_schema", "all_schemas", "templates", "everything"],
            format_func=lambda x: {
                "current_schema": "Current Schema Only",
                "all_schemas": "All Schemas", 
                "templates": "Templates Only",
                "everything": "Complete Backup"
            }[x]
        )
        
        include_data = st.checkbox("Include sample data", value=False)
        compress_backup = st.checkbox("Compress backup", value=True)
        
        if st.button("💾 Create Backup"):
            return {
                "action": "create_backup",
                "scope": backup_scope,
                "include_data": include_data,
                "compress": compress_backup
            }
    
    with col2:
        st.subheader("📂 Restore Backup")
        
        backup_file = st.file_uploader(
            "Choose backup file",
            type=['zip', 'json']
        )
        
        if backup_file:
            restore_mode = st.selectbox(
                "Restore Mode",
                options=["replace", "merge", "selective"],
                format_func=lambda x: {
                    "replace": "Replace Existing",
                    "merge": "Merge with Existing",
                    "selective": "Selective Restore"
                }[x]
            )
            
            if st.button("📂 Restore Backup"):
                return {
                    "action": "restore_backup",
                    "file": backup_file,
                    "mode": restore_mode
                }
    
    return {"action": None}


# Utility functions

def validate_imported_schema(schema_data: Dict[str, Any]) -> List[str]:
    """Validate imported schema structure"""
    issues = []
    
    required_fields = ["name", "id", "version"]
    for field in required_fields:
        if field not in schema_data:
            issues.append(f"Missing required field: {field}")
    
    if "fields" in schema_data:
        fields = schema_data["fields"]
        if not isinstance(fields, dict):
            issues.append("Fields must be a dictionary")
        else:
            for field_name, field_config in fields.items():
                if not isinstance(field_config, dict):
                    issues.append(f"Field '{field_name}' must be a dictionary")
                elif "type" not in field_config:
                    issues.append(f"Field '{field_name}' missing type")
    
    return issues


def fix_schema_issues(schema_data: Dict[str, Any], issues: List[str]) -> Dict[str, Any]:
    """Attempt to fix common schema issues"""
    fixed_schema = schema_data.copy()
    
    # Add missing required fields with defaults
    if "name" not in fixed_schema:
        fixed_schema["name"] = "Imported Schema"
    
    if "id" not in fixed_schema:
        fixed_schema["id"] = "imported_schema"
    
    if "version" not in fixed_schema:
        fixed_schema["version"] = "v1.0.0"
    
    if "fields" not in fixed_schema:
        fixed_schema["fields"] = {}
    
    # Fix field structures
    for field_name, field_config in fixed_schema.get("fields", {}).items():
        if not isinstance(field_config, dict):
            fixed_schema["fields"][field_name] = {"type": "text"}
        elif "type" not in field_config:
            fixed_schema["fields"][field_name]["type"] = "text"
    
    return fixed_schema


def render_import_preview(schema_data: Dict[str, Any]) -> None:
    """Render preview of imported schema"""
    st.write("**Schema Preview:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Name:** {schema_data.get('name', 'N/A')}")
        st.write(f"**ID:** {schema_data.get('id', 'N/A')}")
        st.write(f"**Version:** {schema_data.get('version', 'N/A')}")
    
    with col2:
        fields_count = len(schema_data.get('fields', {}))
        st.write(f"**Fields:** {fields_count}")
        st.write(f"**Category:** {schema_data.get('category', 'N/A')}")
        st.write(f"**Status:** {schema_data.get('status', 'N/A')}")
    
    if schema_data.get('description'):
        st.write(f"**Description:** {schema_data['description']}")
    
    # Field preview
    fields = schema_data.get('fields', {})
    if fields:
        st.write("**Fields Preview:**")
        for field_name, field_config in list(fields.items())[:5]:
            field_type = field_config.get('type', 'unknown')
            required = " (Required)" if field_config.get('required') else ""
            st.write(f"- {field_name}: {field_type}{required}")
        
        if len(fields) > 5:
            st.write(f"... and {len(fields) - 5} more fields")


def generate_csv_template() -> str:
    """Generate CSV template for field import"""
    headers = [
        "name",
        "display_name", 
        "type",
        "required",
        "description",
        "placeholder",
        "help_text",
        "examples"
    ]
    
    sample_rows = [
        {
            "name": "customer_name",
            "display_name": "Customer Name",
            "type": "text",
            "required": "true",
            "description": "Full name of the customer",
            "placeholder": "Enter customer name",
            "help_text": "First and last name",
            "examples": "John Doe, Jane Smith"
        },
        {
            "name": "invoice_amount",
            "display_name": "Invoice Amount", 
            "type": "number",
            "required": "true",
            "description": "Total invoice amount",
            "placeholder": "0.00",
            "help_text": "Amount in USD",
            "examples": "100.00, 250.50"
        }
    ]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(sample_rows)
    
    return output.getvalue()


def get_templates_by_category(category: str) -> List[Dict[str, Any]]:
    """Get templates by category (mock implementation)"""
    mock_templates = {
        "Government Documents": [
            {
                "id": "passport_template",
                "name": "Passport",
                "description": "International passport template",
                "fields": [
                    {"name": "passport_number", "display_name": "Passport Number", "type": "text"},
                    {"name": "full_name", "display_name": "Full Name", "type": "text"},
                    {"name": "date_of_birth", "display_name": "Date of Birth", "type": "date"},
                    {"name": "nationality", "display_name": "Nationality", "type": "text"},
                    {"name": "issue_date", "display_name": "Issue Date", "type": "date"},
                    {"name": "expiry_date", "display_name": "Expiry Date", "type": "date"}
                ]
            }
        ],
        "Business Documents": [
            {
                "id": "invoice_template",
                "name": "Standard Invoice",
                "description": "Standard business invoice template",
                "fields": [
                    {"name": "invoice_number", "display_name": "Invoice Number", "type": "text"},
                    {"name": "vendor_name", "display_name": "Vendor Name", "type": "text"},
                    {"name": "total_amount", "display_name": "Total Amount", "type": "currency"},
                    {"name": "issue_date", "display_name": "Issue Date", "type": "date"},
                    {"name": "due_date", "display_name": "Due Date", "type": "date"}
                ]
            }
        ]
    }
    
    return mock_templates.get(category, [])


def generate_export_data(schema_data: Dict[str, Any], format_type: str, options: Dict[str, Any]) -> str:
    """Generate export data in specified format"""
    if format_type == "json":
        clean_data = prepare_schema_for_export(schema_data, options)
        indent = None if options.get("minify_json") else 2
        return json.dumps(clean_data, indent=indent, ensure_ascii=False)
    
    elif format_type == "csv":
        return generate_csv_export(schema_data, options)
    
    elif format_type == "yaml":
        return generate_yaml_export(schema_data, options)
    
    elif format_type == "documentation":
        return generate_documentation_export(schema_data)
    
    elif format_type == "template":
        return generate_template_export(schema_data, options)
    
    else:
        return json.dumps(schema_data, indent=2)


def prepare_schema_for_export(schema_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare schema data for export based on options"""
    clean_data = schema_data.copy()
    
    if not options.get("include_metadata"):
        # Remove metadata fields
        metadata_fields = ["created_date", "updated_date", "created_by", "usage_count"]
        for field in metadata_fields:
            clean_data.pop(field, None)
    
    if not options.get("include_examples"):
        # Remove examples from fields
        for field_config in clean_data.get("fields", {}).values():
            field_config.pop("examples", None)
    
    if not options.get("include_validation"):
        # Remove validation rules
        for field_config in clean_data.get("fields", {}).values():
            field_config.pop("validation_rules", None)
        clean_data.pop("validation_rules", None)
    
    return clean_data


def generate_csv_export(schema_data: Dict[str, Any], options: Dict[str, Any]) -> str:
    """Generate CSV export of schema fields"""
    fields = schema_data.get("fields", {})
    
    output = io.StringIO()
    headers = ["name", "display_name", "type", "required", "description"]
    
    if options.get("include_examples"):
        headers.append("examples")
    
    if options.get("include_validation"):
        headers.append("validation_rules")
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    
    for field_name, field_config in fields.items():
        row = {
            "name": field_name,
            "display_name": field_config.get("display_name", ""),
            "type": field_config.get("type", ""),
            "required": field_config.get("required", False),
            "description": field_config.get("description", "")
        }
        
        if options.get("include_examples"):
            examples = field_config.get("examples", [])
            row["examples"] = ", ".join(examples)
        
        if options.get("include_validation"):
            validation_rules = field_config.get("validation_rules", [])
            row["validation_rules"] = json.dumps(validation_rules)
        
        writer.writerow(row)
    
    return output.getvalue()


def generate_yaml_export(schema_data: Dict[str, Any], options: Dict[str, Any]) -> str:
    """Generate YAML export (simplified implementation)"""
    clean_data = prepare_schema_for_export(schema_data, options)
    
    # Simple YAML-like format (in real implementation, use PyYAML)
    yaml_content = f"""name: {clean_data.get('name', '')}
id: {clean_data.get('id', '')}
version: {clean_data.get('version', '')}
description: {clean_data.get('description', '')}
category: {clean_data.get('category', '')}

fields:"""
    
    for field_name, field_config in clean_data.get("fields", {}).items():
        yaml_content += f"""
  {field_name}:
    display_name: {field_config.get('display_name', '')}
    type: {field_config.get('type', '')}
    required: {field_config.get('required', False)}"""
        
        if field_config.get('description'):
            yaml_content += f"""
    description: {field_config['description']}"""
    
    return yaml_content


def generate_documentation_export(schema_data: Dict[str, Any]) -> str:
    """Generate documentation export"""
    # Use the same function from preview.py
    from .preview import generate_schema_documentation
    return generate_schema_documentation(schema_data)


def generate_template_export(schema_data: Dict[str, Any], options: Dict[str, Any]) -> str:
    """Generate template export"""
    template_data = {
        "template_name": f"{schema_data.get('name', 'Schema')} Template",
        "template_id": f"{schema_data.get('id', 'schema')}_template",
        "description": f"Template created from {schema_data.get('name', 'schema')}",
        "category": schema_data.get("category", "Custom"),
        "schema_structure": prepare_schema_for_export(schema_data, options),
        "created_date": datetime.now().isoformat()
    }
    
    return json.dumps(template_data, indent=2, ensure_ascii=False)


def get_mime_type(format_type: str) -> str:
    """Get MIME type for format"""
    mime_types = {
        "json": "application/json",
        "csv": "text/csv",
        "yaml": "text/yaml",
        "documentation": "text/markdown",
        "template": "application/json"
    }
    return mime_types.get(format_type, "text/plain")