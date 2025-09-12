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

Technical approach: Extend existing LLM-based extraction system with document type schemas, prompt engineering for validation integration, and UI components for document type selection.

## Technical Context
**Language/Version**: Python 3.11+ (inferred from LLM integration requirements)  
**Primary Dependencies**: FastAPI (web API), React/Vue (frontend), LLM libraries (for Llama 4 Scout, Mistral Small 3.2)  
**Storage**: File storage for schemas and documents, optional database for document types  
**Testing**: pytest (backend), Jest/Vitest (frontend), integration tests for AI workflows  
**Target Platform**: Web application (browser + server)
**Project Type**: web - determines frontend + backend structure  
**Performance Goals**: <2s document processing, handle multiple concurrent uploads  
**Constraints**: Support images and PDFs only, validation feedback must be in AI output  
**Scale/Scope**: Small-medium scale (dozens of document types, hundreds of concurrent users)

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
# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/          # DocumentType, Schema, Field
│   ├── services/        # SchemaService, ValidationService, AIService
│   └── api/            # REST endpoints for document processing
└── tests/

frontend/
├── src/
│   ├── components/     # DocumentTypeSelector, UploadForm, ResultsView
│   ├── pages/         # Main extraction page
│   └── services/      # API client, file handling
└── tests/
```

**Structure Decision**: Option 2 (Web application) - frontend for UI, backend for AI processing

## Phase 0: Outline & Research

Research tasks needed to resolve technical decisions:

1. **LLM Integration Patterns**: Research best practices for integrating Llama 4 Scout and Mistral Small 3.2
   - Decision: Direct API calls vs library abstraction
   - Rationale: Performance and control requirements
   - Alternatives: Unified LLM interface vs model-specific implementations

2. **Document Processing Pipeline**: Research optimal approach for image/PDF handling with LLMs
   - Decision: Preprocessing requirements, format conversion
   - Rationale: Quality and compatibility needs
   - Alternatives: Client-side vs server-side processing

3. **Schema Storage Strategy**: Research storage approach for document type schemas
   - Decision: Database vs file-based vs in-memory
   - Rationale: Performance, scalability, ease of management
   - Alternatives: JSON files vs database tables vs configuration

4. **Validation Integration**: Research methods to embed validation in LLM prompts
   - Decision: Prompt engineering patterns for validation feedback
   - Rationale: Accuracy and consistency requirements
   - Alternatives: Post-processing validation vs AI-integrated validation

**Output**: research.md with all technical decisions documented

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

**Design Tasks**:

1. **Extract entities from feature spec** → `data-model.md`:
   - DocumentType: name, description, schema reference
   - Schema: fields array, validation rules, required fields
   - Field: name, type, validation rules, required status
   - ValidationResult: field name, status, error message
   - ExtractionResult: extracted data, validation results per field

2. **Generate API contracts** from functional requirements:
   - GET /api/document-types → list available document types
   - GET /api/document-types/{id}/schema → get schema for document type
   - POST /api/extract → upload document and extract data
   - Contracts output to `/contracts/openapi.yml`

3. **Generate contract tests** from contracts:
   - test_document_types_api.py (list and schema endpoints)
   - test_extraction_api.py (document upload and processing)
   - Tests must fail initially (no implementation)

4. **Extract test scenarios** from user stories:
   - Integration test: Complete extraction workflow
   - Edge case tests: Invalid formats, mismatched types
   - Quickstart validation steps

5. **Update CLAUDE.md incrementally**:
   - Add document processing context
   - Include LLM integration patterns
   - Preserve existing configurations

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs
- Each contract → contract test task [P]
- Each entity → model creation task [P]
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Contract tests → Integration tests → Implementation
- Dependency order: Models → Services → API → Frontend
- Mark [P] for parallel execution (independent components)

**Estimated Output**: 28-32 numbered, ordered tasks focusing on:
1. Contract test setup (3-4 tasks)
2. Data model implementation (4-5 tasks)
3. Backend services (8-10 tasks)
4. Frontend components (6-8 tasks)
5. Integration testing (4-5 tasks)
6. Documentation and deployment (2-3 tasks)

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
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*