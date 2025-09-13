"""
T036: Main API endpoint for AI schema generation
Orchestrates the complete analysis pipeline from document upload to schema generation
"""

import time
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from ..services.document_processor import DocumentProcessor, DocumentProcessingError
from ..services.ai_analyzer import AIAnalyzer, AIAnalysisError
from ..services.field_extractor import FieldExtractor, FieldExtractionError
from ..services.validation_rule_inferencer import ValidationRuleInferencer, ValidationRuleInferencerError
from ..services.schema_generator import SchemaGenerator, SchemaGenerationError
from ..services.confidence_scorer import ConfidenceScorer, ConfidenceScoringError
from ..storage.sample_document_storage import SampleDocumentStorage
from ..storage.analysis_storage import AIAnalysisStorage
from ..storage.generated_schema_storage import GeneratedSchemaStorage


class AISchemaGenerationAPI:
    """Main API class for AI-powered schema generation."""

    def __init__(self):
        """Initialize API with all required services"""
        # Initialize storage services
        self.document_storage = SampleDocumentStorage()
        self.analysis_storage = AIAnalysisStorage()
        self.schema_storage = GeneratedSchemaStorage()

        # Initialize processing services
        self.document_processor = DocumentProcessor(self.document_storage)
        self.ai_analyzer = AIAnalyzer(self.analysis_storage)
        self.field_extractor = FieldExtractor(self.analysis_storage)
        self.validation_rule_inferencer = ValidationRuleInferencer(self.analysis_storage)
        self.schema_generator = SchemaGenerator(self.analysis_storage, self.schema_storage)
        self.confidence_scorer = ConfidenceScorer(self.analysis_storage)

    def analyze_document(self,
                        file_content: bytes,
                        filename: str,
                        model: Optional[str] = None,
                        document_type_hint: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete document analysis pipeline

        Args:
            file_content: Raw file bytes
            filename: Original filename
            model: AI model to use (optional)
            document_type_hint: Document type hint (optional)
            metadata: Additional metadata (optional)

        Returns:
            Complete analysis results including schema

        Raises:
            Various service-specific errors
        """
        start_time = time.time()
        pipeline_results = {
            'success': False,
            'processing_stages': {},
            'errors': [],
            'total_processing_time': 0.0
        }

        try:
            # Stage 1: Document Processing
            stage_start = time.time()
            try:
                document = self.document_processor.process_upload(
                    file_content=file_content,
                    filename=filename,
                    metadata=metadata or {}
                )

                prepared_data = self.document_processor.prepare_for_analysis(document.id)

                pipeline_results['processing_stages']['document_processing'] = {
                    'success': True,
                    'duration': time.time() - stage_start,
                    'document_id': document.id,
                    'file_type': document.file_type,
                    'file_size': document.file_size
                }

            except DocumentProcessingError as e:
                pipeline_results['processing_stages']['document_processing'] = {
                    'success': False,
                    'error': str(e),
                    'duration': time.time() - stage_start
                }
                pipeline_results['errors'].append(f"Document processing failed: {str(e)}")
                raise

            # Stage 2: AI Analysis
            stage_start = time.time()
            try:
                analysis_result = self.ai_analyzer.analyze_document(
                    document=document,
                    prepared_data=prepared_data['prepared_data'],
                    model=model,
                    document_type_hint=document_type_hint
                )

                pipeline_results['processing_stages']['ai_analysis'] = {
                    'success': True,
                    'duration': time.time() - stage_start,
                    'analysis_id': analysis_result.id,
                    'detected_document_type': analysis_result.detected_document_type,
                    'document_type_confidence': analysis_result.document_type_confidence,
                    'total_fields_detected': analysis_result.total_fields_detected,
                    'model_used': analysis_result.model_used
                }

            except AIAnalysisError as e:
                pipeline_results['processing_stages']['ai_analysis'] = {
                    'success': False,
                    'error': str(e),
                    'duration': time.time() - stage_start
                }
                pipeline_results['errors'].append(f"AI analysis failed: {str(e)}")
                raise

            # Stage 3: Field Enhancement
            stage_start = time.time()
            try:
                enhanced_fields = self.field_extractor.process_extracted_fields(analysis_result.id)

                pipeline_results['processing_stages']['field_enhancement'] = {
                    'success': True,
                    'duration': time.time() - stage_start,
                    'enhanced_fields_count': len(enhanced_fields),
                    'high_confidence_fields': sum(1 for f in enhanced_fields if f.overall_confidence_score >= 0.8),
                    'fields_requiring_review': sum(1 for f in enhanced_fields if f.requires_review)
                }

            except FieldExtractionError as e:
                pipeline_results['processing_stages']['field_enhancement'] = {
                    'success': False,
                    'error': str(e),
                    'duration': time.time() - stage_start
                }
                pipeline_results['errors'].append(f"Field enhancement failed: {str(e)}")
                # Continue pipeline with original fields
                enhanced_fields = self.analysis_storage.get_fields_for_analysis(analysis_result.id)

            # Stage 4: Validation Rule Inference
            stage_start = time.time()
            try:
                validation_rules = self.validation_rule_inferencer.infer_validation_rules(analysis_result.id)

                pipeline_results['processing_stages']['validation_inference'] = {
                    'success': True,
                    'duration': time.time() - stage_start,
                    'validation_rules_count': len(validation_rules),
                    'recommended_rules': sum(1 for r in validation_rules if r.is_recommended),
                    'high_priority_rules': sum(1 for r in validation_rules if r.priority >= 8)
                }

            except ValidationRuleInferencerError as e:
                pipeline_results['processing_stages']['validation_inference'] = {
                    'success': False,
                    'error': str(e),
                    'duration': time.time() - stage_start
                }
                pipeline_results['errors'].append(f"Validation rule inference failed: {str(e)}")
                validation_rules = []

            # Stage 5: Schema Generation
            stage_start = time.time()
            try:
                generated_schema = self.schema_generator.generate_schema_from_analysis(
                    analysis_result_id=analysis_result.id,
                    include_low_confidence=False  # Only include high/medium confidence fields by default
                )

                pipeline_results['processing_stages']['schema_generation'] = {
                    'success': True,
                    'duration': time.time() - stage_start,
                    'schema_id': generated_schema.id,
                    'schema_name': generated_schema.name,
                    'total_fields_generated': generated_schema.total_fields_generated,
                    'high_confidence_fields': generated_schema.high_confidence_fields,
                    'generation_confidence': generated_schema.generation_confidence
                }

            except SchemaGenerationError as e:
                pipeline_results['processing_stages']['schema_generation'] = {
                    'success': False,
                    'error': str(e),
                    'duration': time.time() - stage_start
                }
                pipeline_results['errors'].append(f"Schema generation failed: {str(e)}")
                raise

            # Stage 6: Confidence Analysis
            stage_start = time.time()
            try:
                confidence_analysis = self.confidence_scorer.calculate_comprehensive_confidence(analysis_result.id)
                schema_confidence = self.confidence_scorer.analyze_schema_confidence(generated_schema)

                pipeline_results['processing_stages']['confidence_analysis'] = {
                    'success': True,
                    'duration': time.time() - stage_start,
                    'overall_confidence': confidence_analysis['overall_confidence'],
                    'confidence_level': confidence_analysis['confidence_level'],
                    'schema_production_ready': schema_confidence['production_readiness']
                }

            except ConfidenceScoringError as e:
                pipeline_results['processing_stages']['confidence_analysis'] = {
                    'success': False,
                    'error': str(e),
                    'duration': time.time() - stage_start
                }
                pipeline_results['errors'].append(f"Confidence analysis failed: {str(e)}")
                # Provide default confidence data
                confidence_analysis = {'overall_confidence': 0.5, 'confidence_level': 'medium'}
                schema_confidence = {'production_readiness': False}

            # Compile final results
            total_time = time.time() - start_time
            pipeline_results.update({
                'success': True,
                'total_processing_time': total_time,
                'document': {
                    'id': document.id,
                    'filename': document.filename,
                    'file_type': document.file_type,
                    'file_size': document.file_size,
                    'processing_status': document.processing_status
                },
                'analysis': {
                    'id': analysis_result.id,
                    'detected_document_type': analysis_result.detected_document_type,
                    'document_type_confidence': analysis_result.document_type_confidence,
                    'total_fields_detected': analysis_result.total_fields_detected,
                    'high_confidence_fields': analysis_result.high_confidence_fields,
                    'overall_quality_score': analysis_result.overall_quality_score,
                    'model_used': analysis_result.model_used
                },
                'schema': {
                    'id': generated_schema.id,
                    'name': generated_schema.name,
                    'description': generated_schema.description,
                    'total_fields': generated_schema.total_fields_generated,
                    'high_confidence_fields': generated_schema.high_confidence_fields,
                    'generation_confidence': generated_schema.generation_confidence,
                    'validation_status': generated_schema.validation_status,
                    'user_review_status': generated_schema.user_review_status,
                    'production_ready': schema_confidence.get('production_readiness', False)
                },
                'confidence': confidence_analysis,
                'recommendations': confidence_analysis.get('recommendations', [])
            })

            return pipeline_results

        except Exception as e:
            # Handle any unexpected errors
            pipeline_results.update({
                'success': False,
                'total_processing_time': time.time() - start_time,
                'fatal_error': str(e),
                'traceback': traceback.format_exc()
            })
            pipeline_results['errors'].append(f"Unexpected error: {str(e)}")
            return pipeline_results

    def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        """
        Get complete analysis results by ID

        Args:
            analysis_id: Analysis result ID

        Returns:
            Complete analysis data including all components
        """
        try:
            # Get analysis result
            analysis_result = self.analysis_storage.get_analysis_result(analysis_id)
            if not analysis_result:
                return {'success': False, 'error': 'Analysis not found'}

            # Get associated data
            fields = self.analysis_storage.get_fields_for_analysis(analysis_id)
            doc_type_suggestion = self.analysis_storage.get_suggestion_for_analysis(analysis_id)

            # Get validation rules for all fields
            all_validation_rules = []
            for field in fields:
                rules = self.analysis_storage.get_rules_for_field(field.id)
                all_validation_rules.extend(rules)

            # Get generated schemas from this analysis
            generated_schemas = self.schema_storage.get_by_analysis_result(analysis_id)

            # Calculate confidence analysis
            confidence_analysis = None
            try:
                confidence_analysis = self.confidence_scorer.calculate_comprehensive_confidence(analysis_id)
            except Exception:
                pass

            return {
                'success': True,
                'analysis': analysis_result.to_dict(),
                'fields': [field.to_dict() for field in fields],
                'validation_rules': [rule.to_dict() for rule in all_validation_rules],
                'document_type_suggestion': doc_type_suggestion.to_dict() if doc_type_suggestion else None,
                'generated_schemas': [schema.to_dict() for schema in generated_schemas],
                'confidence_analysis': confidence_analysis
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to retrieve analysis results: {str(e)}'
            }

    def get_schema_details(self, schema_id: str) -> Dict[str, Any]:
        """
        Get complete schema details

        Args:
            schema_id: Generated schema ID

        Returns:
            Complete schema data with analysis
        """
        try:
            schema = self.schema_storage.get_by_id(schema_id)
            if not schema:
                return {'success': False, 'error': 'Schema not found'}

            # Get confidence analysis for schema
            schema_confidence = None
            try:
                schema_confidence = self.confidence_scorer.analyze_schema_confidence(schema)
            except Exception:
                pass

            # Get quality metrics
            quality_metrics = schema.get_quality_metrics()
            review_summary = schema.get_review_summary()

            return {
                'success': True,
                'schema': schema.to_dict(),
                'confidence_analysis': schema_confidence,
                'quality_metrics': quality_metrics,
                'review_summary': review_summary,
                'compatibility_info': schema.get_compatibility_info(),
                'standard_format': schema.convert_to_standard_schema()
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to retrieve schema details: {str(e)}'
            }

    def retry_analysis(self,
                      document_id: str,
                      previous_analysis_id: str,
                      model: Optional[str] = None) -> Dict[str, Any]:
        """
        Retry analysis with different model or parameters

        Args:
            document_id: Document ID
            previous_analysis_id: Previous analysis ID
            model: Model to use for retry (optional)

        Returns:
            New analysis results
        """
        try:
            # Get document
            document = self.document_storage.get_by_id(document_id)
            if not document:
                return {'success': False, 'error': 'Document not found'}

            # Prepare document for analysis
            prepared_data = self.document_processor.prepare_for_analysis(document_id)

            # Retry analysis
            analysis_result = self.ai_analyzer.retry_analysis(
                document=document,
                prepared_data=prepared_data['prepared_data'],
                previous_analysis_id=previous_analysis_id,
                model=model
            )

            # Continue with enhancement pipeline
            enhanced_fields = self.field_extractor.process_extracted_fields(analysis_result.id)
            validation_rules = self.validation_rule_inferencer.infer_validation_rules(analysis_result.id)

            # Generate new schema
            generated_schema = self.schema_generator.generate_schema_from_analysis(
                analysis_result_id=analysis_result.id
            )

            # Calculate confidence
            confidence_analysis = self.confidence_scorer.calculate_comprehensive_confidence(analysis_result.id)

            return {
                'success': True,
                'retry_analysis': {
                    'id': analysis_result.id,
                    'model_used': analysis_result.model_used,
                    'retry_count': analysis_result.retry_count
                },
                'schema': {
                    'id': generated_schema.id,
                    'name': generated_schema.name,
                    'total_fields': generated_schema.total_fields_generated,
                    'generation_confidence': generated_schema.generation_confidence
                },
                'confidence': confidence_analysis,
                'improved': confidence_analysis['overall_confidence'] > 0.6
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Retry analysis failed: {str(e)}'
            }

    def get_supported_models(self) -> Dict[str, Any]:
        """Get list of supported AI models"""
        try:
            models = self.ai_analyzer.get_supported_models()
            return {
                'success': True,
                'models': models,
                'default_model': self.ai_analyzer.default_model
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get supported models: {str(e)}'
            }

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        try:
            return {
                'success': True,
                'services': {
                    'document_processor': {
                        'available': True,
                        'stats': self.document_processor.get_processing_stats()
                    },
                    'ai_analyzer': {
                        'available': True,
                        'stats': self.ai_analyzer.get_analysis_stats()
                    },
                    'field_extractor': {
                        'available': True,
                        'stats': self.field_extractor.get_field_extraction_stats()
                    },
                    'validation_rule_inferencer': {
                        'available': True,
                        'stats': self.validation_rule_inferencer.get_inference_stats()
                    },
                    'schema_generator': {
                        'available': True,
                        'stats': self.schema_generator.get_schema_generation_stats()
                    },
                    'confidence_scorer': {
                        'available': True,
                        'stats': self.confidence_scorer.get_confidence_scoring_stats()
                    }
                },
                'storage': {
                    'documents': self.document_storage.get_stats(),
                    'analyses': self.analysis_storage.get_analysis_stats(),
                    'schemas': self.schema_storage.get_stats()
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get service status: {str(e)}'
            }