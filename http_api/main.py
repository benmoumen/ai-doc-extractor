"""
FastAPI HTTP server for document data extraction
Implements the proven approach from app.py with direct LiteLLM calls
"""

import os
import sys
import time
import base64
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from io import BytesIO

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import fitz  # PyMuPDF

# Add project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from main app modules
from config import get_model_param, PROVIDER_OPTIONS, MODEL_OPTIONS
from utils import extract_and_parse_json, format_schema_aware_response
from schema_utils import create_schema_prompt
from schema_compatibility import get_extraction_configuration, validate_schema_for_extraction
from dynamic_structured_output import (
    create_response_format_for_document,
    validate_extraction_with_schema,
    generate_simplified_prompt,
    get_schema_from_storage
)
from ai_schema_generation.models.sample_document import SampleDocument
from ai_schema_generation.api.main_endpoint import AISchemaGenerationAPI

# Import LiteLLM for direct API calls
try:
    from litellm import completion
except ImportError:
    raise ImportError("LiteLLM is required. Install with: pip install litellm")

# Set up API keys for FastAPI environment
def setup_fastapi_api_keys():
    """Set up API keys for FastAPI environment"""
    import os
    import toml

    # Try to load from environment variables first
    if not os.getenv("GROQ_API_KEY") or not os.getenv("MISTRAL_API_KEY"):
        # Try to read from Streamlit secrets file directly
        try:
            secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.streamlit', 'secrets.toml')
            if os.path.exists(secrets_path):
                secrets = toml.load(secrets_path)

                if not os.getenv("GROQ_API_KEY") and "GROQ_API_KEY" in secrets:
                    os.environ["GROQ_API_KEY"] = secrets["GROQ_API_KEY"]
                    print("✅ Loaded GROQ_API_KEY from Streamlit secrets")

                if not os.getenv("MISTRAL_API_KEY") and "MISTRAL_API_KEY" in secrets:
                    os.environ["MISTRAL_API_KEY"] = secrets["MISTRAL_API_KEY"]
                    print("✅ Loaded MISTRAL_API_KEY from Streamlit secrets")
        except Exception as e:
            print(f"⚠️  Could not load secrets file: {e}")

    # Final check and warnings
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  Warning: GROQ_API_KEY not found. Set GROQ_API_KEY environment variable.")
    if not os.getenv("MISTRAL_API_KEY"):
        print("⚠️  Warning: MISTRAL_API_KEY not found. Set MISTRAL_API_KEY environment variable.")

setup_fastapi_api_keys()

# Initialize FastAPI app
app = FastAPI(
    title="Document Data Extraction API",
    description="HTTP API for extracting structured data from documents using AI",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI Schema Generation API for document upload workflow
ai_api = AISchemaGenerationAPI()
print("✅ AISchemaGenerationAPI initialized successfully")

def image_to_base64(image: Image.Image) -> str:
    """Convert PIL image to base64 string"""
    buffer = BytesIO()
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    image.save(buffer, format="JPEG", quality=95)
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')

def pdf_to_images(pdf_bytes: bytes, page_num: int = 1) -> Image.Image:
    """Convert PDF page to PIL Image"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if page_num > len(doc):
        page_num = 1
    page = doc.load_page(page_num - 1)  # 0-indexed
    pix = page.get_pixmap()
    img_data = pix.tobytes("ppm")
    image = Image.open(BytesIO(img_data))
    doc.close()
    return image

def determine_file_type(filename: str) -> str:
    """Determine file type from filename"""
    extension = filename.lower().split('.')[-1]
    if extension == 'pdf':
        return 'pdf'
    elif extension in ['jpg', 'jpeg', 'png', 'tiff', 'bmp']:
        return 'image'
    else:
        raise ValueError(f"Unsupported file type: {extension}")

def create_default_provider_model():
    """Get default provider and model for extraction"""
    # Use first available provider/model as default
    first_provider_display = next(iter(PROVIDER_OPTIONS.keys()))
    first_provider_id = PROVIDER_OPTIONS[first_provider_display]
    first_model_id = next(iter(MODEL_OPTIONS[first_provider_id].values()))
    return first_provider_id, first_model_id

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "backend_available": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/models")
async def get_supported_models():
    """Get list of supported AI models"""
    models = []
    # PROVIDER_OPTIONS maps display name to provider ID
    # MODEL_OPTIONS maps provider ID to available models
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
        "models": models
    }

@app.get("/api/schemas")
async def get_available_schemas():
    """Get list of available document schemas"""
    try:
        from schema_utils import get_available_document_types
        document_types = get_available_document_types()

        # Format for frontend
        schemas = {}
        for name, schema_id in document_types.items():
            schemas[schema_id] = {
                "id": schema_id,
                "name": name,
                "display_name": name
            }

        return {
            "success": True,
            "schemas": schemas
        }
    except Exception as e:
        print(f"Schema loading error: {e}")
        return {
            "success": True,
            "schemas": {}
        }

@app.get("/api/schemas/{schema_id}")
async def get_schema_details(schema_id: str):
    """Get detailed schema information"""
    try:
        schema = get_schema_from_storage(schema_id)
        if not schema:
            raise HTTPException(status_code=404, detail="Schema not found")

        return {
            "success": True,
            "schema": schema
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extract")
async def extract_data(
    file: UploadFile = File(...),
    schema_id: Optional[str] = Form(None),
    use_ai: bool = Form(True),
    model: Optional[str] = Form(None)
):
    """
    Extract structured data from document using the proven app.py approach
    This is the focused data extraction endpoint that mimics app.py lines 99-227
    """
    try:
        # Read file data
        file_data = await file.read()
        file_type = determine_file_type(file.filename)

        # Convert document to image for processing
        if file_type == 'pdf':
            image = pdf_to_images(file_data, page_num=1)
        else:
            image = Image.open(BytesIO(file_data))

        # Convert image to base64 for API
        image_base64 = image_to_base64(image)

        # Determine provider and model
        if model:
            # Parse model format: "provider_model_id" (e.g., "groq_meta-llama/llama-4-scout-17b-16e-instruct")
            if '_' in model and len(model.split('_', 1)) == 2:
                provider_id, model_id = model.split('_', 1)
            else:
                provider_id, model_id = create_default_provider_model()
        else:
            provider_id, model_id = create_default_provider_model()

        # Get model parameter for LiteLLM
        model_param = get_model_param(provider_id, model_id)

        # Create extraction prompt based on schema selection
        if schema_id:
            # Use schema-aware prompt from app.py approach
            from schema_utils import create_schema_prompt
            prompt = create_schema_prompt(schema_id, schema_id)
            if not prompt:
                # Fallback if schema not found
                prompt = f"""Extract data from this document using schema: {schema_id}.
Return JSON with extracted_data and validation_results sections."""
        else:
            # AI-powered free-form extraction
            prompt = """Extract all text, data, and structure from this document image.
Analyze the document and intelligently organize the information into logical fields.
Return the data as structured JSON with clear field names and values.

Focus on:
- Key-value pairs (labels and their corresponding values)
- Tables and structured data
- Important identifying information
- Dates, amounts, and reference numbers

Format your response as JSON with descriptive field names."""

        # Prepare LiteLLM completion request (following app.py approach)
        completion_kwargs = {
            "model": model_param,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            "temperature": 0.1
        }

        # Add response_format for structured output when using schema (like app.py)
        if schema_id:
            response_format = create_response_format_for_document(schema_id, provider_id)
            if response_format:
                completion_kwargs["response_format"] = response_format

        # Make API call
        start_time = time.time()
        response = completion(**completion_kwargs)
        end_time = time.time()

        processing_time = end_time - start_time

        # Process response
        raw_content = response.choices[0].message.content

        # Parse JSON response
        is_json, parsed_data, formatted_text = extract_and_parse_json(raw_content)

        # Handle schema-aware vs generic extraction differently
        if schema_id and is_json and parsed_data:
            # Schema-aware extraction: expect extracted_data and validation_results
            if 'extracted_data' in parsed_data and 'validation_results' in parsed_data:
                # Use extracted_data as the main structured data
                structured_data = parsed_data['extracted_data']
                validation_results = parsed_data['validation_results']

                # Check validation status
                validation_passed = all(
                    result.get('status') in ['valid', 'warning']
                    for result in validation_results.values()
                    if isinstance(result, dict)
                )

                # Collect validation errors
                validation_errors = [
                    f"{field}: {result.get('message', 'Validation failed')}"
                    for field, result in validation_results.items()
                    if isinstance(result, dict) and result.get('status') in ['invalid', 'missing']
                ]

                # Use formatted schema results
                result_text = format_schema_aware_response(parsed_data)
            else:
                # Fallback to generic handling
                structured_data = parsed_data
                validation_passed = True
                validation_errors = []
                result_text = formatted_text
        else:
            # Generic extraction
            structured_data = parsed_data
            validation_passed = True
            validation_errors = []
            result_text = formatted_text

        return {
            "success": True,
            "extracted_data": {
                "raw_content": raw_content,
                "formatted_text": result_text,
                "structured_data": structured_data if is_json else None,
                "is_structured": is_json
            },
            "validation": {
                "passed": validation_passed,
                "errors": validation_errors
            },
            "metadata": {
                "processing_time": processing_time,
                "file_type": file_type,
                "model_used": f"{provider_id} - {model_id}",
                "extraction_mode": "schema" if schema_id else "ai_freeform",
                "schema_id": schema_id,
                "prompt_used": prompt
            }
        }

    except Exception as e:
        print(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@app.post("/api/documents")
async def upload_document(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    document_type_hint: Optional[str] = Form(None)
):
    """
    Upload document for AI schema generation analysis
    This endpoint uses the existing AI Schema Generation pipeline
    """
    try:
        # Read file data
        file_data = await file.read()

        # Create SampleDocument
        sample_doc = SampleDocument.from_upload(
            filename=file.filename,
            file_data=file_data
        )

        # Use AI Schema API for document analysis
        analysis_result = ai_api.analyze_document(
            file_content=file_data,
            filename=file.filename,
            model=model,
            document_type_hint=document_type_hint
        )

        return {
            "success": True,
            "document_id": sample_doc.id,
            "analysis_id": analysis_result.get("analysis_id"),
            "message": "Document uploaded and analysis started",
            "analysis_result": analysis_result
        }

    except Exception as e:
        print(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/analysis/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """Get analysis results by ID"""
    try:
        results = ai_api.get_analysis_results(analysis_id)
        return {
            "success": True,
            "analysis": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_service_status():
    """Get service status"""
    try:
        status = ai_api.get_service_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "error"
        }

if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting FastAPI HTTP server...")
    print("📡 Focused data extraction API with app.py approach")
    print("🔗 Next.js frontend can connect to: http://localhost:8000")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,  # Use port 8000 to avoid conflicts
        reload=False,
        log_level="info"
    )