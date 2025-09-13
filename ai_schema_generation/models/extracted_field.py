"""
T023: ExtractedField model
Individual field definitions derived from document analysis
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import json


@dataclass
class ExtractedField:
    """Field extracted from document analysis."""

    id: str
    analysis_result_id: str

    # Field identification
    detected_name: str
    display_name: str
    field_type: str
    source_text: Optional[str] = None

    # Confidence scoring (0.0-1.0)
    visual_clarity_score: float = 0.0
    label_confidence_score: float = 0.0
    value_confidence_score: float = 0.0
    type_confidence_score: float = 0.0
    context_confidence_score: float = 0.0
    overall_confidence_score: float = 0.0

    # Location and context
    bounding_box: Optional[Dict[str, float]] = None
    page_number: Optional[int] = None
    context_description: str = ""

    # Field properties
    is_required: bool = False
    has_validation_hints: bool = False
    field_group: Optional[str] = None

    # Alternative interpretations
    alternative_names: List[str] = field(default_factory=list)
    alternative_types: List[Dict[str, float]] = field(default_factory=list)

    # Processing metadata
    extraction_method: str = "ai_ocr_analysis"
    requires_review: bool = False
    review_reason: Optional[str] = None

    def __post_init__(self):
        """Validate field data after initialization"""
        # Validate confidence scores
        confidence_fields = [
            'visual_clarity_score', 'label_confidence_score', 'value_confidence_score',
            'type_confidence_score', 'context_confidence_score', 'overall_confidence_score'
        ]

        for field_name in confidence_fields:
            score = getattr(self, field_name)
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {score}")

        # Validate field type
        valid_types = ['string', 'number', 'date', 'boolean', 'email', 'phone', 'url', 'currency']
        if self.field_type not in valid_types:
            raise ValueError(f"Invalid field_type: {self.field_type}. Must be one of {valid_types}")

        # Validate bounding box if provided
        if self.bounding_box:
            required_keys = ['x', 'y', 'width', 'height']
            for key in required_keys:
                if key not in self.bounding_box:
                    raise ValueError(f"Bounding box missing required key: {key}")
                if not isinstance(self.bounding_box[key], (int, float)) or self.bounding_box[key] < 0:
                    raise ValueError(f"Bounding box {key} must be a non-negative number")

        # Auto-calculate overall confidence if not set
        if self.overall_confidence_score == 0.0:
            self.overall_confidence_score = self._calculate_overall_confidence()

        # Auto-determine if review is needed
        if not self.requires_review and self.overall_confidence_score < 0.6:
            self.requires_review = True
            if not self.review_reason:
                self.review_reason = "Low overall confidence score"

    def _calculate_overall_confidence(self) -> float:
        """Calculate overall confidence from individual scores"""
        individual_scores = [
            self.visual_clarity_score,
            self.label_confidence_score,
            self.value_confidence_score,
            self.type_confidence_score,
            self.context_confidence_score
        ]

        # Filter out zero scores (not all may be applicable)
        non_zero_scores = [score for score in individual_scores if score > 0.0]

        if not non_zero_scores:
            return 0.0

        return sum(non_zero_scores) / len(non_zero_scores)

    @classmethod
    def create_from_analysis(
        cls,
        analysis_result_id: str,
        detected_name: str,
        field_type: str,
        source_text: Optional[str] = None,
        confidence_scores: Optional[Dict[str, float]] = None
    ) -> 'ExtractedField':
        """Create field from analysis results"""
        import uuid

        # Generate display name from detected name
        display_name = detected_name.replace('_', ' ').title()

        # Set confidence scores
        scores = confidence_scores or {}

        field = cls(
            id=str(uuid.uuid4()),
            analysis_result_id=analysis_result_id,
            detected_name=detected_name,
            display_name=display_name,
            field_type=field_type,
            source_text=source_text,
            visual_clarity_score=scores.get('visual_clarity', 0.0),
            label_confidence_score=scores.get('label_confidence', 0.0),
            value_confidence_score=scores.get('value_confidence', 0.0),
            type_confidence_score=scores.get('type_confidence', 0.0),
            context_confidence_score=scores.get('context_confidence', 0.0)
        )

        return field

    def set_location(self, x: float, y: float, width: float, height: float, page_number: Optional[int] = None):
        """Set field location in document"""
        if any(val < 0 for val in [x, y, width, height]):
            raise ValueError("Location coordinates must be non-negative")

        self.bounding_box = {
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }

        if page_number is not None:
            self.page_number = page_number

    def add_alternative_name(self, alternative_name: str):
        """Add alternative field name interpretation"""
        if alternative_name and alternative_name not in self.alternative_names:
            self.alternative_names.append(alternative_name)

    def add_alternative_type(self, field_type: str, confidence: float):
        """Add alternative field type interpretation"""
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

        valid_types = ['string', 'number', 'date', 'boolean', 'email', 'phone', 'url', 'currency']
        if field_type not in valid_types:
            raise ValueError(f"Invalid field_type: {field_type}")

        # Check if type already exists
        for alt_type in self.alternative_types:
            if alt_type.get('type') == field_type:
                alt_type['confidence'] = confidence
                return

        # Add new alternative type
        self.alternative_types.append({
            'type': field_type,
            'confidence': confidence
        })

    def set_field_group(self, group_name: str):
        """Set logical field group (e.g., 'header', 'billing', 'totals')"""
        self.field_group = group_name

    def mark_for_review(self, reason: str):
        """Mark field for manual review"""
        self.requires_review = True
        self.review_reason = reason

    def clear_review_flag(self):
        """Clear review requirement"""
        self.requires_review = False
        self.review_reason = None

    def get_confidence_level(self) -> str:
        """Get confidence level as string"""
        if self.overall_confidence_score >= 0.8:
            return "high"
        elif self.overall_confidence_score >= 0.6:
            return "medium"
        else:
            return "low"

    def get_confidence_color(self) -> str:
        """Get color for UI confidence display"""
        confidence_level = self.get_confidence_level()
        color_map = {
            "high": "green",
            "medium": "orange",
            "low": "red"
        }
        return color_map[confidence_level]

    def update_from_user_feedback(self, feedback: Dict[str, Any]):
        """Update field based on user feedback"""
        if 'display_name' in feedback:
            self.display_name = feedback['display_name']

        if 'field_type' in feedback:
            valid_types = ['string', 'number', 'date', 'boolean', 'email', 'phone', 'url', 'currency']
            if feedback['field_type'] in valid_types:
                self.field_type = feedback['field_type']

        if 'is_required' in feedback:
            self.is_required = bool(feedback['is_required'])

        if 'user_confidence' in feedback:
            # User feedback can override AI confidence
            user_conf = float(feedback['user_confidence'])
            if 0.0 <= user_conf <= 1.0:
                # Boost overall confidence with user input
                self.overall_confidence_score = min(1.0, (self.overall_confidence_score + user_conf) / 2)

        # Clear review flag if user provides feedback
        if self.requires_review:
            self.clear_review_flag()

    def get_validation_hints(self) -> List[str]:
        """Get validation hints based on field characteristics"""
        hints = []

        if self.field_type == 'email':
            hints.append("Should contain @ symbol and domain")

        elif self.field_type == 'phone':
            hints.append("Should contain digits and optional formatting")

        elif self.field_type == 'date':
            hints.append("Should be in recognizable date format")

        elif self.field_type == 'number' or self.field_type == 'currency':
            hints.append("Should contain only digits and decimal point")

        elif self.field_type == 'url':
            hints.append("Should start with http:// or https://")

        # Add hints based on source text
        if self.source_text:
            if len(self.source_text) < 2:
                hints.append("Very short text - verify completeness")
            elif len(self.source_text) > 100:
                hints.append("Long text - consider if it should be multiple fields")

        return hints

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            'id': self.id,
            'analysis_result_id': self.analysis_result_id,
            'detected_name': self.detected_name,
            'display_name': self.display_name,
            'field_type': self.field_type,
            'source_text': self.source_text,
            'visual_clarity_score': self.visual_clarity_score,
            'label_confidence_score': self.label_confidence_score,
            'value_confidence_score': self.value_confidence_score,
            'type_confidence_score': self.type_confidence_score,
            'context_confidence_score': self.context_confidence_score,
            'overall_confidence_score': self.overall_confidence_score,
            'bounding_box': self.bounding_box,
            'page_number': self.page_number,
            'context_description': self.context_description,
            'is_required': self.is_required,
            'has_validation_hints': self.has_validation_hints,
            'field_group': self.field_group,
            'alternative_names': self.alternative_names,
            'alternative_types': self.alternative_types,
            'extraction_method': self.extraction_method,
            'requires_review': self.requires_review,
            'review_reason': self.review_reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractedField':
        """Create from dictionary (for loading from storage)"""
        return cls(
            id=data['id'],
            analysis_result_id=data['analysis_result_id'],
            detected_name=data['detected_name'],
            display_name=data['display_name'],
            field_type=data['field_type'],
            source_text=data.get('source_text'),
            visual_clarity_score=data.get('visual_clarity_score', 0.0),
            label_confidence_score=data.get('label_confidence_score', 0.0),
            value_confidence_score=data.get('value_confidence_score', 0.0),
            type_confidence_score=data.get('type_confidence_score', 0.0),
            context_confidence_score=data.get('context_confidence_score', 0.0),
            overall_confidence_score=data.get('overall_confidence_score', 0.0),
            bounding_box=data.get('bounding_box'),
            page_number=data.get('page_number'),
            context_description=data.get('context_description', ''),
            is_required=data.get('is_required', False),
            has_validation_hints=data.get('has_validation_hints', False),
            field_group=data.get('field_group'),
            alternative_names=data.get('alternative_names', []),
            alternative_types=data.get('alternative_types', []),
            extraction_method=data.get('extraction_method', 'ai_ocr_analysis'),
            requires_review=data.get('requires_review', False),
            review_reason=data.get('review_reason')
        )