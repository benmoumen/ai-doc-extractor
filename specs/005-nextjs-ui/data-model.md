# Data Model: HTTP API Layer + Next.js Frontend (Leveraging Existing Backend)

## Overview
This data model describes the HTTP API layer that exposes existing `AISchemaGenerationAPI` functionality and the Next.js frontend data structures that consume these APIs.

## Architecture: Existing Backend + HTTP Layer + Frontend

```
┌─────────────────────┐    HTTP API     ┌──────────────────────┐    Uses      ┌─────────────────────┐
│   Next.js Frontend  │ ──────────────> │   FastAPI HTTP Layer │ ──────────> │   Existing Backend   │
│   - React Components│                 │   - REST Endpoints   │             │   - AISchemaGenAPI   │
│   - TypeScript Types│                 │   - Request/Response │             │   - Schema Management│
│   - State Management│                 │   - Error Handling   │             │   - Storage Systems  │
└─────────────────────┘                 └──────────────────────┘             └─────────────────────┘
```

## Existing Backend Data Structures (Preserved)

### From AISchemaGenerationAPI
These data structures already exist and are fully implemented:

#### SampleDocument (Existing)
- `id: str` - Document identifier
- `filename: str` - Original filename
- `file_type: str` - MIME type
- `file_size: int` - Size in bytes
- `processing_status: str` - Current status
- `upload_timestamp: datetime` - When uploaded
- `file_path: str` - Storage path
- `metadata: dict` - Additional metadata

#### AIAnalysisResult (Existing)
- `id: str` - Analysis identifier
- `document_id: str` - Reference to document
- `detected_document_type: str` - Detected type
- `document_type_confidence: float` - Detection confidence
- `total_fields_detected: int` - Number of fields found
- `high_confidence_fields: int` - High-confidence fields
- `overall_quality_score: float` - Analysis quality
- `model_used: str` - AI model identifier
- `processing_timestamp: datetime` - Analysis time
- `retry_count: int` - Number of retries

#### ExtractedField (Existing)
- `id: str` - Field identifier
- `analysis_id: str` - Parent analysis
- `name: str` - Field name
- `display_name: str` - Human-readable label
- `field_type: str` - Data type
- `extracted_value: Any` - The extracted value
- `confidence_score: float` - Extraction confidence
- `validation_status: str` - Validation result
- `requires_review: bool` - Needs human review
- `extraction_source: str` - Where found in document
- `alternatives: list` - Alternative values

#### GeneratedSchema (Existing)
- `id: str` - Schema identifier
- `name: str` - Schema name
- `description: str` - Schema description
- `analysis_result_id: str` - Source analysis
- `fields: list[SchemaField]` - Schema fields
- `total_fields_generated: int` - Number of fields
- `high_confidence_fields: int` - High-confidence fields
- `generation_confidence: float` - Overall confidence
- `validation_status: str` - Validation state
- `user_review_status: str` - Review status
- `created_timestamp: datetime` - Creation time

#### ValidationRule (Existing)
- `id: str` - Rule identifier
- `field_id: str` - Associated field
- `rule_type: str` - Type of validation
- `rule_value: Any` - Rule parameters
- `priority: int` - Rule priority
- `is_recommended: bool` - System recommendation
- `confidence: float` - Rule confidence

## HTTP API Data Transfer Objects

### Request DTOs

#### DocumentUploadRequest
```typescript
interface DocumentUploadRequest {
  file: File                    // Document file
  model?: string               // AI model preference
  document_type_hint?: string  // Type hint for analysis
  metadata?: Record<string, unknown>  // Additional metadata
}
```

#### AnalysisRetryRequest
```typescript
interface AnalysisRetryRequest {
  model?: string               // Different model to try
  document_type_hint?: string  // New type hint
}
```

### Response DTOs (Match Existing API Output)

#### DocumentAnalysisResponse
```typescript
interface DocumentAnalysisResponse {
  success: boolean
  processing_stages: {
    document_processing: ProcessingStage
    ai_analysis: ProcessingStage
    field_enhancement: ProcessingStage
    validation_inference: ProcessingStage
    schema_generation: ProcessingStage
    confidence_analysis: ProcessingStage
  }
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
    validation_status: string
    production_ready: boolean
  }
  confidence: {
    overall_confidence: number
    confidence_level: 'low' | 'medium' | 'high'
  }
  recommendations: string[]
  errors: string[]
  total_processing_time: number
}
```

#### ProcessingStage
```typescript
interface ProcessingStage {
  success: boolean
  duration: number
  error?: string
}
```

#### AnalysisResults
```typescript
interface AnalysisResults {
  success: boolean
  analysis: {
    id: string
    detected_document_type: string
    document_type_confidence: number
    total_fields_detected: number
    model_used: string
    processing_timestamp: string
  }
  fields: ExtractedField[]
  validation_rules: ValidationRule[]
  generated_schemas: GeneratedSchema[]
  confidence_analysis: {
    overall_confidence: number
    field_confidences: Record<string, number>
    quality_metrics: object
  }
}
```

#### ExtractedField (HTTP)
```typescript
interface ExtractedField {
  id: string
  name: string
  display_name: string
  field_type: 'string' | 'number' | 'date' | 'boolean' | 'array'
  extracted_value: unknown
  confidence_score: number
  validation_status: 'valid' | 'warning' | 'invalid' | 'missing'
  requires_review: boolean
  extraction_source: string
  alternatives: unknown[]
}
```

#### ValidationRule (HTTP)
```typescript
interface ValidationRule {
  id: string
  field_id: string
  rule_type: 'pattern' | 'min_length' | 'max_length' | 'required' | 'format'
  rule_value: unknown
  priority: number
  is_recommended: boolean
  confidence: number
}
```

#### GeneratedSchema (HTTP)
```typescript
interface GeneratedSchema {
  id: string
  name: string
  description: string
  fields: SchemaField[]
  total_fields_generated: number
  high_confidence_fields: number
  generation_confidence: number
  validation_status: string
  user_review_status: string
  created_timestamp: string
}
```

#### SchemaField
```typescript
interface SchemaField {
  name: string
  display_name: string
  field_type: string
  required: boolean
  validation_rules: ValidationRule[]
  description: string
  examples: string[]
}
```

## Next.js Frontend State Management

### Document Upload State
```typescript
interface DocumentUploadState {
  file: File | null
  isUploading: boolean
  uploadProgress: number
  analysisId: string | null
  error: string | null
}
```

### Processing State
```typescript
interface ProcessingState {
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error'
  currentStage: string | null
  stageProgress: Record<string, ProcessingStage>
  estimatedTimeRemaining: number | null
  startTime: number | null
}
```

### Analysis Results State
```typescript
interface AnalysisResultsState {
  analysisId: string
  documentType: string
  confidence: number
  extractedFields: ExtractedField[]
  generatedSchema: GeneratedSchema | null
  validationResults: ValidationRule[]
  errors: string[]
  isEditing: boolean
  unsavedChanges: boolean
}
```

### Schema Management State
```typescript
interface SchemaManagementState {
  availableSchemas: SchemaListItem[]
  selectedSchema: GeneratedSchema | null
  isLoading: boolean
  searchQuery: string
  filters: {
    documentType: string | null
    confidenceLevel: string | null
    isCustom: boolean | null
  }
}
```

### Form State (React Hook Form)
```typescript
interface DocumentFormState {
  extractedData: Record<string, unknown>
  validationErrors: Record<string, string>
  fieldStates: Record<string, {
    isEdited: boolean
    originalValue: unknown
    currentValue: unknown
    confidence: number
    validationStatus: string
  }>
}
```

## Integration Patterns

### API Client Service
```typescript
class APIClient {
  private baseURL = '/api'

  async uploadDocument(request: DocumentUploadRequest): Promise<DocumentAnalysisResponse> {
    const formData = new FormData()
    formData.append('file', request.file)
    if (request.model) formData.append('model', request.model)
    if (request.document_type_hint) formData.append('document_type_hint', request.document_type_hint)
    if (request.metadata) formData.append('metadata', JSON.stringify(request.metadata))

    const response = await fetch(`${this.baseURL}/documents`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error)
    }

    return response.json()
  }

  async getAnalysisResults(analysisId: string): Promise<AnalysisResults> {
    const response = await fetch(`${this.baseURL}/analysis/${analysisId}`)
    if (!response.ok) throw new Error('Failed to get analysis results')
    return response.json()
  }

  async retryAnalysis(analysisId: string, request: AnalysisRetryRequest): Promise<RetryAnalysisResponse> {
    const response = await fetch(`${this.baseURL}/analysis/${analysisId}/retry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    })
    if (!response.ok) throw new Error('Retry analysis failed')
    return response.json()
  }

  async getSchemas(): Promise<SchemaListItem[]> {
    const response = await fetch(`${this.baseURL}/schemas`)
    if (!response.ok) throw new Error('Failed to get schemas')
    return response.json()
  }

  async getSchemaDetails(schemaId: string): Promise<SchemaDetails> {
    const response = await fetch(`${this.baseURL}/schemas/${schemaId}`)
    if (!response.ok) throw new Error('Failed to get schema details')
    return response.json()
  }
}
```

### React Hook for Document Processing
```typescript
function useDocumentProcessing() {
  const [state, setState] = useState<ProcessingState>({
    status: 'idle',
    currentStage: null,
    stageProgress: {},
    estimatedTimeRemaining: null,
    startTime: null
  })

  const processDocument = async (file: File, options?: {
    model?: string
    documentTypeHint?: string
  }) => {
    try {
      setState(prev => ({ ...prev, status: 'uploading', startTime: Date.now() }))

      const result = await apiClient.uploadDocument({
        file,
        model: options?.model,
        document_type_hint: options?.documentTypeHint
      })

      setState(prev => ({
        ...prev,
        status: 'completed',
        stageProgress: result.processing_stages
      }))

      return result
    } catch (error) {
      setState(prev => ({
        ...prev,
        status: 'error'
      }))
      throw error
    }
  }

  return { state, processDocument }
}
```

## Data Flow Patterns

### Document Upload → Processing → Results
```
1. User selects file in Next.js frontend
2. Frontend calls POST /api/documents
3. FastAPI receives request, calls AISchemaGenerationAPI.analyze_document()
4. Existing backend processes document through full pipeline
5. FastAPI returns complete analysis results
6. Frontend displays results using existing data structures
```

### Schema Management
```
1. Frontend calls GET /api/schemas
2. FastAPI calls existing schema management system
3. Frontend displays schemas using existing schema data
4. User selects schema, frontend calls GET /api/schemas/{id}
5. FastAPI returns detailed schema using existing storage
```

### Field Editing & Validation
```
1. Frontend displays extracted fields from analysis results
2. User edits field values in React form
3. Frontend validates against existing validation rules
4. Changes stored in local state until save
5. On save, frontend could call update endpoint (future enhancement)
```

## Key Benefits of This Approach

### Preserves Existing Investment ✅
- All existing data structures remain unchanged
- Complete AISchemaGenerationAPI pipeline preserved
- Schema management system fully leveraged
- Storage systems (SQLite + JSON) continue to work

### Adds Modern Frontend ✅
- TypeScript type safety across API boundaries
- React state management for real-time updates
- Form validation with immediate feedback
- Responsive UI with shadcn/ui components

### Scalable Architecture ✅
- HTTP API layer can be extended with new endpoints
- Frontend can add new features consuming existing APIs
- Backend can be enhanced without breaking frontend
- Clear separation of concerns between layers

This data model ensures we leverage the sophisticated existing backend while providing a modern, type-safe frontend experience.