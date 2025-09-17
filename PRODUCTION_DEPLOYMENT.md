# Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the AI Data Extractor for internal production use with enterprise-grade security, monitoring, and performance optimizations.

## Production Features Implemented

### Security

- ✅ File validation with MIME type checking
- ✅ Input sanitization to prevent injection attacks
- ✅ Rate limiting (100 requests/min, burst of 10)
- ✅ API key authentication
- ✅ Security headers (XSS, CSRF, clickjacking protection)
- ✅ Non-root Docker containers
- ✅ File size restrictions (10MB default)
- ✅ Suspicious filename detection

### Performance

- ✅ Request caching with Redis
- ✅ Image optimization and resizing
- ✅ Concurrent request limiting
- ✅ Gzip compression
- ✅ Connection pooling
- ✅ Async request handling
- ✅ PDF DPI optimization

### Monitoring & Observability

- ✅ Structured logging with request IDs
- ✅ Health check endpoints
- ✅ Request/response timing
- ✅ Error tracking with context
- ✅ Performance metrics

### Error Handling

- ✅ Comprehensive validation messages
- ✅ Retry logic with exponential backoff
- ✅ Graceful degradation
- ✅ User-friendly error messages
- ✅ Request cancellation support

## File Structure

```
ai-doc-extractor/
├── backend/
│   ├── main.py                # Production-ready backend
│   ├── config.py               # Configuration management
│   ├── middleware.py           # Security & monitoring middleware
│   ├── validators.py          # Input validation & sanitization
│   ├── Dockerfile.production  # Optimized Docker image
│   └── requirements.txt       # Production dependencies
├── frontend/
│   └── src/components/document-upload/
│       └── document-upload-production.tsx  # Enhanced upload component
├── docker-compose.yml
└── .env.production.template  # Environment template
```

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- API keys for AI services (Groq/Mistral)
- Internal network access

### 2. Configuration

```bash
# Copy environment template
cp .env.production.template .env.production

# Edit configuration
nano .env.production
```

Required environment variables:

```env
GROQ_API_KEY=your-key
MISTRAL_API_KEY=your-key
API_KEYS=secure-api-key-1,secure-api-key-2
REDIS_PASSWORD=strong-password
```

### 3. Build and Deploy

#### Using Makefile (Recommended)

```bash
# Quick start: setup environment and start services
make quickstart

# Or step by step:
# Set up environment
make env-setup

# Build all services
make build

# Start development environment
make dev

# Check health of all services
make health

# View logs
make logs-backend
```

#### Manual Docker Compose

```bash
# Build production images
docker-compose build

# Start services
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

## Security Best Practices

### 1. API Key Management

Generate strong API keys:

```python
import secrets
api_key = secrets.token_urlsafe(32)
print(f"API_KEYS={api_key}")
```

### 2. File Upload Security

- Maximum file size: 10MB (configurable)
- Allowed types: PDF, JPEG, PNG
- MIME type validation
- Magic byte verification
- Filename sanitization

### 3. Rate Limiting

Default limits:

- API endpoints: 100 req/min
- Burst allowance: 10 requests

Rate limiting is handled by the application middleware.

### 4. Network Security

- Implement firewall rules for internal network
- Restrict access to internal services only
- Use private networks for deployment

## Performance Optimization

### 1. Caching Strategy

Redis caching is configured for:

- API responses (5 min TTL)
- Processed documents (1 hour TTL)
- Schema definitions (24 hour TTL)

### 2. Image Processing

- Auto-resize large images (max 4096px)
- JPEG compression (quality 95)
- PDF rendering at 200 DPI

### 3. Concurrent Limits

- Max concurrent AI requests: 10
- Worker processes: 4 (production)
- Connection pool size: 32

## Monitoring

### 1. Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Full system health
docker-compose ps
```

### 2. Logging

Logs are stored in:

- Backend: `/app/logs/app.log`
- Docker: `docker-compose logs [service]`

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
backend:
  deploy:
    replicas: 3
```

### Database Integration

For production scale, integrate PostgreSQL:

```python
DATABASE_URL=postgresql://user:pass@db:5432/aiextractor
```

## Troubleshooting

### Common Issues

1. **File upload fails with size limit**

   - Adjust `MAX_FILE_SIZE_MB` in environment variables
   - Check application configuration

2. **AI requests timeout**

   - Check AI service API limits
   - Adjust timeout settings in configuration

3. **Rate limit errors**

   - Check middleware rate limiting settings
   - Implement request queuing if needed

4. **Memory issues**
   - Adjust Docker memory limits
   - Enable swap for containers

### Debug Mode

Enable debug logging:

```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

## Backup & Recovery

### Data Backup

```bash
# Backup Redis data
docker exec redis redis-cli --rdb /backup/dump.rdb

# Backup logs
tar -czf logs-$(date +%Y%m%d).tar.gz /var/log/ai-doc-extractor/
```

### Disaster Recovery

1. Keep configuration in version control
2. Backup API keys securely
3. Document dependencies
4. Test restore procedures

## Compliance & Auditing

### GDPR Compliance

- No permanent file storage
- Request/response logging excludes PII
- Data deletion on processing completion
- User consent for data processing

### Audit Logging

All requests are logged with:

- Request ID
- Timestamp
- User IP (hashed)
- Action performed
- Response status

## Maintenance

### Rolling Updates

```bash
# Update backend without downtime
docker-compose up -d --no-deps --build backend

# Verify health
curl http://localhost:8000/health
```

### Security Updates

```bash
# Update dependencies
pip list --outdated
pip install --upgrade -r requirements.txt

# Rebuild containers
docker-compose build --no-cache
```

## Support

For production issues:

1. Check health endpoints
2. Review logs with request ID
3. Test with minimal payload

## License

[Your License Here]
