"""
FastAPI backend for AI Data Extractor
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Import configuration and middleware
from config import settings
from middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    CacheMiddleware,
    ErrorHandlingMiddleware,
    APIKeyMiddleware
)

# Import routers
from routers.health import router as health_router
from routers.models import router as models_router
from routers.schemas import router as schemas_router, load_default_schemas
from routers.documents import router as documents_router
from routers.extraction import router as extraction_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.logging.log_level.upper()),
    format=settings.logging.log_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.logging.log_file) if settings.logging.log_file else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Verify AI service imports
    try:
        import litellm
        logger.info("LiteLLM initialized successfully")
        litellm.enable_json_schema_validation = True
    except ImportError:
        logger.error("LiteLLM is required. Install with: pip install litellm")
        raise

    # Verify API keys are configured
    import os
    if not os.getenv("GROQ_API_KEY"):
        logger.warning("GROQ_API_KEY not configured")
    if not os.getenv("MISTRAL_API_KEY"):
        logger.warning("MISTRAL_API_KEY not configured")

    # Initialize database service
    from services.database import db_service
    logger.info(f"Database initialized at {db_service.db_path}")

    # Load default schemas
    load_default_schemas()

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered document data extraction service",
    lifespan=lifespan
)

# Add middleware stack (order matters - first added is innermost)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(ErrorHandlingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security and performance middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CacheMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.security.rate_limit_requests)

# API key middleware for protected endpoints
app.add_middleware(APIKeyMiddleware)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(models_router, tags=["Models"])
app.include_router(schemas_router, tags=["Schemas"])
app.include_router(documents_router, tags=["Documents"])
app.include_router(extraction_router, tags=["Extraction"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.logging.log_level.lower()
    )