/**
 * TypeScript types matching existing AISchemaGenerationAPI responses
 * These interfaces preserve the existing backend data structures
 */

// Processing stage result from existing backend
export interface StageResult {
  success: boolean
  duration: number
  error?: string
  [key: string]: any
}

// Complete document analysis response from AISchemaGenerationAPI.analyze_document()
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
  recommendations?: string[]
}

// Analysis results response from AISchemaGenerationAPI.get_analysis_results()
export interface AnalysisResultsResponse {
  success: boolean
  analysis?: {
    id: string
    detected_document_type: string
    document_type_confidence: number
    total_fields_detected: number
    high_confidence_fields: number
    overall_quality_score: number
    model_used: string
    created_at: string
    processing_time: number
  }
  fields?: Array<{
    id: string
    field_name: string
    display_name: string
    field_type: string
    extracted_value: any
    confidence_score: number
    validation_status: string
    requires_review: boolean
    field_description?: string
    validation_rules?: Array<{
      rule_type: string
      rule_value: any
      rule_description: string
      is_recommended: boolean
    }>
  }>
  validation_rules?: Array<{
    id: string
    field_id: string
    rule_type: string
    rule_value: any
    rule_description: string
    priority: number
    is_recommended: boolean
    confidence_score: number
  }>
  document_type_suggestion?: {
    suggested_type: string
    confidence_score: number
    reasoning: string
    alternative_types: Array<{
      type: string
      confidence: number
    }>
  }
  generated_schemas?: Array<{
    id: string
    name: string
    description: string
    total_fields_generated: number
    high_confidence_fields: number
    generation_confidence: number
    validation_status: string
    user_review_status: string
    production_ready: boolean
  }>
  confidence_analysis?: {
    overall_confidence: number
    confidence_level: string
    field_confidence_breakdown: Record<string, number>
    recommendations: string[]
  }
  error?: string
}

// Schema details response from AISchemaGenerationAPI.get_schema_details()
export interface SchemaDetailsResponse {
  success: boolean
  schema?: {
    id: string
    name: string
    description: string
    total_fields_generated: number
    high_confidence_fields: number
    generation_confidence: number
    validation_status: string
    user_review_status: string
    production_ready: boolean
    created_at: string
    updated_at: string
  }
  confidence_analysis?: {
    overall_confidence: number
    confidence_breakdown: Record<string, number>
    production_readiness: boolean
  }
  quality_metrics?: {
    completeness_score: number
    consistency_score: number
    validation_coverage: number
  }
  review_summary?: {
    total_reviews: number
    approved_fields: number
    rejected_fields: number
    pending_fields: number
  }
  compatibility_info?: {
    json_schema_version: string
    supported_formats: string[]
  }
  standard_format?: Record<string, any>
  error?: string
}

// Service status response from AISchemaGenerationAPI.get_service_status()
export interface ServiceStatusResponse {
  success: boolean
  services?: {
    document_processor: {
      available: boolean
      stats: Record<string, any>
    }
    ai_analyzer: {
      available: boolean
      stats: Record<string, any>
    }
    field_extractor: {
      available: boolean
      stats: Record<string, any>
    }
    validation_rule_inferencer: {
      available: boolean
      stats: Record<string, any>
    }
    schema_generator: {
      available: boolean
      stats: Record<string, any>
    }
    confidence_scorer: {
      available: boolean
      stats: Record<string, any>
    }
  }
  storage?: {
    documents: Record<string, any>
    analyses: Record<string, any>
    schemas: Record<string, any>
  }
  error?: string
}

// Supported models response from AISchemaGenerationAPI.get_supported_models()
export interface SupportedModelsResponse {
  success: boolean
  models?: Array<{
    id: string
    name: string
    provider: string
    description: string
    max_tokens?: number
    cost_per_token?: number
  }>
  default_model?: string
  error?: string
}

// Retry analysis response from AISchemaGenerationAPI.retry_analysis()
export interface RetryAnalysisResponse {
  success: boolean
  retry_analysis?: {
    id: string
    model_used: string
    retry_count: number
  }
  schema?: {
    id: string
    name: string
    total_fields: number
    generation_confidence: number
  }
  confidence?: {
    overall_confidence: number
    confidence_level: string
  }
  improved?: boolean
  error?: string
}

// API request types for frontend
export interface DocumentUploadRequest {
  file: File
  model?: string
  document_type_hint?: string
}

export interface RetryAnalysisRequest {
  analysis_id: string
  document_id: string
  model?: string
}

// UI state types
export interface ProcessingProgress {
  stage: string
  progress: number
  message: string
  completed_stages: string[]
  current_stage: string
  remaining_stages: string[]
}

export interface UploadState {
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error'
  progress: number
  file?: File
  result?: DocumentAnalysisResponse
  error?: string
}

// Form validation types using Zod
export interface FieldValidation {
  field_name: string
  value: any
  is_valid: boolean
  error_message?: string
  confidence_score?: number
}

export interface FormValidationResult {
  is_valid: boolean
  field_validations: Record<string, FieldValidation>
  overall_confidence: number
  warnings: string[]
  errors: string[]
}

// Export data types
export interface ExportOptions {
  format: 'json' | 'csv' | 'pdf' | 'xlsx'
  include_confidence_scores: boolean
  include_metadata: boolean
  fields_to_include?: string[]
}

export interface ExportResult {
  success: boolean
  download_url?: string
  filename?: string
  error?: string
}