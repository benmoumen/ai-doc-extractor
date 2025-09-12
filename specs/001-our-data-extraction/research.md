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

## Extension Research: Schema Management UI

### Current State Analysis
The existing implementation provides a solid foundation with hardcoded schemas in `config.py`. The extension requirement is to make these schemas manageable via a rich UI.

### 6. Rich UI Schema Management
**Decision**: Hybrid Streamlit approach with streamlit-elements for advanced interactions
**Rationale**:
- Native Streamlit provides excellent forms, tabs, and basic widgets
- streamlit-elements enables drag-drop field reordering and dynamic components
- Maintains deployment simplicity (single Streamlit app)
- No separate frontend build process required

**Alternatives Considered**:
- Pure native Streamlit: Limited drag-drop and dynamic UI capabilities
- Separate React frontend: Breaks current architecture, adds deployment complexity
- Full custom components: Over-engineering for the scope

### 7. Dynamic Schema Storage
**Decision**: File-based JSON with SQLite for metadata
**Rationale**:
- JSON files maintain current approach while enabling user modifications
- SQLite provides versioning, metadata, and search capabilities
- Hybrid approach balances simplicity with functionality
- Easy backup and version control

**Storage Architecture**:
```
data/
├── schemas/              # User-created schemas (JSON)
│   ├── custom_national_id_v1.json
│   └── custom_passport_v1.json
├── templates/           # Field and validation templates
│   ├── field_types.json
│   └── validation_presets.json
└── schema_metadata.db   # SQLite: versions, timestamps, usage stats
```

### 8. Schema Builder UI Design
**Decision**: Multi-tab interface with real-time preview
**Rationale**:
- Tabs organize complexity (Basic Info, Fields, Validation, Preview)
- Real-time preview maintains immediate feedback
- Streamlit's native tab component provides good UX

**UI Structure**:
```
Schema Management (New Page)
├── Tab 1: Basic Info (name, description, category)
├── Tab 2: Field Management
│   ├── Field List (with drag-drop reordering via streamlit-elements)
│   ├── Add Field Interface
│   └── Field Editor (type, validation, display properties)
├── Tab 3: Validation Rules
│   ├── Field-level validation builder
│   └── Cross-field validation rules
└── Tab 4: Preview & Test
    ├── Schema preview (JSON + UI representation)
    └── Test extraction with sample document
```

### 9. Field Type System Extension
**Decision**: Template-based extensible field types
**Rationale**:
- Builds upon existing field type definitions
- Templates provide common configurations (address, phone, etc.)
- Custom field types enable future flexibility
- Maintains validation consistency

**Field Type Architecture**:
```python
FIELD_TYPES = {
    "text": {
        "display": "Text Field",
        "validation_options": ["required", "min_length", "max_length", "pattern"],
        "templates": ["name", "address", "description"]
    },
    "number": {
        "display": "Number Field", 
        "validation_options": ["required", "min_value", "max_value", "integer_only"],
        "templates": ["age", "amount", "quantity"]
    },
    # ... additional types
}
```

### 10. Schema Versioning Strategy
**Decision**: Simple version control with schema snapshots
**Rationale**:
- Version snapshots prevent accidental data loss
- Simple versioning (v1, v2, v3) easier to understand than git-like
- Rollback capability for production safety
- Audit trail for schema changes

**Version Management**:
```python
# Each schema change creates new version
# Old versions preserved for rollback
# Metadata tracks: version, timestamp, changes, creator
# Migration support for existing extraction workflows
```

## Implementation Strategy for Schema Management UI

### Phase 1: Storage Foundation
1. Create dynamic schema storage system
2. Migrate existing hardcoded schemas to JSON files
3. Build schema loading/saving utilities
4. Add basic CRUD operations

### Phase 2: Basic UI
1. Create schema management page in Streamlit
2. Basic form-based schema editing
3. Field addition/removal interface
4. Save/load functionality

### Phase 3: Advanced UI
1. Integrate streamlit-elements for drag-drop
2. Real-time preview functionality
3. Field templates and presets
4. Advanced validation rule builder

### Phase 4: Integration
1. Connect with existing extraction workflow
2. Schema selection integration
3. Backward compatibility maintenance
4. Testing and validation

### Performance and UX Considerations
- Session state management for large schemas
- Debounced real-time updates (300ms delay)
- Progressive loading for schema collections
- Error handling and validation feedback
- Export/import capabilities for schema sharing

## Conclusion
The existing architecture provides an excellent foundation for both the original schema-driven extraction and the new schema management UI extension. The hybrid approach using native Streamlit enhanced with streamlit-elements provides the rich UI capabilities required while maintaining the simplicity and deployment advantages of the current Streamlit-based solution. The file-based storage with SQLite metadata offers the right balance of functionality and simplicity for the schema management requirements.