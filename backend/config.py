"""
Production configuration and settings for AI Document Extractor
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class SecurityConfig(BaseModel):
    """Security configuration settings"""
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    allowed_file_types: List[str] = Field(
        default=["application/pdf", "image/jpeg", "image/png", "image/tiff", "image/bmp"],
        description="Allowed MIME types for upload"
    )
    allowed_extensions: List[str] = Field(
        default=["pdf", "jpg", "jpeg", "png", "tiff", "bmp"],
        description="Allowed file extensions"
    )
    rate_limit_requests: int = Field(default=100, description="Max requests per minute")
    rate_limit_burst: int = Field(default=10, description="Burst limit for rate limiting")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    api_key_header: str = Field(default="X-API-Key", description="Header for API key")
    enable_api_key_auth: bool = Field(default=False, description="Enable API key authentication")

class PerformanceConfig(BaseModel):
    """Performance optimization settings"""
    max_image_dimension: int = Field(default=4096, description="Maximum image dimension (width/height)")
    image_compression_quality: int = Field(default=95, description="JPEG compression quality (1-100)")
    pdf_dpi: int = Field(default=200, description="DPI for PDF to image conversion")
    response_timeout: int = Field(default=60, description="API response timeout in seconds")
    max_concurrent_requests: int = Field(default=10, description="Maximum concurrent AI requests")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    enable_response_caching: bool = Field(default=True, description="Enable response caching")

class LoggingConfig(BaseModel):
    """Logging configuration"""
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        description="Log format string"
    )
    log_file: Optional[str] = Field(default=None, description="Log file path")
    enable_request_logging: bool = Field(default=True, description="Enable request/response logging")
    enable_performance_logging: bool = Field(default=True, description="Enable performance metrics logging")

class MonitoringConfig(BaseModel):
    """Monitoring and observability settings"""
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Port for metrics endpoint")
    enable_health_checks: bool = Field(default=True, description="Enable health check endpoints")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")
    tracing_sample_rate: float = Field(default=0.1, description="Tracing sample rate (0.0-1.0)")

class AIConfig(BaseModel):
    """AI model configuration"""
    default_provider: str = Field(default="groq", description="Default AI provider")
    default_model: str = Field(
        default="meta-llama/llama-4-scout-17b-16e-instruct",
        description="Default AI model"
    )
    temperature: float = Field(default=0.1, description="AI model temperature")
    max_retries: int = Field(default=3, description="Maximum retries for AI calls")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    request_timeout: int = Field(default=30, description="AI request timeout in seconds")

class Settings(BaseModel):
    """Main application settings"""
    app_name: str = Field(default="AI Document Data Extractor", description="Application name")
    app_version: str = Field(default="3.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development/staging/production)")
    debug: bool = Field(default=False, description="Debug mode")

    security: SecurityConfig = Field(default_factory=SecurityConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    ai: AIConfig = Field(default_factory=AIConfig)

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables"""
        environment = os.getenv("ENVIRONMENT", "development")

        settings = cls(
            environment=environment,
            debug=environment == "development"
        )

        # Override with environment variables if present
        if os.getenv("MAX_FILE_SIZE_MB"):
            settings.security.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB"))

        if os.getenv("RATE_LIMIT_REQUESTS"):
            settings.security.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS"))

        if os.getenv("LOG_LEVEL"):
            settings.logging.log_level = os.getenv("LOG_LEVEL")

        if os.getenv("ENABLE_API_KEY_AUTH"):
            settings.security.enable_api_key_auth = os.getenv("ENABLE_API_KEY_AUTH").lower() == "true"

        # Production optimizations
        if environment == "production":
            settings.debug = False
            settings.logging.log_level = "WARNING"
            settings.security.enable_api_key_auth = True
            settings.monitoring.enable_metrics = True
            settings.monitoring.enable_tracing = True
            settings.performance.enable_response_caching = True

        return settings

# Global settings instance
settings = Settings.from_env()