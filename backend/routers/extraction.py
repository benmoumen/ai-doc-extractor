"""
Data extraction and schema generation endpoints
"""

import json
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException, Depends, status

from config import settings
from validators import InputSanitizer
from services.document_processor import process_uploaded_document, prepare_document_for_ai
from services.ai_service import determine_ai_model, make_ai_request_with_retry, extract_json_from_text
from routers.schemas import get_schemas_dict

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize sanitizer
input_sanitizer = InputSanitizer()


def check_ai_request_limit():
    """Dependency to check AI request limits"""
    from services.ai_service import get_active_ai_requests
    active_requests = get_active_ai_requests()
    if active_requests >= settings.performance.max_concurrent_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many active AI requests. Please try again later."
        )


@router.post("/api/extract")
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

        # Get schemas dict and sanitize schema_id
        SCHEMAS = get_schemas_dict()
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


@router.post("/api/generate-schema")
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

        # Get schemas dict to store result
        SCHEMAS = get_schemas_dict()

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

    SCHEMAS = get_schemas_dict()
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