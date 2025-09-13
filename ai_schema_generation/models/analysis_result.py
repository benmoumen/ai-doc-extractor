"""
T022: AIAnalysisResult model
Contains the AI's interpretation of documents with confidence scores and metadata
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import json


@dataclass
class AIAnalysisResult:
    """Result of AI analysis on sample document."""

    id: str
    sample_document_id: str
    analysis_timestamp: datetime
    model_used: str
    processing_time: float  # Processing duration in seconds

    # Document analysis
    detected_document_type: str
    document_type_confidence: float  # 0.0-1.0
    alternative_types: List[Dict[str, Any]] = field(default_factory=list)

    # Structure analysis
    layout_description: str = ""
    field_locations: Dict[str, Dict] = field(default_factory=dict)  # Field positions and bounding boxes
    text_blocks: List[Dict[str, Any]] = field(default_factory=list)  # Identified text blocks

    # Processing metadata
    total_fields_detected: int = 0
    high_confidence_fields: int = 0
    requires_review_count: int = 0
    analysis_notes: List[str] = field(default_factory=list)

    # Quality metrics
    overall_quality_score: float = 0.0  # 0.0-1.0
    confidence_distribution: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Validate analysis result data after initialization"""
        if not (0.0 <= self.document_type_confidence <= 1.0):
            raise ValueError(f"document_type_confidence must be between 0.0 and 1.0, got {self.document_type_confidence}")

        if not (0.0 <= self.overall_quality_score <= 1.0):
            raise ValueError(f"overall_quality_score must be between 0.0 and 1.0, got {self.overall_quality_score}")

        if self.processing_time < 0:
            raise ValueError("processing_time cannot be negative")

        if self.high_confidence_fields > self.total_fields_detected:
            raise ValueError("high_confidence_fields cannot exceed total_fields_detected")

        # Initialize confidence distribution if empty
        if not self.confidence_distribution:
            self.confidence_distribution = {"high": 0, "medium": 0, "low": 0}

    @classmethod
    def create_new(cls, sample_document_id: str, model_used: str, processing_time: float) -> 'AIAnalysisResult':
        """Create new analysis result with basic information"""
        import uuid

        return cls(
            id=str(uuid.uuid4()),
            sample_document_id=sample_document_id,
            analysis_timestamp=datetime.now(),
            model_used=model_used,
            processing_time=processing_time,
            detected_document_type="unknown",
            document_type_confidence=0.0
        )

    def set_document_type_analysis(self, document_type: str, confidence: float, alternatives: Optional[List[Dict[str, Any]]] = None):
        """Set document type analysis results"""
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

        self.detected_document_type = document_type
        self.document_type_confidence = confidence

        if alternatives:
            # Validate alternative types format
            for alt in alternatives:
                if 'type' not in alt or 'confidence' not in alt:
                    raise ValueError("Alternative types must have 'type' and 'confidence' keys")
                if not (0.0 <= alt['confidence'] <= 1.0):
                    raise ValueError(f"Alternative confidence must be between 0.0 and 1.0, got {alt['confidence']}")

            self.alternative_types = alternatives

    def add_text_block(self, text: str, confidence: float, location: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Add identified text block"""
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

        text_block = {
            'text': text,
            'confidence': confidence,
            'location': location or {},
            'metadata': metadata or {}
        }

        self.text_blocks.append(text_block)

    def add_field_location(self, field_name: str, location_data: Dict[str, Any]):
        """Add field location information"""
        required_keys = ['x', 'y', 'width', 'height']
        if not all(key in location_data for key in required_keys):
            raise ValueError(f"Field location must contain: {required_keys}")

        # Validate numeric values
        for key in required_keys:
            if not isinstance(location_data[key], (int, float)) or location_data[key] < 0:
                raise ValueError(f"Location {key} must be a non-negative number")

        self.field_locations[field_name] = location_data

    def update_field_statistics(self, total_detected: int, high_confidence: int, requires_review: int):
        """Update field detection statistics"""
        if total_detected < 0 or high_confidence < 0 or requires_review < 0:
            raise ValueError("Field statistics cannot be negative")

        if high_confidence > total_detected:
            raise ValueError("High confidence fields cannot exceed total detected")

        if requires_review > total_detected:
            raise ValueError("Fields requiring review cannot exceed total detected")

        self.total_fields_detected = total_detected
        self.high_confidence_fields = high_confidence
        self.requires_review_count = requires_review

        # Update confidence distribution
        medium_confidence = total_detected - high_confidence - requires_review
        self.confidence_distribution = {
            "high": high_confidence,
            "medium": max(0, medium_confidence),
            "low": requires_review
        }

    def set_layout_description(self, description: str):
        """Set document layout description"""
        self.layout_description = description

    def add_analysis_note(self, note: str):
        """Add analysis note"""
        if note and note not in self.analysis_notes:
            self.analysis_notes.append(note)

    def calculate_overall_quality_score(self, field_confidences: List[float], layout_quality: float = 0.8) -> float:
        """Calculate overall quality score based on various factors"""
        if not field_confidences:
            quality_score = layout_quality * 0.5  # Lower score if no fields detected
        else:
            # Average field confidence
            avg_field_confidence = sum(field_confidences) / len(field_confidences)

            # Document type confidence weight
            doc_type_weight = min(self.document_type_confidence * 1.2, 1.0)

            # Combine factors
            quality_score = (
                avg_field_confidence * 0.4 +
                doc_type_weight * 0.3 +
                layout_quality * 0.2 +
                (1.0 - self.requires_review_count / max(self.total_fields_detected, 1)) * 0.1
            )

        self.overall_quality_score = max(0.0, min(1.0, quality_score))
        return self.overall_quality_score

    def get_confidence_summary(self) -> Dict[str, Any]:
        """Get summary of confidence levels"""
        return {
            'document_type_confidence': self.document_type_confidence,
            'overall_quality_score': self.overall_quality_score,
            'confidence_distribution': self.confidence_distribution.copy(),
            'high_confidence_ratio': self.high_confidence_fields / max(self.total_fields_detected, 1),
            'review_required_ratio': self.requires_review_count / max(self.total_fields_detected, 1)
        }

    def get_processing_summary(self) -> Dict[str, Any]:
        """Get processing summary information"""
        return {
            'model_used': self.model_used,
            'processing_time': self.processing_time,
            'analysis_timestamp': self.analysis_timestamp,
            'total_fields_detected': self.total_fields_detected,
            'text_blocks_found': len(self.text_blocks),
            'field_locations_mapped': len(self.field_locations),
            'analysis_notes_count': len(self.analysis_notes)
        }

    def is_analysis_successful(self) -> bool:
        """Check if analysis was successful enough for schema generation"""
        return (
            self.overall_quality_score > 0.3 and
            self.total_fields_detected > 0 and
            self.document_type_confidence > 0.5
        )

    def get_review_priority_fields(self) -> List[str]:
        """Get list of field names that should be prioritized for review"""
        # This would be populated by field extraction process
        # For now, return fields from locations that might need review based on confidence
        low_confidence_fields = []

        for field_name, location in self.field_locations.items():
            # If location has confidence info and it's low, prioritize for review
            if 'confidence' in location and location['confidence'] < 0.6:
                low_confidence_fields.append(field_name)

        return low_confidence_fields

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            'id': self.id,
            'sample_document_id': self.sample_document_id,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'model_used': self.model_used,
            'processing_time': self.processing_time,
            'detected_document_type': self.detected_document_type,
            'document_type_confidence': self.document_type_confidence,
            'alternative_types': self.alternative_types,
            'layout_description': self.layout_description,
            'field_locations': self.field_locations,
            'text_blocks': self.text_blocks,
            'total_fields_detected': self.total_fields_detected,
            'high_confidence_fields': self.high_confidence_fields,
            'requires_review_count': self.requires_review_count,
            'analysis_notes': self.analysis_notes,
            'overall_quality_score': self.overall_quality_score,
            'confidence_distribution': self.confidence_distribution
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIAnalysisResult':
        """Create from dictionary (for loading from storage)"""
        return cls(
            id=data['id'],
            sample_document_id=data['sample_document_id'],
            analysis_timestamp=datetime.fromisoformat(data['analysis_timestamp']),
            model_used=data['model_used'],
            processing_time=data['processing_time'],
            detected_document_type=data['detected_document_type'],
            document_type_confidence=data['document_type_confidence'],
            alternative_types=data.get('alternative_types', []),
            layout_description=data.get('layout_description', ''),
            field_locations=data.get('field_locations', {}),
            text_blocks=data.get('text_blocks', []),
            total_fields_detected=data.get('total_fields_detected', 0),
            high_confidence_fields=data.get('high_confidence_fields', 0),
            requires_review_count=data.get('requires_review_count', 0),
            analysis_notes=data.get('analysis_notes', []),
            overall_quality_score=data.get('overall_quality_score', 0.0),
            confidence_distribution=data.get('confidence_distribution', {"high": 0, "medium": 0, "low": 0})
        )