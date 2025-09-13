"""
Data models for AI schema generation
"""

from .sample_document import SampleDocument
from .analysis_result import AIAnalysisResult
from .extracted_field import ExtractedField
from .validation_rule_inference import ValidationRuleInference
from .document_type_suggestion import DocumentTypeSuggestion
from .generated_schema import GeneratedSchema

__all__ = [
    'SampleDocument',
    'AIAnalysisResult',
    'ExtractedField',
    'ValidationRuleInference',
    'DocumentTypeSuggestion',
    'GeneratedSchema'
]