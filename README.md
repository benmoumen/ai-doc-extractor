# AI Data Extractor

A modern web application for extracting structured data from documents using AI. Features document analysis, schema generation, and intelligent data extraction with confidence scoring.

## Features

- **Document Analysis** - AI-powered analysis of document structure and content
- **Schema Generation** - Automatically generate extraction schemas from sample documents
- **Data Extraction** - Extract structured data using predefined schemas or AI free-form discovery
- **Document Verification** - KYC-compliant document authenticity and tampering detection
- **Multi-format Support** - Process PDFs, images, and various document types
- **Real-time Processing** - Live progress tracking during AI analysis
- **Export Capabilities** - Export extracted data in JSON format

## Tech Stack

- **Frontend**: Next.js 15 with TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI with Python 3.11+
- **AI Integration**: LiteLLM supporting multiple providers (Groq, Mistral)
- **Database**: SQLite (file-based, no external dependencies)
- **Deployment**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- API keys for at least one AI provider (Groq or Mistral)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-doc-extractor
cp .env.example .env
```

### 2. Configure API Keys

Edit `.env` file with your API keys:

```bash
# Required: At least one AI provider
GROQ_API_KEY=your_groq_key
MISTRAL_API_KEY=your_mistral_key
```

### 3. Start Development Environment

```bash
make dev-build
```

### 4. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Development

### Available Commands

```bash
# Development
make dev              # Start development environment
make dev-build        # Build and start development
make dev-down         # Stop development environment

# Production
make prod             # Start production environment
make prod-build       # Build and start production
make prod-down        # Stop production environment

# Utilities
make logs             # View all logs
make logs-backend     # View backend logs
make logs-frontend    # View frontend logs
make health           # Check service health
make clean            # Clean up containers and volumes
```

### Development Features

- **Hot Reloading**: Both frontend and backend support hot reloading
- **Volume Mounting**: Source code mounted for instant changes
- **Debug Mode**: Detailed logging and error information
- **File Watching**: Automatic rebuilds on dependency changes

## Architecture

```
ai-doc-extractor/
├── frontend/              # Next.js application
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # React components
│   │   ├── lib/          # Utilities and API client
│   │   └── types/        # TypeScript definitions
│   └── public/           # Static assets
├── backend/              # FastAPI application
│   ├── main.py           # Application entry point
│   ├── routers/          # API route handlers
│   ├── services/         # Business logic (database, AI)
│   ├── requirements.txt
│   ├── Dockerfile        # Production build
│   └── Dockerfile.dev    # Development build
├── data/                 # SQLite database storage
├── docker-compose.yml    # Base configuration
├── docker-compose.dev.yml # Development overrides
└── .env.example          # Environment template
```

## Usage

### 1. Document Analysis

1. Navigate to the **Document Analysis** tab
2. Upload a sample document (PDF or image)
3. Select AI model and click **Generate Schema**
4. Review the generated schema with field definitions
5. Save schema for future extractions

### 2. Data Extraction

1. Navigate to the **Data Extraction** tab
2. Choose extraction mode:
   - **Schema-guided**: Use predefined schemas
   - **AI Free-form Discovery**: Let AI discover all data
3. Upload document and select model
4. Review extracted data with confidence scores
5. Export results as JSON

### 3. Document Verification

The system automatically performs KYC-compliant verification:

- **Document Type Confidence**: Accuracy of document classification
- **Authenticity Score**: Document legitimacy assessment
- **Tampering Detection**: Identifies potential alterations
- **Risk Level**: Overall security assessment (Low/Medium/High)

## AI Models

Supported AI providers and models:

- **Groq**: Llama Scout 17B (meta-llama/llama-4-scout-17b-16e-instruct)
- **Mistral**: Mistral Small 3.2 (mistral-small-2506)

## API Documentation

### API Endpoints

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

### Interactive Documentation

Interactive API documentation available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```bash
# Document analysis
POST /api/generate-schema    # Generate schema from document
GET  /api/schemas           # List available schemas
GET  /api/schemas/{id}      # Get schema details

# Data extraction
POST /api/extract           # Extract data from document
GET  /api/models           # List supported AI models
GET  /api/status           # Service health status
```

## Production Deployment

### Environment Setup

1. Copy and configure production environment:

```bash
cp .env.example .env.production
# Edit .env.production with production values
```

2. Set production environment variables:

- `ENVIRONMENT=production`
- `DEBUG=false`
- `ENABLE_API_KEY_AUTH=true`
- Valid AI API keys

### Deploy with Docker

```bash
# Build and start production services
docker-compose up --build -d

# Check service health
curl http://localhost:8000/health
```

### Production Features

- **SQLite Database**: File-based storage with persistence via Docker volumes
- **Health Checks**: Automatic service monitoring
- **Internal Deployment**: No external HTTPS/nginx required
- **Auto-restart**: Services restart on failure
- **API Authentication**: Optional API key protection

## Database Management

The application uses SQLite for schema storage:

- **Database Location**: `./data/schemas.db`
- **Persistence**: Mounted as Docker volume for data retention
- **Backups**: Simple file copy of `./data/schemas.db`

```bash
# Backup database (simple file copy)
cp ./data/schemas.db ./backups/schemas_backup_$(date +%Y%m%d_%H%M%S).db

# View database location
ls -la ./data/
```

## Troubleshooting

### Common Issues

**Services won't start:**

```bash
make clean        # Clean up containers
make dev-build    # Rebuild from scratch
```

**AI API key errors:**

- Verify `.env` file exists and contains valid AI provider keys
- Check AI API key permissions and quotas
- Ensure at least one AI provider is configured

**File upload issues:**

- Check file size limits (default: 50MB)
- Verify supported formats: PDF, PNG, JPG, JPEG
- Ensure backend storage permissions

**Database connection errors:**

```bash
# Check if database directory exists and has permissions
ls -la ./data/
# Check backend logs for database errors
make logs-backend
```

### Development Issues

**Hot reload not working:**

- Ensure file watching is enabled in Docker Desktop
- Check volume mounts in `docker-compose.dev.yml`
- Restart development environment

**TypeScript errors:**

```bash
make shell-frontend
pnpm run type-check
```
