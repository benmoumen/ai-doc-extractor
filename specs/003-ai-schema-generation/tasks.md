# Tasks: AI-Powered Schema Generation from Sample Documents

**Input**: Design documents from `/specs/003-ai-schema-generation/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Extract: Python 3.11, Streamlit, LiteLLM, streamlit-elements, pytest
   → Structure: Single project extending existing Streamlit application
2. Load optional design documents: ✓
   → data-model.md: SampleDocument, AIAnalysisResult, ExtractedField, ValidationRuleInference, DocumentTypeSuggestion, GeneratedSchema
   → contracts/: ai_analyzer_service.yaml, schema_generator_service.yaml, ui_integration_api.yaml
   → research.md: Multi-stage extraction, confidence scoring, performance optimization
3. Generate tasks by category: ✓
   → Setup: ai_schema_generation module, dependencies, database extensions
   → Tests: contract tests, integration tests
   → Core: models, services, UI components
   → Integration: storage, AI processing, UI workflow
   → Polish: unit tests, performance, documentation
4. Apply task rules: ✓
   → Different files = mark [P] for parallel
   → Tests before implementation (TDD)
   → Constitutional compliance: library approach, RED-GREEN-Refactor
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `ai_schema_generation/`, `tests/` at repository root
- Extends existing Streamlit application architecture
- Follows existing schema management patterns

## Phase 3.1: Setup

- [ ] **T001** Create ai_schema_generation module structure with models/, services/, ui/, utils/ subdirectories
- [ ] **T002** [P] Create database schema extensions in ai_schema_generation/storage/ai_schema_extensions.sql
- [ ] **T003** [P] Configure pytest for AI schema generation tests in tests/ai_schema_generation/
- [ ] **T004** [P] Add AI schema generation dependencies to requirements.txt (no new dependencies needed)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests [P] - All can run in parallel
- [ ] **T005** [P] Contract test POST /analyze_document in tests/ai_schema_generation/contract/test_ai_analyzer_contract.py
- [ ] **T006** [P] Contract test POST /analyze_document/confidence_scores in tests/ai_schema_generation/contract/test_confidence_scoring_contract.py
- [ ] **T007** [P] Contract test POST /analyze_document/retry in tests/ai_schema_generation/contract/test_analysis_retry_contract.py
- [ ] **T008** [P] Contract test POST /generate_schema in tests/ai_schema_generation/contract/test_schema_generator_contract.py
- [ ] **T009** [P] Contract test POST /generate_schema/validation_rules in tests/ai_schema_generation/contract/test_validation_rules_contract.py
- [ ] **T010** [P] Contract test POST /generate_schema/preview in tests/ai_schema_generation/contract/test_schema_preview_contract.py
- [ ] **T011** [P] Contract test POST /save_generated_schema in tests/ai_schema_generation/contract/test_schema_save_contract.py
- [ ] **T012** [P] Contract test POST /ui/upload_sample_document in tests/ai_schema_generation/contract/test_ui_upload_contract.py
- [ ] **T013** [P] Contract test GET /ui/analysis_progress/{document_id} in tests/ai_schema_generation/contract/test_ui_progress_contract.py
- [ ] **T014** [P] Contract test POST /ui/transition_to_editor in tests/ai_schema_generation/contract/test_ui_transition_contract.py

### Integration Tests [P] - Different user scenarios
- [ ] **T015** [P] Integration test complete workflow: upload→analyze→generate→save in tests/ai_schema_generation/integration/test_complete_workflow.py
- [ ] **T016** [P] Integration test PDF invoice analysis and schema generation in tests/ai_schema_generation/integration/test_pdf_invoice_workflow.py
- [ ] **T017** [P] Integration test image document (driver's license) workflow in tests/ai_schema_generation/integration/test_image_document_workflow.py
- [ ] **T018** [P] Integration test low confidence handling and retry workflow in tests/ai_schema_generation/integration/test_low_confidence_workflow.py
- [ ] **T019** [P] Integration test error handling and fallback mechanisms in tests/ai_schema_generation/integration/test_error_handling_workflow.py
- [ ] **T020** [P] Integration test UI transition to schema editor in tests/ai_schema_generation/integration/test_ui_editor_integration.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models [P] - Independent entities
- [ ] **T021** [P] SampleDocument model in ai_schema_generation/models/sample_document.py
- [ ] **T022** [P] AIAnalysisResult model in ai_schema_generation/models/analysis_result.py
- [ ] **T023** [P] ExtractedField model in ai_schema_generation/models/extracted_field.py
- [ ] **T024** [P] ValidationRuleInference model in ai_schema_generation/models/validation_rule_inference.py
- [ ] **T025** [P] DocumentTypeSuggestion model in ai_schema_generation/models/document_type_suggestion.py
- [ ] **T026** [P] GeneratedSchema model in ai_schema_generation/models/generated_schema.py

### Storage Layer [P] - Independent storage services
- [ ] **T027** [P] SampleDocumentStorage service in ai_schema_generation/storage/sample_document_storage.py
- [ ] **T028** [P] AIAnalysisStorage service in ai_schema_generation/storage/analysis_storage.py
- [ ] **T029** [P] Schema generation storage integration in ai_schema_generation/storage/generated_schema_storage.py

### Core Services - Sequential due to dependencies
- [ ] **T030** DocumentProcessor service in ai_schema_generation/services/document_processor.py (depends on SampleDocument)
- [ ] **T031** AIAnalyzer service in ai_schema_generation/services/ai_analyzer.py (depends on DocumentProcessor)
- [ ] **T032** FieldExtractor service in ai_schema_generation/services/field_extractor.py (depends on AIAnalyzer)
- [ ] **T033** ValidationRuleInferencer service in ai_schema_generation/services/validation_rule_inferencer.py (depends on FieldExtractor)
- [ ] **T034** SchemaGenerator service in ai_schema_generation/services/schema_generator.py (depends on all analysis services)
- [ ] **T035** ConfidenceScorer service in ai_schema_generation/services/confidence_scorer.py (depends on AIAnalyzer)

### API Endpoints - Sequential due to shared service dependencies
- [ ] **T036** POST /analyze_document endpoint implementation
- [ ] **T037** POST /analyze_document/confidence_scores endpoint implementation
- [ ] **T038** POST /analyze_document/retry endpoint implementation
- [ ] **T039** POST /generate_schema endpoint implementation
- [ ] **T040** POST /generate_schema/validation_rules endpoint implementation
- [ ] **T041** POST /generate_schema/preview endpoint implementation
- [ ] **T042** POST /save_generated_schema endpoint implementation

## Phase 3.4: Integration

### UI Components [P] - Independent UI modules
- [ ] **T043** [P] Document upload interface in ai_schema_generation/ui/upload_interface.py
- [ ] **T044** [P] Analysis progress display in ai_schema_generation/ui/analysis_progress.py
- [ ] **T045** [P] Confidence visualization components in ai_schema_generation/ui/confidence_display.py
- [ ] **T046** [P] Schema generation preview in ai_schema_generation/ui/schema_preview.py

### UI Integration - Sequential due to shared state
- [ ] **T047** POST /ui/upload_sample_document endpoint implementation
- [ ] **T048** GET /ui/analysis_progress/{document_id} endpoint implementation
- [ ] **T049** GET /ui/analysis_results/{document_id} endpoint implementation
- [ ] **T050** POST /ui/transition_to_editor endpoint implementation
- [ ] **T051** POST /ui/save_reviewed_schema endpoint implementation
- [ ] **T052** POST /ui/retry_analysis endpoint implementation

### System Integration - Sequential due to dependencies
- [ ] **T053** Database schema migration and setup
- [ ] **T054** Integration with existing schema management system
- [ ] **T055** Performance optimization: caching and memory management
- [ ] **T056** Error handling and logging integration
- [ ] **T057** Streamlit UI workflow integration

## Phase 3.5: Polish

### Utility Functions [P] - Independent utilities
- [ ] **T058** [P] Document validation utilities in ai_schema_generation/utils/document_validator.py
- [ ] **T059** [P] AI prompt generation utilities in ai_schema_generation/utils/prompt_generator.py
- [ ] **T060** [P] Performance monitoring utilities in ai_schema_generation/utils/performance_monitor.py
- [ ] **T061** [P] Error handling utilities in ai_schema_generation/utils/error_handler.py

### Unit Tests [P] - Independent test files
- [ ] **T062** [P] Unit tests for SampleDocument model in tests/ai_schema_generation/unit/test_sample_document.py
- [ ] **T063** [P] Unit tests for AIAnalyzer service in tests/ai_schema_generation/unit/test_ai_analyzer.py
- [ ] **T064** [P] Unit tests for SchemaGenerator service in tests/ai_schema_generation/unit/test_schema_generator.py
- [ ] **T065** [P] Unit tests for ConfidenceScorer service in tests/ai_schema_generation/unit/test_confidence_scorer.py
- [ ] **T066** [P] Unit tests for DocumentProcessor service in tests/ai_schema_generation/unit/test_document_processor.py

### Performance and Validation
- [ ] **T067** Performance tests: <500ms schema generation in tests/ai_schema_generation/performance/test_generation_performance.py
- [ ] **T068** Performance tests: memory usage optimization in tests/ai_schema_generation/performance/test_memory_usage.py
- [ ] **T069** End-to-end validation using quickstart.md scenarios
- [ ] **T070** Documentation updates: module docstrings and API documentation

## Dependencies

### Phase Dependencies
- Setup (T001-T004) before everything
- Tests (T005-T020) before implementation (T021-T057) - **NON-NEGOTIABLE TDD**
- Models (T021-T026) before services (T030-T035)
- Services before endpoints (T036-T042)
- Core before UI integration (T043-T052)
- Implementation before polish (T058-T070)

### Specific Blocking Dependencies
- T030 (DocumentProcessor) blocks T031 (AIAnalyzer)
- T031 (AIAnalyzer) blocks T032, T033, T035 (dependent services)
- T021-T029 (Models & Storage) block T030-T035 (Services)
- T030-T035 (Services) block T036-T042 (API Endpoints)
- T036-T042 (API Endpoints) block T047-T052 (UI Endpoints)
- T053 (Database) blocks T054 (Schema Management Integration)

## Parallel Execution Examples

### Contract Tests Phase (After T001-T004)
```bash
# Launch T005-T014 together (all contract tests):
Task: "Contract test POST /analyze_document in tests/ai_schema_generation/contract/test_ai_analyzer_contract.py"
Task: "Contract test POST /generate_schema in tests/ai_schema_generation/contract/test_schema_generator_contract.py"
Task: "Contract test POST /ui/upload_sample_document in tests/ai_schema_generation/contract/test_ui_upload_contract.py"
# ... all contract tests can run in parallel
```

### Integration Tests Phase (After T005-T014)
```bash
# Launch T015-T020 together (all integration tests):
Task: "Integration test complete workflow in tests/ai_schema_generation/integration/test_complete_workflow.py"
Task: "Integration test PDF invoice workflow in tests/ai_schema_generation/integration/test_pdf_invoice_workflow.py"
Task: "Integration test error handling workflow in tests/ai_schema_generation/integration/test_error_handling_workflow.py"
# ... all integration tests can run in parallel
```

### Data Models Phase (After T015-T020)
```bash
# Launch T021-T026 together (all models):
Task: "SampleDocument model in ai_schema_generation/models/sample_document.py"
Task: "AIAnalysisResult model in ai_schema_generation/models/analysis_result.py"
Task: "ExtractedField model in ai_schema_generation/models/extracted_field.py"
# ... all models can be implemented in parallel
```

### Storage Layer Phase (After T021-T026)
```bash
# Launch T027-T029 together (all storage services):
Task: "SampleDocumentStorage service in ai_schema_generation/storage/sample_document_storage.py"
Task: "AIAnalysisStorage service in ai_schema_generation/storage/analysis_storage.py"
Task: "Schema generation storage integration in ai_schema_generation/storage/generated_schema_storage.py"
```

### UI Components Phase (After T042)
```bash
# Launch T043-T046 together (all UI components):
Task: "Document upload interface in ai_schema_generation/ui/upload_interface.py"
Task: "Analysis progress display in ai_schema_generation/ui/analysis_progress.py"
Task: "Confidence visualization components in ai_schema_generation/ui/confidence_display.py"
Task: "Schema generation preview in ai_schema_generation/ui/schema_preview.py"
```

## Notes

- **[P] tasks**: Different files, no dependencies - safe for parallel execution
- **TDD Enforcement**: All tests (T005-T020) must be written and failing before any implementation
- **Constitutional Compliance**: Library-based approach with ai_schema_generation module
- **Integration**: Extends existing schema management system without breaking changes
- **Performance**: Maintains <500ms response time targets with caching and optimization
- **Error Handling**: Comprehensive fallback strategies and graceful degradation

## Task Generation Rules Applied

1. **From Contracts**: Each API endpoint (3 contract files × ~3-4 endpoints each) → contract test tasks [P]
2. **From Data Model**: Each entity (6 entities) → model creation task [P]
3. **From User Stories**: Each quickstart scenario → integration test [P]
4. **Ordering**: Setup → Tests → Models → Services → Endpoints → UI → Polish
5. **Dependencies**: Services depend on models, endpoints depend on services, UI depends on endpoints

## Validation Checklist

- [x] All contracts have corresponding tests (T005-T014)
- [x] All entities have model tasks (T021-T026)
- [x] All tests come before implementation (T005-T020 before T021+)
- [x] Parallel tasks truly independent (different files, no shared state)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD methodology enforced (tests must fail before implementation)
- [x] Constitutional compliance maintained (library approach, proper testing order)