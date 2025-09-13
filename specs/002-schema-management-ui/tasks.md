# Tasks: Schema Management UI Extension

**Input**: Design documents from `/specs/002-schema-management-ui/`
**Prerequisites**: plan.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓)

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✓ Tech stack: Python 3.11, Streamlit, streamlit-elements, python-jsonschema
   → ✓ Structure: Single project (extending existing Streamlit app)
2. Load optional design documents:
   → ✓ data-model.md: Schema, Field, ValidationRule, Template entities
   → ✓ contracts/: Schema storage and UI component contracts
   → ✓ research.md: Hybrid JSON+SQLite storage, drag-drop UI patterns
3. Generate tasks by category:
   → Setup: dependencies, module structure, database initialization
   → Tests: contract tests, integration tests (TDD enforced)
   → Core: storage, data models, UI components
   → Integration: app navigation, schema integration
   → Polish: validation, performance, documentation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness: ✓ All contracts have tests, entities have models
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `schema_management/`, `tests/` at repository root
- Extending existing Streamlit application architecture

## Phase 3.1: Setup & Infrastructure

- [x] **T001** Create schema_management module structure with __init__.py, subdirectories
- [x] **T002** Install and verify dependencies: streamlit-elements>=0.1.0, python-jsonschema>=4.0.0
- [x] **T003** [P] Create data directories: data/schemas/, data/templates/
- [x] **T004** [P] Initialize SQLite database with schema_metadata tables per data-model.md
- [x] **T005** [P] Configure pytest setup for schema_management module testing

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (Parallel)
- [x] **T006** [P] Schema storage contract tests in `tests/contract/test_schema_storage_contract.py`
- [x] **T007** [P] UI components contract tests in `tests/contract/test_ui_components_contract.py`
- [x] **T008** [P] Field editor contract tests in `tests/contract/test_field_editor_contract.py`
- [x] **T009** [P] Validation builder contract tests in `tests/contract/test_validation_builder_contract.py`

### Integration Tests (Parallel)
- [x] **T010** [P] Business analyst schema creation workflow in `tests/integration/test_schema_creation_workflow.py`
- [x] **T011** [P] Data manager schema modification workflow in `tests/integration/test_schema_modification_workflow.py` 
- [x] **T012** [P] QA specialist schema testing workflow in `tests/integration/test_schema_testing_workflow.py`
- [x] **T013** [P] Admin schema organization workflow in `tests/integration/test_schema_organization_workflow.py`

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models & Storage (Parallel Foundation)
- [x] **T014** [P] Schema entity model in `schema_management/models/schema.py`
- [x] **T015** [P] Field entity model in `schema_management/models/field.py`
- [x] **T016** [P] ValidationRule entity model in `schema_management/models/validation_rule.py`
- [x] **T017** [P] Template entities in `schema_management/models/templates.py`
- [x] **T018** [P] Hybrid storage manager in `schema_management/storage/schema_storage.py`

### Core Services (Sequential - depend on models)
- [x] **T019** Schema CRUD operations in `schema_management/services/schema_service.py`
- [x] **T020** Field management service in `schema_management/services/field_service.py`
- [x] **T021** Validation service in `schema_management/services/validation_service.py`
- [x] **T022** Template management service in `schema_management/services/template_service.py`

### UI Components (Parallel - different files)
- [x] **T023** [P] Basic info tab component in `schema_management/ui/basic_info.py`
- [x] **T024** [P] Field editor component in `schema_management/ui/field_editor.py`
- [x] **T025** [P] Field list with drag-drop in `schema_management/ui/field_list.py`
- [x] **T026** [P] Validation builder component in `schema_management/ui/validation_builder.py`
- [x] **T027** [P] Schema preview component in `schema_management/ui/preview.py`
- [x] **T028** [P] Import/export interface in `schema_management/ui/import_export.py`

### Main UI Integration
- [x] **T029** Main schema management page in `schema_management/schema_builder.py`
- [x] **T030** Session state management in `schema_management/state_manager.py`
- [x] **T031** Error handling and validation in `schema_management/error_handling.py`

## Phase 3.4: Integration & Navigation

- [x] **T032** App.py navigation integration with schema management page
- [x] **T033** Document type selector integration with custom schemas
- [x] **T034** Schema compatibility layer with existing extraction workflow
- [x] **T035** Performance optimizations: caching, debounced updates, lazy loading

## Phase 3.5: Polish & Validation

### Unit Tests (Parallel)
- [ ] **T036** [P] Schema model unit tests in `tests/unit/test_schema_model.py`
- [ ] **T037** [P] Field model unit tests in `tests/unit/test_field_model.py`
- [ ] **T038** [P] Storage service unit tests in `tests/unit/test_storage_service.py`
- [ ] **T039** [P] Validation service unit tests in `tests/unit/test_validation_service.py`

### Performance & Quality
- [ ] **T040** Performance tests: <500ms UI response, 100+ field schemas in `tests/performance/test_schema_performance.py`
- [ ] **T041** Error handling validation and recovery testing
- [ ] **T042** [P] Schema import/export functionality validation
- [ ] **T043** [P] Cross-browser Streamlit compatibility testing

### Documentation & Deployment
- [ ] **T044** [P] Update quickstart.md with complete implementation examples
- [ ] **T045** [P] Create schema_management module documentation
- [ ] **T046** [P] Update CLAUDE.md with implementation details and usage patterns
- [ ] **T047** End-to-end manual testing following quickstart.md procedures

## Dependencies

**Phase Dependencies**:
- Setup (T001-T005) → Tests (T006-T013) → Implementation (T014-T035) → Polish (T036-T047)

**Specific Dependencies**:
- T001-T005 must complete before any other tasks
- T006-T013 (tests) must FAIL before T014-T031 (implementation)
- T014-T018 (models/storage) block T019-T022 (services)
- T023-T028 (UI components) can run parallel to T014-T022
- T029-T031 require T014-T028 complete
- T032-T035 require T029-T031 complete

## Parallel Execution Examples

### Phase 3.2: Contract Tests (Run Together)
```bash
# Launch T006-T009 together:
Task: "Schema storage contract tests in tests/contract/test_schema_storage_contract.py"
Task: "UI components contract tests in tests/contract/test_ui_components_contract.py" 
Task: "Field editor contract tests in tests/contract/test_field_editor_contract.py"
Task: "Validation builder contract tests in tests/contract/test_validation_builder_contract.py"
```

### Phase 3.2: Integration Tests (Run Together)
```bash
# Launch T010-T013 together:
Task: "Business analyst schema creation workflow in tests/integration/test_schema_creation_workflow.py"
Task: "Data manager schema modification workflow in tests/integration/test_schema_modification_workflow.py"
Task: "QA specialist schema testing workflow in tests/integration/test_schema_testing_workflow.py" 
Task: "Admin schema organization workflow in tests/integration/test_schema_organization_workflow.py"
```

### Phase 3.3: Data Models (Run Together)
```bash
# Launch T014-T018 together:
Task: "Schema entity model in schema_management/models/schema.py"
Task: "Field entity model in schema_management/models/field.py"
Task: "ValidationRule entity model in schema_management/models/validation_rule.py"
Task: "Template entities in schema_management/models/templates.py"
Task: "Hybrid storage manager in schema_management/storage/schema_storage.py"
```

### Phase 3.3: UI Components (Run Together)
```bash
# Launch T023-T028 together:
Task: "Basic info tab component in schema_management/ui/basic_info.py"
Task: "Field editor component in schema_management/ui/field_editor.py"
Task: "Field list with drag-drop in schema_management/ui/field_list.py"
Task: "Validation builder component in schema_management/ui/validation_builder.py"
Task: "Schema preview component in schema_management/ui/preview.py"
Task: "Import/export interface in schema_management/ui/import_export.py"
```

## Task Details & Specifications

### T006: Schema Storage Contract Tests
**File**: `tests/contract/test_schema_storage_contract.py`
**Basis**: `/specs/002-schema-management-ui/contracts/schema_storage_contract.py`
**Requirements**: 
- Copy exact contract tests from specification
- Tests must FAIL initially (no implementation exists)
- Cover: save_schema, load_schema, list_schemas, delete_schema, version_management, usage_tracking, backup_restore

### T007: UI Components Contract Tests  
**File**: `tests/contract/test_ui_components_contract.py`
**Basis**: `/specs/002-schema-management-ui/contracts/ui_components_contract.py`
**Requirements**:
- Copy exact contract tests from specification
- Tests must FAIL initially (no implementation exists)
- Cover: render_schema_management_page, render_basic_info_tab, render_field_list, render_field_editor, render_validation_builder, render_schema_preview

### T014: Schema Entity Model
**File**: `schema_management/models/schema.py`
**Basis**: Data model specification in `/specs/002-schema-management-ui/data-model.md`
**Requirements**:
- Implement Schema class with all attributes from data model
- JSON serialization/deserialization methods
- Validation methods per data model rules
- Integration with FieldType and ValidationRule enums

### T018: Hybrid Storage Manager
**File**: `schema_management/storage/schema_storage.py`
**Basis**: Research decisions and data model storage architecture
**Requirements**:
- Implement hybrid JSON + SQLite storage strategy
- File naming: `{schema_id}_v{version}.json`
- SQLite tables per data model schema
- CRUD operations matching contract tests
- Version control and metadata management

### T029: Main Schema Management Page
**File**: `schema_management/schema_builder.py`
**Basis**: Quickstart implementation + UI contracts
**Requirements**:
- Main render_schema_management_page() function
- Tab-based interface: Basic Info, Fields, Validation, Preview
- Integration with all UI components (T023-T028)
- Session state management integration
- Navigation and workflow coordination

### T032: App.py Navigation Integration
**File**: `app.py` (existing file modification)
**Requirements**:
- Add schema management to sidebar navigation
- Page routing between extraction and schema management
- Graceful fallback if dependencies missing
- Preserve existing extraction functionality
- Share session state and configuration

## Notes

- **[P] tasks** = different files, no dependencies, can run parallel
- **TDD Enforcement**: All tests (T006-T013) must FAIL before implementation starts
- **Constitutional Compliance**: RED-GREEN-Refactor cycle strictly enforced
- **File Isolation**: Each [P] task modifies different files to ensure true parallelism
- **Version Control**: Commit after each task completion with descriptive messages

## Task Generation Rules Applied

1. **From Contracts**: 
   - ✅ schema_storage_contract.py → T006 contract test
   - ✅ ui_components_contract.py → T007 contract test

2. **From Data Model**:
   - ✅ Schema entity → T014 model creation task
   - ✅ Field entity → T015 model creation task
   - ✅ ValidationRule entity → T016 model creation task
   - ✅ Template entities → T017 model creation task

3. **From User Stories**:
   - ✅ Business analyst creates schema → T010 integration test
   - ✅ Data manager modifies schema → T011 integration test
   - ✅ QA specialist tests schema → T012 integration test
   - ✅ Admin organizes schemas → T013 integration test

4. **From Architecture**:
   - ✅ Hybrid storage strategy → T018 storage implementation
   - ✅ streamlit-elements integration → T024-T025 drag-drop components
   - ✅ App integration → T032 navigation integration

## Validation Checklist

✅ All contracts have corresponding tests (T006-T009)
✅ All entities have model tasks (T014-T017)  
✅ All tests come before implementation (T006-T013 before T014+)
✅ Parallel tasks truly independent (different files)
✅ Each task specifies exact file path
✅ No task modifies same file as another [P] task
✅ TDD cycle enforced (tests must fail first)
✅ Constitutional requirements met (library structure, testing order)

**Status**: ✅ READY FOR EXECUTION - All 47 tasks generated and validated