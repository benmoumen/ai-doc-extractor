# Implementation Plan: Next.js Document Processing App with Schema-Driven UI

**Branch**: `005-build-a-next` | **Date**: 2025-09-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-build-a-next/spec.md`

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

Primary requirement: Create a modern Next.js 15 frontend with FastAPI HTTP layer that exposes the existing sophisticated AISchemaGenerationAPI backend over REST endpoints, preserving all current AI processing, schema management, and business logic.

Technical approach: **REVISED STRATEGY** - FastAPI HTTP layer as thin wrapper over existing AISchemaGenerationAPI classes + Next.js 15 App Router frontend consuming HTTP endpoints. This leverages the complete existing backend (6-stage AI pipeline, LiteLLM integration, storage systems) while adding modern web interface.

## Technical Context

**Language/Version**: TypeScript with Next.js 15+ (App Router), Node.js 18+
**Primary Dependencies**:
- Frontend: Next.js 15, React, shadcn/ui, Tailwind CSS, Zod (validation), React Hook Form, Lucide React (icons)
- HTTP Layer: FastAPI, uvicorn, python-multipart (CORS middleware)
- Backend: Existing AISchemaGenerationAPI, LiteLLM, schema management system (unchanged)
**Storage**: Existing hybrid JSON/SQLite storage system (unchanged)
**Testing**: Vitest, React Testing Library, Playwright (E2E), pytest for HTTP API
**Target Platform**: Web browsers (modern Chrome, Firefox, Safari, Edge)
**Project Type**: web - HTTP API wrapper + frontend consuming existing backend
**Performance Goals**: <2s initial load, <500ms form interactions, preserve existing backend performance
**Constraints**: Minimal UI design, neutral colors, clean spacing, inline editing, mobile responsive
**Scale/Scope**: Leverage existing backend capacity, no regression in document processing capabilities

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

**Simplicity**:

- Projects: 3 (HTTP API layer, Next.js frontend, existing backend integration) (max 3 - at limit but justified)
- Using framework directly? Yes (Next.js App Router, FastAPI, shadcn/ui components)
- Single data model? Yes (existing backend data structures preserved, TypeScript DTOs added)
- Avoiding patterns? Yes (HTTP layer is thin wrapper, direct API calls, no unnecessary abstraction)

**Architecture**:

- EVERY feature as library? Yes (leveraging existing backend libraries + new frontend components)
- Existing Libraries (unchanged):
  - AISchemaGenerationAPI: Complete 6-stage document processing pipeline
  - schema_management: Schema storage and validation system
  - ai_schema_generation.services: All AI processing services
- New Libraries:
  - http_api: HTTP endpoints exposing existing APIs
  - nextjs-app/components: UI component library (upload, processing, results)
  - nextjs-app/lib: API client and utilities
- CLI per library: N/A (web-only application)
- Library docs: Component documentation with shadcn/ui patterns

**Testing (NON-NEGOTIABLE)**:

- RED-GREEN-Refactor cycle enforced? Yes (failing tests first)
- Git commits show tests before implementation? Yes (TDD approach)
- Order: Contract→Integration→E2E→Unit strictly followed? Yes
- Real dependencies used? Yes (actual file system, real API calls)
- Integration tests for: HTTP API endpoints, frontend-backend communication, existing backend preservation
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:

- Structured logging included? Yes (console structured logging, error tracking)
- Frontend logs → backend? Yes (error reporting integration)
- Error context sufficient? Yes (user-friendly error states, detailed dev logging)

**Versioning**:

- Version number assigned? 1.0.0 (MAJOR.MINOR.BUILD)
- BUILD increments on every change? Yes
- Breaking changes handled? Yes (versioned API contracts, fallback UI states)

## Project Structure

### Documentation (this feature)

```
specs/005-build-a-next/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)

```
ai-doc-extractor/              # Existing project root
├── http_api/                  # NEW: FastAPI HTTP layer
│   ├── main.py               # HTTP endpoints using existing AISchemaGenerationAPI
│   ├── requirements.txt      # FastAPI dependencies
│   └── tests/               # HTTP API tests
├── nextjs-app/               # NEW: Next.js 15 Frontend
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   │   ├── layout.tsx   # Root layout
│   │   │   ├── page.tsx     # Home page with upload
│   │   │   └── documents/   # Document processing pages
│   │   ├── components/      # UI Components
│   │   │   ├── ui/         # shadcn/ui components
│   │   │   ├── document-upload/  # Upload components
│   │   │   ├── processing/ # Progress components
│   │   │   └── results/    # Results display
│   │   ├── lib/            # API client and utilities
│   │   │   ├── api.ts      # HTTP API client
│   │   │   └── utils.ts    # Utilities
│   │   └── types/          # TypeScript definitions
│   ├── next.config.js      # Next.js configuration
│   ├── package.json        # Dependencies (pnpm)
│   └── tailwind.config.js  # Tailwind configuration
└── ai_schema_generation/     # EXISTING: Sophisticated backend (unchanged)
    ├── api/
    │   └── main_endpoint.py  # AISchemaGenerationAPI
    ├── services/            # All processing services
    └── storage/             # Storage systems
```

**Structure Decision**: Option 2 (Web application) - FastAPI HTTP layer + Next.js frontend leveraging existing AISchemaGenerationAPI backend

## Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:

   - FastAPI HTTP layer patterns for exposing existing Python API classes
   - Next.js 15 App Router best practices for consuming REST APIs
   - shadcn/ui component integration with real-time document processing
   - HTTP polling vs WebSocket strategies for progress updates
   - TypeScript interface generation from existing Python API responses
   - CORS and proxy configuration for Next.js + FastAPI integration

2. **Generate and dispatch research agents**:

   ```
   Task: "Research FastAPI patterns for wrapping existing Python API classes over HTTP"
   Task: "Find Next.js 15 App Router best practices for consuming REST APIs"
   Task: "Research real-time progress feedback patterns with HTTP polling"
   Task: "Find CORS and proxy configuration for Next.js + FastAPI integration"
   Task: "Research TypeScript type generation from existing Python API responses"
   Task: "Find shadcn/ui component patterns for document processing workflows"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts

_Prerequisites: research.md complete_

1. **Extract entities from feature spec** → `data-model.md`:

   - DocumentAnalysisResponse: Complete response from AISchemaGenerationAPI (existing)
   - ProcessingStages: 6-stage pipeline status from existing backend
   - AnalysisResult: AI analysis results with confidence scores (existing)
   - GeneratedSchema: Schema generation results from backend (existing)
   - DocumentUploadRequest: HTTP API request/response types (new)
   - APIClientTypes: TypeScript interfaces matching Python responses (new)

2. **Generate API contracts** from functional requirements:

   - POST /api/documents → Upload & analyze using existing AISchemaGenerationAPI.analyze_document()
   - GET /api/analysis/{id} → Get results using existing AISchemaGenerationAPI.get_analysis_results()
   - GET /api/schemas/{id} → Get schema details using existing AISchemaGenerationAPI.get_schema_details()
   - POST /api/analysis/{id}/retry → Retry analysis using existing AISchemaGenerationAPI.retry_analysis()
   - GET /api/status → Service status using existing AISchemaGenerationAPI.get_service_status()
   - Output OpenAPI schema to `/contracts/` exposing existing functionality

3. **Generate contract tests** from contracts:

   - HTTP API endpoint tests (FastAPI integration)
   - Existing backend preservation tests (no regression)
   - Next.js API client integration tests
   - End-to-end document processing flow tests
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:

   - Upload via Next.js → HTTP API → AISchemaGenerationAPI processing
   - Real-time progress updates via HTTP polling
   - Results display with existing confidence scores
   - All existing backend functionality accessible via HTTP

5. **Update agent file incrementally** (O(1) operation):
   - Update CLAUDE.md with FastAPI HTTP layer approach
   - Add Next.js 15 + existing backend integration patterns
   - Include AISchemaGenerationAPI context and usage
   - Preserve existing backend architecture notes

**Output**: data-model.md, /contracts/\*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach

_This section describes what the /tasks command will do - DO NOT execute during /plan_

**Task Generation Strategy**:

- Generate tasks for three-layer architecture: HTTP API + Next.js + Backend Integration
- Phase 1: HTTP API layer (FastAPI endpoints exposing existing AISchemaGenerationAPI)
- Phase 2: Next.js frontend (components consuming HTTP endpoints)
- Phase 3: Integration & Testing (end-to-end validation)
- Each layer can be developed in parallel after HTTP API contracts defined
- Preserve existing backend functionality (no regression tests)

**Ordering Strategy**:

- TDD order: Contract tests → HTTP API → Frontend → Integration
- Dependency order: HTTP endpoints → TypeScript types → Components → Pages
- Mark [P] for parallel execution (HTTP API + Frontend setup)
- Critical path: HTTP API → API client → Upload component → Processing workflow

**Estimated Output**: 35 numbered, ordered tasks in tasks.md (as per revised tasks-final.md)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

_These phases are beyond the scope of the /plan command_

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking

_No constitutional violations detected - all requirements met within guidelines_

## Progress Tracking

_This checklist is updated during execution flow_

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
- [x] Complexity deviations documented

---

_Based on Constitution v2.1.1 - See `/memory/constitution.md`_
