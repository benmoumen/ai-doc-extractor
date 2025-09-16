"""
T034: SchemaGenerator
Service for generating complete schema definitions from AI analysis results
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..models.analysis_result import AIAnalysisResult
from ..models.extracted_field import ExtractedField
from ..models.validation_rule_inference import ValidationRuleInference
from ..models.document_type_suggestion import DocumentTypeSuggestion
from ..models.generated_schema import GeneratedSchema
from ..storage.analysis_storage import AIAnalysisStorage
from ..storage.generated_schema_storage import GeneratedSchemaStorage


class SchemaGenerationError(Exception):
    """Custom exception for schema generation errors"""
    pass


class SchemaGenerator:
    """Service for generating complete schema definitions from analysis results."""

    # Schema naming templates based on document type
    SCHEMA_NAME_TEMPLATES = {
        'invoice': 'Invoice Schema',
        'receipt': 'Receipt Schema',
        'form': 'Form Schema',
        'drivers_license': 'Driver\'s License Schema',
        'passport': 'Passport Schema',
        'bank_statement': 'Bank Statement Schema',
        'tax_document': 'Tax Document Schema',
        'contract': 'Contract Schema',
        'insurance_policy': 'Insurance Policy Schema',
        'medical_record': 'Medical Record Schema',
        'employment_document': 'Employment Document Schema',
        'utility_bill': 'Utility Bill Schema',
        'certificate': 'Certificate Schema'
    }

    # Field priority for schema organization
    FIELD_PRIORITY = {
        'id': 10, 'identifier': 10, 'number': 10,
        'name': 9, 'full_name': 9, 'first_name': 8, 'last_name': 8,
        'date': 7, 'issue_date': 7, 'due_date': 7,
        'amount': 6, 'total': 6, 'subtotal': 5,
        'email': 4, 'phone': 4,
        'address': 3, 'city': 3, 'state': 3, 'zip': 3
    }

    # Auto-include thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    MEDIUM_CONFIDENCE_THRESHOLD = 0.6
    MINIMUM_QUALITY_THRESHOLD = 0.5

    def __init__(self,
                 analysis_storage: Optional[AIAnalysisStorage] = None,
                 schema_storage: Optional[GeneratedSchemaStorage] = None):
        """Initialize schema generator"""
        self.analysis_storage = analysis_storage or AIAnalysisStorage()
        self.schema_storage = schema_storage or GeneratedSchemaStorage()

    def generate_schema_from_analysis(self,
                                    analysis_result_id: str,
                                    schema_name: Optional[str] = None,
                                    include_low_confidence: bool = False) -> GeneratedSchema:
        """
        Generate complete schema from analysis result

        Args:
            analysis_result_id: ID of analysis result
            schema_name: Custom schema name (optional)
            include_low_confidence: Whether to include low confidence fields

        Returns:
            GeneratedSchema instance

        Raises:
            SchemaGenerationError: If generation fails
        """
        try:
            # Get analysis result
            analysis_result = self.analysis_storage.get_analysis_result(analysis_result_id)
            if not analysis_result:
                raise SchemaGenerationError("Analysis result not found")

            # Get extracted fields
            fields = self.analysis_storage.get_fields_for_analysis(analysis_result_id)

            # Get validation rules
            all_rules = []
            for field in fields:
                rules = self.analysis_storage.get_rules_for_field(field.id)
                all_rules.extend(rules)

            # Get document type suggestion
            doc_type_suggestion = self.analysis_storage.get_suggestion_for_analysis(analysis_result_id)

            # Generate schema
            schema = self._build_schema(
                analysis_result=analysis_result,
                fields=fields,
                validation_rules=all_rules,
                doc_type_suggestion=doc_type_suggestion,
                schema_name=schema_name,
                include_low_confidence=include_low_confidence
            )

            # Save schema
            self.schema_storage.save(schema)

            return schema

        except Exception as e:
            raise SchemaGenerationError(f"Schema generation failed: {str(e)}")

    def _build_schema(self,
                     analysis_result: AIAnalysisResult,
                     fields: List[ExtractedField],
                     validation_rules: List[ValidationRuleInference],
                     doc_type_suggestion: Optional[DocumentTypeSuggestion],
                     schema_name: Optional[str],
                     include_low_confidence: bool) -> GeneratedSchema:
        """Build complete schema from components"""

        # Generate schema name
        if not schema_name:
            schema_name = self._generate_schema_name(analysis_result.detected_document_type, doc_type_suggestion)

        # Create schema using factory method
        schema = GeneratedSchema.create_from_analysis(
            analysis_result_id=analysis_result.id,
            source_document_id=analysis_result.sample_document_id,
            schema_name=schema_name,
            ai_model_used=analysis_result.model_used,
            fields_data={},  # Will be populated below
            generation_confidence=analysis_result.overall_quality_score
        )

        # Build field definitions
        schema_fields = self._build_field_definitions(fields, validation_rules, include_low_confidence)

        # Sort fields by priority
        sorted_fields = self._sort_fields_by_priority(schema_fields)

        # Add fields to schema
        for field_name, field_config in sorted_fields.items():
            schema.add_field(field_name, field_config, field_config.get('ai_metadata', {}).get('confidence_score', 0))

        # Set schema description
        schema.description = self._generate_schema_description(analysis_result, doc_type_suggestion, len(schema_fields))

        # Set validation status based on rules
        schema.validation_status = self._determine_validation_status(schema_fields, validation_rules)

        # Set user review status based on confidence
        schema.user_review_status = self._determine_review_status(schema)

        return schema

    def _generate_schema_name(self,
                            detected_type: str,
                            doc_type_suggestion: Optional[DocumentTypeSuggestion]) -> str:
        """Generate appropriate schema name"""
        base_name = self.SCHEMA_NAME_TEMPLATES.get(detected_type, f'{detected_type.replace("_", " ").title()} Schema')

        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        # Add confidence indicator if applicable
        if doc_type_suggestion and doc_type_suggestion.type_confidence < 0.7:
            base_name += " (Low Confidence)"

        return f"{base_name}_{timestamp}"

    def _build_field_definitions(self,
                               fields: List[ExtractedField],
                               validation_rules: List[ValidationRuleInference],
                               include_low_confidence: bool) -> Dict[str, Any]:
        """Build field definitions for schema"""
        schema_fields = {}

        # Create rule lookup
        rules_by_field = {}
        for rule in validation_rules:
            if rule.extracted_field_id not in rules_by_field:
                rules_by_field[rule.extracted_field_id] = []
            rules_by_field[rule.extracted_field_id].append(rule)

        for field in fields:
            # Skip low confidence fields unless explicitly included
            if not include_low_confidence and field.overall_confidence_score < self.MINIMUM_QUALITY_THRESHOLD:
                continue

            field_config = self._build_field_config(field, rules_by_field.get(field.id, []))
            schema_fields[field.detected_name] = field_config

        return schema_fields

    def _build_field_config(self, field: ExtractedField, rules: List[ValidationRuleInference]) -> Dict[str, Any]:
        """Build configuration for individual field"""
        config = {
            'display_name': field.display_name,
            'type': field.field_type,
            'required': field.is_required,
            'description': field.context_description or f'Extracted {field.field_type} field',
            'examples': [field.source_text] if field.source_text else []
        }

        # Add validation rules
        if rules:
            config['validation_rules'] = []
            for rule in rules:
                if rule.is_recommended:
                    rule_config = {
                        'type': rule.rule_type,
                        'value': rule.rule_value,
                        'description': rule.rule_description,
                        'priority': rule.priority
                    }
                    config['validation_rules'].append(rule_config)

        # Add AI metadata
        config['ai_metadata'] = {
            'confidence_score': field.overall_confidence_score,
            'source': 'ai_extraction',
            'requires_review': field.requires_review,
            'extraction_method': field.extraction_method,
            'confidence_breakdown': {
                'visual_clarity': field.visual_clarity_score,
                'label_confidence': field.label_confidence_score,
                'value_confidence': field.value_confidence_score,
                'type_confidence': field.type_confidence_score,
                'context_confidence': field.context_confidence_score
            }
        }

        # Add location information if available
        if field.bounding_box:
            config['ai_metadata']['location'] = field.bounding_box

        if field.page_number:
            config['ai_metadata']['page_number'] = field.page_number

        # Add alternative interpretations
        if field.alternative_names:
            config['ai_metadata']['alternative_names'] = field.alternative_names

        if field.alternative_types:
            config['ai_metadata']['alternative_types'] = field.alternative_types

        # Add field group
        if field.field_group:
            config['group'] = field.field_group

        return config

    def _sort_fields_by_priority(self, schema_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Sort fields by priority for better schema organization"""
        def get_field_priority(field_name: str) -> int:
            # Check exact match
            if field_name in self.FIELD_PRIORITY:
                return self.FIELD_PRIORITY[field_name]

            # Check partial matches
            for priority_field, priority in self.FIELD_PRIORITY.items():
                if priority_field in field_name:
                    return priority - 1  # Slightly lower priority for partial matches

            # Default priority
            return 1

        sorted_items = sorted(
            schema_fields.items(),
            key=lambda x: get_field_priority(x[0]),
            reverse=True
        )

        return dict(sorted_items)

    def _generate_schema_description(self,
                                   analysis_result: AIAnalysisResult,
                                   doc_type_suggestion: Optional[DocumentTypeSuggestion],
                                   field_count: int) -> str:
        """Generate descriptive text for schema"""
        doc_type = analysis_result.detected_document_type
        quality_score = analysis_result.overall_quality_score

        base_desc = f"AI-generated schema for {doc_type} documents"

        details = []
        details.append(f"Contains {field_count} fields")
        details.append(f"Generated from {analysis_result.model_used}")

        if quality_score >= 0.8:
            details.append("High quality extraction")
        elif quality_score >= 0.6:
            details.append("Medium quality extraction")
        else:
            details.append("Low quality extraction - review recommended")

        if doc_type_suggestion and doc_type_suggestion.type_confidence < 0.7:
            details.append("Document type classification has low confidence")

        return f"{base_desc}. {'. '.join(details)}."

    def _determine_validation_status(self,
                                   schema_fields: Dict[str, Any],
                                   validation_rules: List[ValidationRuleInference]) -> str:
        """Determine validation status for schema"""
        total_fields = len(schema_fields)

        if total_fields == 0:
            return 'failed'

        # Count fields with validation rules
        fields_with_rules = sum(
            1 for field_config in schema_fields.values()
            if field_config.get('validation_rules')
        )

        # Count high-confidence rules
        high_confidence_rules = sum(
            1 for rule in validation_rules
            if rule.confidence_score >= 0.8
        )

        rules_coverage = fields_with_rules / total_fields

        if rules_coverage >= 0.8 and high_confidence_rules >= total_fields * 0.6:
            return 'complete'
        elif rules_coverage >= 0.5:
            return 'partial'
        else:
            return 'pending'

    def _determine_review_status(self, schema: GeneratedSchema) -> str:
        """Determine user review status needed"""
        if schema.generation_confidence >= 0.9 and schema.validation_status == 'complete':
            return 'reviewed'  # High confidence, minimal review needed
        elif schema.generation_confidence >= 0.7:
            return 'pending'  # Medium confidence, review recommended
        else:
            return 'pending'  # Low confidence, review required

    def generate_schema_preview(self, analysis_result_id: str) -> Dict[str, Any]:
        """
        Generate schema preview without saving

        Args:
            analysis_result_id: ID of analysis result

        Returns:
            Dictionary with schema preview data
        """
        try:
            # Get analysis components
            analysis_result = self.analysis_storage.get_analysis_result(analysis_result_id)
            if not analysis_result:
                raise SchemaGenerationError("Analysis result not found")

            fields = self.analysis_storage.get_fields_for_analysis(analysis_result_id)
            doc_type_suggestion = self.analysis_storage.get_suggestion_for_analysis(analysis_result_id)

            # Generate preview
            preview = {
                'schema_name': self._generate_schema_name(analysis_result.detected_document_type, doc_type_suggestion),
                'document_type': analysis_result.detected_document_type,
                'confidence': analysis_result.overall_quality_score,
                'total_fields': len(fields),
                'field_preview': []
            }

            # Add field previews
            high_confidence_count = 0
            for field in fields[:10]:  # Show first 10 fields
                field_preview = {
                    'name': field.detected_name,
                    'display_name': field.display_name,
                    'type': field.field_type,
                    'confidence': field.overall_confidence_score,
                    'required': field.is_required,
                    'sample_value': field.source_text
                }

                if field.overall_confidence_score >= self.HIGH_CONFIDENCE_THRESHOLD:
                    high_confidence_count += 1

                preview['field_preview'].append(field_preview)

            preview['high_confidence_fields'] = high_confidence_count
            preview['auto_include_recommended'] = high_confidence_count
            preview['requires_review'] = sum(1 for f in fields if f.requires_review)

            return preview

        except Exception as e:
            raise SchemaGenerationError(f"Schema preview generation failed: {str(e)}")

    def enhance_existing_schema(self,
                              schema_id: str,
                              additional_analysis_id: str) -> GeneratedSchema:
        """
        Enhance existing schema with additional analysis data

        Args:
            schema_id: ID of existing schema
            additional_analysis_id: ID of additional analysis result

        Returns:
            Enhanced GeneratedSchema instance
        """
        try:
            # Get existing schema
            existing_schema = self.schema_storage.get_by_id(schema_id)
            if not existing_schema:
                raise SchemaGenerationError("Existing schema not found")

            # Get additional analysis data
            additional_fields = self.analysis_storage.get_fields_for_analysis(additional_analysis_id)

            # Merge fields intelligently
            for field in additional_fields:
                if field.detected_name not in existing_schema.fields:
                    # New field - add if confidence is sufficient
                    if field.overall_confidence_score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
                        field_config = self._build_field_config(field, [])
                        existing_schema.add_field(field.detected_name, field_config, field.overall_confidence_score)
                else:
                    # Existing field - potentially enhance
                    existing_field_config = existing_schema.fields[field.detected_name]
                    existing_confidence = existing_field_config.get('ai_metadata', {}).get('confidence_score', 0)

                    # Update if new analysis has higher confidence
                    if field.overall_confidence_score > existing_confidence:
                        field_config = self._build_field_config(field, [])
                        existing_schema.fields[field.detected_name] = field_config

            # Update schema metadata
            existing_schema.last_modified_by = 'ai'
            existing_schema.total_fields_generated = len(existing_schema.fields)

            # Recalculate high confidence count
            existing_schema.high_confidence_fields = sum(
                1 for field_config in existing_schema.fields.values()
                if field_config.get('ai_metadata', {}).get('confidence_score', 0) >= self.HIGH_CONFIDENCE_THRESHOLD
            )

            # Save enhanced schema
            self.schema_storage.save(existing_schema)

            return existing_schema

        except Exception as e:
            raise SchemaGenerationError(f"Schema enhancement failed: {str(e)}")

    def generate_multiple_schema_options(self,
                                       analysis_result_id: str,
                                       confidence_thresholds: List[float] = None) -> List[GeneratedSchema]:
        """
        Generate multiple schema options with different confidence thresholds

        Args:
            analysis_result_id: ID of analysis result
            confidence_thresholds: List of confidence thresholds to try

        Returns:
            List of GeneratedSchema options
        """
        if not confidence_thresholds:
            confidence_thresholds = [0.8, 0.6, 0.4]

        schemas = []

        for i, threshold in enumerate(confidence_thresholds):
            try:
                # Temporarily set threshold and generate schema
                original_threshold = self.MINIMUM_QUALITY_THRESHOLD
                self.MINIMUM_QUALITY_THRESHOLD = threshold

                schema = self.generate_schema_from_analysis(
                    analysis_result_id=analysis_result_id,
                    schema_name=f"Option {i+1} (Confidence >= {threshold})",
                    include_low_confidence=(threshold <= 0.5)
                )

                schemas.append(schema)

                # Restore original threshold
                self.MINIMUM_QUALITY_THRESHOLD = original_threshold

            except Exception:
                # Skip this option if generation fails
                continue

        return schemas

    def get_schema_generation_stats(self) -> Dict[str, Any]:
        """Get schema generation service statistics"""
        schema_stats = self.schema_storage.get_stats()

        generation_stats = {
            'supported_document_types': list(self.SCHEMA_NAME_TEMPLATES.keys()),
            'confidence_thresholds': {
                'high_confidence': self.HIGH_CONFIDENCE_THRESHOLD,
                'medium_confidence': self.MEDIUM_CONFIDENCE_THRESHOLD,
                'minimum_quality': self.MINIMUM_QUALITY_THRESHOLD
            },
            'field_priority_mappings': len(self.FIELD_PRIORITY)
        }

        schema_stats.update(generation_stats)
        return schema_stats