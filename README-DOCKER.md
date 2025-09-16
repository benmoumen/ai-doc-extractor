# Docker Setup for AI Document Data Extractor

This guide provides instructions for running the AI Document Data Extractor using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)
- API keys for LLM providers (Groq, Mistral, OpenAI, Anthropic)

## Quick Start

1. **Clone the repository and navigate to the project directory:**

   ```bash
   git clone <repository-url>
   cd ai-doc-extractor
   ```

2. **Set up environment variables:**

   ```bash
   make env-setup
   # Edit .env file with your API keys
   ```

3. **Start the application:**

   ```bash
   make quickstart
   ```

4. **Access the application:**
   - Frontend (Next.js): http://localhost:3000
   - Backend (FastAPI): http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Architecture

The Docker setup includes:

- **Backend**: FastAPI application for document processing API (port 8000)
- **Frontend**: Next.js 15 application for modern UI (port 3000)
- **Database**: PostgreSQL for data persistence (port 5432)
- **Cache**: Redis for performance optimization (port 6379)
- **Proxy**: Nginx for production routing (port 80/443)

## Development

### Start development environment with hot reloading:

```bash
make dev
```

### Access container shells:

```bash
make shell-backend    # Backend shell
make shell-frontend   # Frontend shell
make shell-db        # Database shell
```

### View logs:

```bash
make logs           # All services
make logs-backend   # Backend only
make logs-frontend  # Frontend only
```

## Production

### Start production environment:

```bash
make prod
```

### Production features:

- Resource limits and reservations
- Health checks for all services
- Log rotation
- Nginx reverse proxy
- SSL support (configure in nginx/nginx.conf)

## Database Management

### Backup database:

```bash
make db-backup
```

### Restore database:

```bash
make db-restore FILE=./backups/db_backup_20240101_120000.sql
```

## Testing

### Run all tests:

```bash
make test-all
```

### Run specific tests:

```bash
make test-backend   # Backend tests
make test-frontend  # Frontend tests
```

## Health Checks

### Check service health:

```bash
make health
```

## Troubleshooting

### Container won't start:

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild containers
make clean
make build
```

### API key issues:

- Ensure .env file contains valid API keys
- Check backend logs for authentication errors

### Port conflicts:

- Modify port mappings in docker-compose.yml
- Default ports: 3000 (frontend), 8000 (backend), 5432 (db), 6379 (redis)

### Memory issues:

- Increase Docker Desktop memory allocation
- Reduce resource limits in docker-compose.prod.yml

## Environment Variables

Key environment variables (set in .env):

```bash
# API Keys
GROQ_API_KEY=your_key
MISTRAL_API_KEY=your_key

# Database
DB_PASSWORD=secure_password
DB_HOST=db
DB_PORT=5432

# Application
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Makefile Commands

| Command         | Description                   |
| --------------- | ----------------------------- |
| `make help`     | Show all available commands   |
| `make dev`      | Start development environment |
| `make prod`     | Start production environment  |
| `make build`    | Build Docker images           |
| `make up`       | Start all services            |
| `make down`     | Stop all services             |
| `make logs`     | View logs                     |
| `make clean`    | Remove containers and volumes |
| `make test-all` | Run all tests                 |
| `make health`   | Check service health          |

## Docker Compose Files

- **docker-compose.yml**: Base configuration
- **docker-compose.dev.yml**: Development overrides
- **docker-compose.prod.yml**: Production overrides
- **Dockerfile.backend**: FastAPI backend image
- **nextjs-app/Dockerfile**: Next.js frontend image

## Security Considerations

1. **API Keys**: Never commit .env file with real API keys
2. **Database**: Use strong passwords in production
3. **Network**: Services communicate via internal Docker network
4. **SSL**: Configure SSL certificates for production deployment
5. **Rate Limiting**: Nginx configured with rate limiting

## Performance Optimization

- Redis caching for frequently accessed data
- Nginx gzip compression enabled
- Docker layer caching for faster builds
- Resource limits to prevent memory leaks
- Health checks for automatic container recovery

## Support

For issues or questions:

1. Check logs: `make logs`
2. Verify health: `make health`
3. Review environment variables in .env
4. Consult main README.md for application-specific details
