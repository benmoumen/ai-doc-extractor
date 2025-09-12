"""
Utility functions for JSON parsing and image processing.
"""
import json
import re
import fitz  # PyMuPDF
from PIL import Image
import io
import streamlit as st


def extract_and_parse_json(text):
    """
    Extract and parse JSON from text output, handling various formats.
    
    Args:
        text: Text that may contain JSON data
        
    Returns:
        tuple: (is_json, parsed_data, formatted_text)
    """
    # Try to parse the entire text as JSON first
    try:
        parsed = json.loads(text.strip())
        return True, parsed, json.dumps(parsed, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        pass
    
    # Look for JSON blocks wrapped in ```json or ``` markers
    json_patterns = [
        r'```json\s*\n?(.*?)\n?```',
        r'```\s*\n?(.*?)\n?```',
        r'\{.*\}',  # Look for object-like structures
        r'\[.*\]'   # Look for array-like structures
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                parsed = json.loads(match.strip())
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                return True, parsed, formatted
            except json.JSONDecodeError:
                continue
    
    # No valid JSON found
    return False, None, text


def pdf_to_images(pdf_file, page_num=0):
    """
    Convert PDF page to PIL Image.
    
    Args:
        pdf_file: Streamlit uploaded file object
        page_num: Page number to convert (0-indexed)
        
    Returns:
        tuple: (success, image, total_pages)
    """
    try:
        # Open PDF from bytes
        pdf_bytes = pdf_file.getvalue()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        total_pages = len(pdf_document)
        
        if page_num >= total_pages:
            return False, None, total_pages
        
        # Get the specified page
        page = pdf_document[page_num]
        
        # Convert page to image with high resolution
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        
        pdf_document.close()
        return True, image, total_pages
        
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return False, None, 0


def image_to_base64(image):
    """
    Convert PIL Image to base64 string.
    
    Args:
        image: PIL Image object
        
    Returns:
        str: Base64 encoded image string
    """
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG')
    image_bytes = img_buffer.getvalue()
    return img_buffer, image_bytes


def format_time_display(time_seconds):
    """
    Format time duration for display.
    
    Args:
        time_seconds: Time in seconds
        
    Returns:
        str: Formatted time string (ms or s)
    """
    if time_seconds < 1:
        return f"{time_seconds*1000:.0f}ms"
    else:
        return f"{time_seconds:.2f}s"


def is_schema_aware_response(parsed_data):
    """
    Check if parsed JSON data contains schema-aware validation results.
    
    Args:
        parsed_data: Parsed JSON data dictionary
        
    Returns:
        bool: True if response contains validation results structure
    """
    if not isinstance(parsed_data, dict):
        return False
    
    return ('extracted_data' in parsed_data and 
            'validation_results' in parsed_data and
            isinstance(parsed_data['validation_results'], dict))


def extract_validation_info(parsed_data):
    """
    Extract validation information from schema-aware response.
    
    Args:
        parsed_data: Parsed JSON data with validation results
        
    Returns:
        tuple: (extracted_data, validation_results) or (None, None) if not schema-aware
    """
    if not is_schema_aware_response(parsed_data):
        return None, None
    
    extracted_data = parsed_data.get('extracted_data', {})
    validation_results = parsed_data.get('validation_results', {})
    
    return extracted_data, validation_results


def format_schema_aware_response(parsed_data):
    """
    Format schema-aware response for better display.
    
    Args:
        parsed_data: Parsed JSON data with validation results
        
    Returns:
        str: Formatted text for display
    """
    if not is_schema_aware_response(parsed_data):
        return json.dumps(parsed_data, indent=2, ensure_ascii=False)
    
    extracted_data, validation_results = extract_validation_info(parsed_data)
    
    # Create a more readable format
    formatted_sections = []
    
    # Extracted Data section
    formatted_sections.append("📊 EXTRACTED DATA:")
    for field_name, field_value in extracted_data.items():
        formatted_sections.append(f"  • {field_name}: {field_value}")
    
    formatted_sections.append("\n🔍 VALIDATION RESULTS:")
    for field_name, validation in validation_results.items():
        status = validation.get('status', 'unknown')
        message = validation.get('message', 'No details')
        confidence = validation.get('confidence', 0.0)
        
        status_icons = {
            'valid': '✅',
            'invalid': '❌',
            'warning': '⚠️',
            'missing': '❓'
        }
        icon = status_icons.get(status, '❔')
        
        formatted_sections.append(f"  {icon} {field_name}: {status.upper()}")
        formatted_sections.append(f"     {message}")
        if confidence > 0:
            formatted_sections.append(f"     Confidence: {confidence:.1%}")
    
    return "\n".join(formatted_sections)


def clear_session_state():
    """Clear all result-related session state variables."""
    keys_to_clear = [
        'ocr_result', 'provider_used', 'is_json_result', 
        'parsed_data', 'formatted_result', 'current_image', 
        'processing_time', 'token_usage', 'cost_data',
        'selected_document_type', 'selected_document_type_name'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]