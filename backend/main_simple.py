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