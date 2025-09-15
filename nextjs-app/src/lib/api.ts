/**
 * API client for communicating with FastAPI HTTP endpoints
 * that expose existing AISchemaGenerationAPI functionality
 */

import {
  DocumentUploadRequest,
  DocumentAnalysisResponse,
  AnalysisResultsResponse,
  SchemaDetailsResponse,
  ServiceStatusResponse,
  SupportedModelsResponse,
  RetryAnalysisResponse,
  RetryAnalysisRequest
} from '@/types'

// API base URL - uses Next.js proxy in development
const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: Response
  ) {
    super(message)
    this.name = 'APIError'
  }
}

/**
 * API Client for document processing operations
 */
export class APIClient {
  private baseURL: string

  constructor(baseURL: string = API_BASE) {
    this.baseURL = baseURL
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      throw new APIError(
        `HTTP ${response.status}: ${errorText}`,
        response.status,
        response
      )
    }

    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      return response.json()
    } else {
      throw new APIError('Expected JSON response from API')
    }
  }

  /**
   * Upload and analyze document using existing AISchemaGenerationAPI
   * Calls POST /api/documents endpoint which uses AISchemaGenerationAPI.analyze_document()
   */
  async uploadDocument(request: DocumentUploadRequest): Promise<DocumentAnalysisResponse> {
    const formData = new FormData()
    formData.append('file', request.file)

    if (request.model) {
      formData.append('model', request.model)
    }

    if (request.document_type_hint) {
      formData.append('document_type_hint', request.document_type_hint)
    }

    const response = await fetch(`${this.baseURL}/api/documents`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - let browser set it for multipart/form-data
    })

    return this.handleResponse<DocumentAnalysisResponse>(response)
  }

  /**
   * Get complete analysis results by ID
   * Calls GET /api/analysis/{id} endpoint which uses AISchemaGenerationAPI.get_analysis_results()
   */
  async getAnalysisResults(analysisId: string): Promise<AnalysisResultsResponse> {
    const response = await fetch(`${this.baseURL}/api/analysis/${analysisId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return this.handleResponse<AnalysisResultsResponse>(response)
  }

  /**
   * Get complete schema details
   * Calls GET /api/schemas/{id} endpoint which uses AISchemaGenerationAPI.get_schema_details()
   */
  async getSchemaDetails(schemaId: string): Promise<SchemaDetailsResponse> {
    const response = await fetch(`${this.baseURL}/api/schemas/${schemaId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return this.handleResponse<SchemaDetailsResponse>(response)
  }

  /**
   * Retry analysis with different model or parameters
   * Calls POST /api/analysis/{id}/retry endpoint which uses AISchemaGenerationAPI.retry_analysis()
   */
  async retryAnalysis(request: RetryAnalysisRequest): Promise<RetryAnalysisResponse> {
    const body = {
      document_id: request.document_id,
      ...(request.model && { model: request.model })
    }

    const response = await fetch(`${this.baseURL}/api/analysis/${request.analysis_id}/retry`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    return this.handleResponse<RetryAnalysisResponse>(response)
  }

  /**
   * Get list of supported AI models
   * Calls GET /api/models endpoint which uses AISchemaGenerationAPI.get_supported_models()
   */
  async getSupportedModels(): Promise<SupportedModelsResponse> {
    const response = await fetch(`${this.baseURL}/api/models`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return this.handleResponse<SupportedModelsResponse>(response)
  }

  /**
   * Get status of all backend services
   * Calls GET /api/status endpoint which uses AISchemaGenerationAPI.get_service_status()
   */
  async getServiceStatus(): Promise<ServiceStatusResponse> {
    const response = await fetch(`${this.baseURL}/api/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return this.handleResponse<ServiceStatusResponse>(response)
  }

  /**
   * Extract data from document using focused extraction endpoint
   */
  async extractData(
    file: File,
    schemaId?: string,
    useAI: boolean = true,
    model?: string
  ): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)

    if (schemaId) {
      formData.append('schema_id', schemaId)
    }

    formData.append('use_ai', useAI.toString())

    if (model) {
      formData.append('model', model)
    }

    const response = await fetch(`${this.baseURL}/api/extract`, {
      method: 'POST',
      body: formData,
    })

    return this.handleResponse(response)
  }

  /**
   * Health check endpoint for monitoring
   */
  async healthCheck(): Promise<{ status: string; backend_available: boolean; timestamp: string }> {
    const response = await fetch(`${this.baseURL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return this.handleResponse(response)
  }
}

// Export singleton instance
export const apiClient = new APIClient()

// Export utility functions for common patterns

/**
 * Upload document with progress tracking
 */
export async function uploadDocumentWithProgress(
  request: DocumentUploadRequest,
  onProgress?: (progress: number) => void
): Promise<DocumentAnalysisResponse> {
  return new Promise((resolve, reject) => {
    const formData = new FormData()
    formData.append('file', request.file)

    if (request.model) {
      formData.append('model', request.model)
    }

    if (request.document_type_hint) {
      formData.append('document_type_hint', request.document_type_hint)
    }

    const xhr = new XMLHttpRequest()

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded * 100) / e.total)
          onProgress(percent)
        }
      })
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const result = JSON.parse(xhr.responseText)
          resolve(result)
        } catch (error) {
          reject(new APIError('Failed to parse response JSON'))
        }
      } else {
        reject(new APIError(`Upload failed: ${xhr.status} ${xhr.statusText}`, xhr.status))
      }
    }

    xhr.onerror = () => {
      reject(new APIError('Network error during upload'))
    }

    xhr.open('POST', `${API_BASE}/api/documents`)
    xhr.send(formData)
  })
}

/**
 * Poll for analysis progress (for real-time updates)
 */
export async function pollAnalysisProgress(
  analysisId: string,
  onProgress: (progress: any) => void,
  intervalMs: number = 2000
): Promise<() => void> {
  let isPolling = true

  const poll = async () => {
    while (isPolling) {
      try {
        const result = await apiClient.getAnalysisResults(analysisId)
        onProgress(result)

        // Stop polling if analysis is completed or failed
        if (result.success === false ||
            (result.analysis && ['completed', 'failed'].includes(result.analysis.id))) {
          break
        }

        await new Promise(resolve => setTimeout(resolve, intervalMs))
      } catch (error) {
        console.error('Error polling analysis progress:', error)
        // Continue polling on error, but with longer interval
        await new Promise(resolve => setTimeout(resolve, intervalMs * 2))
      }
    }
  }

  // Start polling
  poll()

  // Return stop function
  return () => {
    isPolling = false
  }
}