"""
Input validation and sanitization utilities
"""

import os
import hashlib
import magic
from typing import Optional, Tuple, BinaryIO
from PIL import Image
import fitz  # PyMuPDF
from io import BytesIO

class FileValidator:
    """Validate and sanitize uploaded files"""

    ALLOWED_MIME_TYPES = {
        'application/pdf': {'extensions': ['pdf'], 'magic': b'%PDF'},
        'image/jpeg': {'extensions': ['jpg', 'jpeg'], 'magic': b'\xFF\xD8\xFF'},
        'image/png': {'extensions': ['png'], 'magic': b'\x89PNG\r\n\x1a\n'},
        'image/tiff': {'extensions': ['tiff', 'tif'], 'magic': [b'II*\x00', b'MM\x00*']},
        'image/bmp': {'extensions': ['bmp'], 'magic': b'BM'}
    }

    def __init__(self, max_file_size_mb: int = 10, max_image_dimension: int = 4096):
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.max_image_dimension = max_image_dimension

    def validate_file_size(self, file_data: bytes) -> Tuple[bool, Optional[str]]:
        """Validate file size"""
        if len(file_data) > self.max_file_size:
            size_mb = len(file_data) / (1024 * 1024)
            return False, f"File size {size_mb:.1f}MB exceeds maximum of {self.max_file_size / (1024 * 1024):.0f}MB"
        return True, None

    def validate_file_extension(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate file extension"""
        if not filename or '.' not in filename:
            return False, "Invalid filename"

        extension = filename.lower().split('.')[-1]
        valid_extensions = []
        for mime_info in self.ALLOWED_MIME_TYPES.values():
            valid_extensions.extend(mime_info['extensions'])

        if extension not in valid_extensions:
            return False, f"File extension '{extension}' not allowed. Allowed: {', '.join(valid_extensions)}"

        return True, None

    def validate_mime_type(self, file_data: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate MIME type using python-magic"""
        try:
            # Use python-magic to detect MIME type
            detected_mime = magic.from_buffer(file_data, mime=True)

            if detected_mime not in self.ALLOWED_MIME_TYPES:
                return False, f"File type '{detected_mime}' not allowed"

            # Additional validation: check file signature
            for mime_type, info in self.ALLOWED_MIME_TYPES.items():
                if detected_mime == mime_type:
                    magic_bytes = info['magic']
                    if isinstance(magic_bytes, list):
                        # Handle multiple possible magic bytes (e.g., TIFF)
                        if not any(file_data.startswith(mb) for mb in magic_bytes):
                            return False, "File signature does not match detected type"
                    else:
                        if not file_data.startswith(magic_bytes):
                            return False, "File signature does not match detected type"
                    break

            return True, None

        except Exception as e:
            return False, f"Could not determine file type: {str(e)}"

    def validate_pdf(self, file_data: bytes) -> Tuple[bool, Optional[str]]:
        """Validate PDF file integrity"""
        try:
            # Try to open PDF
            doc = fitz.open(stream=file_data, filetype="pdf")

            # Check for encrypted PDFs
            if doc.is_encrypted:
                doc.close()
                return False, "Encrypted PDFs are not supported"

            # Check page count
            if len(doc) == 0:
                doc.close()
                return False, "PDF has no pages"

            if len(doc) > 100:  # Reasonable limit for document processing
                doc.close()
                return False, f"PDF has {len(doc)} pages, maximum 100 allowed"

            # Try to render first page (will fail if corrupted)
            page = doc.load_page(0)
            _ = page.get_pixmap()

            doc.close()
            return True, None

        except Exception as e:
            return False, f"Invalid or corrupted PDF: {str(e)}"

    def validate_image(self, file_data: bytes) -> Tuple[bool, Optional[str]]:
        """Validate image file and check dimensions"""
        try:
            # Try to open image
            image = Image.open(BytesIO(file_data))

            # Verify the image (will raise exception if corrupted)
            image.verify()

            # Re-open for dimension check (verify() closes the file)
            image = Image.open(BytesIO(file_data))

            # Check dimensions
            width, height = image.size
            if width > self.max_image_dimension or height > self.max_image_dimension:
                return False, (
                    f"Image dimensions {width}x{height} exceed maximum "
                    f"{self.max_image_dimension}x{self.max_image_dimension}"
                )

            # Check for suspicious image properties
            if width < 10 or height < 10:
                return False, "Image is too small (minimum 10x10 pixels)"

            # Check image mode (detect unusual formats)
            suspicious_modes = ['P', 'PA', 'LAB', 'HSV']
            if image.mode in suspicious_modes:
                # Convert to RGB for safety
                try:
                    image = image.convert('RGB')
                except:
                    return False, f"Unsupported image mode: {image.mode}"

            return True, None

        except Exception as e:
            return False, f"Invalid or corrupted image: {str(e)}"

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal and other attacks"""
        # Remove any directory components
        filename = os.path.basename(filename)

        # Remove any non-alphanumeric characters except dot and dash
        import re
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Limit length
        name, ext = os.path.splitext(filename)
        if len(name) > 50:
            name = name[:50]
        filename = name + ext

        # Add timestamp to ensure uniqueness
        import time
        timestamp = str(int(time.time()))
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"

        return filename

    def calculate_file_hash(self, file_data: bytes) -> str:
        """Calculate SHA-256 hash of file for deduplication"""
        return hashlib.sha256(file_data).hexdigest()

    def validate_file(self, file_data: bytes, filename: str) -> Tuple[bool, Optional[str], dict]:
        """
        Comprehensive file validation
        Returns: (is_valid, error_message, metadata)
        """
        metadata = {
            'original_filename': filename,
            'sanitized_filename': self.sanitize_filename(filename),
            'file_size': len(file_data),
            'file_hash': self.calculate_file_hash(file_data)
        }

        # Check file size
        valid, error = self.validate_file_size(file_data)
        if not valid:
            return False, error, metadata

        # Check extension
        valid, error = self.validate_file_extension(filename)
        if not valid:
            return False, error, metadata

        # Check MIME type
        valid, error = self.validate_mime_type(file_data, filename)
        if not valid:
            return False, error, metadata

        # Detect file type for specific validation
        detected_mime = magic.from_buffer(file_data, mime=True)
        metadata['mime_type'] = detected_mime

        # Type-specific validation
        if detected_mime == 'application/pdf':
            valid, error = self.validate_pdf(file_data)
            if not valid:
                return False, error, metadata
            metadata['file_type'] = 'pdf'

        elif detected_mime.startswith('image/'):
            valid, error = self.validate_image(file_data)
            if not valid:
                return False, error, metadata
            metadata['file_type'] = 'image'

            # Get image metadata
            try:
                image = Image.open(BytesIO(file_data))
                metadata['image_width'] = image.width
                metadata['image_height'] = image.height
                metadata['image_mode'] = image.mode
                metadata['image_format'] = image.format
            except:
                pass

        return True, None, metadata


class InputSanitizer:
    """Sanitize user inputs to prevent injection attacks"""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not value:
            return ""

        # Truncate to max length
        value = value[:max_length]

        # Remove null bytes
        value = value.replace('\x00', '')

        # Strip whitespace
        value = value.strip()

        # Remove control characters
        import unicodedata
        value = ''.join(ch for ch in value if unicodedata.category(ch)[0] != 'C')

        return value

    @staticmethod
    def sanitize_json_field(value: any) -> any:
        """Sanitize JSON field values recursively"""
        if isinstance(value, str):
            return InputSanitizer.sanitize_string(value)
        elif isinstance(value, dict):
            return {k: InputSanitizer.sanitize_json_field(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [InputSanitizer.sanitize_json_field(item) for item in value]
        else:
            return value