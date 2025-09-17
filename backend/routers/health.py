"""
Health and system monitoring endpoints
"""

from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import Response

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


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    active_requests = get_active_ai_requests()

    metrics_data = f"""# HELP ai_requests_active Current number of active AI requests
# TYPE ai_requests_active gauge
ai_requests_active {active_requests}

# HELP schemas_total Total number of loaded schemas
# TYPE schemas_total counter
schemas_total 0

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{{le="0.1"}} 0
http_request_duration_seconds_bucket{{le="0.5"}} 0
http_request_duration_seconds_bucket{{le="1.0"}} 0
http_request_duration_seconds_bucket{{le="2.5"}} 0
http_request_duration_seconds_bucket{{le="5.0"}} 0
http_request_duration_seconds_bucket{{le="10.0"}} 0
http_request_duration_seconds_bucket{{le="+Inf"}} 0
http_request_duration_seconds_count 0
http_request_duration_seconds_sum 0
"""

    return Response(content=metrics_data, media_type="text/plain")