# Implementation Plan: Schema-Driven Document Data Extraction with Validation

**Branch**: `001-our-data-extraction` | **Date**: 2025-09-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-our-data-extraction/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → Feature spec loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detected web application type (frontend + backend)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → No major violations detected
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → Research tasks generated for technology decisions
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
6. Re-evaluate Constitution Check section
   → Post-design constitution compliance verified
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Primary requirement: Add schema-driven document data extraction with predefined document types (National ID, Passport, Business License) that validate extracted data through AI-integrated feedback. Users select document type, upload images/PDFs, and receive structured data with field-level validation results embedded in the AI's JSON response.

**EXTENSION**: Document types and schemas should be manageable via a rich UI, allowing administrators to create, edit, and manage document schemas without code changes.

Technical approach: Extend existing LLM-based extraction system with dynamic schema management UI, including a schema builder interface, field editor, validation rule configurator, and real-time schema preview capabilities.

## Technical Context
**Language/Version**: Python 3.12 + Streamlit (from existing codebase analysis)  
**Primary Dependencies**: Streamlit (UI framework), LiteLLM (unified LLM interface), PIL/PyMuPDF (document processing)  
**Storage**: Dynamic schema storage (JSON/database), document type persistence, version control for schemas  
**Testing**: pytest (backend), Streamlit testing framework, integration tests for AI workflows  
**Target Platform**: Streamlit web application (single process, browser interface)
**Project Type**: single - Streamlit application with modular components  
**Performance Goals**: <2s document processing, responsive schema editor, real-time preview  
**Constraints**: Rich UI for schema management, drag-drop field builder, validation rule editor  
**Scale/Scope**: Schema management for dozens of document types, field templates, validation presets

**Rich UI Requirements**: 
- Schema Builder: Visual interface for creating/editing document schemas
- Field Editor: Drag-and-drop field creation with type selection and validation rules
- Validation Configurator: UI for setting up field validation rules (required, format, pattern, etc.)
- Schema Preview: Real-time preview of how schema will appear to users
- Schema Import/Export: JSON schema import/export capabilities
- Version Management: Schema versioning and rollback capabilities

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 2 (backend API, frontend UI) (max 3 ✓)
- Using framework directly? (FastAPI/React directly, no heavy wrappers ✓)
- Single data model? (DocumentType, Schema, Field entities ✓)
- Avoiding patterns? (Simple service layer, no Repository/UoW ✓)

**Architecture**:
- EVERY feature as library? (document-schema lib, validation lib ✓)
- Libraries listed: [document-schema + schema management, ai-validation + LLM integration]
- CLI per library: [schema-cli --help/--version/--format, validation-cli --test/--validate]
- Library docs: llms.txt format planned? (Yes ✓)

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? (Contract tests first, then integration ✓)
- Git commits show tests before implementation? (Will enforce ✓)
- Order: Contract→Integration→E2E→Unit strictly followed? (Yes ✓)
- Real dependencies used? (Real LLM APIs, actual file uploads ✓)
- Integration tests for: new libraries, contract changes, shared schemas? (Yes ✓)
- FORBIDDEN: Implementation before test, skipping RED phase (Understood ✓)

**Observability**:
- Structured logging included? (JSON logs for AI calls, validation results ✓)
- Frontend logs → backend? (Error reporting, usage analytics ✓)
- Error context sufficient? (Field-level validation details ✓)

**Versioning**:
- Version number assigned? (0.1.0 for initial implementation ✓)
- BUILD increments on every change? (Yes ✓)
- Breaking changes handled? (Schema version compatibility ✓)

## Project Structure

### Documentation (this feature)
```
specs/001-our-data-extraction/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single Streamlit Application (current architecture)
/
├── app.py                    # Main Streamlit app
├── config.py                # Configuration and schema storage
├── schema_utils.py          # Schema management utilities
├── ui_components.py         # UI component modules
├── utils.py                 # General utilities
├── cost_tracking.py         # Cost and performance tracking
├── performance.py          # Performance monitoring
├── schema_management/       # NEW: Rich UI schema management
│   ├── __init__.py
│   ├── schema_builder.py    # Schema creation UI
│   ├── field_editor.py      # Field management UI
│   ├── validation_rules.py  # Validation configurator
│   ├── schema_storage.py    # Dynamic schema persistence
│   └── import_export.py     # Schema import/export
├── data/
│   ├── schemas/            # Dynamic schema storage (JSON)
│   └── templates/          # Field and validation templates
└── tests/
    ├── test_schema_management/
    └── test_integration/
```

**Structure Decision**: Option 1 (Single Streamlit Application) - extend existing modular architecture

## Phase 0: Outline & Research

Research tasks needed to resolve technical decisions for schema management UI extension:

1. **Streamlit Advanced UI Components**: Research rich UI capabilities in Streamlit
   - Decision: Native Streamlit vs custom components vs third-party libraries
   - Rationale: Need drag-drop, dynamic forms, real-time preview
   - Alternatives: streamlit-elements, streamlit-agraph, custom React components

2. **Dynamic Schema Storage**: Research persistent storage for user-created schemas  
   - Decision: File-based JSON vs SQLite vs cloud storage
   - Rationale: Version control, concurrent access, backup requirements
   - Alternatives: Local files vs database vs hybrid approach

3. **Schema Builder UI Patterns**: Research best practices for visual schema builders
   - Decision: Form-based vs drag-drop vs code editor hybrid
   - Rationale: User experience, complexity management, validation feedback
   - Alternatives: Step-by-step wizard vs single-page editor vs modular approach

4. **Field Type System**: Research extensible field type architecture
   - Decision: Fixed types vs plugin system vs custom field definitions
   - Rationale: Flexibility, validation consistency, future extensibility
   - Alternatives: Predefined types vs user-defined types vs template system

5. **Schema Versioning**: Research schema version management strategies
   - Decision: Git-like versioning vs simple versioning vs immutable schemas
   - Rationale: Rollback capabilities, migration support, audit trail
   - Alternatives: File versioning vs database versioning vs external version control

**Output**: research.md with all technical decisions documented for schema management UI

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

**Design Tasks**:

1. **Extract entities from feature spec** → `data-model.md`:
   - DocumentType: name, description, schema reference, version, created/modified dates
   - Schema: fields array, validation rules, required fields, version history
   - Field: name, type, validation rules, required status, display properties
   - ValidationResult: field name, status, error message, confidence
   - ExtractionResult: extracted data, validation results per field
   - **NEW Schema Management Entities**:
     - FieldTemplate: reusable field configurations for common field types
     - ValidationTemplate: common validation rule patterns
     - SchemaVersion: version control for schema changes
     - SchemaImportResult: results of schema import/validation

2. **Generate Streamlit interface contracts** from functional requirements:
   - Schema Management Page: Create/Edit/Delete schema functionality
   - Field Editor Component: Add/remove/configure fields interface  
   - Validation Rule Builder: UI for creating validation rules
   - Schema Preview Component: Real-time schema visualization
   - Import/Export Interface: JSON schema import/export capabilities
   - Contracts output to `/contracts/ui_contracts.md` (Streamlit interface specs)

3. **Generate component tests** from contracts:
   - test_schema_builder.py (schema creation and editing UI)
   - test_field_editor.py (field management interface)
   - test_validation_builder.py (validation rule configuration)
   - test_schema_storage.py (persistent storage operations)
   - test_import_export.py (schema import/export functionality)
   - Tests must fail initially (no implementation)

4. **Extract test scenarios** from user stories:
   - Integration test: Complete schema creation → document extraction workflow
   - Edge case tests: Invalid schema configurations, import failures
   - UI interaction tests: Form validation, real-time preview updates
   - Quickstart validation steps for schema management

5. **Update CLAUDE.md incrementally**:
   - Add schema management UI context
   - Include Streamlit advanced component patterns
   - Document dynamic schema storage approach
   - Preserve existing configurations

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs focusing on schema management UI
- Each UI component → component test task [P]
- Each entity → model/storage implementation task [P]
- Each user interaction → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Component tests → Integration tests → Implementation
- Dependency order: Storage → Models → UI Components → Integration
- Mark [P] for parallel execution (independent UI components)

**Estimated Output**: 35-40 numbered, ordered tasks focusing on:
1. Schema storage setup (4-5 tasks)
2. Data model extensions (5-6 tasks)
3. Schema management UI components (12-15 tasks)
   - Schema builder interface
   - Field editor with drag-drop
   - Validation rule configurator  
   - Schema preview and versioning
   - Import/export functionality
4. Integration with existing extraction flow (6-8 tasks)
5. Testing and validation (5-6 tasks)
6. Documentation and deployment (2-3 tasks)

**Key Focus Areas**:
- Rich UI components for schema building
- Dynamic schema persistence and versioning
- Real-time preview and validation
- Seamless integration with existing extraction workflow
- Import/export capabilities for schema portability

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations requiring justification*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - Extended with schema management UI research
- [x] Phase 1: Design complete (/plan command) - Extended data model and UI contracts created
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS - Schema management UI meets simplicity requirements
- [x] All NEEDS CLARIFICATION resolved - Technical decisions documented
- [x] Complexity deviations documented (none) - Hybrid storage approach justified

**Extension Status**:
- [x] Schema management UI research complete
- [x] Extended data model with UI entities (FieldTemplate, SchemaVersion, etc.)
- [x] UI component contracts defined in /contracts/ui_contracts.md
- [x] Quickstart updated with schema management workflow

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*