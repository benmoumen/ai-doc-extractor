# Quickstart: Schema-Driven Document Data Extraction

## Overview
This guide walks through implementing and testing the schema-driven document data extraction feature that extends the existing LiteLLM-based extraction system.

## Prerequisites
- Existing AI document extractor application (Streamlit + LiteLLM)
- Python 3.11+ environment
- API keys for Groq (Llama Scout 17B) and/or Mistral (Small 3.2)

## Implementation Steps

### Step 1: Schema Configuration
Add document type schemas to `config.py`:

```python
# Add to config.py
DOCUMENT_SCHEMAS = {
    "national_id": {
        "id": "national_id",
        "name": "National ID",
        "description": "Government-issued identification document",
        "fields": {
            "full_name": {
                "name": "full_name",
                "display_name": "Full Name",
                "type": "string",
                "required": True,
                "description": "Complete name as shown on document",
                "examples": ["John Smith", "Maria Garcia"]
            },
            "id_number": {
                "name": "id_number", 
                "display_name": "ID Number",
                "type": "string",
                "required": True,
                "validation_rules": [
                    {"type": "pattern", "value": "^[A-Z0-9]{8,12}$", "message": "Must be 8-12 alphanumeric characters"}
                ],
                "description": "Unique identification number",
                "examples": ["AB123456789", "CD987654321"]
            },
            "date_of_birth": {
                "name": "date_of_birth",
                "display_name": "Date of Birth", 
                "type": "date",
                "required": True,
                "description": "Birth date in YYYY-MM-DD format",
                "examples": ["1985-03-15", "1992-11-08"]
            }
        }
    }
}
```

### Step 2: Enhanced Prompt Engineering
Create schema-aware prompt generation:

```python
# Add to utils.py
def create_schema_prompt(document_type_schema, document_type_name):
    """Generate schema-aware extraction prompt."""
    fields_description = {}
    for field_name, field_def in document_type_schema['fields'].items():
        field_info = {
            "type": field_def["type"],
            "required": field_def["required"],
            "description": field_def["description"]
        }
        if "validation_rules" in field_def:
            field_info["validation"] = field_def["validation_rules"]
        fields_description[field_name] = field_info
    
    prompt = f"""Analyze the {document_type_name} document in the provided image.

Extract data according to this exact schema:
{json.dumps(fields_description, indent=2)}

Return JSON in this format:
{{
    "extracted_data": {{
        // field values extracted from document
    }},
    "validation_results": {{
        "field_name": {{
            "status": "valid|invalid|warning|missing",
            "message": "detailed feedback about extraction and validation",
            "extracted_value": "the actual value found",
            "confidence": 0.0-1.0
        }}
    }}
}}

Requirements:
- Include validation_results for EVERY field in the schema
- Use "missing" status if field not found in document
- Use "invalid" status if field doesn't meet validation rules
- Provide specific feedback in validation messages
- Extract exactly what you see, don't infer missing information"""
    
    return prompt
```

### Step 3: UI Enhancement
Add document type selector to sidebar:

```python
# Update ui_components.py render_sidebar function
def render_sidebar():
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # Add document type selection
        from config import DOCUMENT_SCHEMAS
        st.subheader("📋 Document Type")
        
        document_type_options = {v['name']: k for k, v in DOCUMENT_SCHEMAS.items()}
        selected_doc_type_name = st.selectbox(
            "Select document type:",
            options=list(document_type_options.keys()),
            help="Choose the type of document you're uploading"
        )
        selected_doc_type = document_type_options[selected_doc_type_name]
        
        # Display schema preview
        if selected_doc_type:
            schema = DOCUMENT_SCHEMAS[selected_doc_type]
            with st.expander("📝 Expected Fields"):
                for field_name, field_def in schema['fields'].items():
                    required_marker = "🔴" if field_def['required'] else "⚪"
                    st.write(f"{required_marker} **{field_def['display_name']}**: {field_def['description']}")
        
        # Existing provider and model selection...
        # ... rest of existing function
        
        return selected_provider, selected_model, selected_provider_name, selected_model_name, uploaded_file, selected_doc_type
```

### Step 4: Enhanced Processing Logic
Update extraction to use schema-aware prompts:

```python
# Update app.py extraction logic
# Replace the generic prompt with:
if selected_doc_type:
    schema = DOCUMENT_SCHEMAS[selected_doc_type]
    prompt_text = create_schema_prompt(schema, schema['name'])
else:
    # Fallback to generic extraction
    prompt_text = "Analyze the text in the provided image. Extract all readable content and present it in JSON format"

# Update the completion call
response = completion(
    model=model_param,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        }
    ],
    temperature=0.1,  # Lower temperature for more consistent structured output
    max_tokens=1024
)
```

### Step 5: Enhanced Results Display
Update results rendering to show validation feedback:

```python
# Update ui_components.py render_results_content function
def render_results_content(result_text, is_json, parsed_data, formatted_result, document_type=None):
    if is_json and parsed_data:
        # Check for schema-aware extraction format
        if isinstance(parsed_data, dict) and "validation_results" in parsed_data:
            st.subheader("📊 Extracted Data with Validation")
            
            extracted_data = parsed_data.get("extracted_data", {})
            validation_results = parsed_data.get("validation_results", {})
            
            # Display in a nice table format
            for field_name, field_value in extracted_data.items():
                validation = validation_results.get(field_name, {})
                status = validation.get("status", "unknown")
                message = validation.get("message", "No validation info")
                
                # Status indicators
                status_icons = {
                    "valid": "✅",
                    "invalid": "❌", 
                    "warning": "⚠️",
                    "missing": "❓"
                }
                
                col1, col2, col3 = st.columns([2, 3, 4])
                with col1:
                    st.write(f"**{field_name}**")
                with col2:
                    st.write(f"{field_value}")
                with col3:
                    st.write(f"{status_icons.get(status, '❓')} {message}")
        
        # Existing JSON display logic...
    # ... rest of existing function
```

## Testing Scenarios

### Test 1: Valid National ID Document
**Given**: A clear National ID image with all required fields
**When**: User selects "National ID" type and uploads document
**Then**: 
- All fields extracted with "valid" status
- Validation messages confirm format correctness
- Confidence scores > 0.8 for clear text

### Test 2: Missing Required Field
**Given**: A National ID image missing the ID number
**When**: User processes the document
**Then**:
- Missing field shows "missing" status
- Validation message explains what was expected
- Other fields validate normally

### Test 3: Invalid Field Format
**Given**: A document with incorrectly formatted date
**When**: User processes the document
**Then**:
- Date field shows "invalid" status
- Validation message explains expected format
- Extracted value shows what was actually found

### Test 4: Fallback to Generic Extraction
**Given**: User doesn't select a specific document type
**When**: User uploads any document
**Then**:
- System uses generic extraction prompt
- Results displayed in original format
- No validation feedback shown

## Validation Checklist

- [ ] Document type selector appears in sidebar
- [ ] Schema preview shows expected fields
- [ ] Enhanced prompts include schema information
- [ ] Extraction results include validation feedback
- [ ] Invalid fields are clearly marked
- [ ] Missing fields are identified
- [ ] Confidence scores are displayed when available
- [ ] Fallback to generic extraction works
- [ ] PDF processing still works with schemas
- [ ] Cost tracking continues to function

## Performance Expectations

- **Processing Time**: 2-4 seconds (slight increase due to enhanced prompts)
- **Token Usage**: +15-25% increase due to schema information in prompts
- **Accuracy**: Improved due to structured extraction guidance
- **User Experience**: Enhanced with clear validation feedback

## Schema Management UI Extension

### Step 6: Dynamic Schema Storage
Set up dynamic schema storage system:

```bash
# Create data directory structure
mkdir -p data/schemas
mkdir -p data/templates
touch data/schema_metadata.db  # SQLite will create this
```

```python
# Add to requirements.txt
streamlit-elements>=0.1.0
python-jsonschema>=4.0.0

# Create schema_management/__init__.py
from .schema_storage import SchemaStorage
from .schema_builder import render_schema_builder
from .field_editor import render_field_editor
```

### Step 7: Schema Management Page
Create the main schema management interface:

```python
# Create schema_management/schema_builder.py
def render_schema_management_page():
    st.title("🏗️ Schema Management")
    
    # Tab interface
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Basic Info", "🔧 Fields", "✅ Validation", "👁️ Preview"])
    
    with tab1:
        render_basic_info_tab()
    with tab2:
        render_field_management_tab()
    with tab3:
        render_validation_rules_tab()
    with tab4:
        render_preview_tab()

# Add to app.py main navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Document Extraction", "Schema Management"],
    index=0
)

if page == "Schema Management":
    render_schema_management_page()
else:
    # Existing document extraction interface
    ...
```

### Step 8: Field Management with Drag-Drop
Implement rich field editor:

```python
# Create schema_management/field_editor.py
from streamlit_elements import elements, mui, html

def render_field_management_tab():
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Fields")
        # Field list with drag-drop
        with elements("field_list"):
            # Use streamlit-elements for drag-drop functionality
            for field in current_schema.get('fields', []):
                render_field_card(field)
    
    with col2:
        st.subheader("Field Editor")
        if selected_field:
            render_field_editor(selected_field)
```

### Step 9: Schema Templates
Create reusable field and validation templates:

```python
# Create data/templates/field_types.json
{
    "templates": {
        "personal_name": {
            "name": "Personal Name",
            "config": {
                "type": "string",
                "required": true,
                "validation_rules": [
                    {"type": "required", "message": "Name is required"},
                    {"type": "length", "min": 2, "max": 100}
                ]
            }
        },
        "government_id": {
            "name": "Government ID",
            "config": {
                "type": "string", 
                "required": true,
                "validation_rules": [
                    {"type": "pattern", "value": "^[A-Z0-9]{8,12}$"}
                ]
            }
        }
    }
}
```

### Step 10: Real-Time Preview
Add schema preview with live updates:

```python
# Create schema_management/preview.py
def render_preview_tab():
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Schema JSON")
        st.json(current_schema)
        
        # Download button
        st.download_button(
            "Download Schema",
            data=json.dumps(current_schema, indent=2),
            file_name=f"{current_schema['id']}_schema.json",
            mime="application/json"
        )
    
    with col2:
        st.subheader("Form Preview")
        # Show how the schema will appear to users
        for field_name, field_def in current_schema.get('fields', {}).items():
            render_field_preview(field_name, field_def)
```

## Extended Testing Scenarios

### Test 5: Schema Creation Workflow
**Given**: User accesses Schema Management page
**When**: User creates a new schema with custom fields
**Then**:
- Schema is saved to data/schemas/ directory
- Schema appears in document type selector
- Extraction works with new schema

### Test 6: Field Template Usage
**Given**: User is adding a new field
**When**: User selects a field template
**Then**:
- Field is pre-configured with template settings
- User can modify template values
- Custom changes are preserved

### Test 7: Schema Import/Export
**Given**: User has created custom schemas
**When**: User exports schemas to JSON file
**Then**:
- Schemas can be re-imported on another system
- Import validation catches conflicts
- Version compatibility is maintained

### Test 8: Real-Time Preview
**Given**: User is editing a schema
**When**: User makes changes to fields
**Then**:
- Preview updates immediately
- JSON format is always valid
- Form preview reflects changes

### Test 9: Schema Versioning
**Given**: User modifies an existing schema
**When**: User saves changes
**Then**:
- New version is created
- Old version is preserved
- Migration path is clear

## Extended Validation Checklist

### Schema Management UI
- [ ] Schema management page accessible from main navigation
- [ ] Multi-tab interface with Basic Info, Fields, Validation, Preview
- [ ] Drag-drop field reordering works
- [ ] Field templates available and functional
- [ ] Validation rule builder provides appropriate options
- [ ] Real-time preview updates correctly
- [ ] Schema save/load operations work
- [ ] Import/export functionality operational
- [ ] Schema versioning maintains history
- [ ] Integration with existing extraction workflow

### Data Persistence
- [ ] Schemas saved to data/schemas/ directory
- [ ] Metadata tracked in SQLite database
- [ ] Templates loaded from data/templates/
- [ ] Version control maintains audit trail
- [ ] Backup and recovery possible

### User Experience
- [ ] Intuitive interface design
- [ ] Clear validation error messages
- [ ] Responsive UI with loading states
- [ ] Help text and tooltips provided
- [ ] Keyboard shortcuts where appropriate

## Next Steps

After schema management UI implementation:
1. Add advanced field types (arrays, nested objects)
2. Implement schema sharing and collaboration features
3. Add schema analytics and usage tracking
4. Create schema validation API endpoints
5. Add automated testing for schema reliability
6. Implement schema migration tools
7. Add integration with external schema registries

## Performance Expectations (Extended)

- **Schema Loading**: <500ms for typical schemas
- **UI Responsiveness**: Real-time updates within 300ms
- **Storage Efficiency**: JSON files under 50KB each
- **Concurrent Access**: Multiple users can manage schemas
- **Memory Usage**: Minimal impact on main application

## Advanced Features

### Schema Collaboration
- Export/import for schema sharing
- Version control for team collaboration
- Schema validation and conflict resolution
- Backup and recovery procedures

### Integration Testing
- Schema compatibility with existing extractions
- Performance impact measurement
- Error handling and graceful degradation
- Migration path from static to dynamic schemas

## Support

For implementation questions or issues:
- Check existing code structure in modular components
- Review Streamlit documentation for advanced UI patterns
- Test streamlit-elements integration carefully
- Monitor performance with large schema collections
- Review LiteLLM documentation for model-specific considerations
- Test with both Llama Scout 17B and Mistral Small 3.2 models
- Monitor token usage and costs during development