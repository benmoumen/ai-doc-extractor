# Research Findings: HTTP API + Next.js Frontend (Revised)

## Technical Decisions (Revised After Codebase Analysis)

### Critical Discovery: Existing Sophisticated Backend
**Decision**: Leverage existing `AISchemaGenerationAPI` and comprehensive backend systems
**Rationale**:
- Discovered fully implemented `AISchemaGenerationAPI` with complete document processing pipeline
- Existing schema management system with storage, validation, and UI components
- Working LiteLLM integration with multiple providers (Groq Llama Scout, Mistral Small)
- Sophisticated storage system (SQLite + JSON hybrid)
- Cost tracking, performance monitoring, and error handling already implemented

**Evidence of Existing Implementation**:
```python
# ai_schema_generation/api/main_endpoint.py
class AISchemaGenerationAPI:
    def analyze_document(self, file_content, filename, model=None, document_type_hint=None):
        # Complete 6-stage pipeline already implemented:
        # 1. Document Processing, 2. AI Analysis, 3. Field Enhancement
        # 4. Validation Rule Inference, 5. Schema Generation, 6. Confidence Analysis
```

**Alternatives Considered**:
- Full rewrite of Python backend: Would lose significant existing investment
- Streamlit wrapper approach: Overcomplicated, ignores existing API classes
- Direct Streamlit to Next.js migration: Would require rewriting all business logic

### HTTP API Layer Architecture
**Decision**: FastAPI endpoints that expose existing API classes over HTTP
**Rationale**:
- FastAPI provides excellent Python async support and automatic OpenAPI docs
- Can directly import and use existing `AISchemaGenerationAPI` class
- Maintains all existing functionality while adding HTTP interface
- Allows gradual migration and testing of individual endpoints

**Implementation Pattern**:
```python
# http_api/main.py
from fastapi import FastAPI, UploadFile
from ai_schema_generation.api.main_endpoint import AISchemaGenerationAPI

app = FastAPI()
api = AISchemaGenerationAPI()  # Use existing class

@app.post("/api/documents")
async def upload_document(file: UploadFile):
    content = await file.read()
    # Call existing method - no rewriting needed
    result = api.analyze_document(content, file.filename)
    return result
```

**Alternatives Considered**:
- Flask: Less automatic documentation, no built-in async support
- Django REST Framework: Too heavy for API wrapper layer
- Direct Streamlit API: No existing HTTP API in Streamlit

### Next.js 15 Frontend Strategy
**Decision**: Next.js 15 App Router with shadcn/ui consuming HTTP endpoints
**Rationale**:
- App Router provides modern server components and improved performance
- shadcn/ui offers minimal, professional components matching requirements
- TypeScript ensures type safety across API boundaries
- React Hook Form + Zod provides client-side validation matching backend rules

**Key Features for Document Processing**:
```typescript
// API client consuming HTTP endpoints
const uploadDocument = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch('/api/documents', {
    method: 'POST',
    body: formData
  })
  return response.json()
}
```

**Alternatives Considered**:
- Next.js 14: Missing latest performance improvements and concurrent features
- Remix: Good for forms but less mature shadcn/ui integration
- Pure React SPA: No server-side rendering, more complex deployment

### State Management Strategy
**Decision**: React state with custom hooks, no external state library needed
**Rationale**:
- Document processing is primarily request-response with some local editing
- Custom hooks can encapsulate API calls and loading states effectively
- Avoids complexity of Redux/Zustand for this use case
- Form state handled by React Hook Form

**Implementation Pattern**:
```typescript
function useDocumentProcessing() {
  const [state, setState] = useState({
    status: 'idle',
    result: null,
    error: null
  })

  const processDocument = async (file: File) => {
    setState(prev => ({ ...prev, status: 'processing' }))
    try {
      const result = await apiClient.uploadDocument(file)
      setState({ status: 'completed', result, error: null })
      return result
    } catch (error) {
      setState(prev => ({ ...prev, status: 'error', error }))
      throw error
    }
  }

  return { state, processDocument }
}
```

**Alternatives Considered**:
- Redux: Overkill for this application's state needs
- Zustand: Simpler than Redux but still unnecessary complexity
- React Query/SWR: Good for caching but not needed for document processing workflow

### Real-time Progress Implementation
**Decision**: HTTP polling for progress updates (initially), with WebSocket upgrade path
**Rationale**:
- Existing backend doesn't have built-in WebSocket support
- HTTP polling simpler to implement initially
- Can upgrade to WebSockets later by adding Socket.IO to FastAPI
- Progress updates during document processing are infrequent enough for polling

**Implementation Pattern**:
```typescript
const useProcessingProgress = (analysisId: string) => {
  const [progress, setProgress] = useState(null)

  useEffect(() => {
    if (!analysisId) return

    const pollProgress = async () => {
      const response = await fetch(`/api/documents/${analysisId}`)
      const data = await response.json()
      setProgress(data.processing_stages)

      if (data.processing_status === 'completed') {
        clearInterval(interval)
      }
    }

    const interval = setInterval(pollProgress, 2000)
    return () => clearInterval(interval)
  }, [analysisId])

  return progress
}
```

**Alternatives Considered**:
- Server-Sent Events: Would require backend modifications
- WebSockets: More complex setup, overkill for progress updates
- Long polling: More complex implementation than regular polling

### File Upload Strategy
**Decision**: Direct multipart upload to FastAPI with progress tracking
**Rationale**:
- FastAPI handles multipart uploads efficiently
- Can provide upload progress via XMLHttpRequest/fetch
- Direct integration with existing document processing pipeline
- No intermediate storage needed

**Implementation Pattern**:
```typescript
const uploadWithProgress = async (file: File, onProgress: (percent: number) => void) => {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()
    formData.append('file', file)

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded * 100) / e.total)
        onProgress(percent)
      }
    })

    xhr.onload = () => {
      if (xhr.status === 200) {
        resolve(JSON.parse(xhr.responseText))
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`))
      }
    }

    xhr.open('POST', '/api/documents')
    xhr.send(formData)
  })
}
```

**Alternatives Considered**:
- Cloud upload (S3, etc.): Adds complexity and cost for no benefit
- Chunked upload: Unnecessary for document sizes typically processed
- Base64 encoding: Increases payload size by ~33%

### Form Validation Integration
**Decision**: Zod schemas matching backend validation rules
**Rationale**:
- Zod provides TypeScript-first validation with excellent error messages
- Can mirror backend validation rules for immediate feedback
- Integrates seamlessly with React Hook Form
- Existing backend validation preserved as final authority

**Implementation Pattern**:
```typescript
// Mirror existing backend validation in TypeScript
const documentFieldSchema = z.object({
  invoice_number: z.string().regex(/^INV-\d{4,}$/, "Must match INV-XXXX format"),
  amount: z.number().min(0, "Amount must be positive").max(999999, "Amount too large"),
  date: z.string().datetime("Invalid date format"),
  vendor_name: z.string().min(1, "Vendor name required").max(100, "Name too long")
})

const form = useForm({
  resolver: zodResolver(documentFieldSchema),
  defaultValues: extractedData  // From backend
})
```

**Alternatives Considered**:
- Yup: Less TypeScript integration, different API style
- Joi: Server-side focused, less React integration
- Custom validation: More work, less type safety

### UI Component Strategy
**Decision**: shadcn/ui with custom document processing components
**Rationale**:
- shadcn/ui provides excellent base components with full customization
- Components are copied to project, allowing modification as needed
- Excellent TypeScript support and accessibility
- Minimal, neutral design matches requirements

**Key Components for Document Processing**:
```typescript
// Document upload with drag-and-drop
<DocumentUpload onUpload={handleUpload} />

// Progress display during processing
<ProcessingProgress stages={progress.processing_stages} />

// Dynamic form based on extracted fields
<ExtractedFieldsForm
  fields={analysis.fields}
  validationRules={analysis.validation_rules}
  onSubmit={handleSave}
/>

// Results display with confidence indicators
<AnalysisResults
  analysis={results.analysis}
  schema={results.schema}
  confidence={results.confidence}
/>
```

**Alternatives Considered**:
- Material-UI: Too opinionated, doesn't match minimal design requirement
- Chakra UI: Less TypeScript focus, different design philosophy
- Ant Design: Heavy, complex, not minimal
- Custom components from scratch: Too much work, less consistency

### Deployment Strategy
**Decision**: Separate deployments for FastAPI and Next.js with reverse proxy
**Rationale**:
- FastAPI can be deployed on Python-optimized infrastructure
- Next.js can be deployed on Node.js-optimized infrastructure (Vercel, etc.)
- Reverse proxy can handle routing between services
- Allows independent scaling and updates

**Architecture**:
```
Internet → Nginx/Cloudflare → Next.js (port 3000) → FastAPI (port 8000) → Existing Backend
```

**Alternatives Considered**:
- Single deployment: Would require Node.js to run Python or vice versa
- Docker compose: Good for development, more complex for production
- Serverless: FastAPI + Lambda would lose persistent connections to existing storage

## Performance Considerations

### API Response Optimization
- FastAPI automatic compression for JSON responses
- Pagination for large result sets (schemas, documents)
- Caching of frequently accessed schemas
- Background processing for long-running AI analysis

### Frontend Optimization
- Next.js 15 App Router for better performance and SEO
- Lazy loading of heavy components (file upload, results display)
- Progressive enhancement for mobile devices
- Service worker for offline capability (future enhancement)

### Backend Integration
- Connection pooling for database access
- Caching of AI model responses where appropriate
- Async processing of document uploads
- Error handling and retry mechanisms preserved from existing system

## Security Considerations

### File Upload Security
- File type validation (PDF, JPEG, PNG only)
- File size limits (configurable, default 100MB)
- Virus scanning integration point (future enhancement)
- Secure file storage with cleanup policies

### API Security
- CORS configuration for Next.js frontend
- Rate limiting on upload endpoints
- Input validation at HTTP layer
- Error message sanitization

### Frontend Security
- Content Security Policy headers
- XSS prevention via React's built-in protections
- Secure file handling (no direct file access)
- Environment variable protection

This revised research shows how the existing sophisticated backend can be leveraged through a thin HTTP API layer while providing a modern Next.js frontend experience.