# Tasks: Next.js Frontend + HTTP API Layer (Final Revision)

**Input**: Analysis of existing sophisticated codebase with AI Schema Generation API
**Prerequisites**: Existing `AISchemaGenerationAPI`, schema management system, LiteLLM integration
**Context**: Create HTTP endpoints over existing API classes + Next.js frontend consuming them

## Critical Discovery: Existing Architecture Analysis
```
✅ ALREADY EXISTS:
- AISchemaGenerationAPI class with full document processing pipeline
- Complete schema management system (schema_management/ module)
- LiteLLM integration with multiple providers (Groq, Mistral)
- Sophisticated storage system (SQLite + JSON hybrid)
- Cost tracking, performance monitoring, error handling
- Document processing (PDF, images), validation, field extraction

❌ MISSING:
- HTTP/REST endpoints to expose existing API classes over web
- Next.js frontend to consume HTTP endpoints
- Modern UI components for document processing workflow
```

## Revised Strategy: Expose Existing APIs + Modern Frontend

### Phase 1: HTTP API Layer (Expose Existing Classes)
Create FastAPI endpoints that use existing `AISchemaGenerationAPI` and related classes

### Phase 2: Next.js Frontend
Build React components that consume the new HTTP endpoints

### Phase 3: Integration & Testing
Connect and test the complete stack

## Phase 1: HTTP API Layer (T001-T010)

### T001-T003: HTTP Server Setup
- [ ] T001 Create FastAPI HTTP server in `http_api/main.py` using existing `AISchemaGenerationAPI`
- [ ] T002 [P] Install FastAPI dependencies: `pip install fastapi uvicorn python-multipart`
- [ ] T003 [P] Configure CORS middleware for Next.js integration

### T004-T010: HTTP Endpoints (Use Existing API Classes)
- [ ] T004 [P] Document upload endpoint `POST /api/documents` using `AISchemaGenerationAPI.analyze_document()`
- [ ] T005 [P] Document status endpoint `GET /api/documents/{id}` using existing document storage
- [ ] T006 [P] Schema list endpoint `GET /api/schemas` using existing schema management
- [ ] T007 [P] Analysis results endpoint `GET /api/analysis/{id}` using `AISchemaGenerationAPI.get_analysis_results()`
- [ ] T008 [P] Schema details endpoint `GET /api/schemas/{id}` using existing schema storage
- [ ] T009 [P] Retry analysis endpoint `POST /api/analysis/{id}/retry` using existing retry logic
- [ ] T010 [P] Service status endpoint `GET /api/status` using existing monitoring

## Phase 2: Next.js Frontend (T011-T025)

### T011-T015: Frontend Setup
- [ ] T011 Create Next.js 15 project in `nextjs-app/` with TypeScript and Tailwind CSS
- [ ] T012 [P] Install dependencies: pnpm add @hookform/resolvers react-hook-form zod lucide-react
- [ ] T013 [P] Initialize shadcn/ui: npx shadcn@latest init && add form input button progress table
- [ ] T014 [P] Configure API client in `nextjs-app/src/lib/api.ts` to call HTTP endpoints
- [ ] T015 [P] Set up TypeScript types matching existing Python API response formats

### T016-T025: React Components
- [ ] T016 [P] Document upload component using existing upload API patterns
- [ ] T017 [P] Document processing progress component using existing status endpoints
- [ ] T018 [P] Schema selector component using existing schema management API
- [ ] T019 [P] Results display component showing AI extraction results
- [ ] T020 [P] Field editing component with inline validation using existing validation rules
- [ ] T021 [P] Cost/performance display using existing tracking data
- [ ] T022 [P] Error handling component with retry functionality
- [ ] T023 [P] Export functionality using existing export capabilities
- [ ] T024 [P] Main layout with sidebar using shadcn/ui components
- [ ] T025 [P] Responsive design optimization for mobile devices

## Phase 3: Pages & Integration (T026-T035)

### T026-T030: Next.js Pages
- [ ] T026 [P] Home page `/` with document upload interface
- [ ] T027 [P] Processing page `/documents/[id]` with real-time status updates
- [ ] T028 [P] Results page `/documents/[id]/results` with extracted data display
- [ ] T029 [P] Schema management page `/schemas` using existing schema system
- [ ] T030 [P] History page `/history` with document processing history

### T031-T035: Integration & Testing
- [ ] T031 [P] HTTP API integration tests for all endpoints
- [ ] T032 [P] Frontend component tests using existing API responses
- [ ] T033 [P] End-to-end workflow test: upload → process → results → export
- [ ] T034 [P] Performance testing: ensure no regression from existing Streamlit speeds
- [ ] T035 [P] Cross-browser testing and mobile responsiveness validation

## Dependencies & Critical Path

### Sequential Dependencies:
- **T001-T003** (HTTP setup) → **T004-T010** (endpoints) → **T031** (API tests)
- **T011-T015** (frontend setup) → **T016-T025** (components) → **T026-T030** (pages)
- **T014** (API client) requires **T004-T010** (endpoints) to be defined
- **T033-T035** (integration tests) require both phases complete

### Parallel Execution:
- **T001-T003** can run parallel with **T011-T015** (different stacks)
- **T004-T010** endpoints are all independent (different routes)
- **T016-T025** components are all independent (different files)
- **T026-T030** pages can be built in parallel

## Implementation Patterns

### HTTP Endpoint Pattern:
```python
# http_api/main.py
from fastapi import FastAPI, UploadFile
from ai_schema_generation.api.main_endpoint import AISchemaGenerationAPI

app = FastAPI()
api = AISchemaGenerationAPI()  # Use existing API class

@app.post("/api/documents")
async def upload_document(file: UploadFile):
    content = await file.read()
    # Call existing method
    result = api.analyze_document(content, file.filename)
    return result
```

### Next.js API Client Pattern:
```typescript
// nextjs-app/src/lib/api.ts
export const apiClient = {
  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch('/api/documents', {
      method: 'POST',
      body: formData
    });
    return response.json();
  }
}
```

### Component Integration Pattern:
```typescript
// nextjs-app/src/components/DocumentUpload.tsx
export function DocumentUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState(null);

  const handleUpload = async () => {
    if (!file) return;
    const data = await apiClient.uploadDocument(file);
    setResult(data);
  };

  return (
    <div>
      <input type="file" onChange={e => setFile(e.target.files?.[0])} />
      <button onClick={handleUpload}>Process Document</button>
      {result && <ResultsDisplay data={result} />}
    </div>
  );
}
```

## MVP Success Criteria (Leveraging Existing System)
1. **HTTP API**: All existing `AISchemaGenerationAPI` functionality accessible via REST
2. **Document Upload**: Next.js frontend can upload and trigger existing AI processing
3. **Real-time Progress**: Frontend shows progress using existing status tracking
4. **Schema Integration**: Frontend uses existing schema management system
5. **Results Display**: Frontend shows AI extraction results with existing confidence scoring
6. **Cost/Performance**: Frontend displays existing cost tracking and performance data
7. **Error Handling**: Frontend handles errors using existing error handling patterns
8. **No Regression**: All existing capabilities preserved and accessible

## What This Approach Preserves ✅
- Complete AI Schema Generation pipeline
- LiteLLM multi-provider integration (Groq, Mistral)
- Sophisticated schema management with validation rules
- Cost tracking and performance monitoring
- Error handling and retry mechanisms
- Document processing (PDF, images) capabilities
- Storage systems (SQLite + JSON hybrid)

## What This Approach Adds 🆕
- Modern HTTP REST API layer over existing classes
- React-based UI with shadcn/ui components
- Real-time progress updates in browser
- Mobile-responsive design
- TypeScript type safety
- Modern developer experience

## Validation Checklist ✓
- [x] Leverages existing `AISchemaGenerationAPI` without modification
- [x] Uses existing schema management system without changes
- [x] Preserves all current AI processing capabilities
- [x] HTTP endpoints expose existing functionality over REST
- [x] Next.js frontend consumes HTTP endpoints
- [x] Parallel development possible (API + frontend)
- [x] MVP scope realistic and achievable
- [x] No rewriting of existing business logic