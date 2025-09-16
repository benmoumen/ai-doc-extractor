"""
Clean MVP FastAPI backend for AI Document Data Extractor
Focuses on core functionality: data extraction and schema generation
"""

import os
import time
import base64
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from io import BytesIO

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import fitz  # PyMuPDF

# Import LiteLLM for AI model calls
try:
    from litellm import completion
except ImportError:
    raise ImportError("LiteLLM is required. Install with: pip install litellm")

# Simple configuration
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

def setup_api_keys():
    """Set up API keys from environment variables"""
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  Warning: GROQ_API_KEY not found. Set GROQ_API_KEY environment variable.")
    if not os.getenv("MISTRAL_API_KEY"):
        print("⚠️  Warning: MISTRAL_API_KEY not found. Set MISTRAL_API_KEY environment variable.")

setup_api_keys()

# Initialize FastAPI app
app = FastAPI(
    title="AI Document Data Extractor - MVP",
    description="Clean MVP for document data extraction and schema generation",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# eGov platform schemas for person and business entities
SCHEMAS = {
    "national_id": {
        "id": "national_id",
        "name": "National ID Card",
        "description": "National identity card for citizens",
        "category": "Government",
        "fields": {
            "id_number": {"type": "text", "required": True, "description": "National ID number"},
            "full_name": {"type": "text", "required": True, "description": "Full name in Arabic and/or English"},
            "date_of_birth": {"type": "date", "required": True, "description": "Date of birth"},
            "place_of_birth": {"type": "text", "required": True, "description": "Place of birth"},
            "nationality": {"type": "text", "required": True, "description": "Nationality"},
            "gender": {"type": "text", "required": True, "description": "Gender (Male/Female)"},
            "issue_date": {"type": "date", "required": True, "description": "ID card issue date"},
            "expiry_date": {"type": "date", "required": True, "description": "ID card expiry date"},
            "issuing_authority": {"type": "text", "required": True, "description": "Authority that issued the ID"}
        }
    },
    "passport": {
        "id": "passport",
        "name": "Passport",
        "description": "International travel passport document",
        "category": "Government",
        "fields": {
            "passport_number": {"type": "text", "required": True, "description": "Passport number"},
            "full_name": {"type": "text", "required": True, "description": "Full name as on passport"},
            "date_of_birth": {"type": "date", "required": True, "description": "Date of birth"},
            "place_of_birth": {"type": "text", "required": True, "description": "Place of birth"},
            "nationality": {"type": "text", "required": True, "description": "Nationality"},
            "gender": {"type": "text", "required": True, "description": "Gender"},
            "issue_date": {"type": "date", "required": True, "description": "Passport issue date"},
            "expiry_date": {"type": "date", "required": True, "description": "Passport expiry date"},
            "issuing_country": {"type": "text", "required": True, "description": "Country that issued passport"},
            "personal_number": {"type": "text", "required": False, "description": "Personal identification number"}
        }
    },
    "residence_permit": {
        "id": "residence_permit",
        "name": "Residence Permit",
        "description": "Residence permit for foreign nationals",
        "category": "Government",
        "fields": {
            "foreigner_identity_number": {"type": "text", "required": True, "description": "Foreigner Identity Number - unique identifier"},
            "name": {"type": "text", "required": True, "description": "Given name(s) of permit holder"},
            "surname": {"type": "text", "required": True, "description": "Surname/family name of permit holder"},
            "date_of_birth": {"type": "date", "required": True, "description": "Date of birth"},
            "nationality": {"type": "text", "required": True, "description": "Nationality of permit holder"},
            "province_of_residence": {"type": "text", "required": True, "description": "Province where permit holder resides"},
            "serial_number": {"type": "text", "required": True, "description": "Serial number of the permit document"},
            "issuer": {"type": "text", "required": True, "description": "Issuing authority or office"}
        }
    },
    "business_license": {
        "id": "business_license",
        "name": "Business License",
        "description": "Commercial business license or trade permit",
        "category": "Business",
        "fields": {
            "license_number": {"type": "text", "required": True, "description": "Business license number"},
            "business_name": {"type": "text", "required": True, "description": "Legal business name"},
            "business_name_arabic": {"type": "text", "required": False, "description": "Business name in Arabic"},
            "business_type": {"type": "text", "required": True, "description": "Type of business activity"},
            "owner_name": {"type": "text", "required": True, "description": "Business owner full name"},
            "issue_date": {"type": "date", "required": True, "description": "License issue date"},
            "expiry_date": {"type": "date", "required": True, "description": "License expiry date"},
            "commercial_registry": {"type": "text", "required": False, "description": "Commercial registry number"},
            "tax_number": {"type": "text", "required": False, "description": "Tax registration number"},
            "issuing_authority": {"type": "text", "required": True, "description": "Authority that issued license"},
            "business_address": {"type": "text", "required": True, "description": "Registered business address"}
        }
    }
}

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

def extract_json_from_text(text: str) -> tuple[bool, Optional[Dict], str]:
    """Extract JSON from AI response text, handling multiple JSON blocks"""
    try:
        # Try to parse as direct JSON
        data = json.loads(text)
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
                # For schema generation, prioritize objects with "id" and "fields" keys
                if isinstance(data, dict) and "id" in data and "fields" in data:
                    return True, data, json.dumps(data, indent=2)
            except:
                continue

    # Look for JSON blocks without markdown
    json_blocks = re.findall(r'(\{[^}]*"fields"[^}]*\{.*?\}[^}]*\})', text, re.DOTALL)
    if json_blocks:
        for block in json_blocks:
            try:
                data = json.loads(block)
                if isinstance(data, dict) and "fields" in data:
                    return True, data, json.dumps(data, indent=2)
            except:
                continue

    # Fallback: try to find any JSON in text
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

def create_extraction_prompt(schema_id: Optional[str] = None) -> str:
    """Create extraction prompt based on schema"""
    base_prompt = """Extract all text, data, and structure from this document image.
Analyze the document and organize the information into logical fields.
Return the data as structured JSON with clear field names and values.

Focus on:
- Key-value pairs (labels and their corresponding values)
- Tables and structured data
- Important identifying information
- Dates, amounts, and reference numbers"""

    if schema_id and schema_id in SCHEMAS:
        schema = SCHEMAS[schema_id]
        schema_prompt = f"""

This appears to be a {schema['name']} document. Extract the following specific fields:
"""
        for field_name, field_info in schema['fields'].items():
            required_text = " (REQUIRED)" if field_info.get('required') else ""
            schema_prompt += f"- {field_name}: {field_info['description']}{required_text}\n"

        schema_prompt += f"""
Return JSON with these exact field names: {list(schema['fields'].keys())}"""

        return base_prompt + schema_prompt

    return base_prompt + "\n\nFormat your response as JSON with descriptive field names."

def create_schema_generation_prompt() -> str:
    """Create prompt for generating eGov schemas compatible with data extraction system"""
    return """Analyze this specific document image and create ONE JSON schema definition that matches the document type shown.

Look at the document carefully and identify what type it is (National ID, Passport, Residence Permit, Business License, etc.).

Return ONLY ONE JSON schema that matches the specific document type in the image.

IMPORTANT: Return ONLY the JSON schema, no additional text, explanations, or multiple schemas. The schema must match this EXACT format:

{
  "id": "document_type_id",
  "name": "Document Type Name",
  "description": "Brief description of this document type",
  "category": "Government|Business|Personal",
  "fields": {
    "field_name": {
      "type": "text|number|date|email|phone|url",
      "required": true|false,
      "description": "What this field contains and where it appears"
    }
  }
}

eGov Schema Requirements:
1. ID: Use snake_case (e.g., "national_id", "passport", "residence_permit", "business_license")
2. Field names: Use snake_case (e.g., "id_number", "full_name", "issue_date", "license_number")
3. Categories: Government (for official IDs), Business (for licenses), Personal (for certificates)
4. Focus on OFFICIAL DATA that government systems need to process

Standard eGov Fields to Include:
- Document numbers (id_number, passport_number, license_number)
- Personal info (full_name, date_of_birth, nationality, gender)
- Validity dates (issue_date, expiry_date)
- Issuing authorities (issuing_authority, issuing_country)
- Business info (business_name, business_type, owner_name, tax_number)

Field Type Guidelines:
- Use "text" for names, addresses, document numbers
- Use "date" for all dates (birth, issue, expiry)
- Use "phone" for contact numbers
- Use "email" for email addresses

Mark as REQUIRED only fields that appear on ALL documents of this type.
Mark as OPTIONAL fields that may not always be present.

Respond with ONLY the JSON schema - no markdown formatting, no explanations, no additional text. Just the raw JSON object."""

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "backend_available": True,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
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
    formatted_schemas = {}
    for schema_id, schema in SCHEMAS.items():
        formatted_schemas[schema_id] = {
            "id": schema_id,
            "name": schema["name"],
            "description": schema["description"],
            "category": schema["category"],
            "field_count": len(schema["fields"])
        }

    return {
        "success": True,
        "schemas": formatted_schemas
    }

@app.get("/api/schemas/{schema_id}")
async def get_schema_details(schema_id: str):
    """Get detailed schema information"""
    if schema_id not in SCHEMAS:
        raise HTTPException(status_code=404, detail="Schema not found")

    return {
        "success": True,
        "schema": SCHEMAS[schema_id]
    }

@app.post("/api/documents")
async def upload_document(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    document_type_hint: Optional[str] = Form(None)
):
    """Upload document and return basic metadata - no AI analysis at this stage"""
    try:
        # Read file data
        file_data = await file.read()
        file_type = determine_file_type(file.filename)

        # Basic file validation only - no AI processing
        if file_type == 'pdf':
            # Just validate PDF can be opened
            pdf_to_images(file_data, page_num=1)
        else:
            # Just validate image can be opened
            Image.open(BytesIO(file_data))

        # Generate document ID
        import uuid
        doc_id = str(uuid.uuid4())
        analysis_id = str(uuid.uuid4())

        # Return basic document info - no AI detection
        return {
            "success": True,
            "processing_stages": {
                "upload": {"success": True, "duration": 0.1},
                "validation": {"success": True, "duration": 0.1}
            },
            "document": {
                "id": doc_id,
                "filename": file.filename,
                "file_type": file_type,
                "file_size": len(file_data),
                "processing_status": "uploaded"
            },
            "analysis": {
                "id": analysis_id,
                "detected_document_type": "unknown",
                "document_type_confidence": 0.0,
                "total_fields_detected": 0,
                "high_confidence_fields": 0,
                "overall_quality_score": 0.0,
                "model_used": "none"
            },
            "schema": {
                "id": "generic",
                "name": "Generic Document",
                "description": "Generic document - schema will be determined during extraction",
                "total_fields": 0,
                "high_confidence_fields": 0,
                "generation_confidence": 0.0,
                "production_ready": False
            },
            "confidence": {
                "overall_confidence": 0.0,
                "field_confidence": {}
            },
            "metadata": {
                "processing_time": 0.2,
                "file_type": file_type,
                "analysis_version": "2.0.0",
                "note": "Upload only - AI analysis will occur during extraction"
            }
        }

    except Exception as e:
        print(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

@app.post("/api/extract")
async def extract_data(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    schema_id: Optional[str] = Form(None)
):
    """Extract structured data from document"""
    try:
        # Read file data
        file_data = await file.read()
        file_type = determine_file_type(file.filename)

        # Convert document to image
        if file_type == 'pdf':
            image = pdf_to_images(file_data, page_num=1)
        else:
            image = Image.open(BytesIO(file_data))

        # Convert image to base64
        image_base64 = image_to_base64(image)

        # Determine model
        if model and '_' in model:
            provider_id, model_id = model.split('_', 1)
        else:
            provider_id = "groq"
            model_id = "meta-llama/llama-4-scout-17b-16e-instruct"

        model_param = get_model_param(provider_id, model_id)

        # Create extraction prompt
        prompt = create_extraction_prompt(schema_id)

        # Prepare completion parameters for debugging
        completion_params = {
            "model": model_param,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64[:50]}..."}}  # Truncate for readability
                ]
            }],
            "temperature": 0.1
        }

        # Make API call
        start_time = time.time()
        response = completion(
            model=model_param,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            temperature=0.1
        )
        end_time = time.time()

        # Process response
        raw_content = response.choices[0].message.content
        raw_response = {
            "id": getattr(response, 'id', None),
            "choices": [{
                "message": {
                    "role": response.choices[0].message.role,
                    "content": response.choices[0].message.content
                },
                "finish_reason": getattr(response.choices[0], 'finish_reason', None)
            }],
            "usage": getattr(response, 'usage', {}).dict() if hasattr(response, 'usage') and response.usage else {},
            "model": getattr(response, 'model', model_param)
        }
        is_json, parsed_data, formatted_text = extract_json_from_text(raw_content)

        # Validate against schema if provided
        validation_results = {"passed": True, "errors": []}
        if schema_id and schema_id in SCHEMAS and is_json and parsed_data:
            schema = SCHEMAS[schema_id]
            for field_name, field_info in schema["fields"].items():
                if field_info.get("required") and field_name not in parsed_data:
                    validation_results["errors"].append(f"Required field '{field_name}' is missing")
                    validation_results["passed"] = False

        return {
            "success": True,
            "extracted_data": {
                "raw_content": raw_content,
                "formatted_text": formatted_text,
                "structured_data": parsed_data if is_json else None,
                "is_structured": is_json
            },
            "validation": validation_results,
            "metadata": {
                "processing_time": end_time - start_time,
                "file_type": file_type,
                "model_used": f"{provider_id} - {model_id}",
                "extraction_mode": "schema_guided" if schema_id else "freeform",
                "schema_used": schema_id
            },
            "debug": {
                "completion_params": completion_params,
                "raw_response": raw_response
            }
        }

    except Exception as e:
        print(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@app.post("/api/generate-schema")
async def generate_schema(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None)
):
    """Generate a schema definition from a sample document"""
    try:
        # Read file data
        file_data = await file.read()
        file_type = determine_file_type(file.filename)

        # Convert document to image
        if file_type == 'pdf':
            image = pdf_to_images(file_data, page_num=1)
        else:
            image = Image.open(BytesIO(file_data))

        # Convert image to base64
        image_base64 = image_to_base64(image)

        # Determine model
        if model and '_' in model:
            provider_id, model_id = model.split('_', 1)
        else:
            provider_id = "groq"
            model_id = "meta-llama/llama-4-scout-17b-16e-instruct"

        model_param = get_model_param(provider_id, model_id)

        # Create schema generation prompt
        prompt = create_schema_generation_prompt()

        # Make API call
        start_time = time.time()
        response = completion(
            model=model_param,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            temperature=0.1
        )
        end_time = time.time()

        # Process response
        raw_content = response.choices[0].message.content
        is_json, parsed_schema, formatted_text = extract_json_from_text(raw_content)

        if is_json and parsed_schema:
            # Use the schema ID from AI response or generate one
            schema_id = parsed_schema.get("id") or parsed_schema.get("name", "custom").lower().replace(" ", "_").replace("-", "_")

            # Validate schema has required fields
            if not parsed_schema.get("fields"):
                raise ValueError("Generated schema must have fields")

            # Format schema for compatibility with extraction system
            formatted_schema = {
                "id": schema_id,
                "name": parsed_schema.get("name", "Generated Schema"),
                "description": parsed_schema.get("description", "AI-generated schema from document"),
                "category": parsed_schema.get("category", "Custom"),
                "fields": {}
            }

            # Validate and format fields
            for field_name, field_config in parsed_schema.get("fields", {}).items():
                # Ensure field has required properties
                if isinstance(field_config, dict):
                    formatted_schema["fields"][field_name] = {
                        "type": field_config.get("type", "text"),
                        "required": field_config.get("required", False),
                        "description": field_config.get("description", f"Field: {field_name}")
                    }

            # Add to in-memory schemas for immediate use
            SCHEMAS[schema_id] = formatted_schema

        return {
            "success": True,
            "generated_schema": {
                "schema_id": schema_id if is_json and parsed_schema else None,
                "schema_data": formatted_schema if is_json and parsed_schema else None,
                "is_valid": is_json and parsed_schema is not None,
                "ready_for_extraction": is_json and parsed_schema is not None,
                "raw_response": raw_content,
                "formatted_text": formatted_text
            },
            "next_steps": {
                "available_in_schemas": is_json and parsed_schema is not None,
                "can_use_for_extraction": is_json and parsed_schema is not None,
                "schema_endpoint": f"/api/schemas/{schema_id}" if is_json and parsed_schema else None
            },
            "metadata": {
                "processing_time": end_time - start_time,
                "file_type": file_type,
                "model_used": f"{provider_id} - {model_id}",
                "fields_generated": len(formatted_schema.get("fields", {})) if is_json and parsed_schema else 0
            }
        }

    except Exception as e:
        print(f"Schema generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Schema generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting AI Document Data Extractor MVP...")
    print("📡 Clean backend with data extraction & schema generation")
    print("🔗 Frontend can connect to: http://localhost:8000")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )