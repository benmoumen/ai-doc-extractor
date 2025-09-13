# Implementation Plan: Schema Management UI Extension

**Branch**: `002-schema-management-ui` | **Date**: 2025-09-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-schema-management-ui/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
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
Schema Management UI Extension adds a rich web-based interface for creating, editing, and managing document type schemas without code changes. This extends the existing schema-driven document extraction system with visual field builders, drag-and-drop functionality, real-time preview, and testing capabilities. Technical approach: Streamlit-based UI with streamlit-elements for advanced components, hybrid JSON+SQLite storage, and integration with existing LiteLLM extraction workflow.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: Streamlit, streamlit-elements, LiteLLM, python-jsonschema  
**Storage**: Hybrid JSON files + SQLite metadata  
**Testing**: pytest with integration tests  
**Target Platform**: Web UI (Streamlit deployment)
**Project Type**: single (extending existing Streamlit app)  
**Performance Goals**: <500ms UI response, handle 100+ field schemas  
**Constraints**: No breaking changes to existing extraction API, must preserve schema compatibility  
**Scale/Scope**: Support for dozens of custom schemas, hundreds of fields per schema

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (extending existing Streamlit app)
- Using framework directly? Yes (Streamlit, streamlit-elements)
- Single data model? Yes (schema objects with no DTOs)
- Avoiding patterns? Yes (no unnecessary abstractions)

**Architecture**:
- EVERY feature as library? Yes (schema_management module)
- Libraries listed: schema_management (schema CRUD, UI components, validation)
- CLI per library: N/A (web UI interface)
- Library docs: llms.txt format planned? No (web UI focused)

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes (tests first)
- Git commits show tests before implementation? Will ensure
- Order: Contract→Integration→E2E→Unit strictly followed? Yes
- Real dependencies used? Yes (actual SQLite, file system)
- Integration tests for: new libraries, contract changes, shared schemas? Yes
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? Yes (for errors and operations)
- Frontend logs → backend? N/A (single Streamlit app)
- Error context sufficient? Yes

**Versioning**:
- Version number assigned? v1.0.0
- BUILD increments on every change? Yes
- Breaking changes handled? Yes (migration support planned)

## Project Structure

### Documentation (this feature)
```
specs/002-schema-management-ui/
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
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Option 1 (extending existing single Streamlit application)

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - streamlit-elements best practices for drag-drop interfaces
   - SQLite + JSON hybrid storage patterns in Python
   - Schema versioning and migration strategies
   - Real-time preview implementation patterns

2. **Generate and dispatch research agents**:
   ```
   Task: "Research streamlit-elements for drag-drop schema builder UI"
   Task: "Find best practices for SQLite + JSON hybrid storage in Python"
   Task: "Research schema versioning patterns for document extraction systems"
   Task: "Find real-time preview patterns for dynamic form builders"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Schema entity with fields, validation rules, metadata
   - Field entity with types, validation, dependencies
   - Template entities for reusable components
   - Version control entities for change tracking

2. **Generate API contracts** from functional requirements:
   - Schema CRUD operations (create, read, update, delete)
   - Field management operations (add, edit, remove, reorder)
   - Validation testing operations
   - Import/export operations
   - Output contracts to `/contracts/`

3. **Generate contract tests** from contracts:
   - Schema storage contract tests
   - Field editor contract tests
   - Validation builder contract tests
   - Import/export contract tests
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Business analyst creates new schema (US1)
   - Data manager modifies existing schema (US2)
   - QA specialist tests schema against documents (US3)
   - Admin organizes and versions schemas (US4)

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/update-agent-context.sh claude` for Claude Code
   - Add new tech: streamlit-elements, python-jsonschema
   - Update with schema management context
   - Keep under 150 lines for token efficiency
   - Output to repository root (CLAUDE.md)

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

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
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*