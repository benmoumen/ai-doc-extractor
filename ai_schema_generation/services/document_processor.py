"""
T030: DocumentProcessor
Service for preprocessing uploaded documents before AI analysis
"""

import hashlib
import base64
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
import tempfile
import os

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from ..models.sample_document import SampleDocument
from ..storage.sample_document_storage import SampleDocumentStorage


class DocumentProcessingError(Exception):
    """Custom exception for document processing errors"""
    pass


class DocumentProcessor:
    """Service for processing and preparing documents for AI analysis."""

    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    SUPPORTED_PDF_FORMAT = {'.pdf'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_IMAGE_DIMENSION = 4096  # pixels

    def __init__(self, storage: Optional[SampleDocumentStorage] = None):
        """Initialize document processor"""
        self.storage = storage or SampleDocumentStorage()
        self._validate_dependencies()

    def _validate_dependencies(self):
        """Validate required dependencies"""
        if not PIL_AVAILABLE:
            raise ImportError("PIL (Pillow) is required for image processing")

        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF is required for PDF processing")

    def process_upload(self, file_content: bytes, filename: str, metadata: Optional[Dict[str, Any]] = None) -> SampleDocument:
        """
        Process uploaded file and create SampleDocument

        Args:
            file_content: Raw file bytes
            filename: Original filename
            metadata: Optional metadata dict

        Returns:
            SampleDocument instance

        Raises:
            DocumentProcessingError: If processing fails
        """
        try:
            # Validate file
            self._validate_file(file_content, filename)

            # Determine file type
            file_type = self._detect_file_type(filename, file_content)

            # Calculate content hash
            content_hash = self._calculate_hash(file_content)

            # Check for duplicates
            existing_doc = self.storage.get_by_content_hash(content_hash)
            if existing_doc:
                return existing_doc

            # Create document model
            document = SampleDocument.create_from_upload(
                filename=filename,
                file_type=file_type,
                file_size=len(file_content),
                content_hash=content_hash,
                metadata=metadata or {}
            )

            # Save file content to temporary storage
            document.file_path = self._save_temporary_file(file_content, filename, document.id)

            # Perform initial processing
            processed_metadata = self._extract_initial_metadata(file_content, file_type, filename)
            document.metadata.update(processed_metadata)

            # Validate processed document
            self._validate_processed_document(document, file_content)

            # Save to storage
            self.storage.save(document)

            return document

        except Exception as e:
            raise DocumentProcessingError(f"Failed to process document {filename}: {str(e)}")

    def prepare_for_analysis(self, document_id: str) -> Dict[str, Any]:
        """
        Prepare document for AI analysis

        Args:
            document_id: Document ID

        Returns:
            Dict containing document data ready for AI analysis

        Raises:
            DocumentProcessingError: If preparation fails
        """
        document = self.storage.get_by_id(document_id)
        if not document:
            raise DocumentProcessingError(f"Document {document_id} not found")

        if not document.file_path or not Path(document.file_path).exists():
            raise DocumentProcessingError(f"File not found for document {document_id}")

        try:
            # Update status
            self.storage.update_status(document_id, 'preparing')

            # Load file content
            with open(document.file_path, 'rb') as f:
                file_content = f.read()

            # Prepare based on file type
            if document.file_type == 'pdf':
                prepared_data = self._prepare_pdf_for_analysis(file_content, document)
            elif document.file_type == 'image':
                prepared_data = self._prepare_image_for_analysis(file_content, document)
            else:
                raise DocumentProcessingError(f"Unsupported file type: {document.file_type}")

            # Update status
            self.storage.update_status(document_id, 'ready_for_analysis')

            return {
                'document': document.to_dict(),
                'prepared_data': prepared_data
            }

        except Exception as e:
            self.storage.update_status(document_id, 'preparation_failed', str(e))
            raise DocumentProcessingError(f"Failed to prepare document {document_id}: {str(e)}")

    def _validate_file(self, file_content: bytes, filename: str):
        """Validate uploaded file"""
        if not file_content:
            raise DocumentProcessingError("Empty file content")

        if len(file_content) > self.MAX_FILE_SIZE:
            raise DocumentProcessingError(f"File too large: {len(file_content)} bytes (max: {self.MAX_FILE_SIZE})")

        file_ext = Path(filename).suffix.lower()
        supported_formats = self.SUPPORTED_IMAGE_FORMATS | self.SUPPORTED_PDF_FORMAT

        if file_ext not in supported_formats:
            raise DocumentProcessingError(f"Unsupported file format: {file_ext}")

    def _detect_file_type(self, filename: str, file_content: bytes) -> str:
        """Detect file type from filename and content"""
        file_ext = Path(filename).suffix.lower()

        if file_ext in self.SUPPORTED_PDF_FORMAT:
            # Verify PDF magic number
            if file_content.startswith(b'%PDF'):
                return 'pdf'
            else:
                raise DocumentProcessingError("Invalid PDF file")

        elif file_ext in self.SUPPORTED_IMAGE_FORMATS:
            # Verify it's a valid image
            try:
                Image.open(io.BytesIO(file_content)).verify()
                return 'image'
            except Exception:
                raise DocumentProcessingError("Invalid image file")

        else:
            raise DocumentProcessingError(f"Unsupported file extension: {file_ext}")

    def _calculate_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()

    def _save_temporary_file(self, file_content: bytes, filename: str, document_id: str) -> str:
        """Save file content to temporary storage"""
        # Create temporary directory structure
        temp_dir = Path(tempfile.gettempdir()) / "ai_schema_generation" / "documents"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Create unique filename
        file_ext = Path(filename).suffix
        temp_filename = f"{document_id}{file_ext}"
        temp_path = temp_dir / temp_filename

        # Write file
        with open(temp_path, 'wb') as f:
            f.write(file_content)

        return str(temp_path)

    def _extract_initial_metadata(self, file_content: bytes, file_type: str, filename: str) -> Dict[str, Any]:
        """Extract initial metadata from file"""
        metadata = {
            'original_filename': filename,
            'processed_timestamp': datetime.now().isoformat(),
            'file_type': file_type
        }

        try:
            if file_type == 'pdf':
                metadata.update(self._extract_pdf_metadata(file_content))
            elif file_type == 'image':
                metadata.update(self._extract_image_metadata(file_content))
        except Exception as e:
            metadata['metadata_extraction_error'] = str(e)

        return metadata

    def _extract_pdf_metadata(self, file_content: bytes) -> Dict[str, Any]:
        """Extract metadata from PDF"""
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            metadata = {
                'page_count': doc.page_count,
                'pdf_metadata': doc.metadata,
                'page_dimensions': []
            }

            # Get dimensions of first few pages
            for page_num in range(min(3, doc.page_count)):
                page = doc[page_num]
                rect = page.rect
                metadata['page_dimensions'].append({
                    'page': page_num + 1,
                    'width': rect.width,
                    'height': rect.height
                })

            doc.close()
            return metadata

        except Exception as e:
            return {'pdf_metadata_error': str(e)}

    def _extract_image_metadata(self, file_content: bytes) -> Dict[str, Any]:
        """Extract metadata from image"""
        try:
            import io

            with Image.open(io.BytesIO(file_content)) as img:
                metadata = {
                    'image_format': img.format,
                    'image_mode': img.mode,
                    'image_dimensions': {
                        'width': img.width,
                        'height': img.height
                    }
                }

                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    try:
                        exif_data = img._getexif()
                        if exif_data:
                            metadata['exif_data'] = dict(exif_data)
                    except Exception:
                        pass

                return metadata

        except Exception as e:
            return {'image_metadata_error': str(e)}

    def _validate_processed_document(self, document: SampleDocument, file_content: bytes):
        """Validate processed document meets requirements"""
        if document.file_type == 'image':
            # Validate image dimensions
            try:
                import io
                with Image.open(io.BytesIO(file_content)) as img:
                    if img.width > self.MAX_IMAGE_DIMENSION or img.height > self.MAX_IMAGE_DIMENSION:
                        raise DocumentProcessingError(
                            f"Image too large: {img.width}x{img.height} "
                            f"(max: {self.MAX_IMAGE_DIMENSION}x{self.MAX_IMAGE_DIMENSION})"
                        )
            except Exception as e:
                if isinstance(e, DocumentProcessingError):
                    raise
                raise DocumentProcessingError(f"Image validation failed: {str(e)}")

    def _prepare_pdf_for_analysis(self, file_content: bytes, document: SampleDocument) -> Dict[str, Any]:
        """Prepare PDF for AI analysis"""
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")

            prepared_data = {
                'type': 'pdf',
                'page_count': doc.page_count,
                'pages': []
            }

            # Convert each page to image for AI analysis
            for page_num in range(doc.page_count):
                page = doc[page_num]

                # Render page to image
                mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")

                # Encode to base64
                img_base64 = base64.b64encode(img_data).decode('utf-8')

                prepared_data['pages'].append({
                    'page_number': page_num + 1,
                    'image_base64': img_base64,
                    'dimensions': {
                        'width': pix.width,
                        'height': pix.height
                    }
                })

                pix = None  # Free memory

            doc.close()

            # Include full document as base64 for reference
            prepared_data['full_document_base64'] = base64.b64encode(file_content).decode('utf-8')

            return prepared_data

        except Exception as e:
            raise DocumentProcessingError(f"PDF preparation failed: {str(e)}")

    def _prepare_image_for_analysis(self, file_content: bytes, document: SampleDocument) -> Dict[str, Any]:
        """Prepare image for AI analysis"""
        try:
            import io

            # Optimize image for AI analysis
            with Image.open(io.BytesIO(file_content)) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize if too large
                max_dim = 2048  # Suitable for AI analysis
                if img.width > max_dim or img.height > max_dim:
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

                # Save optimized image
                output_buffer = io.BytesIO()
                img.save(output_buffer, format='PNG', optimize=True)
                optimized_content = output_buffer.getvalue()

            # Encode to base64
            img_base64 = base64.b64encode(optimized_content).decode('utf-8')

            return {
                'type': 'image',
                'image_base64': img_base64,
                'dimensions': {
                    'width': img.width,
                    'height': img.height
                },
                'optimized': len(optimized_content) < len(file_content),
                'original_size': len(file_content),
                'processed_size': len(optimized_content)
            }

        except Exception as e:
            raise DocumentProcessingError(f"Image preparation failed: {str(e)}")

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get document processing statistics"""
        stats = self.storage.get_stats()

        # Add processing-specific stats
        processing_stats = {
            'supported_formats': {
                'images': list(self.SUPPORTED_IMAGE_FORMATS),
                'documents': list(self.SUPPORTED_PDF_FORMAT)
            },
            'limits': {
                'max_file_size_mb': self.MAX_FILE_SIZE / (1024 * 1024),
                'max_image_dimension': self.MAX_IMAGE_DIMENSION
            },
            'dependencies': {
                'pil_available': PIL_AVAILABLE,
                'pymupdf_available': PYMUPDF_AVAILABLE
            }
        }

        stats.update(processing_stats)
        return stats

    def cleanup_temporary_files(self, older_than_hours: int = 24) -> int:
        """Clean up temporary files older than specified hours"""
        temp_dir = Path(tempfile.gettempdir()) / "ai_schema_generation" / "documents"

        if not temp_dir.exists():
            return 0

        cleaned_count = 0
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)

        try:
            for file_path in temp_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
        except Exception:
            pass  # Ignore cleanup errors

        return cleaned_count

    def validate_document_integrity(self, document_id: str) -> Dict[str, Any]:
        """Validate document file integrity"""
        document = self.storage.get_by_id(document_id)
        if not document:
            return {'valid': False, 'error': 'Document not found'}

        if not document.file_path or not Path(document.file_path).exists():
            return {'valid': False, 'error': 'File not found'}

        try:
            # Read file and verify hash
            with open(document.file_path, 'rb') as f:
                file_content = f.read()

            current_hash = self._calculate_hash(file_content)
            hash_matches = current_hash == document.content_hash

            # Basic format validation
            format_valid = True
            format_error = None

            try:
                if document.file_type == 'pdf':
                    doc = fitz.open(stream=file_content, filetype="pdf")
                    doc.close()
                elif document.file_type == 'image':
                    import io
                    with Image.open(io.BytesIO(file_content)) as img:
                        img.verify()
            except Exception as e:
                format_valid = False
                format_error = str(e)

            return {
                'valid': hash_matches and format_valid,
                'hash_matches': hash_matches,
                'format_valid': format_valid,
                'format_error': format_error,
                'file_size': len(file_content),
                'expected_hash': document.content_hash,
                'actual_hash': current_hash
            }

        except Exception as e:
            return {'valid': False, 'error': str(e)}