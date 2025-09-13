"""
T031: AIAnalyzer
Core service for AI-powered document analysis using LiteLLM
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

from ..models.sample_document import SampleDocument
from ..models.analysis_result import AIAnalysisResult
from ..models.extracted_field import ExtractedField
from ..models.document_type_suggestion import DocumentTypeSuggestion
from ..storage.analysis_storage import AIAnalysisStorage


class AIAnalysisError(Exception):
    """Custom exception for AI analysis errors"""
    pass


class AIAnalyzer:
    """Service for AI-powered document analysis using LiteLLM."""

    # Default models for different providers
    DEFAULT_MODELS = {
        'groq': 'groq/llama-3.1-70b-versatile',
        'mistral': 'mistral/mistral-small-latest',
        'openai': 'gpt-4o-mini'
    }

    # Analysis prompt templates
    ANALYSIS_PROMPT_TEMPLATE = """
Analyze this document image and extract structured data. Return a JSON response with the following structure:

{
  "document_type": {
    "primary": "string (e.g., 'invoice', 'receipt', 'form', 'drivers_license')",
    "confidence": 0.0-1.0,
    "alternatives": [
      {"type": "string", "confidence": 0.0-1.0, "reason": "string"}
    ]
  },
  "fields": [
    {
      "name": "field_name",
      "display_name": "Human Readable Name",
      "type": "string|number|date|boolean|email|phone|url|currency",
      "value": "extracted_value",
      "confidence_scores": {
        "visual_clarity": 0.0-1.0,
        "label_confidence": 0.0-1.0,
        "value_confidence": 0.0-1.0,
        "type_confidence": 0.0-1.0,
        "context_confidence": 0.0-1.0
      },
      "location": {
        "x": float,
        "y": float,
        "width": float,
        "height": float
      },
      "alternatives": [
        {"name": "alt_name", "type": "alt_type", "confidence": 0.0-1.0}
      ]
    }
  ],
  "quality_assessment": {
    "overall_score": 0.0-1.0,
    "clarity_score": 0.0-1.0,
    "completeness_score": 0.0-1.0,
    "structure_score": 0.0-1.0
  },
  "metadata": {
    "processing_notes": "any relevant notes",
    "detected_language": "language_code",
    "image_quality": "high|medium|low"
  }
}

Be thorough in extracting all visible fields. For confidence scores:
- visual_clarity: How clearly the field is visible
- label_confidence: Confidence in field label/name identification
- value_confidence: Confidence in extracted value accuracy
- type_confidence: Confidence in field type classification
- context_confidence: Confidence based on document context

Document Type: {document_type_hint}
"""

    RETRY_PROMPT_TEMPLATE = """
The previous analysis had issues. Please re-analyze this document with extra care and attention.

Focus on:
- More accurate field extraction
- Better confidence scoring
- Clearer field naming
- Complete data extraction

Previous errors: {previous_errors}

{base_prompt}
"""

    def __init__(self,
                 storage: Optional[AIAnalysisStorage] = None,
                 default_model: str = 'groq/llama-3.1-70b-versatile',
                 temperature: float = 0.1):
        """Initialize AI analyzer"""
        if not LITELLM_AVAILABLE:
            raise ImportError("LiteLLM is required for AI analysis")

        self.storage = storage or AIAnalysisStorage()
        self.default_model = default_model
        self.temperature = temperature
        self._setup_litellm()

    def _setup_litellm(self):
        """Configure LiteLLM settings"""
        # Set up LiteLLM with appropriate timeouts and retries
        litellm.set_verbose = False
        litellm.timeout = 300  # 5 minutes
        litellm.num_retries = 2

    def analyze_document(self,
                        document: SampleDocument,
                        prepared_data: Dict[str, Any],
                        model: Optional[str] = None,
                        document_type_hint: Optional[str] = None) -> AIAnalysisResult:
        """
        Perform AI analysis of document

        Args:
            document: SampleDocument instance
            prepared_data: Prepared document data from DocumentProcessor
            model: Model to use (defaults to default_model)
            document_type_hint: Optional document type hint

        Returns:
            AIAnalysisResult instance

        Raises:
            AIAnalysisError: If analysis fails
        """
        model = model or self.default_model
        start_time = time.time()

        try:
            # Create analysis result record
            analysis_result = AIAnalysisResult.create_for_document(
                document_id=document.id,
                model_used=model
            )

            # Prepare messages for AI
            messages = self._prepare_analysis_messages(prepared_data, document_type_hint)

            # Call AI model
            response = self._call_ai_model(model, messages)

            # Parse and validate response
            parsed_response = self._parse_ai_response(response)

            # Update analysis result with findings
            processing_time = time.time() - start_time
            self._populate_analysis_result(analysis_result, parsed_response, processing_time)

            # Create extracted fields
            extracted_fields = self._create_extracted_fields(analysis_result.id, parsed_response)

            # Create document type suggestion
            doc_type_suggestion = self._create_document_type_suggestion(analysis_result.id, parsed_response, model)

            # Save to storage
            self.storage.save_analysis_result(analysis_result)

            # Save extracted fields
            for field in extracted_fields:
                self.storage.save_extracted_field(field)

            # Save document type suggestion
            self.storage.save_document_type_suggestion(doc_type_suggestion)

            return analysis_result

        except Exception as e:
            processing_time = time.time() - start_time
            error_analysis = self._create_error_analysis_result(
                document.id, model, str(e), processing_time
            )
            self.storage.save_analysis_result(error_analysis)
            raise AIAnalysisError(f"Document analysis failed: {str(e)}")

    def retry_analysis(self,
                      document: SampleDocument,
                      prepared_data: Dict[str, Any],
                      previous_analysis_id: str,
                      model: Optional[str] = None) -> AIAnalysisResult:
        """
        Retry analysis with different model or parameters

        Args:
            document: SampleDocument instance
            prepared_data: Prepared document data
            previous_analysis_id: ID of previous failed analysis
            model: Model to use for retry

        Returns:
            AIAnalysisResult instance
        """
        # Get previous analysis for context
        previous_analysis = self.storage.get_analysis_result(previous_analysis_id)
        if not previous_analysis:
            raise AIAnalysisError("Previous analysis not found for retry")

        # Use different model for retry if not specified
        if not model:
            current_model = previous_analysis.model_used
            if 'groq' in current_model:
                model = self.DEFAULT_MODELS['mistral']
            elif 'mistral' in current_model:
                model = self.DEFAULT_MODELS['openai']
            else:
                model = self.DEFAULT_MODELS['groq']

        # Prepare retry prompt with previous errors
        document_type_hint = previous_analysis.detected_document_type
        previous_errors = previous_analysis.error_details or "Low confidence scores"

        # Perform analysis with retry context
        return self._analyze_with_retry_context(
            document, prepared_data, model, previous_errors, document_type_hint
        )

    def _prepare_analysis_messages(self,
                                  prepared_data: Dict[str, Any],
                                  document_type_hint: Optional[str] = None) -> List[Dict[str, Any]]:
        """Prepare messages for AI model"""
        document_type_hint = document_type_hint or "unknown"

        prompt = self.ANALYSIS_PROMPT_TEMPLATE.format(
            document_type_hint=document_type_hint
        )

        messages = [
            {
                "role": "system",
                "content": "You are an expert document analysis AI. Extract structured data from documents with high accuracy and provide confidence scores for all extractions."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        # Add images based on document type
        if prepared_data['type'] == 'pdf':
            # Add first page for PDF analysis
            if prepared_data['pages']:
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{prepared_data['pages'][0]['image_base64']}"
                    }
                })
        elif prepared_data['type'] == 'image':
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{prepared_data['image_base64']}"
                }
            })

        return messages

    def _call_ai_model(self, model: str, messages: List[Dict[str, Any]]) -> str:
        """Call AI model via LiteLLM"""
        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            return response.choices[0].message.content

        except Exception as e:
            raise AIAnalysisError(f"AI model call failed: {str(e)}")

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate AI response"""
        try:
            parsed = json.loads(response_text)

            # Basic validation
            required_keys = ['document_type', 'fields', 'quality_assessment']
            for key in required_keys:
                if key not in parsed:
                    raise AIAnalysisError(f"Missing required key in response: {key}")

            return parsed

        except json.JSONDecodeError as e:
            raise AIAnalysisError(f"Invalid JSON response: {str(e)}")

    def _populate_analysis_result(self,
                                 analysis_result: AIAnalysisResult,
                                 parsed_response: Dict[str, Any],
                                 processing_time: float):
        """Populate analysis result with AI findings"""
        doc_type = parsed_response['document_type']
        quality = parsed_response['quality_assessment']
        fields = parsed_response['fields']

        analysis_result.detected_document_type = doc_type['primary']
        analysis_result.document_type_confidence = doc_type['confidence']
        analysis_result.total_fields_detected = len(fields)
        analysis_result.processing_time_seconds = processing_time
        analysis_result.overall_quality_score = quality['overall_score']

        # Count high confidence fields
        analysis_result.high_confidence_fields = sum(
            1 for field in fields
            if field.get('confidence_scores', {}).get('visual_clarity', 0) >= 0.8
        )

        # Store metadata
        analysis_result.analysis_metadata = {
            'quality_breakdown': quality,
            'document_metadata': parsed_response.get('metadata', {}),
            'field_count_by_type': self._count_fields_by_type(fields)
        }

    def _create_extracted_fields(self,
                               analysis_result_id: str,
                               parsed_response: Dict[str, Any]) -> List[ExtractedField]:
        """Create ExtractedField instances from AI response"""
        fields = []

        for field_data in parsed_response['fields']:
            confidence_scores = field_data.get('confidence_scores', {})

            field = ExtractedField.create_from_analysis(
                analysis_result_id=analysis_result_id,
                detected_name=field_data['name'],
                field_type=field_data['type'],
                source_text=field_data.get('value', ''),
                confidence_scores={
                    'visual_clarity': confidence_scores.get('visual_clarity', 0.0),
                    'label_confidence': confidence_scores.get('label_confidence', 0.0),
                    'value_confidence': confidence_scores.get('value_confidence', 0.0),
                    'type_confidence': confidence_scores.get('type_confidence', 0.0),
                    'context_confidence': confidence_scores.get('context_confidence', 0.0)
                }
            )

            # Set display name
            field.display_name = field_data.get('display_name', field.display_name)

            # Set location if provided
            if 'location' in field_data:
                loc = field_data['location']
                field.set_location(
                    loc['x'], loc['y'], loc['width'], loc['height']
                )

            # Add alternative interpretations
            for alt in field_data.get('alternatives', []):
                field.add_alternative_name(alt.get('name', ''))
                field.add_alternative_type(alt.get('type', ''), alt.get('confidence', 0.0))

            fields.append(field)

        return fields

    def _create_document_type_suggestion(self,
                                       analysis_result_id: str,
                                       parsed_response: Dict[str, Any],
                                       model: str) -> DocumentTypeSuggestion:
        """Create DocumentTypeSuggestion from AI response"""
        doc_type = parsed_response['document_type']

        suggestion = DocumentTypeSuggestion.create_suggestion(
            analysis_result_id=analysis_result_id,
            suggested_type=doc_type['primary'],
            confidence=doc_type['confidence'],
            model_used=model
        )

        # Add alternative suggestions
        for alt in doc_type.get('alternatives', []):
            suggestion.add_alternative_type(
                alt['type'], alt['confidence'], alt.get('reason', 'AI alternative suggestion')
            )

        # Add classification factors (inferred from quality assessment)
        quality = parsed_response.get('quality_assessment', {})
        if quality.get('structure_score', 0) > 0.8:
            suggestion.add_classification_factor("Strong document structure")
        if quality.get('clarity_score', 0) > 0.8:
            suggestion.add_classification_factor("High visual clarity")

        return suggestion

    def _create_error_analysis_result(self,
                                    document_id: str,
                                    model: str,
                                    error: str,
                                    processing_time: float) -> AIAnalysisResult:
        """Create analysis result for failed analysis"""
        analysis_result = AIAnalysisResult.create_for_document(
            document_id=document_id,
            model_used=model
        )

        analysis_result.detected_document_type = "unknown"
        analysis_result.document_type_confidence = 0.0
        analysis_result.total_fields_detected = 0
        analysis_result.high_confidence_fields = 0
        analysis_result.processing_time_seconds = processing_time
        analysis_result.overall_quality_score = 0.0
        analysis_result.error_details = error

        return analysis_result

    def _analyze_with_retry_context(self,
                                   document: SampleDocument,
                                   prepared_data: Dict[str, Any],
                                   model: str,
                                   previous_errors: str,
                                   document_type_hint: str) -> AIAnalysisResult:
        """Perform analysis with retry context"""
        base_prompt = self.ANALYSIS_PROMPT_TEMPLATE.format(
            document_type_hint=document_type_hint
        )

        retry_prompt = self.RETRY_PROMPT_TEMPLATE.format(
            previous_errors=previous_errors,
            base_prompt=base_prompt
        )

        # Modify prepared messages with retry context
        messages = [
            {
                "role": "system",
                "content": "You are an expert document analysis AI. This is a retry analysis - please be extra careful and thorough."
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": retry_prompt}]
            }
        ]

        # Add document images
        if prepared_data['type'] == 'pdf' and prepared_data['pages']:
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{prepared_data['pages'][0]['image_base64']}"
                }
            })
        elif prepared_data['type'] == 'image':
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{prepared_data['image_base64']}"
                }
            })

        # Perform analysis with retry context
        start_time = time.time()

        try:
            analysis_result = AIAnalysisResult.create_for_document(
                document_id=document.id,
                model_used=model
            )
            analysis_result.retry_count = 1

            response = self._call_ai_model(model, messages)
            parsed_response = self._parse_ai_response(response)

            processing_time = time.time() - start_time
            self._populate_analysis_result(analysis_result, parsed_response, processing_time)

            # Save analysis result
            self.storage.save_analysis_result(analysis_result)

            # Create and save extracted fields
            extracted_fields = self._create_extracted_fields(analysis_result.id, parsed_response)
            for field in extracted_fields:
                self.storage.save_extracted_field(field)

            # Create and save document type suggestion
            doc_type_suggestion = self._create_document_type_suggestion(analysis_result.id, parsed_response, model)
            self.storage.save_document_type_suggestion(doc_type_suggestion)

            return analysis_result

        except Exception as e:
            processing_time = time.time() - start_time
            error_analysis = self._create_error_analysis_result(
                document.id, model, f"Retry failed: {str(e)}", processing_time
            )
            error_analysis.retry_count = 1
            self.storage.save_analysis_result(error_analysis)
            raise AIAnalysisError(f"Retry analysis failed: {str(e)}")

    def _count_fields_by_type(self, fields: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count fields by type"""
        counts = {}
        for field in fields:
            field_type = field.get('type', 'unknown')
            counts[field_type] = counts.get(field_type, 0) + 1
        return counts

    def get_supported_models(self) -> List[Dict[str, Any]]:
        """Get list of supported models"""
        return [
            {
                'id': 'groq/llama-3.1-70b-versatile',
                'name': 'Llama 3.1 70B (Groq)',
                'provider': 'groq',
                'good_for': ['general_analysis', 'high_accuracy']
            },
            {
                'id': 'mistral/mistral-small-latest',
                'name': 'Mistral Small (Mistral)',
                'provider': 'mistral',
                'good_for': ['fast_processing', 'structured_documents']
            },
            {
                'id': 'gpt-4o-mini',
                'name': 'GPT-4o Mini (OpenAI)',
                'provider': 'openai',
                'good_for': ['complex_documents', 'high_precision']
            }
        ]

    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get analysis service statistics"""
        storage_stats = self.storage.get_analysis_stats()

        service_stats = {
            'litellm_available': LITELLM_AVAILABLE,
            'default_model': self.default_model,
            'supported_models': len(self.get_supported_models()),
            'temperature': self.temperature
        }

        storage_stats.update(service_stats)
        return storage_stats