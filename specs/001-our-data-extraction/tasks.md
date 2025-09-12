# Tasks: Schema Management UI Extension

**Input**: Design documents from `/specs/001-our-data-extraction/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/ui_contracts.md, quickstart.md
**Implementation Guide**: `/specs/001-our-data-extraction/implementation-guide.md` (detailed instructions with cross-references)

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Implementation plan found: Schema management UI for Streamlit app
   → Extract: Python 3.12 + Streamlit, extend existing modular structure
2. Load optional design documents:
   → data-model.md: FieldTemplate, ValidationTemplate, SchemaVersion, SchemaImportResult entities
   → contracts/: UI component contracts for schema management interface
   → research.md: Extend existing with streamlit-elements, dynamic storage
3. Generate tasks by category:
   → Setup: schema management module, dependencies, storage structure
   → Tests: UI component tests, integration tests, storage tests
   → Core: schema storage, UI components, field management, validation
   → Integration: existing workflow integration, template system
   → Polish: performance tests, error handling, documentation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness: All UI contracts tested, all entities implemented, integration complete
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Streamlit project**: Root-level Python files (app.py, config.py, utils.py, etc.)
- **Schema management**: New schema_management/ directory for UI components
- **Tests**: tests/ directory for new test files
- Paths assume single Streamlit project structure

## Phase 3.1: Setup & Infrastructure
- [ ] T001 Create schema management module structure at /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/
- [ ] T002 Create data directory structure for dynamic schema storage at /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/data/
- [ ] T003 [P] Install and configure streamlit-elements dependency in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/requirements.txt
- [ ] T004 [P] Create schema storage utilities in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/schema_storage.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T005 [P] Schema storage CRUD test in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_schema_management/test_schema_storage.py
- [ ] T006 [P] Schema builder UI component test in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_schema_management/test_schema_builder.py
- [ ] T007 [P] Field editor component test in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_schema_management/test_field_editor.py
- [ ] T008 [P] Validation rule builder test in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_schema_management/test_validation_builder.py
- [ ] T009 [P] Schema import/export functionality test in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_schema_management/test_import_export.py
- [ ] T010 [P] Template system test in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_schema_management/test_templates.py
- [ ] T011 [P] Integration test for complete schema management workflow in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_integration/test_schema_workflow.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T012 [P] Implement SchemaStorage class for dynamic schema persistence in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/schema_storage.py
- [ ] T013 [P] Create field template system in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/templates.py
- [ ] T014 [P] Implement validation template system in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/validation_templates.py
- [ ] T015 [P] Create schema version control utilities in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/versioning.py
- [ ] T016 Implement main schema management page in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/schema_builder.py
- [ ] T017 Create basic info tab component in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/basic_info.py
- [ ] T018 Implement field management tab with drag-drop in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/field_editor.py
- [ ] T019 Create validation rule builder component in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/validation_rules.py
- [ ] T020 Implement real-time schema preview in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/preview.py
- [ ] T021 Create schema import/export functionality in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/import_export.py

## Phase 3.4: Integration & Navigation
- [ ] T022 Add schema management navigation to main app in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/app.py
- [ ] T023 Update document type selector to use dynamic schemas in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/ui_components.py
- [ ] T024 Integrate dynamic schema loading with existing extraction workflow in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_utils.py
- [ ] T025 Update config.py to support hybrid static/dynamic schema loading in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/config.py
- [ ] T026 Add session state management for schema builder in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/state_manager.py
- [ ] T027 Implement error handling and user feedback in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/error_handling.py

## Phase 3.5: Advanced Features & Polish
- [ ] T028 [P] Create default field and validation templates in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/data/templates/
- [ ] T029 [P] Implement schema testing interface for validation in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/testing.py
- [ ] T030 [P] Add performance optimization for large schemas in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/performance.py
- [ ] T031 [P] Unit tests for individual schema management utilities in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_schema_management/test_utilities.py
- [ ] T032 Add comprehensive error handling and validation in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/validators.py
- [ ] T033 Update existing documentation with schema management features in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/CLAUDE.md

## Dependencies
- Setup (T001-T004) before tests (T005-T011)
- Tests (T005-T011) before implementation (T012-T021)
- T012 (storage) blocks T013-T015 (template systems)
- T016 (main page) blocks T017-T021 (UI components)
- Core implementation (T012-T021) before integration (T022-T027)
- Integration before polish (T028-T033)

## Parallel Example
```
# Launch T005-T010 together (Tests First):
Task: "Schema storage CRUD test in tests/test_schema_management/test_schema_storage.py - create failing tests for dynamic schema loading, saving, versioning, and template management"
Task: "Schema builder UI component test in tests/test_schema_management/test_schema_builder.py - create failing tests for main schema management interface with multi-tab functionality"
Task: "Field editor component test in tests/test_schema_management/test_field_editor.py - create failing tests for drag-drop field management with validation"
Task: "Validation rule builder test in tests/test_schema_management/test_validation_builder.py - create failing tests for visual validation rule creation interface"
Task: "Schema import/export test in tests/test_schema_management/test_import_export.py - create failing tests for JSON schema import/export with validation"
Task: "Template system test in tests/test_schema_management/test_templates.py - create failing tests for field and validation template management"

# Launch T012-T015 together (Core Storage):
Task: "Implement SchemaStorage class in schema_management/schema_storage.py - dynamic schema persistence with JSON files and SQLite metadata"
Task: "Create field template system in schema_management/templates.py - reusable field configurations with category organization"
Task: "Implement validation template system in schema_management/validation_templates.py - common validation patterns for field types"
Task: "Create schema version control in schema_management/versioning.py - version management with rollback and audit trail"
```

## Task Details

**📖 For detailed implementation instructions with code examples and cross-references, see `/specs/001-our-data-extraction/implementation-guide.md`**

### T001: Schema Management Module Structure  
**Reference**: Implementation Guide Setup Phase → T001 section
Create `/Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_management/` directory with `__init__.py`. Set up module structure for UI components, storage, and utilities.

### T002: Data Directory Structure  
**Reference**: Implementation Guide Setup Phase → T002 section  
**Cross-ref**: research.md Storage Architecture (lines 164-174)
Create `/Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/data/schemas/` and `/Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/data/templates/` directories. Initialize SQLite database for metadata at `data/schema_metadata.db`.

### T003: Streamlit Elements Dependency  
**Reference**: Implementation Guide Setup Phase → T003 section  
**Cross-ref**: research.md streamlit-elements decision (lines 143-154)
Add streamlit-elements>=0.1.0 and python-jsonschema>=4.0.0 to requirements.txt for advanced UI components and schema validation.

### T004: Schema Storage Utilities  
**Reference**: Implementation Guide Setup Phase → T004 section  
**Cross-ref**: data-model.md Storage Strategy (lines 324-346)
Create base schema storage interface and file system utilities for JSON schema persistence and SQLite metadata management.

### T005: Schema Storage CRUD Tests  
**Reference**: Implementation Guide Tests Phase → T005 section  
**Cross-ref**: data-model.md entities (lines 181-307)
Write failing tests for schema creation, reading, updating, deletion, and version management functionality.

### T006: Schema Builder UI Tests  
**Reference**: Implementation Guide Tests Phase → T006 section  
**Cross-ref**: contracts/ui_contracts.md Main Interface Contract (lines 15-28)
Write failing tests for main schema management page with multi-tab interface and navigation state management.

### T007: Field Editor Component Tests  
**Reference**: Implementation Guide Tests Phase → T007 section  
**Cross-ref**: contracts/ui_contracts.md Field Editor Contract (lines 94-131)
Write failing tests for drag-drop field list, field configuration editor, and field type selection components.

### T008: Validation Rule Builder Tests  
**Reference**: Implementation Guide Tests Phase → T008 section
Write failing tests for visual validation rule creation, rule type selection, and validation parameter configuration.

### T009: Import/Export Tests  
**Reference**: Implementation Guide Tests Phase → T009 section
Write failing tests for JSON schema import with validation, export functionality, and conflict resolution.

### T010: Template System Tests  
**Reference**: Implementation Guide Tests Phase → T010 section
Write failing tests for field template management, validation template application, and template categorization.

### T011: Integration Workflow Tests  
**Reference**: Implementation Guide Tests Phase → T011 section
Write failing end-to-end tests for complete schema creation → document extraction workflow integration.

### T012: SchemaStorage Implementation  
**Reference**: Implementation Guide Core Implementation → T012 section  
**Cross-ref**: data-model.md Storage Strategy (lines 324-346)
Implement dynamic schema persistence with JSON file storage and SQLite metadata tracking including version control.

### T013: Field Template System  
**Reference**: Implementation Guide Core Implementation → T013 section  
**Cross-ref**: data-model.md FieldTemplate (lines 181-209)
Create reusable field configuration templates organized by categories (personal, contact, identification, etc.).

### T014: Validation Template System  
**Reference**: Implementation Guide Core Implementation → T014 section  
**Cross-ref**: data-model.md ValidationTemplate (lines 212-235)
Implement common validation rule patterns applicable to different field types with reusable configurations.

### T015: Schema Version Control
Create version management system with schema snapshots, rollback capabilities, and migration support.

### T016: Main Schema Management Page
Implement primary schema management interface with multi-tab layout (Basic Info, Fields, Validation, Preview).

### T017: Basic Info Tab Component
Create schema basic information form with name, description, category selection, and validation.

### T018: Field Management Tab
Implement drag-drop field list with streamlit-elements, field addition/removal, and field configuration editor.

### T019: Validation Rule Builder
Create visual interface for building field validation rules with type-specific parameter inputs and templates.

### T020: Real-Time Schema Preview
Implement live schema preview with JSON display, form visualization, and download functionality.

### T021: Import/Export Functionality
Create schema import from JSON files with validation, export capabilities, and conflict resolution interface.

### T022: Navigation Integration
Add schema management page navigation to main Streamlit app with page selection and state management.

### T023: Dynamic Schema Integration
Update document type selector to load from both static config and dynamic user-created schemas.

### T024: Extraction Workflow Integration
Modify existing extraction workflow to support dynamic schemas with seamless fallback to static schemas.

### T025: Hybrid Schema Loading
Update config.py to support loading schemas from multiple sources with proper priority and caching.

### T026: Session State Management
Implement comprehensive session state management for schema builder with unsaved changes tracking.

### T027: Error Handling System
Create robust error handling with user-friendly feedback, validation messages, and graceful degradation.

### T028: Default Templates
Create comprehensive set of default field and validation templates for common document types and field patterns.

### T029: Schema Testing Interface
Implement interface for testing schemas with sample documents and validation feedback display.

### T030: Performance Optimization
Add performance optimizations for large schema collections with lazy loading and caching mechanisms.

### T031: Unit Tests
Create comprehensive unit tests for individual schema management utilities and helper functions.

### T032: Validation System
Implement comprehensive schema validation with clear error messages and user guidance.

### T033: Documentation Updates
Update project documentation with schema management features, usage examples, and troubleshooting guide.

## Notes
- [P] tasks = different files, can run in parallel
- Verify tests fail before implementing (TDD requirement)
- Maintain existing functionality while adding schema management features  
- Test with both static and dynamic schemas
- Ensure drag-drop functionality works with streamlit-elements

## Validation Checklist
*GATE: Checked before execution*

- [x] All UI contracts from data-model.md have corresponding implementation tasks
- [x] All entities (FieldTemplate, ValidationTemplate, SchemaVersion) have model tasks
- [x] Schema management UI components covered comprehensively
- [x] Tests come before implementation (TDD)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Integration with existing extraction workflow preserved
- [x] Hybrid static/dynamic schema loading supported