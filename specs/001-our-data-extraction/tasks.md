# Tasks: Schema-Driven Document Data Extraction

**Input**: Design documents from `/specs/001-our-data-extraction/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Implementation plan found: Schema-driven extraction for Streamlit app
   → Extract: Streamlit + LiteLLM, extend existing modular structure
2. Load optional design documents:
   → data-model.md: DocumentType, Schema, Field, ValidationResult entities
   → contracts/: API structure for reference (Streamlit doesn't need REST API)
   → research.md: Extend existing LiteLLM integration, file-based schemas
3. Generate tasks by category:
   → Setup: schema configuration, enhanced utils
   → Tests: validation tests, integration tests
   → Core: schema management, prompt engineering, UI enhancements
   → Integration: enhanced results display, cost tracking
   → Polish: unit tests, documentation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness: All entities covered, UI enhanced, validation integrated
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Streamlit project**: Root-level Python files (app.py, config.py, utils.py, etc.)
- **Tests**: tests/ directory for new test files
- Paths assume single Streamlit project structure

## Phase 3.1: Setup
- [ ] T001 Create tests directory structure for schema validation tests
- [ ] T002 [P] Add schema configuration structure to /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/config.py
- [ ] T003 [P] Create schema validation utilities in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_utils.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T004 [P] Schema loading and validation test in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_schema_validation.py
- [ ] T005 [P] Prompt generation test in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_prompt_generation.py
- [ ] T006 [P] Document type selection integration test in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_document_type_integration.py
- [ ] T007 [P] Validation result parsing test in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_validation_parsing.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T008 [P] Implement DOCUMENT_SCHEMAS configuration in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/config.py
- [ ] T009 [P] Implement schema-aware prompt generation in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_utils.py
- [ ] T010 [P] Create enhanced JSON parsing for validation results in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/utils.py
- [ ] T011 Add document type selector to sidebar in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/ui_components.py
- [ ] T012 Integrate schema-aware prompt in main extraction flow in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/app.py
- [ ] T013 Update results display with validation feedback in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/ui_components.py
- [ ] T014 Add schema preview display in sidebar in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/ui_components.py

## Phase 3.4: Integration
- [ ] T015 Integrate document type selection with extraction workflow in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/app.py
- [ ] T016 Update session state management for schema features in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/app.py
- [ ] T017 Ensure cost tracking works with enhanced prompts in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/app.py
- [ ] T018 Add fallback to generic extraction when no schema selected in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/app.py

## Phase 3.5: Polish
- [ ] T019 [P] Unit tests for schema utility functions in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_schema_utils_unit.py
- [ ] T020 [P] Unit tests for validation result parsing in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_validation_utils_unit.py
- [ ] T021 [P] Performance test for enhanced prompts (<3s processing) in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/test_performance.py
- [ ] T022 Add additional document type schemas (passport, business license) in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/config.py
- [ ] T023 Update CLAUDE.md with implementation details in /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/CLAUDE.md

## Dependencies
- Setup (T001-T003) before tests (T004-T007)
- Tests (T004-T007) before implementation (T008-T014)
- T008 (schemas) blocks T009 (prompt generation)
- T009 (prompts) blocks T012 (integration)
- T010 (parsing) blocks T013 (results display)
- T011 (selector) blocks T015 (integration)
- Core implementation (T008-T014) before integration (T015-T018)
- Integration before polish (T019-T023)

## Parallel Example
```
# Launch T004-T007 together (Tests First):
Task: "Schema loading and validation test in tests/test_schema_validation.py - create failing tests for DOCUMENT_SCHEMAS loading, field validation, and schema structure verification"
Task: "Prompt generation test in tests/test_prompt_generation.py - create failing tests for create_schema_prompt function with different document types"
Task: "Document type integration test in tests/test_document_type_integration.py - create failing tests for complete workflow with schema selection"
Task: "Validation parsing test in tests/test_validation_parsing.py - create failing tests for parsing AI responses with validation results"

# Launch T008-T010 together (Core Models):
Task: "Implement DOCUMENT_SCHEMAS in config.py - add national_id schema with full field definitions and validation rules"
Task: "Schema-aware prompt generation in schema_utils.py - implement create_schema_prompt function"
Task: "Enhanced JSON parsing in utils.py - extend extract_and_parse_json to handle validation results"
```

## Task Details

### T001: Create tests directory structure
Create `/Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/tests/` directory with `__init__.py`. Set up structure for integration and unit tests.

### T002: Schema configuration in config.py
Add DOCUMENT_SCHEMAS dictionary with at least "national_id" document type including fields (full_name, id_number, date_of_birth) with validation rules and examples.

### T003: Schema validation utilities
Create `/Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor/schema_utils.py` with functions for schema loading, validation, and prompt generation.

### T004: Schema validation tests
Write failing tests for schema structure validation, field requirement checking, and validation rule parsing.

### T005: Prompt generation tests
Write failing tests for `create_schema_prompt()` function with different document types and edge cases.

### T006: Integration tests
Write failing end-to-end tests for document type selection → extraction → validation feedback workflow.

### T007: Validation parsing tests
Write failing tests for parsing AI responses containing extracted_data and validation_results sections.

### T008: Implement schemas
Add complete DOCUMENT_SCHEMAS configuration to config.py with national_id document type and all required fields.

### T009: Prompt generation
Implement `create_schema_prompt()` function that generates schema-aware extraction prompts with validation instructions.

### T010: Enhanced parsing
Extend `extract_and_parse_json()` to handle new validation results format from AI responses.

### T011: Document type selector
Add selectbox for document type selection in sidebar with schema preview functionality.

### T012: Integration with extraction
Modify main extraction flow in app.py to use schema-aware prompts when document type is selected.

### T013: Validation results display
Update `render_results_content()` to show validation feedback with status indicators (✅❌⚠️❓).

### T014: Schema preview
Add expandable section in sidebar showing expected fields and their descriptions for selected document type.

### T015-T018: Integration tasks
Connect all components together, ensure session state management, and maintain backward compatibility.

### T019-T023: Polish and enhancement
Add comprehensive unit tests, performance validation, additional document types, and documentation updates.

## Notes
- [P] tasks = different files, can run in parallel
- Verify tests fail before implementing (TDD requirement)
- Maintain existing functionality while adding schema features  
- Test with both Llama Scout 17B and Mistral Small 3.2
- Keep token usage monitoring for enhanced prompts

## Validation Checklist
*GATE: Checked before execution*

- [x] All entities from data-model.md have corresponding implementation tasks
- [x] Schema loading and validation covered
- [x] UI enhancements for document type selection included
- [x] Validation feedback display implemented
- [x] Tests come before implementation (TDD)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Backward compatibility maintained
- [x] Integration with existing LiteLLM architecture preserved