# Implementation Plan: AI-Powered Schema Generation from Sample Documents

**Branch**: `003-ai-schema-generation` | **Date**: 2025-09-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-ai-schema-generation/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✓
   → Feature spec loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
AI-Powered Schema Generation from Sample Documents allows users to upload sample documents (PDF/images) and automatically generate document type schemas using the same AI utilities as the main data extraction function. The system extracts field names, infers types and validation rules, then opens the schema management interface in edit mode for user review and refinement. This extends the existing schema management system (002-schema-management-ui) with AI assistance to reduce manual schema creation effort.

## Technical Context
**Language/Version**: Python 3.11 (matches existing codebase)
**Primary Dependencies**: Streamlit, LiteLLM, streamlit-elements, python-jsonschema (existing stack)
**Storage**: JSON + SQLite hybrid (existing schema management storage)
**Testing**: pytest (existing testing framework)
**Target Platform**: Streamlit web application (existing platform)
**Project Type**: single (extending existing Streamlit application)
**Performance Goals**: <500ms schema generation (consistent with main extraction function)
**Constraints**: Same file size limits as main extraction, memory efficiency for document processing
**Scale/Scope**: Support for 100+ field schemas, multiple document types, integration with existing workflows

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (extending existing Streamlit app)
- Using framework directly? Yes (direct Streamlit, LiteLLM integration)
- Single data model? Yes (extending existing schema models)
- Avoiding patterns? Yes (no unnecessary abstractions, direct integration)

**Architecture**:
- EVERY feature as library? Yes (ai_schema_generation/ module)
- Libraries listed: ai_schema_generation (AI-powered schema generation from samples)
- CLI per library: Integration with existing Streamlit UI workflow
- Library docs: Will update existing CLAUDE.md incrementally

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes (tests first, then implementation)
- Git commits show tests before implementation? Required
- Order: Contract→Integration→E2E→Unit strictly followed? Yes
- Real dependencies used? Yes (actual AI models, file processing)
- Integration tests for: AI analysis, schema generation, UI integration
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? Yes (following existing patterns)
- Frontend logs → backend? N/A (single Streamlit application)
- Error context sufficient? Yes (comprehensive error handling)

**Versioning**:
- Version number assigned? Follows existing project versioning
- BUILD increments on every change? Yes
- Breaking changes handled? Backward compatible extension

## Project Structure

### Documentation (this feature)
```
specs/003-ai-schema-generation/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
ai_schema_generation/
├── models/
│   ├── sample_document.py
│   ├── analysis_result.py
│   └── generated_schema.py
├── services/
│   ├── ai_analyzer.py
│   ├── schema_generator.py
│   └── field_extractor.py
├── ui/
│   ├── upload_interface.py
│   └── generation_progress.py
└── utils/
    ├── document_processor.py
    └── validation.py

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Option 1 (single project extending existing Streamlit application)

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - No NEEDS CLARIFICATION items remain in spec
   - Research AI analysis integration patterns with existing LiteLLM setup
   - Research document processing optimization for schema extraction
   - Research schema generation confidence scoring methods

2. **Generate and dispatch research agents**:
   ```
   Task: "Research AI prompt engineering for schema field extraction from documents"
   Task: "Research confidence scoring methods for AI-generated schema elements"
   Task: "Research integration patterns between document analysis and schema management"
   Task: "Research performance optimization for document processing in schema generation"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all technical decisions documented

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - SampleDocument, AIAnalysisResult, GeneratedSchema, ExtractedField
   - ValidationRuleInference, DocumentTypeSuggestion entities
   - State transitions for generation workflow

2. **Generate API contracts** from functional requirements:
   - Schema generation endpoint contract
   - Document analysis service contract
   - Field extraction service contract
   - Output contracts to `/contracts/`

3. **Generate contract tests** from contracts:
   - AI analysis contract tests
   - Schema generation contract tests
   - UI integration contract tests
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Primary flow: Upload → Analyze → Generate → Edit → Save
   - Edge cases: corrupted files, unclear fields, processing failures
   - Quickstart test scenarios for validation

5. **Update agent file incrementally** (O(1) operation):
   - Update CLAUDE.md with AI schema generation context
   - Add new technical details from current plan
   - Preserve existing manual additions
   - Update recent changes section
   - Keep under 150 lines for token efficiency

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md update

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P]
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations identified - all requirements align with simplicity principles*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✓
- [x] Phase 1: Design complete (/plan command) ✓
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✓
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✓
- [x] Post-Design Constitution Check: PASS ✓
- [x] All NEEDS CLARIFICATION resolved ✓
- [x] Complexity deviations documented ✓

**Artifacts Generated**:
- [x] research.md: Complete technical research and decisions ✓
- [x] data-model.md: Entity definitions and database extensions ✓
- [x] contracts/: API specifications for all services ✓
- [x] quickstart.md: Complete user journey and testing guide ✓
- [x] CLAUDE.md: Updated with current feature context ✓

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*