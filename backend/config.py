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
    # API key authentication not implemented

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

class MonitoringConfig(BaseModel):
    """Monitoring and observability settings"""
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
    app_name: str = Field(default="AI Data Extractor", description="Application name")
    app_version: str = Field(default="0.0.1", description="Application version")
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
        debug = os.getenv("DEBUG", "false").lower() == "true" if environment != "production" else False

        settings = cls(
            app_name=os.getenv("APP_NAME", "AI Data Extractor"),
            app_version=os.getenv("APP_VERSION", "0.0.1"),
            environment=environment,
            debug=debug
        )

        # Security settings
        if os.getenv("MAX_FILE_SIZE_MB"):
            settings.security.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB"))
        if os.getenv("RATE_LIMIT_REQUESTS"):
            settings.security.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS"))
        # API key auth not implemented
        if os.getenv("CORS_ORIGINS"):
            settings.security.cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS").split(",")]

        # Logging settings
        if os.getenv("LOG_LEVEL"):
            settings.logging.log_level = os.getenv("LOG_LEVEL").upper()
        if os.getenv("LOG_FILE"):
            settings.logging.log_file = os.getenv("LOG_FILE")
        if os.getenv("ENABLE_REQUEST_LOGGING"):
            settings.logging.enable_request_logging = os.getenv("ENABLE_REQUEST_LOGGING").lower() == "true"

        # Performance settings
        if os.getenv("MAX_IMAGE_DIMENSION"):
            settings.performance.max_image_dimension = int(os.getenv("MAX_IMAGE_DIMENSION"))
        if os.getenv("IMAGE_COMPRESSION_QUALITY"):
            settings.performance.image_compression_quality = int(os.getenv("IMAGE_COMPRESSION_QUALITY"))
        if os.getenv("PDF_DPI"):
            settings.performance.pdf_dpi = int(os.getenv("PDF_DPI"))
        if os.getenv("RESPONSE_TIMEOUT"):
            settings.performance.response_timeout = int(os.getenv("RESPONSE_TIMEOUT"))
        if os.getenv("MAX_CONCURRENT_REQUESTS"):
            settings.performance.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS"))
        if os.getenv("CACHE_TTL_SECONDS"):
            settings.performance.cache_ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS"))
        if os.getenv("ENABLE_RESPONSE_CACHING"):
            settings.performance.enable_response_caching = os.getenv("ENABLE_RESPONSE_CACHING").lower() == "true"

        # AI settings
        if os.getenv("DEFAULT_AI_PROVIDER"):
            settings.ai.default_provider = os.getenv("DEFAULT_AI_PROVIDER")
        if os.getenv("DEFAULT_AI_MODEL"):
            settings.ai.default_model = os.getenv("DEFAULT_AI_MODEL")
        if os.getenv("AI_TEMPERATURE"):
            settings.ai.temperature = float(os.getenv("AI_TEMPERATURE"))
        if os.getenv("AI_MAX_RETRIES"):
            settings.ai.max_retries = int(os.getenv("AI_MAX_RETRIES"))
        if os.getenv("AI_RETRY_DELAY"):
            settings.ai.retry_delay = float(os.getenv("AI_RETRY_DELAY"))
        if os.getenv("AI_REQUEST_TIMEOUT"):
            settings.ai.request_timeout = int(os.getenv("AI_REQUEST_TIMEOUT"))

        # Monitoring settings
        if os.getenv("ENABLE_HEALTH_CHECKS"):
            settings.monitoring.enable_health_checks = os.getenv("ENABLE_HEALTH_CHECKS").lower() == "true"
        if os.getenv("ENABLE_TRACING"):
            settings.monitoring.enable_tracing = os.getenv("ENABLE_TRACING").lower() == "true"
        if os.getenv("TRACING_SAMPLE_RATE"):
            settings.monitoring.tracing_sample_rate = float(os.getenv("TRACING_SAMPLE_RATE"))

        # Production optimizations
        if environment == "production":
            settings.debug = False
            settings.logging.log_level = os.getenv("LOG_LEVEL", "WARNING")
            settings.performance.enable_response_caching = True

        return settings

# Global settings instance
settings = Settings.from_env()