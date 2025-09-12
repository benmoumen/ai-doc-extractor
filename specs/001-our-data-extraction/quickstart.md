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

## Next Steps

After basic implementation:
1. Add more document types (passport, business license, etc.)
2. Implement custom validation rules
3. Add schema versioning support
4. Create schema management UI
5. Add batch processing capabilities

## Support

For implementation questions or issues:
- Check existing code structure in modular components
- Review LiteLLM documentation for model-specific considerations
- Test with both Llama Scout 17B and Mistral Small 3.2 models
- Monitor token usage and costs during development