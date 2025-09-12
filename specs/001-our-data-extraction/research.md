# Research Findings: Schema-Driven Document Data Extraction

## Current Architecture Analysis

The existing codebase is a Streamlit-based document extraction application with the following key components:

### Current LLM Integration
- **Framework**: LiteLLM for unified API interface
- **Models**: Llama Scout 17B (via Groq) and Mistral Small 3.2 (via Mistral)
- **Integration Pattern**: Direct `completion()` calls with provider prefixes
- **Current Prompt**: Generic text extraction to JSON format

### Existing Infrastructure
- **Frontend**: Streamlit web UI (`app.py` with modular components)
- **Document Processing**: PyMuPDF for PDF-to-image conversion, PIL for image handling
- **Cost Tracking**: Built-in token usage and cost calculation
- **Performance Monitoring**: Timing data collection and history tracking

## Research Decisions

### 1. LLM Integration Patterns
**Decision**: Extend existing LiteLLM architecture with schema-aware prompting
**Rationale**: 
- LiteLLM already provides unified interface for both target models
- Existing cost tracking and performance monitoring can be preserved
- Provider switching mechanism already implemented
- No need for additional abstraction layers

**Alternatives Considered**:
- Direct API integration: Rejected due to loss of unified interface
- New LLM abstraction layer: Rejected due to existing working solution
- Model-specific implementations: Rejected due to current provider flexibility

### 2. Document Processing Pipeline
**Decision**: Build upon existing image/PDF processing with schema integration
**Rationale**:
- PyMuPDF already handles PDF-to-image conversion effectively
- Base64 encoding pipeline established and working
- Image quality optimization (2x zoom) already implemented

**Alternatives Considered**:
- Client-side preprocessing: Rejected due to bandwidth and processing constraints
- Alternative PDF libraries: Rejected due to current stability
- Raw document analysis: Rejected due to model limitations

### 3. Schema Storage Strategy
**Decision**: File-based schema definitions with in-memory caching
**Rationale**:
- Simple deployment model matches current Streamlit architecture
- No database dependency required for small-scale operation
- Easy version control and modification of schema definitions
- Fits existing configuration pattern (config.py)

**Alternatives Considered**:
- Database storage: Rejected due to added infrastructure complexity
- External API: Rejected due to deployment simplicity requirements
- Dynamic schema creation: Rejected due to validation consistency needs

### 4. Validation Integration Approach
**Decision**: Enhanced prompt engineering with structured validation instructions
**Rationale**:
- Both Llama Scout 17B and Mistral Small 3.2 excel at structured output
- Current JSON parsing logic can be extended
- Maintains single API call efficiency
- Validation feedback embedded in model response

**Alternatives Considered**:
- Post-processing validation: Rejected due to loss of model context
- Separate validation calls: Rejected due to cost and latency
- Rule-based validation: Rejected due to flexibility limitations

### 5. UI Enhancement Strategy
**Decision**: Extend existing Streamlit components with document type selection
**Rationale**:
- Current modular UI structure (`ui_components.py`) supports easy extension
- Streamlit's form handling suitable for document type selection
- Existing two-column layout can accommodate new controls

**Alternatives Considered**:
- Complete UI rewrite: Rejected due to working current implementation
- Separate web framework: Rejected due to deployment simplicity
- React frontend: Rejected due to added complexity

## Technical Implementation Approach

### Schema Definition Format
```python
# Document type schemas as Python dictionaries in config
DOCUMENT_SCHEMAS = {
    "national_id": {
        "name": "National ID",
        "fields": {
            "full_name": {"type": "string", "required": True, "validation": "non_empty"},
            "id_number": {"type": "string", "required": True, "validation": "alphanumeric"},
            "date_of_birth": {"type": "date", "required": True, "validation": "date_format"},
            "address": {"type": "string", "required": False, "validation": "non_empty"}
        }
    }
}
```

### Enhanced Prompt Structure
```python
def create_schema_prompt(schema, document_type_name):
    return f"""
    Analyze the {document_type_name} document in the image. 
    Extract data according to this schema and include validation status for each field:
    
    Expected fields: {json.dumps(schema['fields'], indent=2)}
    
    Return JSON with format:
    {{
        "extracted_data": {{field_name: value, ...}},
        "validation_results": {{field_name: {{"status": "valid/invalid", "message": "details"}}, ...}}
    }}
    """
```

### Integration Points
1. **Config Extension**: Add schema definitions to `config.py`
2. **UI Enhancement**: New document type selector in sidebar
3. **Prompt Engineering**: Schema-aware prompt generation
4. **Result Processing**: Enhanced JSON parsing for validation results
5. **Display Enhancement**: Validation feedback in results UI

## Performance Considerations
- **Latency**: Single API call maintains current performance (~2-3 seconds)
- **Cost**: Minimal increase due to enhanced prompts (estimated +10-15% tokens)
- **Scalability**: File-based schemas support dozens of document types
- **Memory**: In-memory schema caching minimal impact

## Risk Mitigation
- **Model Consistency**: Use temperature=0.1 for more consistent structured output
- **Fallback Strategy**: Maintain current extraction if schema validation fails
- **Error Handling**: Graceful degradation to current functionality
- **Schema Validation**: Pre-validate schema definitions at startup

## Conclusion
The existing architecture provides an excellent foundation for schema-driven extraction. The modular design, established LLM integration, and working document processing pipeline can be naturally extended without major architectural changes. The approach maintains the simplicity and effectiveness of the current solution while adding the requested schema validation capabilities.