/**
 * API client for communicating with FastAPI HTTP endpoints
 * that expose existing AISchemaGenerationAPI functionality
 */

import {
  DocumentUploadRequest,
  DocumentAnalysisResponse,
  SchemaDetailsResponse,
  SupportedModelsResponse,
  AvailableSchemasResponse,
  ExtractDataResponse,
  SchemaGenerationResponse,
  SchemaGenerationRequest,
} from "@/types";

// API base URL - point to the data extraction API server
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: Response
  ) {
    super(message);
    this.name = "APIError";
  }
}

/**
 * API Client for document processing operations
 */
export class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE) {
    this.baseURL = baseURL;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = "Unknown error occurred";

      try {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const errorData = await response.json();
          // Extract user-friendly message from API error response
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (errorData.message) {
            errorMessage = errorData.message;
          } else {
            errorMessage = JSON.stringify(errorData);
          }
        } else {
          errorMessage = await response.text();
        }
      } catch {
        errorMessage = `HTTP ${response.status} error`;
      }

      throw new APIError(errorMessage, response.status, response);
    }

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return response.json();
    } else {
      throw new APIError("Expected JSON response from API");
    }
  }

  // Analysis results tracking removed - not implemented in backend

  /**
   * Get complete schema details
   * Calls GET /api/schemas/{id} endpoint which uses AISchemaGenerationAPI.get_schema_details()
   */
  async getSchemaDetails(schemaId: string): Promise<SchemaDetailsResponse> {
    // Add cache-busting timestamp
    const timestamp = new Date().getTime();
    const response = await fetch(`${this.baseURL}/api/schemas/${schemaId}?_t=${timestamp}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
      },
    });

    return this.handleResponse<SchemaDetailsResponse>(response);
  }

  // Analysis retry functionality removed - not implemented in backend

  /**
   * Get list of supported AI models
   * Calls GET /api/models endpoint which uses AISchemaGenerationAPI.get_supported_models()
   */
  async getSupportedModels(): Promise<SupportedModelsResponse> {
    const response = await fetch(`${this.baseURL}/api/models`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    return this.handleResponse<SupportedModelsResponse>(response);
  }

  /**
   * Get list of available document schemas/types
   * Calls GET /api/schemas endpoint
   */
  async getAvailableSchemas(): Promise<AvailableSchemasResponse> {
    // Add cache-busting timestamp
    const timestamp = new Date().getTime();
    const response = await fetch(`${this.baseURL}/api/schemas?_t=${timestamp}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
      },
    });

    return this.handleResponse<AvailableSchemasResponse>(response);
  }

  // Service status endpoint removed - not implemented in backend
  // Use healthCheck() instead for basic health monitoring

  /**
   * Extract data from document using focused extraction endpoint
   */
  async extractData(
    file: File,
    schemaId?: string,
    useAI: boolean = true,
    model?: string
  ): Promise<ExtractDataResponse> {
    const formData = new FormData();
    formData.append("file", file);

    if (schemaId) {
      formData.append("schema_id", schemaId);
    }

    formData.append("use_ai", useAI.toString());

    if (model) {
      formData.append("model", model);
    }

    const response = await fetch(`${this.baseURL}/api/extract`, {
      method: "POST",
      body: formData,
    });

    return this.handleResponse<ExtractDataResponse>(response);
  }

  /**
   * Generate schema from sample document
   * Calls POST /api/generate-schema endpoint
   */
  async generateSchema(
    request: SchemaGenerationRequest
  ): Promise<SchemaGenerationResponse> {
    const formData = new FormData();
    formData.append("file", request.file);

    if (request.model) {
      formData.append("model", request.model);
    }

    const response = await fetch(`${this.baseURL}/api/generate-schema`, {
      method: "POST",
      body: formData,
      // Don't set Content-Type header - let browser set it for multipart/form-data
    });

    return this.handleResponse<SchemaGenerationResponse>(response);
  }

  /**
   * Save a generated schema to make it available for data extraction
   * Calls POST /api/schemas endpoint
   */
  async saveSchema(schemaData: {
    id: string;
    name: string;
    description: string;
    category: string;
    fields: Record<string, unknown>;
  }): Promise<{
    success: boolean;
    message: string;
    schema_id: string;
    schema: {
      id: string;
      name: string;
      category: string;
      field_count: number;
    };
  }> {
    const formData = new FormData();
    formData.append("schema_name", schemaData.name);
    formData.append("schema_category", schemaData.category);
    formData.append("schema_data", JSON.stringify({ fields: schemaData.fields }));

    const response = await fetch(`${this.baseURL}/api/schemas`, {
      method: "POST",
      body: formData,
    });

    return this.handleResponse(response);
  }

  /**
   * Update an existing schema
   * Calls PUT /api/schemas/{id} endpoint
   */
  async updateSchema(
    schemaId: string,
    schemaData: {
      name: string;
      description?: string;
      category: string;
      fields: Record<string, unknown>;
    }
  ): Promise<{
    success: boolean;
    message: string;
    schema_id: string;
    schema: {
      id: string;
      name: string;
      category: string;
      field_count: number;
    };
  }> {
    const formData = new FormData();
    formData.append("schema_name", schemaData.name);
    formData.append("schema_category", schemaData.category);
    formData.append("schema_data", JSON.stringify({ fields: schemaData.fields }));

    const response = await fetch(`${this.baseURL}/api/schemas/${schemaId}`, {
      method: "PUT",
      body: formData,
    });

    return this.handleResponse(response);
  }

  /**
   * Delete an existing schema
   * Calls DELETE /api/schemas/{id} endpoint
   */
  async deleteSchema(schemaId: string): Promise<{
    success: boolean;
    message: string;
    schema_id: string;
  }> {
    const response = await fetch(`${this.baseURL}/api/schemas/${schemaId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    return this.handleResponse(response);
  }

  /**
   * Health check endpoint for monitoring
   */
  async healthCheck(): Promise<{
    status: string;
    backend_available: boolean;
    timestamp: string;
  }> {
    const response = await fetch(`${this.baseURL}/health`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    return this.handleResponse(response);
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export utility functions for common patterns

/**
 * Upload document with progress tracking
 */
export async function uploadDocumentWithProgress(
  request: DocumentUploadRequest,
  onProgress?: (progress: number) => void
): Promise<DocumentAnalysisResponse> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", request.file);

    const xhr = new XMLHttpRequest();

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded * 100) / e.total);
          onProgress(percent);
        }
      });
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const result = JSON.parse(xhr.responseText);
          resolve(result);
        } catch {
          reject(new APIError("Failed to parse response JSON"));
        }
      } else {
        reject(
          new APIError(
            `Upload failed: ${xhr.status} ${xhr.statusText}`,
            xhr.status
          )
        );
      }
    };

    xhr.onerror = () => {
      reject(new APIError("Network error during upload"));
    };

    xhr.open("POST", `${API_BASE}/api/documents`);
    xhr.send(formData);
  });
}

// Analysis progress polling removed - not implemented in backend
// Current backend uses synchronous processing without polling
