"""
AI Analysis Implementation for Schema Generation
Uses LiteLLM with Groq and Mistral models
"""

import time
import json
import base64
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import io
from litellm import completion
import streamlit as st

# Import from main app config
from config import get_model_param, PROVIDER_OPTIONS, MODEL_OPTIONS


class AIAnalyzer:
    """AI analyzer using LiteLLM with Groq and Mistral models"""

    def __init__(self):
        """Initialize AI analyzer"""
        # Map UI model names to actual provider/model combinations
        self.model_mapping = {
            "Llama Scout 17B (Groq)": ("groq", "meta-llama/llama-4-scout-17b-16e-instruct"),
            "Mistral Small 3.2": ("mistral", "mistral-small-2506"),
        }

    def generate_schema_from_document(self, uploaded_file, document_type: str, ai_model: str) -> Dict[str, Any]:
        """
        Generate schema from document using real AI analysis

        Args:
            uploaded_file: Streamlit uploaded file object
            document_type: Type of document (Invoice, Receipt, etc.)
            ai_model: AI model to use

        Returns:
            Dictionary with analysis results
        """
        try:
            start_time = time.time()

            # Get provider and model
            provider, model = self._get_provider_model(ai_model)

            # Process document to base64
            image_base64 = self._process_document_to_base64(uploaded_file)

            # Generate AI prompt
            prompt = self._generate_schema_prompt(document_type, uploaded_file.name)

            # Call LiteLLM
            response = self._call_ai_model(provider, model, prompt, image_base64)

            # Parse response
            schema_data = self._parse_ai_response(response, document_type, uploaded_file.name, ai_model)

            end_time = time.time()
            processing_time = end_time - start_time

            # Add timing and metadata
            schema_data.update({
                "analysis_time": processing_time,
                "ai_model": ai_model,
                "provider": provider,
                "model": model,
                "prompt_used": prompt,
                "success": True
            })

            return schema_data

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "ai_model": ai_model,
                "analysis_time": 0,
                "schema": {},
                "confidence_score": 0,
                "fields_detected": 0
            }

    def _get_provider_model(self, ai_model: str) -> Tuple[str, str]:
        """Get actual provider and model from UI model name"""
        if ai_model in self.model_mapping:
            return self.model_mapping[ai_model]
        else:
            # Default to Groq/Llama if unknown model
            return "groq", "meta-llama/llama-4-scout-17b-16e-instruct"

    def _process_document_to_base64(self, uploaded_file) -> str:
        """Convert uploaded document to base64 for AI processing"""
        if uploaded_file.type == "application/pdf":
            # For PDFs, convert first page to image
            return self._pdf_to_base64(uploaded_file)
        else:
            # For images, convert directly
            return self._image_to_base64(uploaded_file)

    def _pdf_to_base64(self, uploaded_file) -> str:
        """Convert PDF first page to base64 image"""
        try:
            import fitz  # PyMuPDF

            # Read PDF
            pdf_bytes = uploaded_file.read()
            uploaded_file.seek(0)  # Reset file pointer

            # Open PDF and get first page
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = doc[0]  # First page

            # Convert to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            img_data = pix.tobytes("png")

            # Convert to base64
            img_base64 = base64.b64encode(img_data).decode()

            doc.close()
            return img_base64

        except Exception as e:
            st.error(f"Failed to process PDF: {e}")
            # Return a placeholder base64 for error handling
            return ""

    def _image_to_base64(self, uploaded_file) -> str:
        """Convert image to base64"""
        try:
            # Read image
            image = Image.open(uploaded_file)
            uploaded_file.seek(0)  # Reset file pointer

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Save to bytes
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=95)
            img_bytes = buffer.getvalue()

            # Convert to base64
            img_base64 = base64.b64encode(img_bytes).decode()
            return img_base64

        except Exception as e:
            st.error(f"Failed to process image: {e}")
            return ""

    def _generate_schema_prompt(self, document_type: str, filename: str) -> str:
        """Generate AI prompt for schema generation"""
        import uuid

        # Generate unique ID
        schema_id = f"ai_{uuid.uuid4().hex[:8]}"

        base_instructions = f"""Analyze this document and FIRST detect what type of document it is (e.g., Invoice, Receipt, Contract, Passport, ID Card, Bank Statement, Form, etc.), then extract a structured JSON schema that describes the data fields present.

Document: {filename}

IMPORTANT: Return your response as a valid JSON object with this exact structure:
{{
    "detected_type": "The type of document you detected (e.g., Passport, Invoice, Receipt, etc.)",
    "schema": {{
        "id": "{schema_id}",
        "name": "[Detected Document Type]",
        "description": "[Brief description of what this document is and what was extracted from {filename}]",
        "fields": {{
            "field_name": {{
                "type": "string|number|date|email|phone|boolean",
                "required": true|false,
                "display_name": "Human readable name",
                "description": "What this field represents",
                "confidence": 0.85,
                "examples": ["example1", "example2"]
            }}
        }}
    }},
    "analysis": {{
        "confidence_score": 0.85,
        "fields_detected": 5,
        "processing_notes": "Brief notes about the analysis"
    }}
}}

"""

        # Add document-specific instructions
        if document_type == "Auto-detect":
            specific_instructions = """
ANALYZE THE DOCUMENT TO DETERMINE ITS TYPE:
1. First identify what type of document this is based on:
   - Visual layout and structure
   - Key text/headers visible
   - Types of fields present
   - Common document patterns

2. Common document types include:
   - Passport (contains passport number, name, nationality, dates)
   - Driver's License (contains license number, name, address, DOB)
   - Invoice (contains invoice number, dates, amounts, vendor/customer info)
   - Receipt (contains merchant, items, prices, total)
   - Contract (contains parties, terms, signatures)
   - Bank Statement (contains account info, transactions, balances)
   - Form (contains various input fields)
   - Business Letter (contains sender, recipient, date, body text)
   - ID Card (contains ID number, name, photo, personal details)

3. Set the "detected_type" field to the document type you identified
4. Set the schema "name" field to the detected document type
5. Extract ALL relevant fields you can identify in the document
6. For each field, provide accurate type, description, and confidence score"""
        elif document_type == "Invoice":
            specific_instructions = """
Focus on identifying these common invoice fields:
- Invoice number/ID (string, high confidence if clearly visible)
- Invoice date and due date (date fields)
- Vendor/company information (string fields)
- Customer/billing information (string fields)
- Line items and descriptions (string/array fields)
- Financial amounts: subtotal, tax, total (number fields, required)
- Payment terms (string, optional)

Look for monetary values, dates, company names, and reference numbers."""

        elif document_type == "Receipt":
            specific_instructions = """
Focus on identifying these common receipt fields:
- Merchant/store name (string, required)
- Purchase date and time (date/string fields)
- Items purchased (array/string fields)
- Payment method (string, credit/debit/cash)
- Total amount, tax, subtotal (number fields)
- Receipt number or transaction ID (string)

Look for store names, timestamps, monetary amounts, and transaction details."""

        elif document_type == "Contract":
            specific_instructions = """
Focus on identifying these common contract fields:
- Contract title/subject (string)
- Party names and addresses (string fields, required)
- Effective date, execution date, expiration date (date fields)
- Contract value or financial terms (number fields)
- Key terms and conditions (string/text fields)
- Signature information (string fields)

Look for party names, dates, monetary values, and legal terms."""

        elif document_type == "Bank Statement":
            specific_instructions = """
Focus on identifying these common bank statement fields:
- Account holder name (string, required)
- Account number (string, partially masked)
- Statement period dates (date fields)
- Opening and closing balance (number fields, required)
- Bank name and routing information (string fields)
- Transaction details if visible (array/structured data)

Look for account information, balances, dates, and bank details."""

        else:  # Auto-detect or other
            specific_instructions = """
Automatically detect the document type and extract relevant fields:
- Look for dates, names, addresses, phone numbers, emails
- Identify monetary amounts, percentages, quantities
- Find reference numbers, IDs, codes
- Detect any structured data like tables or lists
- Classify field types based on content patterns

Be conservative with confidence scores for unclear fields."""

        return base_instructions + specific_instructions + """

Assign confidence scores (0.0 to 1.0) based on:
- 0.9-1.0: Clearly visible and unambiguous
- 0.7-0.9: Visible but may need interpretation
- 0.5-0.7: Partially visible or inferred
- 0.3-0.5: Unclear but likely present
- 0.0-0.3: Very uncertain or poorly visible

Return ONLY the JSON response, no additional text."""

    def _call_ai_model(self, provider: str, model: str, prompt: str, image_base64: str) -> Any:
        """Call LiteLLM with the specified model"""
        try:
            # Get model parameter for LiteLLM
            model_param = get_model_param(provider, model)

            # Prepare messages for vision model
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }]

            # Make API call
            response = completion(
                model=model_param,
                messages=messages,
                temperature=0.1,  # Low temperature for consistent output
                max_tokens=2000   # Enough for schema JSON
            )

            return response

        except Exception as e:
            raise Exception(f"AI model call failed: {str(e)}")

    def _parse_ai_response(self, response, document_type: str, filename: str, ai_model: str) -> Dict[str, Any]:
        """Parse AI response and extract schema data"""
        try:
            # Get response content
            content = response.choices[0].message.content.strip()

            # Try to parse as JSON
            try:
                parsed_response = json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    parsed_response = json.loads(json_match.group())
                else:
                    raise Exception("No valid JSON found in response")

            # Extract schema and analysis data
            schema = parsed_response.get("schema", {})
            analysis = parsed_response.get("analysis", {})
            detected_type = parsed_response.get("detected_type", document_type)

            # Update schema name to detected type if auto-detecting
            if document_type == "Auto-detect" and detected_type:
                schema["name"] = detected_type
                document_type = detected_type

            # Ensure required fields exist
            if not schema.get("fields"):
                raise Exception("No fields found in schema")

            # Add AI metadata to fields
            fields = schema.get("fields", {})
            for field_name, field_config in fields.items():
                if "ai_metadata" not in field_config:
                    field_config["ai_metadata"] = {
                        "source": ai_model,
                        "confidence": field_config.get("confidence", 0.7),
                        "generated_by": "ai_analysis"
                    }

            # Calculate overall confidence if not provided
            confidence_score = analysis.get("confidence_score")
            if confidence_score is None:
                confidences = [field.get("confidence", 0.7) for field in fields.values()]
                confidence_score = sum(confidences) / len(confidences) if confidences else 0.7

            return {
                "schema": schema,
                "confidence_score": confidence_score,
                "fields_detected": len(fields),
                "document_type": detected_type if document_type == "Auto-detect" else document_type,
                "detected_type": detected_type,
                "processing_notes": analysis.get("processing_notes", "AI analysis completed"),
                "raw_response": content  # For debugging
            }

        except Exception as e:
            # Fallback: create a basic schema if parsing fails
            return self._create_fallback_schema(document_type, filename, ai_model, str(e))

    def _create_fallback_schema(self, document_type: str, filename: str, ai_model: str, error: str) -> Dict[str, Any]:
        """Create a fallback schema if AI response parsing fails"""

        fallback_schemas = {
            "Invoice": {
                "invoice_number": {"type": "string", "required": True, "display_name": "Invoice Number"},
                "invoice_date": {"type": "date", "required": True, "display_name": "Invoice Date"},
                "total_amount": {"type": "number", "required": True, "display_name": "Total Amount"}
            },
            "Receipt": {
                "merchant_name": {"type": "string", "required": True, "display_name": "Merchant Name"},
                "purchase_date": {"type": "date", "required": True, "display_name": "Purchase Date"},
                "total_amount": {"type": "number", "required": True, "display_name": "Total Amount"}
            }
        }

        fields = fallback_schemas.get(document_type, {
            "document_title": {"type": "string", "required": True, "display_name": "Document Title"},
            "date": {"type": "date", "required": False, "display_name": "Date"},
            "amount": {"type": "number", "required": False, "display_name": "Amount"}
        })

        # Add AI metadata
        for field_config in fields.values():
            field_config["ai_metadata"] = {
                "source": ai_model,
                "confidence": 0.5,  # Low confidence for fallback
                "generated_by": "fallback_schema",
                "error": error
            }

        return {
            "schema": {
                "id": f"fallback_{document_type.lower()}",
                "name": f"Fallback {document_type} Schema",
                "description": f"Fallback schema for {filename} (AI parsing failed)",
                "fields": fields
            },
            "confidence_score": 0.5,
            "fields_detected": len(fields),
            "document_type": document_type,
            "processing_notes": f"AI response parsing failed: {error}",
            "is_fallback": True
        }

    def get_available_models(self) -> list:
        """Get list of available AI models"""
        return [
            "Llama Scout 17B (Groq)",
            "Mistral Small 3.2"
        ]


# Global analyzer instance
_ai_analyzer = None

def get_ai_analyzer() -> AIAnalyzer:
    """Get singleton AI analyzer instance"""
    global _ai_analyzer
    if _ai_analyzer is None:
        _ai_analyzer = AIAnalyzer()
    return _ai_analyzer