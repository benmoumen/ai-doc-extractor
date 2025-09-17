"""
Document processing service - handles file upload, validation, and conversion
"""

import logging
import time
import base64
from io import BytesIO
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from fastapi import UploadFile, HTTPException, status
from PIL import Image
import fitz  # PyMuPDF

from config import settings
from validators import FileValidator, InputSanitizer

logger = logging.getLogger(__name__)

# Initialize validators
file_validator = FileValidator(
    max_file_size_mb=settings.security.max_file_size_mb,
    max_image_dimension=settings.performance.max_image_dimension
)

input_sanitizer = InputSanitizer()


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
) -> Tuple[bytes, dict]:
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
) -> Tuple[Image.Image, str]:
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