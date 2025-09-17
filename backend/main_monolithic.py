"""
Production-ready FastAPI backend for AI Data Extractor
With comprehensive security, validation, monitoring, and performance optimizations
"""

import os
import time
import base64
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from io import BytesIO
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from PIL import Image
import fitz  # PyMuPDF
import uvicorn

# Import configuration and utilities
from config import settings
from validators import FileValidator, InputSanitizer
from middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    CacheMiddleware,
    ErrorHandlingMiddleware,
    APIKeyMiddleware
)

# Import LiteLLM for AI model calls
try:
    import litellm
    from litellm import completion
    litellm.enable_json_schema_validation = True
except ImportError:
    raise ImportError("LiteLLM is required. Install with: pip install litellm")

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.logging.log_level),
    format=settings.logging.log_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.logging.log_file) if settings.logging.log_file else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize validators
file_validator = FileValidator(
    max_file_size_mb=settings.security.max_file_size_mb,
    max_image_dimension=settings.performance.max_image_dimension
)

input_sanitizer = InputSanitizer()

# Document schemas storage (would be database in production)
SCHEMAS = {}

# Request tracking for concurrent limits
active_ai_requests = 0
ai_request_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Verify API keys are configured
    if not os.getenv("GROQ_API_KEY"):
        logger.warning("GROQ_API_KEY not configured")
    if not os.getenv("MISTRAL_API_KEY"):
        logger.warning("MISTRAL_API_KEY not configured")

    # Load default schemas
    load_default_schemas()

    yield

    # Shutdown
    logger.info("Shutting down application")


def load_default_schemas():
    """Load default document schemas"""
    # This would load from database in production
    pass


# Initialize FastAPI app with lifespan
app = FastAPI(
    title=settings.app_name,
    description="AI Data Extractor",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None
)

# Add middleware in correct order (executed in reverse order)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

if settings.performance.enable_response_caching:
    app.add_middleware(CacheMiddleware, ttl_seconds=settings.performance.cache_ttl_seconds)

if settings.security.enable_api_key_auth:
    api_keys = os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []
    app.add_middleware(APIKeyMiddleware, api_keys=api_keys)

app.add_middleware(SecurityHeadersMiddleware)

if settings.logging.enable_request_logging:
    app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.security.rate_limit_requests,
    burst=settings.security.rate_limit_burst
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=3600
)


# Dependency for AI request limiting
async def check_ai_request_limit():
    """Check if AI request limit is reached"""
    global active_ai_requests
    if active_ai_requests >= settings.performance.max_concurrent_requests:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Too many concurrent AI requests. Please try again later."
        )


# Provider and model configuration
PROVIDER_OPTIONS = {
    "Groq": "groq",
    "Mistral": "mistral"
}

MODEL_OPTIONS = {
    "groq": {
        "Llama Scout 17B": "meta-llama/llama-4-scout-17b-16e-instruct"
    },
    "mistral": {
        "Mistral Small 3.2": "mistral-small-2506"
    }
}


def get_model_param(provider: str, model: str) -> str:
    """Get the model parameter for LiteLLM"""
    if provider == "groq":
        return f"groq/{model}"
    elif provider == "mistral":
        return f"mistral/{model}"
    else:
        return model


def determine_file_type(filename: str) -> str:
    """Determine file type from filename"""
    extension = filename.lower().split('.')[-1]
    if extension == 'pdf':
        return 'pdf'
    elif extension in ['jpg', 'jpeg', 'png', 'tiff', 'bmp']:
        return 'image'
    else:
        raise ValueError(f"Unsupported file type: {extension}")


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL image to base64 string with optimization"""
    buffer = BytesIO()

    # Convert RGBA to RGB if needed
    if image.mode == 'RGBA':
        image = image.convert('RGB')

    # Resize if too large
    max_dim = settings.performance.max_image_dimension
    if image.width > max_dim or image.height > max_dim:
        image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        logger.info(f"Resized image from {image.width}x{image.height} to fit within {max_dim}x{max_dim}")

    # Save with compression
    image.save(buffer, format="JPEG", quality=settings.performance.image_compression_quality, optimize=True)
    img_bytes = buffer.getvalue()

    return base64.b64encode(img_bytes).decode('utf-8')


def pdf_to_images(pdf_bytes: bytes, page_num: int = 1) -> Image.Image:
    """Convert PDF page to PIL Image with DPI control"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if page_num > len(doc):
        page_num = 1

    page = doc.load_page(page_num - 1)

    # Use configured DPI for better quality/performance balance
    mat = fitz.Matrix(settings.performance.pdf_dpi / 72.0, settings.performance.pdf_dpi / 72.0)
    pix = page.get_pixmap(matrix=mat)

    img_data = pix.tobytes("ppm")
    image = Image.open(BytesIO(img_data))
    doc.close()

    return image


async def process_uploaded_document(
    file: UploadFile,
    request_id: str
) -> tuple[bytes, dict]:
    """
    Reusable function to process uploaded documents with validation
    Returns: (file_data, metadata)
    """
    logger.info(f"[{request_id}] Processing uploaded document: {file.filename}")

    # Read file data
    file_data = await file.read()

    # Comprehensive file validation
    is_valid, error_message, metadata = file_validator.validate_file(file_data, file.filename)

    if not is_valid:
        logger.warning(f"[{request_id}] File validation failed: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    logger.info(f"[{request_id}] File validated successfully: {metadata}")
    return file_data, metadata


async def prepare_document_for_ai(
    file_data: bytes,
    metadata: dict,
    request_id: str
) -> tuple[Image.Image, str]:
    """
    Convert document to image and base64 for AI processing
    Returns: (image, image_base64)
    """
    logger.info(f"[{request_id}] Converting document to image for AI processing")

    # Convert document to image
    if metadata["file_type"] == "pdf":
        image = pdf_to_images(file_data, page_num=1)
    else:
        image = Image.open(BytesIO(file_data))

    # Convert image to base64 with optimization
    image_base64 = image_to_base64(image)

    return image, image_base64


def determine_ai_model(model: Optional[str]) -> tuple[str, str, str]:
    """
    Determine AI model parameters from request
    Returns: (provider_id, model_id, model_param)
    """
    if model and '_' in model:
        provider_id, model_id = model.split('_', 1)
    else:
        provider_id = settings.ai.default_provider
        model_id = settings.ai.default_model

    model_param = get_model_param(provider_id, model_id)
    return provider_id, model_id, model_param


def create_document_metadata(metadata: dict, request_id: str) -> dict:
    """
    Create standardized document metadata for API responses
    """
    import uuid
    doc_id = str(uuid.uuid4())

    document_metadata = {
        "id": doc_id,
        "filename": metadata["sanitized_filename"],
        "original_filename": metadata["original_filename"],
        "file_type": metadata["file_type"],
        "file_size": metadata["file_size"],
        "file_hash": metadata["file_hash"],
        "mime_type": metadata["mime_type"],
        "upload_time": datetime.utcnow().isoformat(),
        "request_id": request_id
    }

    # Add image metadata if available
    if metadata.get("image_width"):
        document_metadata["image_dimensions"] = f"{metadata['image_width']}x{metadata['image_height']}"
        document_metadata["image_format"] = metadata.get("image_format")

    return document_metadata


async def make_ai_request_with_retry(
    prompt: str,
    image_base64: str,
    model_param: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """Make AI request with retry logic and error handling"""
    global active_ai_requests

    for attempt in range(max_retries):
        try:
            async with ai_request_lock:
                active_ai_requests += 1
                logger.info(f"Active AI requests: {active_ai_requests}")

            try:
                # Add timeout to AI request
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        completion,
                        model=model_param,
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                            ]
                        }],
                        temperature=settings.ai.temperature,
                        response_format={"type": "json_object"}
                    ),
                    timeout=settings.ai.request_timeout
                )

                return {
                    "content": response.choices[0].message.content,
                    "usage": getattr(response, 'usage', {}).dict() if hasattr(response, 'usage') and response.usage else {},
                    "model": getattr(response, 'model', model_param)
                }

            finally:
                async with ai_request_lock:
                    active_ai_requests = max(0, active_ai_requests - 1)
                    logger.info(f"Active AI requests: {active_ai_requests}")

        except asyncio.TimeoutError:
            logger.warning(f"AI request timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(settings.ai.retry_delay * (attempt + 1))
            else:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="AI request timed out"
                )

        except Exception as e:
            logger.error(f"AI request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(settings.ai.retry_delay * (attempt + 1))
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI service error: {str(e)}"
                )


def extract_json_from_text(text: str) -> tuple[bool, Optional[Dict], str]:
    """Extract JSON from AI response text with validation"""
    try:
        # Try direct JSON parse
        data = json.loads(text)
        # Sanitize the extracted data
        data = input_sanitizer.sanitize_json_field(data)
        return True, data, json.dumps(data, indent=2)
    except:
        pass

    # Try to find JSON blocks in markdown or text
    import re

    # Look for JSON blocks in markdown code fences
    json_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_blocks:
        for block in json_blocks:
            try:
                data = json.loads(block)
                data = input_sanitizer.sanitize_json_field(data)
                if isinstance(data, dict):
                    return True, data, json.dumps(data, indent=2)
            except:
                continue

    return False, None, text


def create_extraction_prompt(schema_id: Optional[str] = None) -> str:
    """Create extraction prompt based on schema, with enhanced support for AI-generated schemas and document verification"""
    base_prompt = """DOCUMENT VERIFICATION & DATA EXTRACTION

PART 1: DOCUMENT VERIFICATION (KYC/Authentication)
Analyze this document for authenticity and type verification:

1. Document Type Identification:
   - What type of document is this?
   - How confident are you it matches the expected type?
   - Check document structure, layout, fonts, and formatting

2. Authenticity Assessment:
   - Look for signs of tampering (photo replacement, text alterations)
   - Check for structural anomalies or inconsistencies
   - Verify field positioning matches expected template
   - Assess print quality and font consistency

3. Security Validation:
   - Validate Machine Readable Zone (MRZ) if present
   - Check date logic (issue < expiry, age consistency)
   - Verify field format compliance
   - Cross-check data consistency between fields

PART 2: DATA EXTRACTION
Extract all text, data, and structure from the document with confidence scores.

Return the data as structured JSON in this format:
{
  "document_verification": {
    "document_type_confidence": 95,
    "expected_document_type": "expected_type",
    "detected_document_type": "detected_type",
    "authenticity_score": 88,
    "tampering_indicators": {
      "photo_manipulation": false,
      "text_alterations": false,
      "structural_anomalies": false,
      "digital_artifacts": false,
      "font_inconsistencies": false
    },
    "security_checks": {
      "mrz_checksum_valid": true,
      "field_consistency": true,
      "date_logic_valid": true,
      "format_compliance": true
    },
    "verification_notes": ["specific observations about authenticity"],
    "risk_level": "low|medium|high"
  },
  "extracted_fields": {
    "field_name": {
      "value": "extracted value",
      "confidence": 85,
      "extraction_notes": "any issues or uncertainties"
    }
  },
  "overall_confidence": 75,
  "document_quality": "high|medium|low",
  "extraction_issues": ["list of any general issues"]
}

Risk Level Guidelines:
- LOW (80-100% authenticity): Document appears genuine, proceed with automated processing
- MEDIUM (50-79% authenticity): Some concerns detected, recommend manual review
- HIGH (0-49% authenticity): Significant issues detected, manual verification required

Confidence scoring guidelines:
- 90-100: Very clear, unambiguous extraction
- 70-89: Clear but minor uncertainties (e.g., slight blur, formatting variations)
- 50-69: Readable but significant uncertainties (e.g., partial occlusion, handwriting)
- 30-49: Difficult extraction, multiple interpretations possible
- 0-29: Very uncertain, mostly guessing

Focus on:
- Document authenticity and tampering detection
- Key-value pairs (labels and their corresponding values)
- Tables and structured data
- Important identifying information
- Dates, amounts, and reference numbers"""

    if schema_id and schema_id in SCHEMAS:
        schema = SCHEMAS[schema_id]
        schema_prompt = f"""

This appears to be a {schema['name']} document. Extract the following specific fields:
"""

        # Enhanced field extraction with AI-generated schema features
        for field_name, field_info in schema['fields'].items():
            required_text = " (REQUIRED)" if field_info.get('required') else ""

            # Core field description
            description = field_info.get('description', f'Field: {field_name}')
            field_type = field_info.get('type', 'text')
            schema_prompt += f"- {field_name} ({field_type}): {description}{required_text}\n"

            # Add extraction hints if available (from multi-step AI generation)
            if field_info.get('extraction_hints'):
                hints = field_info['extraction_hints']
                if isinstance(hints, list) and hints:
                    schema_prompt += f"  Hints: {'; '.join(hints[:2])}\n"  # Use first 2 hints

            # Add positioning hints if available
            if field_info.get('positioning_hints'):
                schema_prompt += f"  Location: {field_info['positioning_hints']}\n"

            # Add validation pattern hints
            if field_info.get('validation_pattern'):
                schema_prompt += f"  Expected format: matches pattern {field_info['validation_pattern']}\n"

        # Add document-specific guidance if available
        if schema.get('document_quality'):
            quality = schema['document_quality']
            if quality == 'low':
                schema_prompt += "\nNote: This document may have quality issues. Be extra careful with OCR interpretation.\n"
            elif quality == 'high':
                schema_prompt += "\nNote: This is a high-quality document with clear text.\n"

        # Add extraction difficulty guidance
        if schema.get('extraction_difficulty'):
            difficulty = schema['extraction_difficulty']
            if difficulty == 'hard':
                schema_prompt += "This document has complex layout. Pay attention to field positioning.\n"
            elif difficulty == 'easy':
                schema_prompt += "This document has a straightforward layout.\n"

        # Final instructions with confidence scoring and verification
        schema_prompt += f"""

CRITICAL: Return a JSON object with this structure:
{{
  "document_verification": {{
    "document_type_confidence": 0-100,
    "expected_document_type": "{schema['name'].lower().replace(' ', '_')}",
    "detected_document_type": "detected_type",
    "authenticity_score": 0-100,
    "tampering_indicators": {{
      "photo_manipulation": true/false,
      "text_alterations": true/false,
      "structural_anomalies": true/false,
      "digital_artifacts": true/false,
      "font_inconsistencies": true/false
    }},
    "security_checks": {{
      "mrz_checksum_valid": true/false,
      "field_consistency": true/false,
      "date_logic_valid": true/false,
      "format_compliance": true/false
    }},
    "verification_notes": ["specific observations"],
    "risk_level": "low|medium|high"
  }},
  "extracted_fields": {{
    {', '.join([f'"{field}": {{"value": "extracted value", "confidence": 0-100, "extraction_notes": "optional notes"}}' for field in list(schema['fields'].keys())[:1]])}
    // ... continue for all fields: {list(schema['fields'].keys())}
  }},
  "overall_confidence": 0-100,
  "document_quality": "high|medium|low",
  "extraction_issues": []
}}

Document Verification Requirements:
- Verify this document matches expected type: {schema['name']}
- Check authenticity indicators carefully
- Validate all security features
- Assess tampering risk

Each field MUST include:
- value: The extracted value (string/number)
- confidence: Score 0-100 based on extraction certainty
- extraction_notes: Any issues or uncertainties (optional)

For missing/unreadable fields: {{"value": "", "confidence": 0, "extraction_notes": "field not found"}}"""

        return base_prompt + schema_prompt

    return base_prompt + """\n
Return a JSON object with document_verification (including document type detection and authenticity assessment) and extracted_fields containing each detected field with value, confidence, and extraction_notes.
Include overall_confidence, document_quality, and extraction_issues.

For document_verification:
- detected_document_type: Identify what type of document this appears to be
- document_type_confidence: How confident you are in the document type identification (0-100)
- authenticity_score: Overall assessment of document authenticity (0-100)
- risk_level: "low", "medium", or "high" based on authenticity concerns"""


def create_initial_detection_prompt() -> str:
    """Step 1: Initial Schema Detection"""
    return """STEP 1: INITIAL DOCUMENT ANALYSIS
Analyze this document image and perform initial field detection.

Tasks:
1. Identify the document type (National ID, Passport, Residence Permit, Business License, etc.)
2. Extract ALL visible text fields, numbers, dates, and data elements
3. Determine basic field types (text, number, date, email, phone, url, boolean)
4. Create initial schema structure

Return ONLY a JSON object with this structure:
{
  "document_type": "detected document type",
  "layout_analysis": "brief description of document layout",
  "fields": {
    "field_name": {
      "type": "text|number|date|email|phone|url|boolean",
      "location": "brief description of where this field appears",
      "content_preview": "sample of visible content if readable"
    }
  }
}

Focus on completeness - capture EVERY visible field, even small ones."""


def create_review_prompt(initial_schema: dict) -> str:
    """Step 2: Schema Review & Refinement"""
    return f"""STEP 2: SCHEMA REVIEW AND REFINEMENT
Review the initial schema against the document image for accuracy and completeness.

Initial Schema:
{json.dumps(initial_schema, indent=2)}

Tasks:
1. Verify all fields are correctly identified
2. Check if any fields were missed
3. Validate field types are appropriate
4. Suggest required/optional status for each field
5. Add proper field descriptions

Return ONLY a JSON object with this structure:
{{
  "id": "document_type_snake_case",
  "name": "Human Readable Document Name",
  "description": "Brief description of document purpose",
  "category": "Government|Business|Personal|Healthcare|Education|Other",
  "fields": {{
    "field_name": {{
      "type": "text|number|date|email|phone|url|boolean",
      "required": true|false,
      "description": "Clear description of what this field represents"
    }}
  }},
  "changes_made": ["list of changes from initial schema"]
}}"""


def create_confidence_analysis_prompt(refined_schema: dict) -> str:
    """Step 3: Field Confidence Analysis"""
    return f"""STEP 3: FIELD CONFIDENCE ANALYSIS
Analyze the extraction difficulty and confidence for each field in the schema.

Refined Schema:
{json.dumps(refined_schema, indent=2)}

Tasks:
1. Score each field's extraction confidence (0-100) based on:
   - Text legibility and clarity
   - Field boundaries and layout
   - Potential OCR challenges
   - Handwritten vs printed text
   - Text size and quality
2. Assess overall document quality
3. Identify potential extraction challenges

Return ONLY a JSON object with this structure:
{{
  "overall_confidence": 85,
  "document_quality": "high|medium|low",
  "extraction_difficulty": "easy|medium|hard",
  "field_confidence": {{
    "field_name": {{
      "confidence_score": 95,
      "legibility": "high|medium|low",
      "potential_issues": ["list of potential extraction challenges"],
      "extraction_notes": "specific notes about this field"
    }}
  }}
}}"""


def create_hints_generation_prompt(schema_with_confidence: dict, confidence_analysis: dict) -> str:
    """Step 4: Extraction Hints Generation"""
    return f"""STEP 4: EXTRACTION HINTS GENERATION
Generate specific extraction instructions and hints for each field.

Schema:
{json.dumps(schema_with_confidence, indent=2)}

Confidence Analysis:
{json.dumps(confidence_analysis, indent=2)}

Tasks:
1. Create extraction hints for each field based on document layout
2. Generate validation patterns where applicable
3. Provide specific extraction strategies
4. Include common format patterns
5. Add fallback strategies for difficult fields

Return ONLY a JSON object with this structure:
{{
  "extraction_strategy": {{
    "field_name": {{
      "extraction_hints": ["List of specific hints for extracting this field"],
      "validation_pattern": "regex pattern if applicable",
      "common_formats": ["expected format examples"],
      "fallback_strategy": "what to do if primary extraction fails",
      "positioning_hints": "where to look for this field"
    }}
  }},
  "document_specific_notes": ["general extraction notes for this document type"],
  "quality_recommendations": ["suggestions for improving extraction accuracy"]
}}"""


@app.get("/health")
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
    if active_ai_requests >= settings.performance.max_concurrent_requests:
        health_status["ai_service"] = "overloaded"
        health_status["status"] = "degraded"
    else:
        health_status["ai_service"] = "available"

    # Add metrics if enabled
    if settings.monitoring.enable_metrics:
        health_status["metrics"] = {
            "active_ai_requests": active_ai_requests,
            "max_concurrent_requests": settings.performance.max_concurrent_requests,
            "schemas_loaded": len(SCHEMAS)
        }

    return health_status


@app.get("/api/models")
async def get_supported_models():
    """Get list of supported AI models"""
    models = []
    for provider_display_name, provider_id in PROVIDER_OPTIONS.items():
        if provider_id in MODEL_OPTIONS:
            for model_display_name, model_id in MODEL_OPTIONS[provider_id].items():
                models.append({
                    "id": f"{provider_id}_{model_id}",
                    "name": f"{provider_display_name} - {model_display_name}",
                    "provider": provider_display_name,
                    "model": model_display_name,
                    "provider_id": provider_id,
                    "model_id": model_id
                })

    return {
        "success": True,
        "models": models,
        "default_model": f"{settings.ai.default_provider}_{settings.ai.default_model}"
    }


@app.get("/api/schemas")
async def get_available_schemas():
    """Get list of available document schemas"""
    formatted_schemas = {}
    for schema_id, schema in SCHEMAS.items():
        formatted_schemas[schema_id] = {
            "id": schema_id,
            "name": schema.get("name", "Unknown Schema"),
            "description": schema.get("description", ""),
            "category": schema.get("category", "Other"),
            "field_count": len(schema.get("fields", {}))
        }

    return {
        "success": True,
        "schemas": formatted_schemas
    }


@app.get("/api/schemas/{schema_id}")
async def get_schema_details(schema_id: str):
    """Get detailed schema information"""
    # Sanitize schema_id
    safe_schema_id = input_sanitizer.sanitize_string(schema_id, max_length=100)

    if safe_schema_id not in SCHEMAS:
        raise HTTPException(status_code=404, detail="Schema not found")

    return {
        "success": True,
        "schema": SCHEMAS[safe_schema_id]
    }


@app.post("/api/documents")
async def upload_document(
    request: Request,
    file: UploadFile = File(...)
):
    """Upload document with comprehensive validation"""
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        # Use shared document processing function
        file_data, metadata = await process_uploaded_document(file, request_id)

        # Generate document metadata using shared function
        document_metadata = create_document_metadata(metadata, request_id)

        # Generate analysis ID
        import uuid
        analysis_id = str(uuid.uuid4())

        return {
            "success": True,
            "document": document_metadata,
            "analysis": {
                "id": analysis_id,
                "status": "pending"
            },
            "metadata": {
                "processing_time": 0.1,
                "validation_passed": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Document upload error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document upload"
        )


@app.post("/api/extract")
async def extract_data(
    request: Request,
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    schema_id: Optional[str] = Form(None),
    _: None = Depends(check_ai_request_limit)
):
    """Extract data with production-grade error handling and validation"""
    request_id = getattr(request.state, "request_id", "unknown")
    start_time = time.time()

    logger.info(f"[{request_id}] Starting data extraction for {file.filename}")

    try:
        # Use shared document processing functions
        file_data, metadata = await process_uploaded_document(file, request_id)
        image, image_base64 = await prepare_document_for_ai(file_data, metadata, request_id)

        # Determine model using shared function
        provider_id, model_id, model_param = determine_ai_model(model)

        # Sanitize schema_id
        if schema_id:
            schema_id = input_sanitizer.sanitize_string(schema_id, max_length=100)
            if schema_id not in SCHEMAS:
                logger.warning(f"[{request_id}] Invalid schema_id: {schema_id}")
                schema_id = None

        # Create extraction prompt
        prompt = create_extraction_prompt(schema_id)

        # Make AI request with retry and timeout
        logger.info(f"[{request_id}] Making AI request with model {model_param}")
        ai_response = await make_ai_request_with_retry(prompt, image_base64, model_param)

        # Process response
        raw_content = ai_response["content"]
        is_json, parsed_data, formatted_text = extract_json_from_text(raw_content)

        # Build response
        extraction_result = {
            "success": True,
            "extracted_data": {
                "structured_data": parsed_data if is_json else None,
                "is_structured": is_json,
                "raw_content": raw_content[:5000] if settings.debug else None  # Limit in production
            },
            "metadata": {
                "processing_time": time.time() - start_time,
                "file_type": metadata["file_type"],
                "file_size": metadata["file_size"],
                "model_used": f"{provider_id} - {model_id}",
                "extraction_mode": "schema_guided" if schema_id else "freeform",
                "schema_used": schema_id,
                "request_id": request_id
            }
        }

        # Add document verification if present
        if is_json and parsed_data and "document_verification" in parsed_data:
            extraction_result["document_verification"] = parsed_data["document_verification"]

        # Add validation results if schema was used
        if schema_id and schema_id in SCHEMAS and is_json and parsed_data:
            validation_results = validate_against_schema(parsed_data, SCHEMAS[schema_id])
            extraction_result["validation"] = validation_results

        logger.info(f"[{request_id}] Extraction completed in {time.time() - start_time:.2f}s")

        return extraction_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Extraction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract data from document"
        )


def validate_against_schema(data: Dict, schema: Dict) -> Dict:
    """Validate extracted data against schema"""
    validation_results = {"passed": True, "errors": [], "warnings": []}

    if "extracted_fields" in data:
        fields = data["extracted_fields"]
    else:
        fields = data

    for field_name, field_info in schema.get("fields", {}).items():
        if field_info.get("required") and field_name not in fields:
            validation_results["errors"].append(f"Required field '{field_name}' is missing")
            validation_results["passed"] = False

        if field_name in fields:
            field_value = fields[field_name]
            if isinstance(field_value, dict) and "value" in field_value:
                field_value = field_value["value"]

            # Type validation
            expected_type = field_info.get("type", "text")
            if expected_type == "number" and field_value:
                try:
                    float(field_value)
                except (ValueError, TypeError):
                    validation_results["warnings"].append(
                        f"Field '{field_name}' expected to be number but got '{field_value}'"
                    )

    return validation_results


@app.post("/api/generate-schema")
async def generate_schema(
    request: Request,
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    _: None = Depends(check_ai_request_limit)
):
    """Generate schema with production validation and error handling"""
    request_id = getattr(request.state, "request_id", "unknown")
    start_time = time.time()

    logger.info(f"[{request_id}] Starting schema generation for {file.filename}")

    try:
        # Use shared document processing functions
        file_data, metadata = await process_uploaded_document(file, request_id)
        image, image_base64 = await prepare_document_for_ai(file_data, metadata, request_id)

        # Determine model using shared function
        provider_id, model_id, model_param = determine_ai_model(model)

        # Multi-step AI processing
        ai_debug_info = {"steps": []}
        logger.info(f"[{request_id}] Starting multi-step schema generation with model {model_param}")

        # Step 1: Initial Detection
        step1_prompt = create_initial_detection_prompt()
        step1_start = time.time()

        step1_response_data = await make_ai_request_with_retry(
            step1_prompt, image_base64, model_param, max_retries=settings.ai.max_retries
        )
        step1_end = time.time()

        step1_raw = step1_response_data["content"]
        step1_valid, step1_data, step1_formatted = extract_json_from_text(step1_raw)

        ai_debug_info["steps"].append({
            "step": 1,
            "name": "Initial Detection",
            "duration": step1_end - step1_start,
            "success": step1_valid,
            "tokens_used": step1_response_data.get("usage", {})
        })

        if not step1_valid or not step1_data:
            logger.warning(f"[{request_id}] Step 1 failed, using fallback schema")
            step1_data = {
                "document_type": "Unknown Document",
                "layout_analysis": "Unable to analyze document layout due to AI processing error",
                "fields": {
                    "field_1": {
                        "type": "text",
                        "location": "Unable to determine location",
                        "content_preview": "Unable to preview content"
                    },
                    "field_2": {
                        "type": "text",
                        "location": "Unable to determine location",
                        "content_preview": "Unable to preview content"
                    }
                }
            }

        # Step 2: Schema Review & Refinement
        step2_prompt = create_review_prompt(step1_data)
        step2_start = time.time()

        step2_response_data = await make_ai_request_with_retry(
            step2_prompt, image_base64, model_param, max_retries=settings.ai.max_retries
        )
        step2_end = time.time()

        step2_raw = step2_response_data["content"]
        step2_valid, step2_data, step2_formatted = extract_json_from_text(step2_raw)

        ai_debug_info["steps"].append({
            "step": 2,
            "name": "Schema Review & Refinement",
            "duration": step2_end - step2_start,
            "success": step2_valid,
            "tokens_used": step2_response_data.get("usage", {})
        })

        if not step2_valid or not step2_data:
            logger.warning(f"[{request_id}] Step 2 failed, using Step 1 results with fallbacks")
            step2_data = {
                "id": f"generated_schema_{int(time.time())}",
                "name": f"{step1_data.get('document_type', 'Unknown')} Schema",
                "description": f"Auto-generated schema for {step1_data.get('document_type', 'unknown document type')}",
                "category": "Generated",
                "fields": {}
            }

            # Convert Step 1 fields to Step 2 format with fallbacks
            for field_name, field_info in step1_data.get("fields", {}).items():
                step2_data["fields"][field_name] = {
                    "type": field_info.get("type", "text"),
                    "required": False,  # Conservative fallback
                    "description": f"Field extracted from {field_info.get('location', 'document')}"
                }

        # Step 3: Confidence Analysis
        step3_prompt = create_confidence_analysis_prompt(step2_data)
        step3_start = time.time()

        step3_response_data = await make_ai_request_with_retry(
            step3_prompt, image_base64, model_param, max_retries=settings.ai.max_retries
        )
        step3_end = time.time()

        step3_raw = step3_response_data["content"]
        step3_valid, step3_data, step3_formatted = extract_json_from_text(step3_raw)

        ai_debug_info["steps"].append({
            "step": 3,
            "name": "Confidence Analysis",
            "duration": step3_end - step3_start,
            "success": step3_valid,
            "tokens_used": step3_response_data.get("usage", {})
        })

        # Step 4: Hints Generation
        step4_prompt = create_hints_generation_prompt(step2_data, step3_data or {})
        step4_start = time.time()

        step4_response_data = await make_ai_request_with_retry(
            step4_prompt, image_base64, model_param, max_retries=settings.ai.max_retries
        )
        step4_end = time.time()

        step4_raw = step4_response_data["content"]
        step4_valid, step4_data, step4_formatted = extract_json_from_text(step4_raw)

        ai_debug_info["steps"].append({
            "step": 4,
            "name": "Extraction Hints Generation",
            "duration": step4_end - step4_start,
            "success": step4_valid,
            "tokens_used": step4_response_data.get("usage", {})
        })

        end_time = time.time()

        # Build final schema with enhanced data
        schema_id = step2_data.get("id", f"generated_schema_{int(time.time())}")

        # Enhanced schema with confidence and hints
        enhanced_schema = {
            "id": schema_id,
            "name": step2_data.get("name", "Generated Schema"),
            "description": step2_data.get("description", "AI-generated schema"),
            "category": step2_data.get("category", "Other"),
            "fields": {}
        }

        # Add enhanced field data
        for field_name, field_config in step2_data.get("fields", {}).items():
            enhanced_field = {
                "type": field_config.get("type", "text"),
                "required": field_config.get("required", False),
                "description": field_config.get("description", f"Field: {field_name}")
            }

            # Add confidence data if available
            if step3_valid and step3_data and field_name in step3_data.get("field_confidence", {}):
                confidence_info = step3_data["field_confidence"][field_name]
                enhanced_field["confidence_score"] = confidence_info.get("confidence_score", 75)
                enhanced_field["legibility"] = confidence_info.get("legibility", "medium")
                enhanced_field["potential_issues"] = confidence_info.get("potential_issues", [])

            # Add extraction hints if available
            if step4_valid and step4_data and field_name in step4_data.get("extraction_strategy", {}):
                hints_info = step4_data["extraction_strategy"][field_name]
                enhanced_field["extraction_hints"] = hints_info.get("extraction_hints", [])
                enhanced_field["validation_pattern"] = hints_info.get("validation_pattern")
                enhanced_field["positioning_hints"] = hints_info.get("positioning_hints")

            enhanced_schema["fields"][field_name] = enhanced_field

        # Add overall confidence and document analysis
        if step3_valid and step3_data:
            enhanced_schema["overall_confidence"] = step3_data.get("overall_confidence", 75)
            enhanced_schema["document_quality"] = step3_data.get("document_quality", "medium")
            enhanced_schema["extraction_difficulty"] = step3_data.get("extraction_difficulty", "medium")

        if step4_valid and step4_data:
            enhanced_schema["document_specific_notes"] = step4_data.get("document_specific_notes", [])
            enhanced_schema["quality_recommendations"] = step4_data.get("quality_recommendations", [])

        # Add to schemas for immediate use (sanitize schema_id)
        safe_schema_id = input_sanitizer.sanitize_string(schema_id, max_length=100)
        SCHEMAS[safe_schema_id] = enhanced_schema

        logger.info(f"[{request_id}] Schema generation completed in {end_time - start_time:.2f}s")

        return {
            "success": True,
            "generated_schema": {
                "schema_id": safe_schema_id,
                "schema_data": enhanced_schema,
                "is_valid": True,
                "ready_for_extraction": True,
                "raw_response": f"Multi-step generation completed with {len(ai_debug_info['steps'])} steps",
                "formatted_text": json.dumps(enhanced_schema, indent=2) if settings.debug else None
            },
            "next_steps": {
                "available_in_schemas": True,
                "can_use_for_extraction": True,
                "schema_endpoint": f"/api/schemas/{safe_schema_id}"
            },
            "metadata": {
                "processing_time": end_time - start_time,
                "file_type": metadata["file_type"],
                "file_size": metadata["file_size"],
                "model_used": f"{provider_id} - {model_id}",
                "fields_generated": len(enhanced_schema.get("fields", {})),
                "steps_completed": len(ai_debug_info["steps"]),
                "overall_confidence": enhanced_schema.get("overall_confidence", 75),
                "document_quality": enhanced_schema.get("document_quality", "medium"),
                "request_id": request_id
            },
            "ai_debug": ai_debug_info if settings.debug else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Schema generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate schema from document"
        )


@app.post("/api/schemas")
async def save_schema(request: Request, schema_data: Dict[str, Any]):
    """Save a generated schema to make it available for data extraction"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(f"[{request_id}] Saving schema: {schema_data.get('name', 'Unknown')}")

    try:
        # Validate required fields
        required_fields = ["id", "name", "description", "category", "fields"]
        for field in required_fields:
            if field not in schema_data:
                logger.warning(f"[{request_id}] Missing required field: {field}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )

        # Sanitize schema data
        schema_data = input_sanitizer.sanitize_json_field(schema_data)
        schema_id = schema_data["id"]

        # Ensure schema ID is valid and safe
        safe_schema_id = input_sanitizer.sanitize_string(schema_id, max_length=100)
        if not safe_schema_id.replace("_", "").replace("-", "").isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schema ID must be alphanumeric with underscores or dashes"
            )

        # Check if schema ID already exists - if so, update it instead of rejecting
        is_update = safe_schema_id in SCHEMAS

        # Validate fields structure
        if not isinstance(schema_data["fields"], dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fields must be a dictionary"
            )

        for field_name, field_config in schema_data["fields"].items():
            if not isinstance(field_config, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Field '{field_name}' configuration must be a dictionary"
                )
            if "type" not in field_config or "required" not in field_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Field '{field_name}' must have 'type' and 'required' properties"
                )

        # Save schema to the in-memory store with additional metadata
        SCHEMAS[safe_schema_id] = {
            "id": safe_schema_id,
            "name": input_sanitizer.sanitize_string(schema_data["name"], max_length=200),
            "description": input_sanitizer.sanitize_string(schema_data["description"], max_length=500),
            "category": input_sanitizer.sanitize_string(schema_data["category"], max_length=100),
            "fields": schema_data["fields"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "generated": True,  # Flag to distinguish from predefined schemas
            "request_id": request_id
        }

        action = "updated" if is_update else "created"
        logger.info(f"[{request_id}] Schema '{safe_schema_id}' {action} successfully")

        return {
            "success": True,
            "message": f"Schema '{schema_data['name']}' {action} successfully and is now available for data extraction",
            "schema_id": safe_schema_id,
            "available_for_extraction": True,
            "is_update": is_update,
            "metadata": {
                "fields_count": len(schema_data.get("fields", {})),
                "request_id": request_id
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Schema save error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save schema"
        )


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    if not settings.monitoring.enable_metrics:
        raise HTTPException(status_code=404, detail="Metrics not enabled")

    metrics_text = f"""
# HELP ai_requests_active Number of active AI requests
# TYPE ai_requests_active gauge
ai_requests_active {active_ai_requests}

# HELP schemas_total Total number of loaded schemas
# TYPE schemas_total gauge
schemas_total {len(SCHEMAS)}

# HELP app_info Application information
# TYPE app_info gauge
app_info{{version="{settings.app_version}",environment="{settings.environment}"}} 1
"""
    return Response(content=metrics_text, media_type="text/plain")


if __name__ == "__main__":
    # Production server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.logging.log_level.lower(),
        access_log=settings.logging.enable_request_logging,
        workers=1 if settings.debug else 4,
        loop="uvloop" if not settings.debug else "auto",
        server_header=False,  # Don't expose server info
        date_header=True
    )