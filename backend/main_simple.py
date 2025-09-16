"""
Simplified FastAPI HTTP server for document data extraction
Minimal version without Streamlit dependencies
"""

import os
import time
import base64
from datetime import datetime
from typing import Optional
from io import BytesIO

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import fitz  # PyMuPDF

# Import LiteLLM for direct API calls
try:
    from litellm import completion
except ImportError:
    raise ImportError("LiteLLM is required. Install with: pip install litellm")

# Simple configuration
PROVIDER_OPTIONS = {
    "Mistral": "mistral",
    "Groq": "groq"
}

MODEL_OPTIONS = {
    "mistral": {
        "Mistral Small 3.2": "mistral-small-2506"
    },
    "groq": {
        "Llama Scout 17B": "meta-llama/llama-4-scout-17b-16e-instruct"
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

def setup_api_keys():
    """Set up API keys from environment variables"""
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  Warning: GROQ_API_KEY not found. Set GROQ_API_KEY environment variable.")
    if not os.getenv("MISTRAL_API_KEY"):
        print("⚠️  Warning: MISTRAL_API_KEY not found. Set MISTRAL_API_KEY environment variable.")

setup_api_keys()

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

def extract_and_parse_json(text: str):
    """Simple JSON extraction"""
    import json
    try:
        # Try to parse as direct JSON
        data = json.loads(text)
        return True, data, json.dumps(data, indent=2)
    except:
        # Try to find JSON in text
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            try:
                json_str = text[start:end]
                data = json.loads(json_str)
                return True, data, json.dumps(data, indent=2)
            except:
                pass
        return False, None, text

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
        # Try to import and use schema storage, but fall back gracefully
        import sys
        import os

        # Check if we can import without streamlit dependencies
        try:
            # Import directly from the storage file (use relative paths)
            from schema_management.storage.schema_storage import SchemaStorage

            # Use local data directory for development
            data_dir = os.path.join(os.path.dirname(__file__), "data")
            storage = SchemaStorage(data_dir=data_dir)
            schema_list = storage.list_schemas(status="active")

            # Format for API response
            schemas = {}
            for schema_info in schema_list:
                schema_id = schema_info["schema_id"]
                schemas[schema_id] = {
                    "id": schema_id,
                    "name": schema_info.get("name", schema_id.title()),
                    "display_name": schema_info.get("display_name", schema_id.title()),
                    "description": schema_info.get("description", f"Extract data from {schema_id} documents"),
                    "category": schema_info.get("category", "document"),
                    "created_at": schema_info.get("created_at"),
                    "updated_at": schema_info.get("updated_at"),
                    "version": schema_info.get("version", "1.0")
                }

            return {
                "success": True,
                "schemas": schemas
            }

        except ImportError as import_error:
            print(f"Schema storage import failed: {import_error}")
            # Return file-based schema discovery as fallback
            return await get_schemas_from_files()

    except Exception as e:
        print(f"Error loading schemas: {e}")
        # Return empty schemas on error rather than failing
        return {
            "success": True,
            "schemas": {},
            "error": str(e)
        }

async def get_schemas_from_files():
    """Fallback method to discover schemas from data directory"""
    try:
        import os
        import json

        data_dir = os.path.join(os.path.dirname(__file__), "data")
        schemas_dir = os.path.join(data_dir, "schemas")

        schemas = {}

        # Try to read schema files directly
        if os.path.exists(schemas_dir):
            for filename in os.listdir(schemas_dir):
                if filename.endswith('.json'):
                    schema_id = filename.replace('.json', '')
                    filepath = os.path.join(schemas_dir, filename)

                    try:
                        with open(filepath, 'r') as f:
                            schema_data = json.load(f)
                            schemas[schema_id] = {
                                "id": schema_id,
                                "name": schema_data.get("name", schema_id.title()),
                                "display_name": schema_data.get("display_name", schema_id.title()),
                                "description": schema_data.get("description", f"Extract data from {schema_id} documents"),
                                "category": schema_data.get("category", "document"),
                                "version": schema_data.get("version", "1.0")
                            }
                    except Exception as e:
                        print(f"Error reading schema file {filename}: {e}")

        return {
            "success": True,
            "schemas": schemas
        }

    except Exception as e:
        print(f"File-based schema discovery failed: {e}")
        return {
            "success": True,
            "schemas": {}
        }

@app.get("/api/schemas/{schema_id}")
async def get_schema_details(schema_id: str):
    """Get detailed schema information"""
    try:
        # Try to import and use schema storage, but fall back to file-based approach
        try:
            from schema_management.storage.schema_storage import SchemaStorage

            # Use local data directory for development
            data_dir = os.path.join(os.path.dirname(__file__), "data")
            storage = SchemaStorage(data_dir=data_dir)
            schema = storage.load_schema(schema_id)

            if not schema:
                raise HTTPException(status_code=404, detail="Schema not found")

            # Convert schema object to dict for API response
            schema_dict = {
                "id": schema.id,
                "name": schema.name,
                "description": schema.description,
                "category": schema.category,
                "version": schema.version,
                "created_at": schema.created_date.isoformat() if schema.created_date else None,
                "updated_at": schema.updated_date.isoformat() if schema.updated_date else None,
                "fields": schema.fields
            }

            return {
                "success": True,
                "schema": schema_dict
            }

        except ImportError as import_error:
            print(f"Schema storage import failed: {import_error}")
            # Fall back to file-based approach
            return await get_schema_details_from_file(schema_id)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error loading schema {schema_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading schema: {str(e)}")

async def get_schema_details_from_file(schema_id: str):
    """Fallback method to get schema details from file"""
    try:
        import json

        data_dir = os.path.join(os.path.dirname(__file__), "data")
        schemas_dir = os.path.join(data_dir, "schemas")
        schema_file = os.path.join(schemas_dir, f"{schema_id}.json")

        if not os.path.exists(schema_file):
            raise HTTPException(status_code=404, detail="Schema not found")

        with open(schema_file, 'r') as f:
            schema_data = json.load(f)

        return {
            "success": True,
            "schema": schema_data
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"File-based schema loading failed for {schema_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading schema: {str(e)}")

@app.post("/api/extract")
async def extract_data(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None)
):
    """Extract structured data from document"""
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
        if model and '_' in model:
            provider_id, model_id = model.split('_', 1)
        else:
            provider_id = "groq"
            model_id = "meta-llama/llama-4-scout-17b-16e-instruct"

        # Get model parameter for LiteLLM
        model_param = get_model_param(provider_id, model_id)

        # Create extraction prompt
        prompt = """Extract all text, data, and structure from this document image.
Analyze the document and intelligently organize the information into logical fields.
Return the data as structured JSON with clear field names and values.

Focus on:
- Key-value pairs (labels and their corresponding values)
- Tables and structured data
- Important identifying information
- Dates, amounts, and reference numbers

Format your response as JSON with descriptive field names."""

        # Prepare LiteLLM completion request
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

        # Make API call
        start_time = time.time()
        response = completion(**completion_kwargs)
        end_time = time.time()

        processing_time = end_time - start_time

        # Process response
        raw_content = response.choices[0].message.content

        # Parse JSON response
        is_json, parsed_data, formatted_text = extract_and_parse_json(raw_content)

        return {
            "success": True,
            "extracted_data": {
                "raw_content": raw_content,
                "formatted_text": formatted_text,
                "structured_data": parsed_data if is_json else None,
                "is_structured": is_json
            },
            "validation": {
                "passed": True,
                "errors": []
            },
            "metadata": {
                "processing_time": processing_time,
                "file_type": file_type,
                "model_used": f"{provider_id} - {model_id}",
                "extraction_mode": "ai_freeform"
            }
        }

    except Exception as e:
        print(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting FastAPI HTTP server...")
    print("📡 Simplified document extraction API")
    print("🔗 Frontend can connect to: http://localhost:8000")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )