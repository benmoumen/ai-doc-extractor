# AI Document Data Extractor - Backend

FastAPI-based backend service for AI-powered document data extraction using LiteLLM.

## Features

- **Document Processing**: Extract structured data from images and PDFs
- **Multi-Model Support**: Groq (Llama), Mistral, OpenAI, Anthropic via LiteLLM
- **Schema Management**: Define and validate document schemas
- **AI Schema Generation**: Automatically generate schemas from sample documents
- **RESTful API**: Clean, documented API endpoints

## Quick Start

### Local Development

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Set up environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run the server:**
```bash
uvicorn http_api.main:app --reload --port 8000
```

4. **Access API documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker Development

```bash
# From project root
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up backend
```

## API Endpoints

### Core Endpoints

- `GET /health` - Health check
- `GET /api/models` - List available AI models
- `GET /api/schemas` - List document schemas
- `POST /api/extract` - Extract data from document

### Schema Management

- `GET /api/schemas/{schema_id}` - Get schema details
- `POST /api/documents` - Upload document for AI analysis
- `GET /api/analysis/{analysis_id}` - Get analysis results

## Project Structure

```
backend/
├── http_api/           # FastAPI application
│   └── main.py        # Main API endpoints
├── ai_schema_generation/  # AI-powered schema generation
├── schema_management/     # Schema CRUD operations
├── config.py             # Configuration and settings
├── utils.py              # Utility functions
├── schema_utils.py       # Schema utilities
├── requirements.txt      # Python dependencies
└── Dockerfile           # Container definition
```

## Environment Variables

```bash
# Required API Keys
GROQ_API_KEY=your_key
MISTRAL_API_KEY=your_key

# Optional API Keys
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# Database (optional)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aidoc_db
DB_USER=aidoc
DB_PASSWORD=changeme

# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=info
```

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Format code
black .
isort .

# Lint code
flake8 .
```

## API Usage Examples

### Extract Data from Document

```bash
curl -X POST "http://localhost:8000/api/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "schema_id=invoice" \
  -F "model=groq_llama-scout-17b"
```

### List Available Models

```bash
curl -X GET "http://localhost:8000/api/models"
```

### Get Schema Details

```bash
curl -X GET "http://localhost:8000/api/schemas/invoice"
```

## Development

### Adding New Models

1. Update `config.py` with model configuration
2. Add provider credentials to `.env`
3. Test with `/api/models` endpoint

### Creating Schemas

1. Define schema in `schema_management/`
2. Register in schema registry
3. Test extraction with new schema

## Docker Build

```bash
# Build image
docker build -t ai-doc-backend .

# Run container
docker run -p 8000:8000 --env-file .env ai-doc-backend
```

## Performance

- Supports concurrent requests
- Response caching via Redis (optional)
- Async document processing
- Optimized for <2s response time

## Security

- API key authentication for LLM providers
- CORS configuration for frontend integration
- Environment-based configuration
- Input validation and sanitization

## Troubleshooting

### API Key Issues
- Verify keys in `.env` file
- Check provider API limits
- Review logs for authentication errors

### Document Processing Errors
- Ensure file size < 100MB
- Verify supported formats (PDF, JPG, PNG)
- Check model availability

### Performance Issues
- Enable Redis caching
- Use appropriate model for task
- Monitor resource usage

## License

See main project LICENSE file.