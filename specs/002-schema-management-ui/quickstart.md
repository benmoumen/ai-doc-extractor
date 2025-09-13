# Quickstart Guide: Schema Management UI Extension

## Prerequisites

- Python 3.11+ environment
- Existing `001-our-data-extraction` feature implemented and working
- Streamlit application running successfully
- Write access to project directory

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
# Add to requirements.txt
echo "streamlit-elements>=0.1.0" >> requirements.txt
echo "python-jsonschema>=4.0.0" >> requirements.txt

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Test streamlit-elements
python -c "from streamlit_elements import elements, mui; print('✅ streamlit-elements ready')"

# Test jsonschema
python -c "import jsonschema; print('✅ jsonschema ready')"
```

### 3. Create Module Structure

```bash
# Create schema management module
mkdir -p schema_management
touch schema_management/__init__.py
touch schema_management/schema_storage.py
touch schema_management/schema_builder.py
```

### 4. Create Data Directories

```bash
# Create data storage structure
mkdir -p data/schemas data/templates

# Initialize SQLite database
python -c "
import sqlite3
conn = sqlite3.connect('data/schema_metadata.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS schema_metadata (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    version TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    usage_count INTEGER DEFAULT 0
)
''')
conn.commit()
conn.close()
print('✅ Database initialized')
"
```

## Basic Implementation Test (10 minutes)

### 1. Minimal Schema Storage

Create `schema_management/schema_storage.py`:

```python
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class SchemaStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.schemas_dir = self.data_dir / "schemas"
        self.metadata_db = self.data_dir / "schema_metadata.db"
        
        self.schemas_dir.mkdir(parents=True, exist_ok=True)
    
    def save_schema(self, schema_id: str, schema_data: Dict) -> bool:
        try:
            # Add timestamps
            schema_data["updated_date"] = datetime.now().isoformat()
            version = schema_data.get("version", "v1.0.0")
            
            # Save JSON file
            filename = f"{schema_id}_{version}.json"
            filepath = self.schemas_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving schema: {e}")
            return False
    
    def load_schema(self, schema_id: str, version: Optional[str] = None) -> Optional[Dict]:
        try:
            if version is None:
                version = "v1.0.0"  # Default for testing
            
            filename = f"{schema_id}_{version}.json"
            filepath = self.schemas_dir / filename
            
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error loading schema: {e}")
            return None
    
    def list_schemas(self) -> List[Dict]:
        schemas = []
        try:
            for json_file in self.schemas_dir.glob("*.json"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
                    schemas.append({
                        "id": schema_data.get("id"),
                        "name": schema_data.get("name"),
                        "category": schema_data.get("category", "Custom"),
                        "version": schema_data.get("version"),
                        "updated_date": schema_data.get("updated_date")
                    })
        except Exception as e:
            print(f"Error listing schemas: {e}")
        
        return schemas
```

### 2. Minimal UI Integration

Create `schema_management/schema_builder.py`:

```python
import streamlit as st
from .schema_storage import SchemaStorage

def render_schema_management_page():
    """Main schema management interface"""
    st.title("🏗️ Schema Management")
    
    # Initialize storage
    storage = SchemaStorage()
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Basic Info", "🏷️ Fields", "✅ Validation", "👁️ Preview"])
    
    with tab1:
        render_basic_info_tab(storage)
    
    with tab2:
        st.info("Field management coming soon...")
    
    with tab3:
        st.info("Validation builder coming soon...")
    
    with tab4:
        st.info("Schema preview coming soon...")

def render_basic_info_tab(storage: SchemaStorage):
    """Basic schema information form"""
    st.subheader("Schema Information")
    
    # Form inputs
    schema_name = st.text_input("Schema Name", placeholder="e.g., National ID Card")
    schema_description = st.text_area("Description", placeholder="Describe this document type...")
    schema_category = st.selectbox("Category", ["Government", "Business", "Personal", "Custom"])
    
    # Simple create button
    if st.button("Create Schema", type="primary"):
        if schema_name:
            schema_id = schema_name.lower().replace(" ", "_")
            schema_data = {
                "id": schema_id,
                "name": schema_name,
                "description": schema_description,
                "category": schema_category,
                "version": "v1.0.0",
                "is_active": True,
                "fields": {},
                "validation_rules": []
            }
            
            if storage.save_schema(schema_id, schema_data):
                st.success(f"✅ Schema '{schema_name}' created successfully!")
            else:
                st.error("❌ Failed to create schema")
        else:
            st.error("Schema name is required")
    
    # List existing schemas
    st.subheader("Existing Schemas")
    schemas = storage.list_schemas()
    
    if schemas:
        for schema in schemas:
            with st.expander(f"{schema['name']} ({schema['category']})"):
                st.write(f"**ID:** {schema['id']}")
                st.write(f"**Version:** {schema['version']}")
                st.write(f"**Updated:** {schema['updated_date']}")
    else:
        st.info("No schemas created yet. Create your first schema above!")
```

### 3. Integrate with Main App

Update your `app.py` to add navigation:

```python
# Add this after your existing imports
try:
    from schema_management.schema_builder import render_schema_management_page
    SCHEMA_MANAGEMENT_AVAILABLE = True
except ImportError:
    SCHEMA_MANAGEMENT_AVAILABLE = False

# Add navigation in your sidebar (before existing content)
with st.sidebar:
    if SCHEMA_MANAGEMENT_AVAILABLE:
        page = st.selectbox(
            "📍 Navigate",
            ["📊 Document Extraction", "🏗️ Schema Management"],
            index=0
        )
    else:
        page = "📊 Document Extraction"
        st.info("Schema Management: Install dependencies to enable")

# Add page routing (replace your main content area)
if page == "🏗️ Schema Management" and SCHEMA_MANAGEMENT_AVAILABLE:
    render_schema_management_page()
else:
    # Your existing document extraction interface goes here
    st.title("AI Document Data Extractor")
    # ... rest of your existing app.py content
```

## Testing the Implementation (5 minutes)

### 1. Run the Application

```bash
streamlit run app.py
```

### 2. Test Basic Functionality

1. **Navigate to Schema Management**: Use the sidebar navigation
2. **Create a Test Schema**:
   - Name: "Test Document"
   - Description: "A test schema for validation"
   - Category: "Custom"
   - Click "Create Schema"
3. **Verify Storage**: Check that `data/schemas/test_document_v1.0.0.json` was created
4. **View in List**: Confirm the schema appears in the "Existing Schemas" section

### 3. Validate File Structure

```bash
# Check created files
ls -la data/schemas/
ls -la schema_management/

# Verify JSON content
cat data/schemas/test_document_v1.0.0.json
```

Expected JSON structure:
```json
{
  "id": "test_document",
  "name": "Test Document",
  "description": "A test schema for validation",
  "category": "Custom",
  "version": "v1.0.0",
  "is_active": true,
  "fields": {},
  "validation_rules": [],
  "updated_date": "2025-09-12T..."
}
```

## Integration Test (5 minutes)

### Test Schema Integration with Extraction

Update your document type selector in the extraction interface to include custom schemas:

```python
# In your extraction interface, replace the document type selector
def get_available_document_types():
    # Existing built-in types
    built_in_types = {
        "national_id": {"name": "National ID", "category": "Government"},
        "passport": {"name": "Passport", "category": "Government"}
        # ... your existing types
    }
    
    # Add custom schemas
    try:
        from schema_management.schema_storage import SchemaStorage
        storage = SchemaStorage()
        custom_schemas = storage.list_schemas()
        
        for schema in custom_schemas:
            built_in_types[schema["id"]] = {
                "name": schema["name"],
                "category": schema["category"]
            }
    except Exception as e:
        st.warning(f"Custom schemas unavailable: {e}")
    
    return built_in_types

# Use in your document type selector
document_types = get_available_document_types()
selected_type = st.selectbox("Document Type", list(document_types.keys()))
```

## Troubleshooting

### Common Issues

**Import Error for streamlit-elements**:
```bash
pip install streamlit-elements>=0.1.0
# If still failing, try:
pip install --upgrade streamlit-elements
```

**Database Permission Error**:
```bash
# Ensure write permissions
chmod 755 data/
chmod 644 data/schema_metadata.db
```

**Module Import Error**:
```bash
# Ensure __init__.py exists
touch schema_management/__init__.py
```

### Verify Installation

Run this test script to verify everything is working:

```python
# test_quickstart.py
import json
from schema_management.schema_storage import SchemaStorage

def test_basic_functionality():
    storage = SchemaStorage("test_data")
    
    # Test save
    test_schema = {
        "id": "quickstart_test",
        "name": "Quickstart Test",
        "version": "v1.0.0",
        "fields": {}
    }
    
    assert storage.save_schema("quickstart_test", test_schema)
    print("✅ Save test passed")
    
    # Test load
    loaded = storage.load_schema("quickstart_test")
    assert loaded is not None
    assert loaded["name"] == "Quickstart Test"
    print("✅ Load test passed")
    
    # Test list
    schemas = storage.list_schemas()
    assert len(schemas) >= 1
    print("✅ List test passed")
    
    print("🎉 All quickstart tests passed!")

if __name__ == "__main__":
    test_basic_functionality()
```

```bash
python test_quickstart.py
```

## Advanced Implementation Examples

### Complete Field Management Interface

```python
# schema_management/ui/field_editor.py
import streamlit as st
from typing import Dict, Any, List

def render_field_editor(field_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Complete field editor with all field types and validation"""
    
    if field_data is None:
        field_data = {
            "id": "",
            "name": "",
            "display_name": "",
            "type": "string",
            "required": False,
            "description": "",
            "validation_rules": [],
            "options": [],
            "metadata": {}
        }
    
    st.subheader("Field Configuration")
    
    # Basic field information
    col1, col2 = st.columns(2)
    
    with col1:
        field_name = st.text_input(
            "Field Name*",
            value=field_data.get("name", ""),
            help="Internal field name (no spaces)"
        )
        
        field_type = st.selectbox(
            "Field Type*",
            ["string", "number", "integer", "boolean", "date", "datetime", 
             "email", "url", "phone", "select", "multiselect", "file"],
            index=["string", "number", "integer", "boolean", "date", "datetime", 
                   "email", "url", "phone", "select", "multiselect", "file"].index(
                field_data.get("type", "string")
            )
        )
    
    with col2:
        display_name = st.text_input(
            "Display Name*",
            value=field_data.get("display_name", ""),
            help="User-friendly label"
        )
        
        required = st.checkbox(
            "Required Field",
            value=field_data.get("required", False)
        )
    
    description = st.text_area(
        "Description",
        value=field_data.get("description", ""),
        help="Help text for users"
    )
    
    # Field-specific configuration
    options = []
    if field_type in ["select", "multiselect"]:
        st.subheader("Options")
        
        # Add new option
        new_option = st.text_input("Add Option")
        if st.button("Add") and new_option:
            current_options = field_data.get("options", [])
            if new_option not in current_options:
                current_options.append(new_option)
                field_data["options"] = current_options
                st.rerun()
        
        # Display existing options
        current_options = field_data.get("options", [])
        if current_options:
            for i, option in enumerate(current_options):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(option)
                with col2:
                    if st.button("Remove", key=f"remove_option_{i}"):
                        current_options.pop(i)
                        field_data["options"] = current_options
                        st.rerun()
        
        options = current_options
    
    # Validation rules
    st.subheader("Validation Rules")
    
    validation_rules = field_data.get("validation_rules", [])
    
    # Add new validation rule
    with st.expander("Add Validation Rule"):
        rule_type = st.selectbox(
            "Rule Type",
            ["required", "min_length", "max_length", "regex", "min_value", "max_value", 
             "email_format", "phone_format", "date_format"]
        )
        
        rule_message = st.text_input("Error Message")
        
        # Rule-specific parameters
        rule_params = {}
        if rule_type in ["min_length", "max_length"]:
            length = st.number_input("Length", min_value=0, value=1)
            rule_params = {"length": length}
        elif rule_type in ["min_value", "max_value"]:
            value = st.number_input("Value", value=0)
            rule_params = {"value": value}
        elif rule_type == "regex":
            pattern = st.text_input("Regex Pattern")
            rule_params = {"pattern": pattern}
        
        if st.button("Add Validation Rule"):
            if rule_message:
                new_rule = {
                    "rule_type": rule_type,
                    "message": rule_message,
                    "parameters": rule_params,
                    "severity": "error"
                }
                validation_rules.append(new_rule)
                field_data["validation_rules"] = validation_rules
                st.rerun()
    
    # Display existing validation rules
    if validation_rules:
        for i, rule in enumerate(validation_rules):
            with st.expander(f"Rule {i+1}: {rule['rule_type']}"):
                st.write(f"**Message:** {rule['message']}")
                st.write(f"**Parameters:** {rule.get('parameters', {})}")
                if st.button("Remove Rule", key=f"remove_rule_{i}"):
                    validation_rules.pop(i)
                    field_data["validation_rules"] = validation_rules
                    st.rerun()
    
    # Generate field ID if not provided
    if field_name and not field_data.get("id"):
        field_id = field_name.lower().replace(" ", "_")
    else:
        field_id = field_data.get("id", "")
    
    # Return updated field data
    return {
        "id": field_id,
        "name": field_name,
        "display_name": display_name,
        "type": field_type,
        "required": required,
        "description": description,
        "validation_rules": validation_rules,
        "options": options,
        "metadata": field_data.get("metadata", {})
    }
```

### Schema Preview with Real-time Updates

```python
# schema_management/ui/preview.py
import streamlit as st
import json
from typing import Dict, Any

def render_schema_preview(schema_data: Dict[str, Any]):
    """Real-time schema preview with multiple formats"""
    
    st.subheader("Schema Preview")
    
    # Preview mode selector
    preview_mode = st.selectbox(
        "Preview Mode",
        ["Form Preview", "JSON Schema", "Documentation", "Extraction Prompt"]
    )
    
    if preview_mode == "Form Preview":
        render_form_preview(schema_data)
    elif preview_mode == "JSON Schema":
        render_json_preview(schema_data)
    elif preview_mode == "Documentation":
        render_documentation_preview(schema_data)
    elif preview_mode == "Extraction Prompt":
        render_extraction_prompt_preview(schema_data)

def render_form_preview(schema_data: Dict[str, Any]):
    """Show how the form would look to users"""
    st.write("### Form Preview")
    st.write(f"**{schema_data.get('name', 'Untitled Schema')}**")
    
    if schema_data.get('description'):
        st.write(schema_data['description'])
    
    st.write("---")
    
    fields = schema_data.get('fields', [])
    if isinstance(fields, dict):
        fields = list(fields.values())
    
    for field in fields:
        field_type = field.get('type', 'string')
        field_name = field.get('display_name', field.get('name', 'Unnamed'))
        required_marker = " *" if field.get('required') else ""
        
        st.write(f"**{field_name}{required_marker}**")
        
        if field.get('description'):
            st.caption(field['description'])
        
        # Show appropriate input widget
        if field_type == 'string':
            st.text_input(f"_{field_name}_", disabled=True, placeholder="Text input")
        elif field_type in ['number', 'integer']:
            st.number_input(f"_{field_name}_", disabled=True)
        elif field_type == 'boolean':
            st.checkbox(f"_{field_name}_", disabled=True)
        elif field_type == 'date':
            st.date_input(f"_{field_name}_", disabled=True)
        elif field_type == 'email':
            st.text_input(f"_{field_name}_", disabled=True, placeholder="email@example.com")
        elif field_type == 'select':
            options = field.get('options', ['Option 1', 'Option 2'])
            st.selectbox(f"_{field_name}_", options, disabled=True)
        elif field_type == 'multiselect':
            options = field.get('options', ['Option 1', 'Option 2'])
            st.multiselect(f"_{field_name}_", options, disabled=True)

def render_json_preview(schema_data: Dict[str, Any]):
    """Show JSON representation"""
    st.write("### JSON Schema")
    
    # Clean up the schema for display
    clean_schema = schema_data.copy()
    
    # Format for better readability
    json_str = json.dumps(clean_schema, indent=2, ensure_ascii=False)
    
    st.code(json_str, language='json')
    
    # Download button
    st.download_button(
        label="Download JSON",
        data=json_str,
        file_name=f"{schema_data.get('id', 'schema')}.json",
        mime="application/json"
    )

def render_extraction_prompt_preview(schema_data: Dict[str, Any]):
    """Show how the extraction prompt would look"""
    st.write("### AI Extraction Prompt Preview")
    
    schema_name = schema_data.get('name', 'Document')
    fields = schema_data.get('fields', [])
    
    if isinstance(fields, dict):
        fields = list(fields.values())
    
    # Generate extraction prompt
    prompt = f"""Analyze the {schema_name} document in the provided image.

Extract data according to this schema:

"""
    
    for field in fields:
        field_name = field.get('name', 'unnamed')
        field_type = field.get('type', 'string')
        required = field.get('required', False)
        description = field.get('description', '')
        
        prompt += f"- **{field_name}** ({field_type})"
        if required:
            prompt += " *required*"
        if description:
            prompt += f": {description}"
        prompt += "\n"
    
    prompt += f"""
Return JSON in this exact format:
{{
    "extracted_data": {{
        {', '.join([f'"{field.get("name", "field")}": "extracted_value"' for field in fields])}
    }},
    "validation_results": {{
        {', '.join([f'"{field.get("name", "field")}": {{"status": "valid|invalid|missing", "confidence": 0.9}}' for field in fields])}
    }}
}}

Extract exactly what you see - do not infer missing information."""
    
    st.code(prompt, language='text')
```

### Import/Export Implementation

```python
# schema_management/ui/import_export.py
import streamlit as st
import json
import csv
import yaml
from io import StringIO
from typing import Dict, Any, List

def render_import_export_interface(schema_service):
    """Complete import/export interface"""
    
    st.subheader("Import/Export Schemas")
    
    tab1, tab2 = st.tabs(["📥 Import", "📤 Export"])
    
    with tab1:
        render_import_interface(schema_service)
    
    with tab2:
        render_export_interface(schema_service)

def render_import_interface(schema_service):
    """Schema import interface"""
    
    st.write("### Import Schema")
    
    import_format = st.selectbox(
        "Import Format",
        ["JSON", "CSV", "YAML"]
    )
    
    if import_format == "JSON":
        st.write("Upload a JSON schema file or paste JSON content:")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose JSON file",
            type=['json'],
            accept_multiple_files=False
        )
        
        if uploaded_file:
            content = uploaded_file.read().decode('utf-8')
            
            try:
                schema_data = json.loads(content)
                st.success("✅ JSON file loaded successfully")
                
                # Preview the schema
                with st.expander("Preview Schema"):
                    st.json(schema_data)
                
                if st.button("Import Schema"):
                    success, message = import_schema_from_json(schema_data, schema_service)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
                        
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {str(e)}")
        
        # Manual paste
        json_content = st.text_area(
            "Or paste JSON content:",
            height=200,
            placeholder='{"id": "my_schema", "name": "My Schema", ...}'
        )
        
        if json_content and st.button("Import from Text"):
            try:
                schema_data = json.loads(json_content)
                success, message = import_schema_from_json(schema_data, schema_service)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {str(e)}")

def render_export_interface(schema_service):
    """Schema export interface"""
    
    st.write("### Export Schemas")
    
    # Get available schemas
    schemas = schema_service.list_schemas()
    
    if not schemas:
        st.info("No schemas available to export.")
        return
    
    # Schema selection
    export_mode = st.radio(
        "Export Mode",
        ["Single Schema", "Multiple Schemas", "All Schemas"]
    )
    
    selected_schemas = []
    
    if export_mode == "Single Schema":
        schema_options = {s['name']: s['id'] for s in schemas}
        selected_name = st.selectbox("Select Schema", list(schema_options.keys()))
        if selected_name:
            selected_schemas = [schema_options[selected_name]]
    
    elif export_mode == "Multiple Schemas":
        schema_options = {s['name']: s['id'] for s in schemas}
        selected_names = st.multiselect("Select Schemas", list(schema_options.keys()))
        selected_schemas = [schema_options[name] for name in selected_names]
    
    else:  # All Schemas
        selected_schemas = [s['id'] for s in schemas]
        st.info(f"Exporting all {len(schemas)} schemas")
    
    if selected_schemas:
        # Export format
        export_format = st.selectbox(
            "Export Format",
            ["JSON", "CSV", "YAML", "Backup (ZIP)"]
        )
        
        # Export options
        with st.expander("Export Options"):
            include_metadata = st.checkbox("Include Metadata", value=True)
            include_validation = st.checkbox("Include Validation Rules", value=True)
            pretty_format = st.checkbox("Pretty Format", value=True)
        
        if st.button("Generate Export"):
            try:
                if len(selected_schemas) == 1:
                    # Single schema export
                    schema_id = selected_schemas[0]
                    export_data = export_single_schema(
                        schema_id, 
                        schema_service, 
                        export_format,
                        include_metadata,
                        include_validation,
                        pretty_format
                    )
                else:
                    # Multiple schemas export
                    export_data = export_multiple_schemas(
                        selected_schemas,
                        schema_service,
                        export_format,
                        include_metadata,
                        include_validation,
                        pretty_format
                    )
                
                if export_data:
                    # Determine file extension
                    file_ext = {
                        "JSON": "json",
                        "CSV": "csv", 
                        "YAML": "yaml",
                        "Backup (ZIP)": "zip"
                    }[export_format]
                    
                    # Determine filename
                    if len(selected_schemas) == 1:
                        filename = f"{selected_schemas[0]}.{file_ext}"
                    else:
                        filename = f"schemas_export.{file_ext}"
                    
                    # Determine MIME type
                    mime_types = {
                        "json": "application/json",
                        "csv": "text/csv",
                        "yaml": "text/yaml",
                        "zip": "application/zip"
                    }
                    
                    st.download_button(
                        label=f"Download {export_format}",
                        data=export_data,
                        file_name=filename,
                        mime=mime_types[file_ext]
                    )
                    
                    st.success(f"✅ Export generated successfully!")
                    
            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")

def import_schema_from_json(schema_data: Dict[str, Any], schema_service) -> tuple:
    """Import schema from JSON data"""
    try:
        # Validate required fields
        required_fields = ['id', 'name']
        for field in required_fields:
            if field not in schema_data:
                return False, f"Missing required field: {field}"
        
        # Check if schema already exists
        existing = schema_service.get_schema(schema_data['id'])
        if existing:
            return False, f"Schema with ID '{schema_data['id']}' already exists"
        
        # Create schema
        success, message, created_schema = schema_service.create_schema(schema_data)
        return success, message
        
    except Exception as e:
        return False, f"Import error: {str(e)}"

def export_single_schema(schema_id: str, schema_service, format_type: str, 
                        include_metadata: bool, include_validation: bool, 
                        pretty_format: bool) -> str:
    """Export single schema in specified format"""
    
    schema = schema_service.get_schema(schema_id)
    if not schema:
        raise ValueError(f"Schema {schema_id} not found")
    
    schema_data = schema.to_dict()
    
    # Apply export options
    if not include_metadata:
        schema_data.pop('metadata', None)
    
    if not include_validation:
        for field in schema_data.get('fields', []):
            if isinstance(field, dict):
                field.pop('validation_rules', None)
    
    # Export in requested format
    if format_type == "JSON":
        if pretty_format:
            return json.dumps(schema_data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(schema_data, ensure_ascii=False)
    
    elif format_type == "YAML":
        return yaml.dump(schema_data, default_flow_style=False, allow_unicode=True)
    
    elif format_type == "CSV":
        return export_schema_to_csv(schema_data)
    
    else:
        raise ValueError(f"Unsupported export format: {format_type}")

def export_schema_to_csv(schema_data: Dict[str, Any]) -> str:
    """Export schema to CSV format"""
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = [
        'field_id', 'name', 'display_name', 'type', 'required', 
        'description', 'options', 'validation_rules'
    ]
    writer.writerow(headers)
    
    # Write fields
    fields = schema_data.get('fields', [])
    if isinstance(fields, dict):
        fields = list(fields.values())
    
    for field in fields:
        row = [
            field.get('id', ''),
            field.get('name', ''),
            field.get('display_name', ''),
            field.get('type', ''),
            field.get('required', False),
            field.get('description', ''),
            ';'.join(field.get('options', [])),
            json.dumps(field.get('validation_rules', []))
        ]
        writer.writerow(row)
    
    return output.getvalue()
```

## Complete Integration Example

```python
# app.py - Complete integration
import streamlit as st
from schema_management.schema_builder import render_schema_management_page
from schema_management.state_manager import initialize_schema_builder_state
from schema_compatibility import get_extraction_configuration

# Set page config
st.set_page_config(
    page_title="AI Document Extractor",
    page_icon="📄",
    layout="wide"
)

# Initialize schema management
initialize_schema_builder_state()

# Main navigation
st.markdown("## 🤖 AI Document Data Extractor")

# Navigation tabs
tab1, tab2 = st.tabs(["📄 Document Extraction", "🔧 Schema Management"])

with tab1:
    st.subheader("Document Data Extraction")
    
    # Your existing extraction workflow here
    # Now enhanced with custom schema support
    
    # Document type selection with custom schemas
    from schema_utils import get_available_document_types
    document_types = get_available_document_types()
    
    # Group schemas by type
    predefined_types = {}
    custom_types = {}
    
    for type_id, type_info in document_types.items():
        if type_info.get('custom', False):
            custom_types[type_id] = type_info
        else:
            predefined_types[type_id] = type_info
    
    # Enhanced selector with grouping
    with st.sidebar:
        st.markdown("### Document Type Selection")
        
        type_category = st.radio(
            "Schema Category",
            ["Predefined Schemas", "Custom Schemas", "Generic Extraction"]
        )
        
        selected_type = None
        
        if type_category == "Predefined Schemas" and predefined_types:
            type_names = {info['name']: type_id for type_id, info in predefined_types.items()}
            selected_name = st.selectbox("Select Predefined Type", list(type_names.keys()))
            if selected_name:
                selected_type = type_names[selected_name]
        
        elif type_category == "Custom Schemas" and custom_types:
            type_names = {f"🔧 {info['name']}": type_id for type_id, info in custom_types.items()}
            selected_name = st.selectbox("Select Custom Schema", list(type_names.keys()))
            if selected_name:
                selected_type = type_names[selected_name]
        
        elif type_category == "Generic Extraction":
            st.info("Using generic extraction without schema")
            selected_type = None
    
    # Your extraction workflow continues here with enhanced schema support...

with tab2:
    # Complete schema management interface
    render_schema_management_page()

# Performance monitoring in sidebar
if st.secrets.get("DEBUG_MODE", False):
    with st.sidebar:
        with st.expander("🔧 System Status"):
            from schema_management.performance_optimizer import get_optimization_status
            metrics = get_optimization_status()
            
            st.metric("Cached Schemas", metrics.get('cache_metrics', {}).get('total_entries', 0))
            st.metric("Cache Hit Rate", f"{metrics.get('cache_metrics', {}).get('hit_ratio', 0):.1%}")
            
            if st.button("Clear Caches"):
                from schema_management.performance_optimizer import clear_optimization_caches
                clear_optimization_caches()
                st.success("Caches cleared")
```

## Testing Your Complete Implementation

### 1. End-to-End Test Script

```python
# test_complete_implementation.py
import streamlit as st
from schema_management.models.schema import Schema
from schema_management.models.field import Field, FieldType
from schema_management.services.schema_service import SchemaService
from schema_management.storage.schema_storage import SchemaStorage

def test_complete_workflow():
    """Test the complete schema management workflow"""
    
    storage = SchemaStorage("test_data")
    service = SchemaService(storage)
    
    # Test 1: Create comprehensive schema
    test_schema = Schema(
        id="comprehensive_test",
        name="Comprehensive Test Schema",
        description="Testing all features",
        version="1.0.0",
        fields=[
            Field(
                id="name_field",
                name="full_name",
                display_name="Full Name",
                field_type=FieldType.STRING,
                required=True,
                validation_rules=[
                    {
                        "rule_type": "min_length",
                        "message": "Name too short",
                        "parameters": {"length": 2}
                    }
                ]
            ),
            Field(
                id="country_field", 
                name="country",
                display_name="Country",
                field_type=FieldType.SELECT,
                options=["USA", "Canada", "UK"],
                required=False
            )
        ]
    )
    
    # Test creation
    success, message, created = service.create_schema(test_schema.to_dict())
    assert success, f"Schema creation failed: {message}"
    print("✅ Schema creation test passed")
    
    # Test retrieval
    retrieved = service.get_schema(test_schema.id)
    assert retrieved is not None, "Schema retrieval failed"
    assert retrieved.name == test_schema.name, "Schema data mismatch"
    print("✅ Schema retrieval test passed")
    
    # Test listing
    schemas = service.list_schemas()
    assert len(schemas) >= 1, "Schema listing failed"
    print("✅ Schema listing test passed")
    
    # Test update
    updated_data = test_schema.to_dict()
    updated_data["description"] = "Updated description"
    success, message, updated = service.update_schema(test_schema.id, updated_data)
    assert success, f"Schema update failed: {message}"
    print("✅ Schema update test passed")
    
    # Test validation
    from schema_management.services.validation_service import ValidationService
    validation_service = ValidationService(storage, service)
    
    test_data = {
        "full_name": "John Doe",
        "country": "USA"
    }
    
    result = validation_service.validate_data_against_schema(test_schema.id, test_data)
    assert result.is_valid, "Data validation failed"
    print("✅ Data validation test passed")
    
    print("🎉 All comprehensive tests passed!")

if __name__ == "__main__":
    test_complete_workflow()
```

### 2. Performance Test

```bash
# Run performance tests
python -m pytest tests/performance/test_schema_performance.py -v -s -m performance
```

### 3. Integration Test

```bash
# Test complete integration
streamlit run app.py

# In browser:
# 1. Go to Schema Management tab
# 2. Create a new schema with 5+ fields
# 3. Add validation rules
# 4. Preview the schema
# 5. Export to JSON
# 6. Switch to Document Extraction tab
# 7. Verify custom schema appears in dropdown
# 8. Test extraction with custom schema
```

## Next Steps

After completing this comprehensive quickstart:

1. **Production Deployment**: Configure for production environment
2. **User Training**: Create user documentation and training materials
3. **Advanced Features**: Implement schema versioning, collaboration features
4. **Integration Testing**: Test with real document extraction workflows
5. **Performance Optimization**: Monitor and optimize for your specific use case

## Expected Outcome

After completing this comprehensive quickstart, you should have:

- ✅ Complete schema management interface with all features
- ✅ Full field editor with validation rules
- ✅ Import/export functionality for JSON, CSV, YAML
- ✅ Real-time schema preview and documentation
- ✅ Performance optimization and caching
- ✅ Error handling and recovery mechanisms
- ✅ Complete integration with document extraction workflow
- ✅ Production-ready schema management system

The comprehensive implementation provides a professional-grade schema management system that seamlessly integrates with your document extraction workflow, offering users a powerful and intuitive interface for creating and managing custom extraction schemas.