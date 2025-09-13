# Claude Code Context: AI Document Data Extractor

## Project Overview
Streamlit-based document data extraction application using LiteLLM for unified LLM API access. Currently supports Llama Scout 17B (via Groq) and Mistral Small 3.2 (via Mistral) for extracting structured data from images and PDFs.

## Current Architecture

### Core Components
- **app.py**: Main Streamlit application with extraction workflow
- **config.py**: API keys, model configuration, provider settings
- **utils.py**: JSON parsing, image/PDF processing utilities  
- **ui_components.py**: Modular UI components (sidebar, results, downloads)
- **cost_tracking.py**: Token usage and cost calculation
- **performance.py**: Processing time tracking and history

### Technology Stack
- **Frontend**: Streamlit web UI
- **LLM Integration**: LiteLLM with provider abstraction
- **Document Processing**: PyMuPDF (PDF), PIL (images)
- **Models**: Llama Scout 17B, Mistral Small 3.2
- **Deployment**: Python 3.11+, requirements-based

### Current Workflow
1. User selects provider/model in sidebar
2. Upload image or PDF document
3. Convert document to base64 for API
4. Send to LLM with generic extraction prompt
5. Parse JSON response and display results
6. Track costs and performance metrics

## Active Development: Schema Management UI Extension

### Feature Branch: `002-schema-management-ui`
Adding rich web-based interface for creating, editing, and managing document type schemas without code changes.

### Key Features in Development
- **Visual Schema Builder**: Drag-and-drop interface for creating document schemas
- **Field Management**: Advanced field editor with validation rule builder
- **Real-time Preview**: Live schema preview and testing capabilities
- **Import/Export**: Schema sharing and backup functionality
- **Version Control**: Schema versioning with migration support

### New Technology Stack
- **streamlit-elements**: Advanced UI components for drag-drop functionality
- **python-jsonschema**: Schema validation and compliance checking
- **SQLite + JSON**: Hybrid storage for metadata and schema content
- **Material-UI**: Professional UI components via streamlit-elements

### Implementation Approach
- Extend existing Streamlit app with new schema management module
- Hybrid storage: JSON files for schemas, SQLite for metadata/indexing
- Preserve existing schema compatibility and extraction workflow
- Test-driven development with comprehensive contract testing
- Modular architecture in schema_management/ package

## Development Guidelines

### Code Style
- Follow existing modular structure (separate concerns by file)
- Use Streamlit session state for UI state management
- Maintain LiteLLM abstraction for model switching
- Keep provider-agnostic implementation

### Testing Approach
- Test with both supported models (Llama Scout, Mistral Small)
- Verify fallback to generic extraction when no schema selected
- Validate cost tracking continues to work with enhanced prompts
- Test PDF and image processing with new schema features

### Schema Definition Pattern
```python
DOCUMENT_SCHEMAS = {
    "document_id": {
        "name": "Display Name",
        "description": "Brief description", 
        "fields": {
            "field_name": {
                "display_name": "Field Label",
                "type": "string|number|date|boolean",
                "required": True|False,
                "validation_rules": [...],
                "description": "Field purpose",
                "examples": [...]
            }
        }
    }
}
```

### Prompt Engineering Notes
- Use temperature=0.1 for consistent structured output
- Include specific validation instructions in prompts
- Request validation_results for every schema field
- Embed confidence scores when possible
- Maintain clarity for both Llama and Mistral models

## File Structure
```
/
├── app.py                 # Main application
├── config.py             # Configuration and schemas  
├── utils.py              # Utilities and prompt generation
├── ui_components.py      # UI components
├── cost_tracking.py      # Cost calculation
├── performance.py        # Performance monitoring
├── requirements.txt      # Dependencies
└── specs/001-our-data-extraction/  # Current feature specs
    ├── plan.md           # Implementation plan
    ├── research.md       # Technical decisions  
    ├── data-model.md     # Entity definitions
    ├── quickstart.md     # Implementation guide
    └── contracts/        # API specifications
```

## Recent Context Updates
- **2025-09-12**: Added schema-driven extraction feature planning
- **Architecture Decision**: Extend existing LiteLLM integration rather than rebuild
- **Schema Storage**: File-based configuration for simplicity
- **Validation Strategy**: AI-integrated validation in single API call

## Key Dependencies
```
streamlit              # Web UI framework
streamlit-elements     # Advanced UI components (NEW)
python-jsonschema      # Schema validation (NEW)
litellm               # Unified LLM API
pillow                # Image processing  
pymupdf               # PDF processing
```

## Development Commands
- `streamlit run app.py` - Start development server
- Check `.streamlit/secrets.toml` for API keys
- Models configured in `config.py` PROVIDER_OPTIONS/MODEL_OPTIONS

## Notes for Claude
- This is an active Streamlit project with working LLM integration
- Current focus: extending existing architecture with schema validation
- Preserve modular structure and existing functionality
- Test changes with both supported LLM providers
- Schema feature should enhance, not replace, current capabilities