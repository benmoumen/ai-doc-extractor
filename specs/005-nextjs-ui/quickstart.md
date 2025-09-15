# Quickstart Guide: Next.js 15 Frontend + HTTP API Layer

## Overview
This quickstart guide provides step-by-step instructions for setting up the Next.js 15 frontend with FastAPI HTTP layer that exposes the existing sophisticated AISchemaGenerationAPI backend.

## Prerequisites
- Node.js 18+ installed
- pnpm package manager (preferred)
- Python 3.11+ with existing AI backend running
- Basic familiarity with Next.js, React, and FastAPI
- Access to existing AISchemaGenerationAPI backend

## Quick Start (10 minutes)

### Phase 1: HTTP API Layer Setup

#### 1. Install FastAPI Dependencies
```bash
# Navigate to existing project root
cd /path/to/ai-doc-extractor

# Install FastAPI and dependencies
pip install fastapi uvicorn python-multipart

# Verify existing backend works
python -c "from ai_schema_generation.api.main_endpoint import AISchemaGenerationAPI; print('✓ Backend ready')"
```

#### 2. Create HTTP API Server
Create `http_api/main.py`:
```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ai_schema_generation.api.main_endpoint import AISchemaGenerationAPI
import traceback

app = FastAPI(title="Document Processing API", version="1.0.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize existing API
api = AISchemaGenerationAPI()

@app.post("/api/documents")
async def upload_document(file: UploadFile = File(...)):
    """Upload and analyze document using existing AISchemaGenerationAPI"""
    try:
        content = await file.read()
        result = api.analyze_document(content, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """Get analysis results using existing API"""
    result = api.get_analysis_results(analysis_id)
    return result

@app.get("/api/status")
async def get_service_status():
    """Get service status using existing monitoring"""
    return api.get_service_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### 3. Test HTTP API
```bash
# Start FastAPI server
cd http_api
python main.py

# In another terminal, test the API
curl -X GET http://localhost:8000/api/status
```

### Phase 2: Next.js Frontend Setup

#### 4. Create Next.js Project
```bash
# Create Next.js 15 project with pnpm
pnpm create next-app@latest nextjs-app \
  --typescript \
  --tailwind \
  --app \
  --import-alias "@/*" \
  --use-pnpm

cd nextjs-app

# Install additional dependencies
pnpm add @hookform/resolvers react-hook-form zod lucide-react
pnpm add @radix-ui/react-slot @radix-ui/react-label
pnpm add class-variance-authority clsx tailwind-merge

# Initialize shadcn/ui
pnpm dlx shadcn@latest init

# Add required shadcn/ui components
pnpm dlx shadcn@latest add form input button progress table card
pnpm dlx shadcn@latest add dialog toast sidebar breadcrumb
```

#### 5. Environment Configuration
Create `nextjs-app/.env.local`:
```env
# HTTP API Integration
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://localhost:8000

# File Upload Configuration
NEXT_PUBLIC_MAX_FILE_SIZE=104857600
NEXT_PUBLIC_ALLOWED_FILE_TYPES=application/pdf,image/jpeg,image/png

# Next.js Configuration
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

#### 6. Next.js 15 Configuration
Update `nextjs-app/next.config.js`:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: '100mb'
    }
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*'
      }
    ]
  }
}

module.exports = nextConfig
```

#### 7. Create Basic App Structure
```bash
# Create required directories in nextjs-app
cd nextjs-app
mkdir -p src/components/ui
mkdir -p src/components/document-upload
mkdir -p src/components/processing
mkdir -p src/components/results
mkdir -p src/lib
mkdir -p src/types
```

#### 8. TypeScript Definitions (Matching Backend)
Create `src/types/index.ts`:
```typescript
// Types matching existing AISchemaGenerationAPI responses
export interface DocumentAnalysisResponse {
  success: boolean
  processing_stages: Record<string, StageResult>
  document: {
    id: string
    filename: string
    file_type: string
    file_size: number
    processing_status: string
  }
  analysis: {
    id: string
    detected_document_type: string
    document_type_confidence: number
    total_fields_detected: number
    high_confidence_fields: number
    overall_quality_score: number
    model_used: string
  }
  schema: {
    id: string
    name: string
    description: string
    total_fields: number
    high_confidence_fields: number
    generation_confidence: number
    production_ready: boolean
  }
  confidence: {
    overall_confidence: number
    confidence_level: string
  }
  total_processing_time: number
  errors?: string[]
}

export interface StageResult {
  success: boolean
  duration: number
  error?: string
  [key: string]: any
}

// API Client types
export interface DocumentUploadRequest {
  file: File
  model?: string
  document_type_hint?: string
}
```

#### 9. Create API Client
Create `src/lib/api.ts`:
```typescript
import { DocumentUploadRequest, DocumentAnalysisResponse } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const apiClient = {
  uploadDocument: async (request: DocumentUploadRequest): Promise<DocumentAnalysisResponse> => {
    const formData = new FormData()
    formData.append('file', request.file)
    if (request.model) formData.append('model', request.model)
    if (request.document_type_hint) formData.append('document_type_hint', request.document_type_hint)

    const response = await fetch(`${API_BASE}/api/documents`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`)
    }

    return response.json()
  },

  getAnalysisResults: async (analysisId: string) => {
    const response = await fetch(`${API_BASE}/api/analysis/${analysisId}`)
    return response.json()
  },

  getServiceStatus: async () => {
    const response = await fetch(`${API_BASE}/api/status`)
    return response.json()
  }
}
```

## Phase 3: Integration Testing

### Test Scenario 1: HTTP API Integration
**Goal**: Verify FastAPI exposes existing backend correctly

**Steps**:
1. Start both servers:
   ```bash
   # Terminal 1: HTTP API
   cd http_api && python main.py

   # Terminal 2: Next.js frontend
   cd nextjs-app && pnpm dev
   ```
2. Test API directly: `curl -X GET http://localhost:8000/api/status`
3. Navigate to `http://localhost:3000`
4. Upload a test document and verify processing

**Expected Result**:
- HTTP API serves existing functionality correctly
- Next.js frontend communicates with HTTP API
- Document processing works end-to-end

### Test Scenario 2: Full Pipeline Validation
**Goal**: Confirm entire AI processing pipeline works through HTTP

**Steps**:
1. Upload document via Next.js frontend
2. Monitor processing stages in real-time
3. Verify AI analysis results display correctly
4. Check that all existing backend features are accessible
5. Confirm schema generation and confidence scoring work

**Expected Result**:
- All 6 processing stages complete successfully
- Generated schema appears with confidence scores
- No functionality lost from existing system

## Development Commands

### Start Development Servers
```bash
# Terminal 1: FastAPI HTTP server
cd http_api
python main.py

# Terminal 2: Next.js frontend
cd nextjs-app
pnpm dev
```
Access application at `http://localhost:3000`

### Run Tests
```bash
# HTTP API tests
cd http_api
python -m pytest tests/

# Frontend tests
cd nextjs-app
pnpm test

# E2E tests
pnpm test:e2e
```

### Build for Production
```bash
# Build Next.js frontend
cd nextjs-app
pnpm build

# Production HTTP API server
cd http_api
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Development Tools
```bash
# Linting and formatting
cd nextjs-app
pnpm lint
pnpm lint:fix

# Type checking
pnpm tsc --noEmit
```

## Final Project Structure

```
ai-doc-extractor/
├── http_api/                   # FastAPI HTTP layer
│   ├── main.py                # HTTP endpoints exposing existing API
│   ├── requirements.txt       # FastAPI dependencies
│   └── tests/                 # HTTP API tests
├── nextjs-app/                # Next.js 15 frontend
│   ├── src/
│   │   ├── app/              # App Router pages
│   │   │   ├── layout.tsx    # Root layout
│   │   │   ├── page.tsx      # Home page with upload
│   │   │   └── documents/    # Document processing pages
│   │   ├── components/
│   │   │   ├── ui/           # shadcn/ui components
│   │   │   ├── document-upload/  # Upload components
│   │   │   ├── processing/   # Progress components
│   │   │   └── results/      # Results display
│   │   ├── lib/
│   │   │   ├── api.ts        # API client
│   │   │   └── utils.ts      # Utilities
│   │   └── types/
│   │       └── index.ts      # TypeScript definitions
│   ├── next.config.js        # Next.js configuration
│   ├── package.json          # Dependencies
│   └── tailwind.config.js    # Tailwind configuration
└── ai_schema_generation/      # Existing backend (unchanged)
    ├── api/
    │   └── main_endpoint.py   # AISchemaGenerationAPI
    ├── services/              # All processing services
    └── storage/               # Storage systems
```

## Architecture Summary

### How It All Works Together

1. **Existing Backend**: AISchemaGenerationAPI remains unchanged with all sophisticated functionality
2. **HTTP Layer**: FastAPI wraps existing API classes with REST endpoints
3. **Frontend**: Next.js 15 provides modern UI consuming HTTP endpoints
4. **Integration**: Next.js proxy routes frontend API calls to FastAPI server

### Key Benefits

**Preserves Existing Investment**:
- All AISchemaGenerationAPI functionality intact
- LiteLLM multi-provider integration preserved
- Schema management system unchanged
- Cost tracking and performance monitoring retained

**Adds Modern Frontend**:
- React-based UI with shadcn/ui components
- Real-time progress updates
- TypeScript type safety
- Mobile-responsive design

**Clean Architecture**:
- HTTP API layer is thin wrapper over existing classes
- Frontend and backend can be developed/deployed independently
- No business logic rewriting required

## Troubleshooting

### Common Issues

**HTTP API Not Starting**:
- Check existing AISchemaGenerationAPI imports work
- Verify Python dependencies installed: `pip install fastapi uvicorn`
- Check port 8000 is available

**Frontend API Connection Fails**:
- Verify FastAPI server running on http://localhost:8000
- Check CORS configuration allows http://localhost:3000
- Test API directly: `curl http://localhost:8000/api/status`

**Document Processing Errors**:
- Check existing backend has required LLM API keys
- Verify document formats supported by existing system
- Check existing storage directories have permissions

**Next.js Build Issues**:
- Ensure pnpm is installed: `npm install -g pnpm`
- Verify Node.js 18+ is installed
- Check TypeScript types match API responses

### Integration Issues

**CORS Errors**:
```python
# In http_api/main.py, ensure CORS is configured:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**API Response Mismatches**:
- Check TypeScript types in `src/types/index.ts` match actual responses
- Use browser dev tools to inspect actual API responses
- Update types to match existing AISchemaGenerationAPI output format

## Next Steps

After completing the quickstart:

1. **Implement Core Components**: Build document upload, progress, and results components
2. **Add Real-time Updates**: Implement polling for processing progress
3. **Enhance Error Handling**: Add comprehensive error boundaries and retry logic
4. **Performance Optimization**: Add caching and optimize API calls
5. **Deploy**: Set up production deployment with both FastAPI and Next.js

## Development Workflow

1. **Backend Development**: All AI/processing changes in existing `ai_schema_generation/`
2. **HTTP API**: Only add endpoints in `http_api/main.py`, no business logic
3. **Frontend Development**: All UI/UX work in `nextjs-app/src/`
4. **Testing**: Test each layer independently then integration

This approach leverages your existing sophisticated backend while providing a modern frontend experience.