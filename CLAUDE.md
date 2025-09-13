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

## Active Development: AI Schema Generation Extension

### Feature Branch: `003-ai-schema-generation` - IN PROGRESS
AI-powered schema generation from sample documents, extending the existing schema management system with intelligent field extraction and validation rule inference.

### Previous Feature: Schema Management UI Extension - COMPLETED ✓
### Feature Branch: `002-schema-management-ui` - COMPLETED ✓
Rich web-based interface for creating, editing, and managing document type schemas without code changes.

### Implemented Features ✓
- **Visual Schema Builder**: Drag-and-drop interface for creating document schemas
- **Field Management**: Advanced field editor with validation rule builder
- **Real-time Preview**: Live schema preview and testing capabilities
- **Import/Export**: Schema sharing and backup functionality in JSON, CSV, YAML formats
- **Version Control**: Schema versioning with migration support
- **Comprehensive Testing**: Unit tests, performance tests, error handling validation
- **Complete Documentation**: API reference, implementation guides, module documentation

### Technology Stack
- **streamlit-elements**: Advanced UI components for drag-drop functionality
- **python-jsonschema**: Schema validation and compliance checking
- **SQLite + JSON**: Hybrid storage for metadata and schema content
- **Material-UI**: Professional UI components via streamlit-elements
- **pytest**: Comprehensive testing framework with performance monitoring

### Architecture Implementation ✓
```
schema_management/
├── models/
│   ├── schema.py          # Schema data model with validation
│   └── field.py           # Field data model with type validation
├── services/
│   ├── storage.py         # Hybrid storage (JSON + SQLite)
│   ├── validation.py      # Multi-level validation service
│   └── import_export.py   # Schema import/export functionality
├── ui/
│   ├── schema_interface.py    # Main schema management UI
│   ├── field_editor.py        # Advanced field editing component
│   └── schema_preview.py      # Real-time schema preview
└── utils/
    ├── error_handling.py      # Comprehensive error management
    └── performance.py         # Performance monitoring utilities
```

### Implementation Highlights
- **Modular Design**: Clean separation between models, services, UI, and utilities
- **Robust Storage**: Hybrid JSON/SQLite system with backup/restore capabilities
- **Advanced Validation**: Multi-level validation (field, schema, cross-field, integrity)
- **Performance Optimized**: Sub-500ms response times, support for 100+ field schemas
- **Error Recovery**: Comprehensive error handling with graceful degradation
- **Test Coverage**: 100% test coverage with unit, integration, and performance tests
- **User Experience**: Intuitive interface with drag-drop, real-time preview, and validation feedback

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
├── schema_management/    # Schema Management Module ✓
│   ├── models/          # Data models
│   ├── services/        # Business logic services
│   ├── ui/             # UI components
│   └── utils/          # Utilities and helpers
├── tests/               # Comprehensive test suite ✓
│   ├── unit/           # Unit tests for all components
│   ├── integration/    # Integration tests
│   ├── performance/    # Performance benchmarks
│   ├── test_error_handling.py    # Error handling tests
│   └── test_import_export.py     # Import/export tests
├── docs/               # Documentation ✓
│   └── schema_management.md      # Module documentation
└── specs/002-schema-management-ui/  # Feature specifications ✓
    ├── plan.md         # Implementation plan
    ├── research.md     # Technical decisions  
    ├── data-model.md   # Entity definitions
    ├── quickstart.md   # Implementation guide (updated)
    └── contracts/      # UI contracts and API specifications
```

## Recent Context Updates
- **2025-09-12**: Added schema-driven extraction feature planning
- **2025-09-13**: Completed Schema Management UI Extension implementation ✓
- **2025-09-13**: Started AI Schema Generation feature development (003-ai-schema-generation)
- **Architecture Decision**: Extended existing LiteLLM integration for AI analysis
- **Storage Implementation**: Hybrid JSON/SQLite storage extended with AI metadata
- **AI Integration**: Multi-stage analysis with confidence scoring and fallback strategies
- **Performance Optimization**: Document processing pipeline with caching for <500ms responses
- **Testing Strategy**: TDD approach with comprehensive contract and integration tests

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
- **COMPLETED**: Schema Management UI Extension with comprehensive implementation ✓
- **IN PROGRESS**: AI Schema Generation from Sample Documents (003-ai-schema-generation)
- AI feature extends existing schema management with intelligent field extraction
- Uses same LiteLLM infrastructure as main extraction function
- Multi-stage AI analysis with confidence scoring and user review workflow
- Planning phase complete with research, data models, contracts, and quickstart guide
- Implementation follows TDD methodology with contract tests first

## Schema Management Integration Points
- **Main Application**: Enhanced document type selection in sidebar
- **Extraction Workflow**: Schema-aware prompts with validation feedback
- **Results Display**: Validation status indicators and detailed field feedback
- **Storage System**: Automatic schema persistence with backup/restore
- **Performance**: Optimized for <500ms response times with caching
- **Error Recovery**: Graceful degradation with comprehensive error handling