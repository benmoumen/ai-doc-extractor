"""
Production middleware for security, performance, and monitoring
"""

import time
import hashlib
import json
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse"""

    def __init__(self, app: ASGIApp, requests_per_minute: int = 100, burst: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.requests: Dict[str, list] = defaultdict(list)

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit and process request"""
        client_ip = self.get_client_ip(request)
        now = time.time()

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > now - 60  # Keep only last minute
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed"
                },
                headers={"Retry-After": "60"}
            )

        # Check burst limit
        recent_requests = [
            req_time for req_time in self.requests[client_ip]
            if req_time > now - 1  # Last second
        ]
        if len(recent_requests) >= self.burst:
            logger.warning(f"Burst limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Burst limit exceeded",
                    "message": f"Maximum {self.burst} requests per second allowed"
                },
                headers={"Retry-After": "1"}
            )

        # Record request
        self.requests[client_ip].append(now)

        # Process request
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

        # HSTS for production
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log requests and responses for monitoring"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()

        # Generate request ID
        request_id = hashlib.md5(
            f"{time.time()}{request.client.host if request.client else ''}".encode()
        ).hexdigest()[:8]

        # Store request ID in state
        request.state.request_id = request_id

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"[{request_id}] {response.status_code} "
                f"in {duration:.3f}s"
            )

            # Add timing header
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}"

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] Request failed after {duration:.3f}s: {str(e)}",
                exc_info=True
            )
            raise


class CompressionMiddleware(BaseHTTPMiddleware):
    """Compress responses for better performance"""

    def should_compress(self, response: Response) -> bool:
        """Check if response should be compressed"""
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < 1024:  # Don't compress small responses
            return False

        content_type = response.headers.get("content-type", "")
        compressible_types = ["application/json", "text/", "application/xml"]
        return any(ct in content_type for ct in compressible_types)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")

        response = await call_next(request)

        # Skip if client doesn't accept gzip or response shouldn't be compressed
        if "gzip" not in accept_encoding or not self.should_compress(response):
            return response

        # For streaming responses, we can't easily compress
        # In production, use nginx/apache for compression
        return response


class CacheMiddleware(BaseHTTPMiddleware):
    """Simple in-memory cache for GET requests"""

    def __init__(self, app: ASGIApp, ttl_seconds: int = 3600):
        super().__init__(app)
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl_seconds = ttl_seconds

    def get_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        return f"{request.method}:{request.url.path}:{request.url.query}"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)

        # Skip cache for certain paths
        skip_paths = ["/health", "/api/status", "/metrics"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        cache_key = self.get_cache_key(request)
        now = time.time()

        # Check cache
        if cache_key in self.cache:
            cached_response, timestamp = self.cache[cache_key]
            if now - timestamp < self.ttl_seconds:
                logger.debug(f"Cache hit for {cache_key}")
                return JSONResponse(
                    content=cached_response,
                    headers={"X-Cache": "HIT", "X-Cache-Age": str(int(now - timestamp))}
                )

        # Process request
        response = await call_next(request)

        # Cache successful JSON responses
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                # Read response body (this consumes the response)
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                try:
                    # Parse and cache JSON
                    json_content = json.loads(body)
                    self.cache[cache_key] = (json_content, now)

                    # Return new response with cache headers
                    return JSONResponse(
                        content=json_content,
                        headers={"X-Cache": "MISS"}
                    )
                except json.JSONDecodeError:
                    # Return original response if not JSON
                    return Response(content=body, headers=dict(response.headers))

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling with proper logging and response format"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # Let FastAPI handle HTTP exceptions
            raise
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(
                f"[{request_id}] Unhandled exception: {str(e)}",
                exc_info=True
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API key authentication middleware"""

    def __init__(self, app: ASGIApp, api_keys: Optional[list] = None):
        super().__init__(app)
        self.api_keys = set(api_keys) if api_keys else set()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip auth for health check and docs
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Check API key if configured
        if self.api_keys:
            api_key = request.headers.get("X-API-Key")
            if not api_key or api_key not in self.api_keys:
                logger.warning(f"Invalid API key from {request.client.host if request.client else 'unknown'}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Unauthorized",
                        "message": "Invalid or missing API key"
                    }
                )

        return await call_next(request)