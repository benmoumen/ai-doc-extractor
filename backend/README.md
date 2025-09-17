# AI Document Data Extractor - Backend API

FastAPI backend providing AI-powered document processing with 8 core endpoints for data extraction and schema management.

## Core Operations

**Document Processing:**
- Extract structured data from documents (PDF, images)
- Generate extraction schemas from sample documents
- Verify document authenticity for KYC compliance

**Schema Management:**
- Create and store custom extraction schemas
- Retrieve available schemas and their details
- In-memory schema storage for fast access

**AI Integration:**
- Multi-provider support (OpenAI, Anthropic, Groq, Mistral)
- Confidence scoring for all extracted fields
- Multi-step schema generation with validation

## API Endpoints

### Health & Configuration

```http
GET /health                    # Health check
GET /api/models               # List supported AI models
```

### Schema Management

```http
GET /api/schemas              # List available schemas
GET /api/schemas/{schema_id}  # Get schema details
POST /api/schemas             # Save generated schema
```

### Document Processing

```http
POST /api/documents           # Upload and analyze document (legacy)
POST /api/extract             # Extract data from document
POST /api/generate-schema     # Generate schema from sample document
```

## Installation

### Prerequisites

- Python 3.11+
- At least one AI provider API key

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your_groq_key"
export MISTRAL_API_KEY="your_mistral_key"
# Add other provider keys as needed

# Run development server
python main.py
```

### Docker Development

```bash
# From project root
make dev-build

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Configuration

### Environment Variables

```bash
# AI API Keys (at least one required)
GROQ_API_KEY=your_groq_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Application Settings
LOG_LEVEL=info
DEBUG=false
PYTHONUNBUFFERED=1

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Supported AI Models

**Groq:**
- `meta-llama/llama-4-scout-17b-16e-instruct` (Llama Scout 17B)

**Mistral:**
- `mistral-small-2506` (Mistral Small 3.2)

*Additional providers can be easily added by updating `PROVIDER_OPTIONS` and `MODEL_OPTIONS`.*

## API Usage

### 1. Extract Data from Document

**Schema-guided extraction:**
```bash
curl -X POST "http://localhost:8000/api/extract" \
  -F "file=@document.pdf" \
  -F "schema_id=passport" \
  -F "use_ai=false" \
  -F "model=mistral-small-2506"
```

**AI free-form discovery:**
```bash
curl -X POST "http://localhost:8000/api/extract" \
  -F "file=@document.pdf" \
  -F "use_ai=true" \
  -F "model=meta-llama/llama-4-scout-17b-16e-instruct"
```

### 2. Generate Schema from Sample

```bash
curl -X POST "http://localhost:8000/api/generate-schema" \
  -F "file=@sample_document.pdf" \
  -F "model=mistral-small-2506"
```

### 3. Save Generated Schema

```bash
curl -X POST "http://localhost:8000/api/schemas" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

## Response Format

### Extraction Response

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
    "raw_content": "...",
    "formatted_text": "...",
    "structured_data": {
      "field1": "value1",
      "field2": "value2"
    },
    "field_confidence": {
      "field1": 95,
      "field2": 87
    },
    "overall_confidence": 91
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

### Schema Generation Response

```json
{
  "success": true,
  "generated_schema": {
    "schema_id": "generated_schema_123",
    "schema_data": {
      "id": "generated_schema_123",
      "name": "Generated Schema",
      "description": "Auto-generated schema",
      "fields": {
        "field_name": {
          "type": "text",
          "required": true,
          "description": "Field description",
          "confidence_score": 95
        }
      }
    },
    "is_valid": true,
    "ready_for_extraction": true
  },
  "next_steps": {
    "available_in_schemas": true,
    "can_use_for_extraction": true,
    "schema_endpoint": "/api/schemas/generated_schema_123"
  }
}
```

## Document Verification

The backend automatically performs KYC-compliant document verification:

**Authenticity Checks:**
- Document type confidence scoring
- Tampering detection (photo manipulation, text alterations)
- Structural anomaly detection
- Font consistency validation

**Security Validation:**
- MRZ checksum validation (for passports/IDs)
- Date logic verification
- Field consistency checks
- Format compliance validation

**Risk Assessment:**
- Overall risk level: `low`, `medium`, `high`
- Detailed tampering indicators
- Confidence scores for each verification aspect

## Development

### File Structure

```
backend/
├── main.py              # Complete FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container definition
└── README.md           # This file
```

### Key Functions

**Document Processing:**
- `pdf_to_images()` - PDF to image conversion
- `image_to_base64()` - Image encoding for AI APIs
- `determine_file_type()` - File type detection

**AI Integration:**
- `create_extraction_prompt()` - Data extraction prompts
- `create_*_prompt()` - Multi-step schema generation prompts
- `extract_json_from_text()` - AI response parsing

**Schema Management:**
- In-memory `SCHEMAS` dictionary
- Dynamic schema registration
- Schema validation and storage

### Adding New AI Providers

1. **Update Configuration:**
```python
PROVIDER_OPTIONS = {
    "Your Provider": "provider_id"
}

MODEL_OPTIONS = {
    "provider_id": {
        "Model Name": "model_identifier"
    }
}
```

2. **Update Model Parameter Function:**
```python
def get_model_param(provider: str, model: str) -> str:
    if provider == "provider_id":
        return f"provider_id/{model}"
    # ... existing providers
```

3. **Set Environment Variable:**
```bash
export YOUR_PROVIDER_API_KEY="your_api_key"
```

### Error Handling

The API uses standard HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid input)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

Error responses include detailed messages:
```json
{
  "detail": "Descriptive error message"
}
```

## Performance

**Optimizations:**
- In-memory schema storage for fast access
- Efficient image processing with PIL
- Single file architecture for minimal overhead
- Stateless design for horizontal scaling

**Typical Response Times:**
- Document extraction: 2-5 seconds
- Schema generation: 10-30 seconds (multi-step AI process)
- Schema retrieval: <100ms

## Production Deployment

### Docker Production

```bash
# Build and deploy
make prod-build

# Health check
curl http://localhost:8000/health
```

### Environment Setup

1. Set production environment variables
2. Configure resource limits in docker-compose.prod.yml
3. Enable logging and monitoring
4. Set up load balancing if needed

### Security Considerations

- Store API keys securely (environment variables, secrets management)
- Enable CORS only for trusted origins
- Use HTTPS in production
- Implement rate limiting if needed
- Monitor API usage and costs

## Monitoring

**Health Endpoint:** `GET /health`
```json
{
  "status": "healthy",
  "backend_available": true,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Logging:**
- Request/response logging via FastAPI
- Error tracking with detailed stack traces
- Performance metrics in response metadata

## Troubleshooting

### Common Issues

**API Key Errors:**
- Verify environment variables are set
- Check API key validity and quotas
- Ensure at least one provider is configured

**File Upload Issues:**
- Check file size limits (default: 50MB)
- Verify supported formats: PDF, PNG, JPG, JPEG
- Ensure proper multipart/form-data encoding

**Model Access Issues:**
- Verify API keys for specific providers
- Check model availability in `MODEL_OPTIONS`
- Review provider-specific rate limits

**Memory Issues:**
- Large documents may require more memory
- Consider implementing file size limits
- Monitor memory usage in production

### Debug Mode

Enable debug logging:
```bash
export DEBUG=true
export LOG_LEVEL=debug
python main.py
```

## License

[License Type] - See main project LICENSE file for details

## Support

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Issues**: Submit to main project repository