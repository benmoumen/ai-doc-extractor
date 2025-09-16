"""
T026: GeneratedSchema model
Schema generated from AI analysis, extending the existing Schema model concept
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import json


@dataclass
class GeneratedSchema:
    """Schema generated from AI analysis, extends existing Schema model."""

    # Core schema properties (from existing Schema model)
    id: str
    name: str
    description: str = ""
    fields: Dict[str, Any] = field(default_factory=dict)

    # AI generation specific fields
    source_document_id: str = ""
    analysis_result_id: str = ""
    generation_method: str = "ai_generated"  # 'ai_generated' | 'ai_assisted' | 'manual_refined'

    # Generation metadata
    generated_timestamp: datetime = field(default_factory=datetime.now)
    ai_model_used: str = ""
    generation_confidence: float = 0.0  # Overall confidence in generated schema

    # Quality metrics
    total_fields_generated: int = 0
    high_confidence_fields: int = 0
    user_modified_fields: List[str] = field(default_factory=list)
    validation_status: str = "pending"  # 'pending' | 'partial' | 'complete' | 'failed'

    # User interaction
    user_review_status: str = "pending"  # 'pending' | 'in_progress' | 'reviewed' | 'approved'
    review_notes: Optional[str] = None
    last_modified_by: str = "ai"  # 'ai' | 'user'

    # Improvement tracking
    accuracy_feedback: Optional[Dict[str, float]] = None
    suggested_improvements: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate generated schema data"""
        if not (0.0 <= self.generation_confidence <= 1.0):
            raise ValueError(f"generation_confidence must be between 0.0 and 1.0, got {self.generation_confidence}")

        # Validate generation method
        valid_methods = ['ai_generated', 'ai_assisted', 'manual_refined']
        if self.generation_method not in valid_methods:
            raise ValueError(f"generation_method must be one of {valid_methods}")

        # Validate validation status
        valid_validation_status = ['pending', 'partial', 'complete', 'failed']
        if self.validation_status not in valid_validation_status:
            raise ValueError(f"validation_status must be one of {valid_validation_status}")

        # Validate user review status
        valid_review_status = ['pending', 'in_progress', 'reviewed', 'approved']
        if self.user_review_status not in valid_review_status:
            raise ValueError(f"user_review_status must be one of {valid_review_status}")

        # Validate last modified by
        if self.last_modified_by not in ['ai', 'user']:
            raise ValueError(f"last_modified_by must be 'ai' or 'user', got {self.last_modified_by}")

        # Validate field counts
        if self.high_confidence_fields > self.total_fields_generated:
            raise ValueError("high_confidence_fields cannot exceed total_fields_generated")

    @classmethod
    def create_from_analysis(
        cls,
        analysis_result_id: str,
        source_document_id: str,
        schema_name: str,
        ai_model_used: str,
        fields_data: Dict[str, Any],
        generation_confidence: float = 0.0
    ) -> 'GeneratedSchema':
        """Create generated schema from analysis results"""
        import uuid

        return cls(
            id=str(uuid.uuid4()),
            name=schema_name,
            description=f"AI-generated schema from document analysis",
            fields=fields_data,
            source_document_id=source_document_id,
            analysis_result_id=analysis_result_id,
            ai_model_used=ai_model_used,
            generation_confidence=generation_confidence,
            total_fields_generated=len(fields_data)
        )

    def add_field(self, field_name: str, field_config: Dict[str, Any], confidence: float = 0.0):
        """Add field to generated schema"""
        # Ensure AI metadata is present
        if 'ai_metadata' not in field_config:
            field_config['ai_metadata'] = {}

        field_config['ai_metadata']['confidence_score'] = confidence
        field_config['ai_metadata']['source'] = 'ai_generation'
        field_config['ai_metadata']['requires_review'] = confidence < 0.6

        self.fields[field_name] = field_config
        self.total_fields_generated = len(self.fields)

        # Update high confidence count
        self.high_confidence_fields = sum(
            1 for field in self.fields.values()
            if field.get('ai_metadata', {}).get('confidence_score', 0) >= 0.8
        )

    def remove_field(self, field_name: str):
        """Remove field from schema"""
        if field_name in self.fields:
            del self.fields[field_name]
            self.total_fields_generated = len(self.fields)

            # Update counts
            self.high_confidence_fields = sum(
                1 for field in self.fields.values()
                if field.get('ai_metadata', {}).get('confidence_score', 0) >= 0.8
            )

            # Track user modification
            if field_name not in self.user_modified_fields:
                self.user_modified_fields.append(field_name)
                self.last_modified_by = 'user'

    def update_field(self, field_name: str, field_updates: Dict[str, Any]):
        """Update existing field with user modifications"""
        if field_name not in self.fields:
            raise ValueError(f"Field {field_name} does not exist in schema")

        # Apply updates
        self.fields[field_name].update(field_updates)

        # Track user modification
        if field_name not in self.user_modified_fields:
            self.user_modified_fields.append(field_name)
            self.last_modified_by = 'user'

        # Update AI metadata to reflect user modification
        if 'ai_metadata' in self.fields[field_name]:
            self.fields[field_name]['ai_metadata']['user_modified'] = True

    def set_user_review_status(self, status: str, notes: Optional[str] = None):
        """Set user review status"""
        valid_statuses = ['pending', 'in_progress', 'reviewed', 'approved']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of {valid_statuses}")

        self.user_review_status = status
        if notes:
            self.review_notes = notes

        if status in ['reviewed', 'approved']:
            self.last_modified_by = 'user'

    def add_accuracy_feedback(self, field_name: str, accuracy_score: float):
        """Add user feedback on field accuracy"""
        if not (0.0 <= accuracy_score <= 1.0):
            raise ValueError("Accuracy score must be between 0.0 and 1.0")

        if self.accuracy_feedback is None:
            self.accuracy_feedback = {}

        self.accuracy_feedback[field_name] = accuracy_score

    def add_improvement_suggestion(self, suggestion: str):
        """Add improvement suggestion"""
        if suggestion and suggestion not in self.suggested_improvements:
            self.suggested_improvements.append(suggestion)

    def calculate_overall_accuracy(self) -> float:
        """Calculate overall accuracy from user feedback"""
        if not self.accuracy_feedback:
            return self.generation_confidence

        feedback_scores = list(self.accuracy_feedback.values())
        user_accuracy = sum(feedback_scores) / len(feedback_scores)

        # Combine AI confidence with user feedback
        return (self.generation_confidence + user_accuracy) / 2

    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get quality metrics for the generated schema"""
        requires_review_count = sum(
            1 for field in self.fields.values()
            if field.get('ai_metadata', {}).get('requires_review', False)
        )

        return {
            'total_fields_generated': self.total_fields_generated,
            'high_confidence_fields': self.high_confidence_fields,
            'auto_included_fields': self.high_confidence_fields,
            'requires_review_fields': requires_review_count,
            'user_modified_fields': len(self.user_modified_fields),
            'overall_schema_confidence': self.generation_confidence,
            'user_accuracy_score': self.calculate_overall_accuracy()
        }

    def get_review_summary(self) -> Dict[str, Any]:
        """Get summary of fields requiring review"""
        review_fields = []
        high_confidence_fields = []
        modified_fields = []

        for field_name, field_config in self.fields.items():
            ai_metadata = field_config.get('ai_metadata', {})
            confidence = ai_metadata.get('confidence_score', 0)

            if ai_metadata.get('requires_review', False):
                review_fields.append({
                    'name': field_name,
                    'confidence': confidence,
                    'reason': ai_metadata.get('review_reason', 'Low confidence')
                })
            elif confidence >= 0.8:
                high_confidence_fields.append(field_name)

            if field_name in self.user_modified_fields:
                modified_fields.append(field_name)

        return {
            'requires_review': review_fields,
            'high_confidence': high_confidence_fields,
            'user_modified': modified_fields,
            'review_priority': sorted(review_fields, key=lambda x: x['confidence'])
        }

    def is_ready_for_production(self) -> bool:
        """Check if schema is ready for production use"""
        return (
            self.user_review_status == 'approved' and
            self.validation_status == 'complete' and
            self.generation_confidence > 0.7
        )

    def get_compatibility_info(self) -> Dict[str, Any]:
        """Get compatibility information with existing schema system"""
        return {
            'compatible_with_existing': True,  # AI schemas are compatible
            'migration_required': False,
            'special_features': [
                'AI confidence scoring',
                'Field provenance tracking',
                'User modification history'
            ],
            'integration_points': [
                'Existing schema management UI',
                'Schema validation system',
                'Import/export functionality'
            ]
        }

    def convert_to_standard_schema(self) -> Dict[str, Any]:
        """Convert to standard schema format (compatible with existing system)"""
        standard_fields = {}

        for field_name, field_config in self.fields.items():
            # Extract standard field properties
            standard_field = {
                'display_name': field_config.get('display_name', field_name.title()),
                'type': field_config.get('type', 'string'),
                'required': field_config.get('required', False),
                'description': field_config.get('description', ''),
                'examples': field_config.get('examples', [])
            }

            # Add validation rules if present
            if 'validation_rules' in field_config:
                standard_field['validation_rules'] = field_config['validation_rules']

            standard_fields[field_name] = standard_field

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'fields': standard_fields,
            # Preserve AI generation metadata
            'generation_metadata': {
                'generated_by': 'ai',
                'source_document_id': self.source_document_id,
                'analysis_result_id': self.analysis_result_id,
                'ai_model_used': self.ai_model_used,
                'generation_confidence': self.generation_confidence,
                'generated_timestamp': self.generated_timestamp.isoformat()
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'fields': self.fields,
            'source_document_id': self.source_document_id,
            'analysis_result_id': self.analysis_result_id,
            'generation_method': self.generation_method,
            'generated_timestamp': self.generated_timestamp.isoformat(),
            'ai_model_used': self.ai_model_used,
            'generation_confidence': self.generation_confidence,
            'total_fields_generated': self.total_fields_generated,
            'high_confidence_fields': self.high_confidence_fields,
            'user_modified_fields': self.user_modified_fields,
            'validation_status': self.validation_status,
            'user_review_status': self.user_review_status,
            'review_notes': self.review_notes,
            'last_modified_by': self.last_modified_by,
            'accuracy_feedback': self.accuracy_feedback,
            'suggested_improvements': self.suggested_improvements
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeneratedSchema':
        """Create from dictionary (for loading from storage)"""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            fields=data.get('fields', {}),
            source_document_id=data.get('source_document_id', ''),
            analysis_result_id=data.get('analysis_result_id', ''),
            generation_method=data.get('generation_method', 'ai_generated'),
            generated_timestamp=datetime.fromisoformat(data['generated_timestamp']),
            ai_model_used=data.get('ai_model_used', ''),
            generation_confidence=data.get('generation_confidence', 0.0),
            total_fields_generated=data.get('total_fields_generated', 0),
            high_confidence_fields=data.get('high_confidence_fields', 0),
            user_modified_fields=data.get('user_modified_fields', []),
            validation_status=data.get('validation_status', 'pending'),
            user_review_status=data.get('user_review_status', 'pending'),
            review_notes=data.get('review_notes'),
            last_modified_by=data.get('last_modified_by', 'ai'),
            accuracy_feedback=data.get('accuracy_feedback'),
            suggested_improvements=data.get('suggested_improvements', [])
        )