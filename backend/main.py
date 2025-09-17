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
    import litellm
    from litellm import completion

    # Enable JSON schema validation for structured outputs
    litellm.enable_json_schema_validation = True
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

        # Make API call with JSON mode for structured output
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
            temperature=0.1,
            response_format={"type": "json_object"}
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

        # Process the new confidence-aware response structure with document verification
        structured_data = {}
        field_confidence = {}
        overall_confidence = 75  # Default fallback
        document_quality = "medium"  # Default fallback
        extraction_issues = []
        document_verification = {}  # New verification data

        if is_json and parsed_data:
            # Parse document verification if present
            if "document_verification" in parsed_data:
                document_verification = parsed_data.get("document_verification", {})

            # Check if response has the new confidence structure
            if "extracted_fields" in parsed_data:
                # New structure with confidence scores
                extracted_fields = parsed_data.get("extracted_fields", {})
                for field_name, field_data in extracted_fields.items():
                    if isinstance(field_data, dict):
                        structured_data[field_name] = field_data.get("value", "")
                        field_confidence[field_name] = field_data.get("confidence", 75)
                    else:
                        # Fallback for simple values
                        structured_data[field_name] = field_data
                        field_confidence[field_name] = 75

                overall_confidence = parsed_data.get("overall_confidence", 75)
                document_quality = parsed_data.get("document_quality", "medium")
                extraction_issues = parsed_data.get("extraction_issues", [])
            else:
                # Legacy structure without confidence - use parsed data as is
                structured_data = parsed_data
                # Estimate confidence based on validation
                for field_name in parsed_data.keys():
                    field_confidence[field_name] = 75  # Default confidence for legacy

        # Validate against schema if provided
        validation_results = {"passed": True, "errors": []}
        if schema_id and schema_id in SCHEMAS and structured_data:
            schema = SCHEMAS[schema_id]
            for field_name, field_info in schema["fields"].items():
                if field_info.get("required") and field_name not in structured_data:
                    validation_results["errors"].append(f"Required field '{field_name}' is missing")
                    validation_results["passed"] = False

                # Validate field value is not an object (should be simple values)
                if field_name in structured_data:
                    field_value = structured_data[field_name]
                    if isinstance(field_value, (dict, list)):
                        validation_results["errors"].append(f"Field '{field_name}' should be a simple value, not an object/array")
                        validation_results["passed"] = False
                        # Convert object to string representation for debugging
                        structured_data[field_name] = str(field_value) if field_value else ""

        # Add extraction issues to validation errors
        if extraction_issues:
            validation_results["errors"].extend(extraction_issues)

        return {
            "success": True,
            "extracted_data": {
                "raw_content": raw_content,
                "formatted_text": formatted_text,
                "structured_data": structured_data if is_json else None,
                "is_structured": is_json,
                "field_confidence": field_confidence,
                "overall_confidence": overall_confidence,
                "document_quality": document_quality
            },
            "document_verification": document_verification,
            "validation": validation_results,
            "metadata": {
                "processing_time": end_time - start_time,
                "file_type": file_type,
                "model_used": f"{provider_id} - {model_id}",
                "extraction_mode": "schema_guided" if schema_id else "freeform",
                "schema_used": schema_id,
                "overall_confidence": overall_confidence,
                "document_quality": document_quality,
                "verification_risk_level": document_verification.get("risk_level", "unknown") if document_verification else "unknown",
                "authenticity_score": document_verification.get("authenticity_score", None) if document_verification else None
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
    """Generate a schema definition using multi-step AI analysis"""
    try:
        start_time = time.time()

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

        # Multi-step AI processing
        ai_debug_info = {"steps": []}

        # Step 1: Initial Detection
        step1_prompt = create_initial_detection_prompt()
        step1_start = time.time()

        step1_response = completion(
            model=model_param,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": step1_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        step1_end = time.time()

        step1_raw = step1_response.choices[0].message.content
        step1_valid, step1_data, step1_formatted = extract_json_from_text(step1_raw)

        ai_debug_info["steps"].append({
            "step": 1,
            "name": "Initial Detection",
            "duration": step1_end - step1_start,
            "prompt": step1_prompt,
            "raw_response": step1_raw,
            "parsed_data": step1_data,
            "success": step1_valid
        })

        if not step1_valid or not step1_data:
            # Step 1 failed - create generic fallback schema
            print(f"Step 1 failed, using fallback schema. Raw response: {step1_raw[:200]}...")
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

        step2_response = completion(
            model=model_param,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": step2_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        step2_end = time.time()

        step2_raw = step2_response.choices[0].message.content
        step2_valid, step2_data, step2_formatted = extract_json_from_text(step2_raw)

        ai_debug_info["steps"].append({
            "step": 2,
            "name": "Schema Review & Refinement",
            "duration": step2_end - step2_start,
            "prompt": step2_prompt,
            "raw_response": step2_raw,
            "parsed_data": step2_data,
            "success": step2_valid
        })

        if not step2_valid or not step2_data:
            # Step 2 failed - create fallback schema from Step 1 results
            print(f"Step 2 failed, using Step 1 results with fallbacks. Raw response: {step2_raw[:200]}...")
            step2_data = {
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

        step3_response = completion(
            model=model_param,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": step3_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        step3_end = time.time()

        step3_raw = step3_response.choices[0].message.content
        step3_valid, step3_data, step3_formatted = extract_json_from_text(step3_raw)

        ai_debug_info["steps"].append({
            "step": 3,
            "name": "Confidence Analysis",
            "duration": step3_end - step3_start,
            "prompt": step3_prompt,
            "raw_response": step3_raw,
            "parsed_data": step3_data,
            "success": step3_valid
        })

        # Step 4: Hints Generation
        step4_prompt = create_hints_generation_prompt(step2_data, step3_data or {})
        step4_start = time.time()

        step4_response = completion(
            model=model_param,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": step4_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        step4_end = time.time()

        step4_raw = step4_response.choices[0].message.content
        step4_valid, step4_data, step4_formatted = extract_json_from_text(step4_raw)

        ai_debug_info["steps"].append({
            "step": 4,
            "name": "Extraction Hints Generation",
            "duration": step4_end - step4_start,
            "prompt": step4_prompt,
            "raw_response": step4_raw,
            "parsed_data": step4_data,
            "success": step4_valid
        })

        end_time = time.time()

        # Build final schema with enhanced data
        schema_id = step2_data.get("id", "generated_schema")

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

        # Add to schemas for immediate use
        SCHEMAS[schema_id] = enhanced_schema

        return {
            "success": True,
            "generated_schema": {
                "schema_id": schema_id,
                "schema_data": enhanced_schema,
                "is_valid": True,
                "ready_for_extraction": True,
                "raw_response": f"Multi-step generation completed with {len(ai_debug_info['steps'])} steps",
                "formatted_text": json.dumps(enhanced_schema, indent=2)
            },
            "next_steps": {
                "available_in_schemas": True,
                "can_use_for_extraction": True,
                "schema_endpoint": f"/api/schemas/{schema_id}"
            },
            "metadata": {
                "processing_time": end_time - start_time,
                "file_type": file_type,
                "model_used": f"{provider_id} - {model_id}",
                "fields_generated": len(enhanced_schema.get("fields", {})),
                "steps_completed": len(ai_debug_info["steps"]),
                "overall_confidence": enhanced_schema.get("overall_confidence", 75),
                "document_quality": enhanced_schema.get("document_quality", "medium")
            },
            "ai_debug": ai_debug_info
        }

    except Exception as e:
        print(f"Multi-step schema generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Multi-step schema generation failed: {str(e)}")

@app.post("/api/schemas")
async def save_schema(schema_data: Dict[str, Any]):
    """Save a generated schema to make it available for data extraction"""
    try:
        # Validate required fields
        required_fields = ["id", "name", "description", "category", "fields"]
        for field in required_fields:
            if field not in schema_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        schema_id = schema_data["id"]

        # Ensure schema ID is valid (snake_case)
        if not schema_id.replace("_", "").replace("-", "").isalnum():
            raise HTTPException(status_code=400, detail="Schema ID must be alphanumeric with underscores or dashes")

        # Check if schema ID already exists - if so, update it instead of rejecting
        is_update = schema_id in SCHEMAS

        # Validate fields structure
        if not isinstance(schema_data["fields"], dict):
            raise HTTPException(status_code=400, detail="Fields must be a dictionary")

        for field_name, field_config in schema_data["fields"].items():
            if not isinstance(field_config, dict):
                raise HTTPException(status_code=400, detail=f"Field '{field_name}' configuration must be a dictionary")
            if "type" not in field_config or "required" not in field_config:
                raise HTTPException(status_code=400, detail=f"Field '{field_name}' must have 'type' and 'required' properties")

        # Save schema to the in-memory store
        SCHEMAS[schema_id] = {
            "id": schema_id,
            "name": schema_data["name"],
            "description": schema_data["description"],
            "category": schema_data["category"],
            "fields": schema_data["fields"],
            "created_at": datetime.now().isoformat(),
            "generated": True  # Flag to distinguish from predefined schemas
        }

        action = "updated" if is_update else "created"
        return {
            "success": True,
            "message": f"Schema '{schema_data['name']}' {action} successfully and is now available for data extraction",
            "schema_id": schema_id,
            "available_for_extraction": True,
            "is_update": is_update
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Schema save error: {e}")
        raise HTTPException(status_code=500, detail=f"Schema save failed: {str(e)}")

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