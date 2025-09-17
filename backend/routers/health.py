"""
Health and system monitoring endpoints
"""

from datetime import datetime
from fastapi import APIRouter

from config import settings
from services.ai_service import get_active_ai_requests

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    health_status = {
        "status": "healthy",
        "backend_available": True,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment
    }

    # Check AI service availability
    active_requests = get_active_ai_requests()
    if active_requests >= settings.performance.max_concurrent_requests:
        health_status["ai_service"] = "overloaded"
        health_status["status"] = "degraded"
    else:
        health_status["ai_service"] = "available"
        health_status["active_ai_requests"] = active_requests

    return health_status


