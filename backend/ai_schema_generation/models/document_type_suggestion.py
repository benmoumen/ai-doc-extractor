"""
T025: DocumentTypeSuggestion model
AI's classification of document type with confidence and alternatives
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import json


@dataclass
class DocumentTypeSuggestion:
    """AI suggestion for document type classification."""

    id: str
    analysis_result_id: str

    # Primary suggestion
    suggested_type: str
    type_confidence: float  # 0.0-1.0
    type_description: str

    # Alternative suggestions
    alternative_types: List[Dict[str, Any]] = field(default_factory=list)
    # Structure: [{"type": str, "confidence": float, "reason": str}]

    # Classification reasoning
    classification_factors: List[str] = field(default_factory=list)
    key_indicators: List[str] = field(default_factory=list)
    confidence_explanation: str = ""

    # Template matching
    matched_templates: List[str] = field(default_factory=list)
    template_similarity_scores: Dict[str, float] = field(default_factory=dict)

    # Metadata
    classification_timestamp: datetime = field(default_factory=datetime.now)
    model_used: str = ""
    requires_confirmation: bool = False

    def __post_init__(self):
        """Validate document type suggestion data"""
        # Validate confidence score
        if not (0.0 <= self.type_confidence <= 1.0):
            raise ValueError(f"type_confidence must be between 0.0 and 1.0, got {self.type_confidence}")

        # Validate alternative types
        for alt_type in self.alternative_types:
            required_keys = ['type', 'confidence', 'reason']
            if not all(key in alt_type for key in required_keys):
                raise ValueError(f"Alternative type must contain: {required_keys}")

            if not (0.0 <= alt_type['confidence'] <= 1.0):
                raise ValueError(f"Alternative confidence must be between 0.0 and 1.0, got {alt_type['confidence']}")

        # Validate template similarity scores
        for template, score in self.template_similarity_scores.items():
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"Template similarity score must be between 0.0 and 1.0, got {score} for {template}")

        # Auto-determine if confirmation is needed
        if not self.requires_confirmation and self.type_confidence < 0.7:
            self.requires_confirmation = True

    @classmethod
    def create_suggestion(
        cls,
        analysis_result_id: str,
        suggested_type: str,
        confidence: float,
        model_used: str,
        description: Optional[str] = None
    ) -> 'DocumentTypeSuggestion':
        """Create new document type suggestion"""
        import uuid

        # Generate description if not provided
        if not description:
            description = cls._generate_type_description(suggested_type)

        return cls(
            id=str(uuid.uuid4()),
            analysis_result_id=analysis_result_id,
            suggested_type=suggested_type,
            type_confidence=confidence,
            type_description=description,
            model_used=model_used
        )

    @staticmethod
    def _generate_type_description(document_type: str) -> str:
        """Generate description for document type"""
        descriptions = {
            'invoice': 'Commercial document requesting payment for goods or services',
            'receipt': 'Proof of payment for goods or services received',
            'contract': 'Legal agreement between parties',
            'form': 'Document with fields for collecting information',
            'drivers_license': 'Government-issued identification and driving permit',
            'passport': 'Government-issued travel document and identification',
            'bank_statement': 'Financial record of account transactions',
            'tax_document': 'Form or statement related to tax obligations',
            'insurance_policy': 'Contract providing coverage for specific risks',
            'medical_record': 'Document containing health and treatment information',
            'employment_document': 'Work-related form or agreement',
            'legal_document': 'Document with legal significance or requirements',
            'financial_statement': 'Summary of financial position or performance',
            'utility_bill': 'Statement for utility services rendered',
            'shipping_document': 'Documentation for goods transportation',
            'certificate': 'Official document verifying qualifications or facts'
        }

        return descriptions.get(document_type, f'{document_type.replace("_", " ").title()} document')

    def add_alternative_type(self, doc_type: str, confidence: float, reason: str):
        """Add alternative document type suggestion"""
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

        # Check if type already exists
        for alt_type in self.alternative_types:
            if alt_type['type'] == doc_type:
                alt_type['confidence'] = confidence
                alt_type['reason'] = reason
                return

        # Add new alternative
        self.alternative_types.append({
            'type': doc_type,
            'confidence': confidence,
            'reason': reason,
            'description': self._generate_type_description(doc_type)
        })

        # Sort alternatives by confidence
        self.alternative_types.sort(key=lambda x: x['confidence'], reverse=True)

    def add_classification_factor(self, factor: str):
        """Add factor that influenced classification"""
        if factor and factor not in self.classification_factors:
            self.classification_factors.append(factor)

    def add_key_indicator(self, indicator: str):
        """Add key indicator found in document"""
        if indicator and indicator not in self.key_indicators:
            self.key_indicators.append(indicator)

    def add_template_match(self, template_name: str, similarity_score: float):
        """Add template matching result"""
        if not (0.0 <= similarity_score <= 1.0):
            raise ValueError("Similarity score must be between 0.0 and 1.0")

        if template_name not in self.matched_templates:
            self.matched_templates.append(template_name)

        self.template_similarity_scores[template_name] = similarity_score

    def set_confidence_explanation(self, explanation: str):
        """Set explanation for confidence level"""
        self.confidence_explanation = explanation

    def get_confidence_level(self) -> str:
        """Get confidence level as string"""
        if self.type_confidence >= 0.9:
            return "very_high"
        elif self.type_confidence >= 0.8:
            return "high"
        elif self.type_confidence >= 0.6:
            return "medium"
        elif self.type_confidence >= 0.4:
            return "low"
        else:
            return "very_low"

    def get_best_alternative(self) -> Optional[Dict[str, Any]]:
        """Get the best alternative type suggestion"""
        if not self.alternative_types:
            return None

        return self.alternative_types[0]  # Already sorted by confidence

    def get_all_suggestions_sorted(self) -> List[Dict[str, Any]]:
        """Get all suggestions (primary + alternatives) sorted by confidence"""
        all_suggestions = [{
            'type': self.suggested_type,
            'confidence': self.type_confidence,
            'reason': 'Primary AI classification',
            'description': self.type_description,
            'is_primary': True
        }]

        for alt_type in self.alternative_types:
            alt_copy = alt_type.copy()
            alt_copy['is_primary'] = False
            all_suggestions.append(alt_copy)

        return sorted(all_suggestions, key=lambda x: x['confidence'], reverse=True)

    def get_classification_summary(self) -> Dict[str, Any]:
        """Get summary of classification results"""
        return {
            'primary_type': self.suggested_type,
            'confidence': self.type_confidence,
            'confidence_level': self.get_confidence_level(),
            'requires_confirmation': self.requires_confirmation,
            'alternatives_count': len(self.alternative_types),
            'key_indicators_count': len(self.key_indicators),
            'template_matches_count': len(self.matched_templates),
            'classification_factors_count': len(self.classification_factors)
        }

    def is_high_confidence(self) -> bool:
        """Check if classification has high confidence"""
        return self.type_confidence >= 0.8 and not self.requires_confirmation

    def needs_user_review(self) -> bool:
        """Check if classification needs user review"""
        return (
            self.requires_confirmation or
            self.type_confidence < 0.6 or
            len(self.alternative_types) > 2  # Many alternatives indicate uncertainty
        )

    def get_recommendation_action(self) -> str:
        """Get recommended action based on confidence"""
        if self.is_high_confidence():
            return "auto_accept"
        elif self.type_confidence >= 0.6:
            return "suggest_with_alternatives"
        else:
            return "manual_review_required"

    def update_from_user_feedback(self, user_selection: str, user_confidence: Optional[float] = None):
        """Update suggestion based on user feedback"""
        # If user selects different type, update primary suggestion
        if user_selection != self.suggested_type:
            # Move current primary to alternatives
            self.add_alternative_type(
                self.suggested_type,
                self.type_confidence,
                "Previous AI classification"
            )

            # Set user selection as primary
            self.suggested_type = user_selection
            self.type_description = self._generate_type_description(user_selection)

            # Remove from alternatives if it was there
            self.alternative_types = [
                alt for alt in self.alternative_types
                if alt['type'] != user_selection
            ]

        # Update confidence if provided
        if user_confidence is not None:
            if 0.0 <= user_confidence <= 1.0:
                self.type_confidence = user_confidence

        # Clear confirmation requirement
        self.requires_confirmation = False

        # Add user feedback to classification factors
        self.add_classification_factor("User confirmation")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            'id': self.id,
            'analysis_result_id': self.analysis_result_id,
            'suggested_type': self.suggested_type,
            'type_confidence': self.type_confidence,
            'type_description': self.type_description,
            'alternative_types': self.alternative_types,
            'classification_factors': self.classification_factors,
            'key_indicators': self.key_indicators,
            'confidence_explanation': self.confidence_explanation,
            'matched_templates': self.matched_templates,
            'template_similarity_scores': self.template_similarity_scores,
            'classification_timestamp': self.classification_timestamp.isoformat(),
            'model_used': self.model_used,
            'requires_confirmation': self.requires_confirmation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentTypeSuggestion':
        """Create from dictionary (for loading from storage)"""
        return cls(
            id=data['id'],
            analysis_result_id=data['analysis_result_id'],
            suggested_type=data['suggested_type'],
            type_confidence=data['type_confidence'],
            type_description=data['type_description'],
            alternative_types=data.get('alternative_types', []),
            classification_factors=data.get('classification_factors', []),
            key_indicators=data.get('key_indicators', []),
            confidence_explanation=data.get('confidence_explanation', ''),
            matched_templates=data.get('matched_templates', []),
            template_similarity_scores=data.get('template_similarity_scores', {}),
            classification_timestamp=datetime.fromisoformat(data['classification_timestamp']),
            model_used=data.get('model_used', ''),
            requires_confirmation=data.get('requires_confirmation', False)
        )