# AI Data Extractor - Backend

Single-file FastAPI backend (`main.py`) providing AI-powered document processing with schema-based and free-form data extraction.

## Implementation

**Architecture:**

- Single FastAPI application (43KB)
- In-memory schema storage
- Multi-provider AI integration via LiteLLM
- Document processing with PIL and PyMuPDF
- KYC document verification

**Providers Supported:**

- Groq (Llama Scout 17B)
- Mistral (Mistral Small 3.2)

**File Formats:**

- PDF (first page processed)
- Images: PNG, JPG, JPEG, TIFF, BMP

## API Endpoints

### Complete Endpoint Reference

| Method | Endpoint               | Purpose            | Description                                  |
| ------ | ---------------------- | ------------------ | -------------------------------------------- |
| `GET`  | `/health`              | Health Check       | Backend health status and availability       |
| `GET`  | `/api/models`          | List AI Models     | Get all available AI models across providers |
| `GET`  | `/api/schemas`         | List Schemas       | Get all stored extraction schemas            |
| `GET`  | `/api/schemas/{id}`    | Get Schema Details | Retrieve complete schema definition          |
| `POST` | `/api/documents`       | Upload Document    | Upload and validate document files           |
| `POST` | `/api/extract`         | Extract Data       | Extract structured data using schemas or AI  |
| `POST` | `/api/generate-schema` | Generate Schema    | Create schema from sample document           |
| `POST` | `/api/schemas`         | Save Schema        | Save generated schema for future use         |
| `GET`  | `/metrics`             | Metrics            | Prometheus-compatible metrics endpoint       |

### Detailed Documentation

### 1. Health Check

```http
GET /health
```

Returns backend health status and availability.

**Response:**

```json
{
  "status": "healthy",
  "backend_available": true,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. List AI Models

```http
GET /api/models
```

Get all available AI models across providers.

**Response:**

```json
{
  "success": true,
  "models": [
    {
      "id": "meta-llama/llama-4-scout-17b-16e-instruct",
      "name": "Llama Scout 17B",
      "provider": "Groq",
      "model": "meta-llama/llama-4-scout-17b-16e-instruct",
      "provider_id": "groq",
      "model_id": "meta-llama/llama-4-scout-17b-16e-instruct"
    }
  ],
  "default_model": "meta-llama/llama-4-scout-17b-16e-instruct"
}
```

### 3. List Available Schemas

```http
GET /api/schemas
```

Get all stored extraction schemas.

**Response:**

```json
{
  "success": true,
  "schemas": {
    "passport": {
      "id": "passport",
      "name": "Passport",
      "display_name": "International Passport"
    }
  }
}
```

### 4. Get Schema Details

```http
GET /api/schemas/{schema_id}
```

Retrieve complete schema definition with all field specifications.

**Response:**

```json
{
  "success": true,
  "schema": {
    "id": "passport",
    "name": "Passport",
    "description": "International passport document",
    "fields": {
      "passport_number": {
        "type": "text",
        "required": true,
        "description": "Passport number"
      },
      "full_name": {
        "type": "text",
        "required": true,
        "description": "Full name as on passport"
      }
    }
  }
}
```

### 5. Extract Data from Document

```http
POST /api/extract
```

Extract structured data using either schemas or AI free-form discovery.

**Parameters:**

- `file` (file): Document to process (PDF/image)
- `schema_id` (string, optional): Schema ID for guided extraction
- `use_ai` (boolean): Enable AI free-form discovery
- `model` (string, optional): AI model to use

**Schema-guided extraction:**

```bash
curl -X POST "http://localhost:8000/api/extract" \
  -F "file=@document.pdf" \
  -F "schema_id=passport" \
  -F "use_ai=false"
```

**AI free-form discovery:**

```bash
curl -X POST "http://localhost:8000/api/extract" \
  -F "file=@document.pdf" \
  -F "use_ai=true"
```

**Response:**

```json
{
  "success": true,
  "document_verification": {
    "document_type_confidence": 95,
    "authenticity_score": 88,
    "tampering_indicators": {
      "photo_manipulation": false,
      "text_alterations": false
    },
    "risk_level": "low"
  },
  "extracted_data": {
    "structured_data": {
      "passport_number": "A12345678",
      "full_name": "John Doe"
    },
    "field_confidence": {
      "passport_number": 95,
      "full_name": 92
    },
    "overall_confidence": 93
  },
  "validation": {
    "passed": true,
    "errors": []
  },
  "metadata": {
    "processing_time": 2.3,
    "model_used": "mistral-small-2506",
    "extraction_mode": "schema_guided"
  }
}
```

### 6. Generate Schema from Sample

```http
POST /api/generate-schema
```

Analyze a sample document to automatically generate an extraction schema.

**Parameters:**

- `file` (file): Sample document to analyze
- `model` (string, optional): AI model for analysis

**Usage:**

```bash
curl -X POST "http://localhost:8000/api/generate-schema" \
  -F "file=@sample_document.pdf" \
  -F "model=mistral-small-2506"
```

**Process:** 4-step AI analysis

1. **Initial Detection** - Identify document type and basic structure
2. **Field Enhancement** - Refine field definitions and descriptions
3. **Confidence Analysis** - Calculate field confidence scores
4. **Hints Generation** - Add extraction hints and validation patterns

**Response:**

```json
{
  "success": true,
  "generated_schema": {
    "schema_id": "generated_schema_123",
    "schema_data": {
      "id": "generated_schema_123",
      "name": "Business Invoice",
      "description": "Commercial invoice schema",
      "fields": {
        "invoice_number": {
          "type": "text",
          "required": true,
          "description": "Unique invoice identifier",
          "confidence_score": 95,
          "extraction_hints": ["top-right corner", "bold text"]
        }
      }
    },
    "is_valid": true,
    "ready_for_extraction": true
  },
  "next_steps": {
    "available_in_schemas": true,
    "schema_endpoint": "/api/schemas/generated_schema_123"
  },
  "metadata": {
    "processing_time": 25.7,
    "steps_completed": 4,
    "fields_generated": 8
  }
}
```

### 7. Save Generated Schema

```http
POST /api/schemas
```

Save a schema to make it available for future data extraction.

**Request Body:**

```json
{
  "id": "custom_schema",
  "name": "Custom Document",
  "description": "Custom document schema",
  "category": "Business",
  "fields": {
    "field_name": {
      "type": "text",
      "required": true,
      "description": "Field description"
    }
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "Schema saved successfully",
  "schema_id": "custom_schema",
  "available_for_extraction": true
}
```

### 8. Document Upload & Analysis

```http
POST /api/documents
```

Alternative document processing endpoint with similar functionality to `/api/generate-schema`.

## Core Functions

**Document Processing:**

- `pdf_to_images()` - Convert PDF to PIL Image
- `image_to_base64()` - Encode images for AI APIs
- `determine_file_type()` - File extension detection

**AI Integration:**

- `create_extraction_prompt()` - Schema-guided extraction prompts
- `create_*_detection_prompt()` - Multi-step schema generation prompts
- `extract_json_from_text()` - Parse JSON from AI responses
- `get_model_param()` - Format model names for LiteLLM

**Schema Management:**

- In-memory `SCHEMAS` dictionary
- Dynamic schema storage and retrieval
- Field validation and confidence scoring

## Data Extraction Modes

**Schema-guided:**

```bash
curl -X POST "http://localhost:8000/api/extract" \
  -F "file=@document.pdf" \
  -F "schema_id=passport" \
  -F "use_ai=false"
```

**AI Free-form Discovery:**

```bash
curl -X POST "http://localhost:8000/api/extract" \
  -F "file=@document.pdf" \
  -F "use_ai=true"
```

## Schema Generation Process

4-step AI analysis pipeline:

1. **Initial Detection** - Document structure analysis
2. **Field Enhancement** - Refine field definitions
3. **Confidence Analysis** - Calculate field confidence scores
4. **Hints Generation** - Add extraction hints and validation patterns

## Document Verification

Automatic KYC compliance features:

- Document type confidence (0-100)
- Tampering detection indicators
- Authenticity scoring
- Risk level assessment (`low`/`medium`/`high`)

## Quick Start

**Run locally:**

```bash
# Set API keys
export GROQ_API_KEY="your_key"
export MISTRAL_API_KEY="your_key"

# Install and run
pip install -r requirements.txt
python main.py
```

**Docker:**

```bash
make dev-build  # Development
make prod-build # Production
```

**API Documentation:**

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health
