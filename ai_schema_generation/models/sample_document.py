"""
T021: SampleDocument model
Represents uploaded documents used for AI schema generation
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib
import json


@dataclass
class SampleDocument:
    """Sample document uploaded for AI schema generation."""

    id: str
    filename: str
    file_type: str  # 'pdf' | 'image'
    file_size: int
    content_hash: str
    upload_timestamp: datetime
    processing_status: str  # 'pending' | 'processing' | 'completed' | 'failed'
    file_data: bytes = field(repr=False)  # Don't show in repr for large files
    page_count: Optional[int] = None
    processed_images: List[str] = field(default_factory=list)  # Base64 encoded images

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_session_id: Optional[str] = None

    def __post_init__(self):
        """Validate document data after initialization"""
        if self.file_type not in ['pdf', 'image']:
            raise ValueError(f"Invalid file_type: {self.file_type}. Must be 'pdf' or 'image'")

        if self.processing_status not in ['pending', 'processing', 'completed', 'failed']:
            raise ValueError(f"Invalid processing_status: {self.processing_status}")

        if self.file_size <= 0:
            raise ValueError("file_size must be positive")

        # Validate content hash if provided
        if self.content_hash and self.file_data:
            expected_hash = self._calculate_content_hash(self.file_data)
            if self.content_hash != expected_hash:
                raise ValueError("Content hash mismatch")

    @classmethod
    def from_upload(cls, filename: str, file_data: bytes, user_session_id: Optional[str] = None) -> 'SampleDocument':
        """Create SampleDocument from uploaded file data"""
        import uuid
        from pathlib import Path

        # Generate unique ID
        doc_id = str(uuid.uuid4())

        # Determine file type from extension
        file_extension = Path(filename).suffix.lower()
        if file_extension == '.pdf':
            file_type = 'pdf'
        elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            file_type = 'image'
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

        # Calculate content hash
        content_hash = cls._calculate_content_hash(file_data)

        # Count pages for PDF
        page_count = None
        if file_type == 'pdf':
            page_count = cls._count_pdf_pages(file_data)

        return cls(
            id=doc_id,
            filename=filename,
            file_type=file_type,
            file_size=len(file_data),
            content_hash=content_hash,
            upload_timestamp=datetime.now(),
            processing_status='pending',
            page_count=page_count,
            file_data=file_data,
            user_session_id=user_session_id
        )

    @staticmethod
    def _calculate_content_hash(file_data: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_data).hexdigest()

    @staticmethod
    def _count_pdf_pages(file_data: bytes) -> int:
        """Count pages in PDF document"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_data, filetype="pdf")
            page_count = len(doc)
            doc.close()
            return page_count
        except Exception:
            # If PyMuPDF fails, try a simple page count estimation
            # This is a fallback for testing when PyMuPDF isn't available
            page_count = file_data.count(b'/Type /Page')
            return max(1, page_count)  # At least 1 page

    def update_processing_status(self, status: str, error_message: Optional[str] = None):
        """Update processing status with optional error message"""
        if status not in ['pending', 'processing', 'completed', 'failed']:
            raise ValueError(f"Invalid status: {status}")

        self.processing_status = status

        if error_message:
            self.metadata['error_message'] = error_message
        elif status == 'completed' and 'error_message' in self.metadata:
            # Clear error message on successful completion
            del self.metadata['error_message']

    def add_processed_image(self, base64_image: str, page_number: Optional[int] = None):
        """Add processed image (base64 encoded) for AI analysis"""
        if page_number is not None:
            # Store with page number for PDFs
            image_entry = f"page_{page_number}:{base64_image}"
        else:
            # Simple storage for single images
            image_entry = base64_image

        self.processed_images.append(image_entry)

    def get_processed_image(self, page_number: Optional[int] = None) -> Optional[str]:
        """Get processed image for specific page or single image"""
        if page_number is not None:
            # Look for specific page
            prefix = f"page_{page_number}:"
            for image_entry in self.processed_images:
                if image_entry.startswith(prefix):
                    return image_entry[len(prefix):]
            return None
        else:
            # Return first image that doesn't have page number
            for image_entry in self.processed_images:
                if not image_entry.startswith("page_"):
                    return image_entry
            # If no plain images, return first one
            if self.processed_images:
                entry = self.processed_images[0]
                if ":" in entry:
                    return entry.split(":", 1)[1]
                return entry
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        data = {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'content_hash': self.content_hash,
            'upload_timestamp': self.upload_timestamp.isoformat(),
            'processing_status': self.processing_status,
            'page_count': self.page_count,
            'processed_images': self.processed_images,
            'metadata': self.metadata,
            'user_session_id': self.user_session_id
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], file_data: Optional[bytes] = None) -> 'SampleDocument':
        """Create from dictionary (for loading from storage)"""
        return cls(
            id=data['id'],
            filename=data['filename'],
            file_type=data['file_type'],
            file_size=data['file_size'],
            content_hash=data['content_hash'],
            upload_timestamp=datetime.fromisoformat(data['upload_timestamp']),
            processing_status=data['processing_status'],
            page_count=data.get('page_count'),
            file_data=file_data or b'',  # File data loaded separately
            processed_images=data.get('processed_images', []),
            metadata=data.get('metadata', {}),
            user_session_id=data.get('user_session_id')
        )

    def is_ready_for_analysis(self) -> bool:
        """Check if document is ready for AI analysis"""
        return (self.processing_status == 'pending' and
                len(self.file_data) > 0 and
                self.file_size > 0)

    def get_display_info(self) -> Dict[str, Any]:
        """Get display information for UI"""
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'upload_time': self.upload_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'processing_status': self.processing_status,
            'page_count': self.page_count,
            'has_processed_images': len(self.processed_images) > 0,
            'error_message': self.metadata.get('error_message')
        }

    def validate_for_analysis(self) -> List[str]:
        """Validate document for analysis and return any issues"""
        issues = []

        if not self.file_data:
            issues.append("No file data available")

        if self.file_size == 0:
            issues.append("File is empty")

        if self.file_size > 50 * 1024 * 1024:  # 50MB limit
            issues.append("File size exceeds maximum limit (50MB)")

        if self.file_type == 'pdf' and not self.page_count:
            issues.append("PDF page count could not be determined")

        return issues