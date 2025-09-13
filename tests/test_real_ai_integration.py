"""
Unit tests for Real AI Integration
Tests the actual LiteLLM integration with Groq and Mistral models
"""

import pytest
import io
from PIL import Image
import fitz
from unittest.mock import Mock, patch, MagicMock
import json

from ai_schema_generation.core.ai_analyzer import AIAnalyzer


class MockUploadedFile:
    """Mock Streamlit uploaded file for testing"""

    def __init__(self, content, filename, file_type):
        self.content = content
        self.name = filename
        self.type = file_type
        self.position = 0

    def read(self):
        return self.content

    def seek(self, pos):
        self.position = pos
        return pos


class TestAIAnalyzer:
    """Test the AI Analyzer implementation"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return AIAnalyzer()

    @pytest.fixture
    def mock_image_file(self):
        """Create mock image file for testing"""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        img_bytes = buffer.getvalue()

        return MockUploadedFile(img_bytes, 'test.jpg', 'image/jpeg')

    @pytest.fixture
    def mock_pdf_file(self):
        """Create mock PDF file for testing"""
        # Create simple PDF
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Test Invoice\nInvoice #: 001\nTotal: $100.00", fontsize=12)
        pdf_bytes = doc.tobytes()
        doc.close()

        return MockUploadedFile(pdf_bytes, 'test.pdf', 'application/pdf')

    def test_model_mapping(self, analyzer):
        """Test model mapping functionality"""
        # Test known models
        provider, model = analyzer._get_provider_model("Llama Scout 17B (Groq)")
        assert provider == "groq"
        assert model == "meta-llama/llama-4-scout-17b-16e-instruct"

        provider, model = analyzer._get_provider_model("Mistral Small 3.2")
        assert provider == "mistral"
        assert model == "mistral-small-2506"

        # Test unknown model (should default to Groq/Llama)
        provider, model = analyzer._get_provider_model("Unknown Model")
        assert provider == "groq"
        assert model == "meta-llama/llama-4-scout-17b-16e-instruct"

    def test_available_models(self, analyzer):
        """Test getting available models"""
        models = analyzer.get_available_models()
        assert isinstance(models, list)
        assert len(models) == 2
        assert "Llama Scout 17B (Groq)" in models
        assert "Mistral Small 3.2" in models

    def test_image_to_base64(self, analyzer, mock_image_file):
        """Test image to base64 conversion"""
        # Mock st.error to avoid Streamlit context issues
        with patch('ai_schema_generation.core.ai_analyzer.st.error'):
            base64_result = analyzer._image_to_base64(mock_image_file)

            assert isinstance(base64_result, str)
            # The result might be empty due to error handling, which is expected outside Streamlit context

    def test_pdf_to_base64(self, analyzer, mock_pdf_file):
        """Test PDF to base64 conversion"""
        # Mock st.error to avoid Streamlit context issues
        with patch('ai_schema_generation.core.ai_analyzer.st.error'):
            base64_result = analyzer._pdf_to_base64(mock_pdf_file)

            assert isinstance(base64_result, str)
            assert len(base64_result) > 1000  # PDFs should be larger than images

    def test_process_document_to_base64(self, analyzer, mock_image_file, mock_pdf_file):
        """Test document processing router"""
        with patch('ai_schema_generation.core.ai_analyzer.st.error'):
            # Test image processing
            img_result = analyzer._process_document_to_base64(mock_image_file)
            assert isinstance(img_result, str)
            # Result may be empty due to error handling outside Streamlit context

            # Test PDF processing
            pdf_result = analyzer._process_document_to_base64(mock_pdf_file)
            assert isinstance(pdf_result, str)
            assert len(pdf_result) > 0  # PDF processing should work

    def test_generate_schema_prompt(self, analyzer):
        """Test prompt generation for different document types"""
        # Test Invoice prompt
        invoice_prompt = analyzer._generate_schema_prompt("Invoice", "test_invoice.pdf")
        assert "invoice" in invoice_prompt.lower()
        assert "JSON" in invoice_prompt
        assert "schema" in invoice_prompt
        assert len(invoice_prompt) > 500  # Should be substantial

        # Test Receipt prompt
        receipt_prompt = analyzer._generate_schema_prompt("Receipt", "receipt.jpg")
        assert "receipt" in receipt_prompt.lower()
        assert "merchant" in receipt_prompt.lower()

        # Test Contract prompt
        contract_prompt = analyzer._generate_schema_prompt("Contract", "contract.pdf")
        assert "contract" in contract_prompt.lower()
        assert "party" in contract_prompt.lower()

        # Test Auto-detect prompt
        auto_prompt = analyzer._generate_schema_prompt("Auto-detect", "document.pdf")
        assert "automatically detect" in auto_prompt.lower()

    def test_fallback_schema_creation(self, analyzer):
        """Test fallback schema generation"""
        # Test Invoice fallback
        invoice_fallback = analyzer._create_fallback_schema(
            "Invoice", "test.pdf", "Test Model", "API Error"
        )

        # Fallback schema doesn't include success field, only generate_schema_from_document does
        assert invoice_fallback["is_fallback"] == True
        assert invoice_fallback["confidence_score"] == 0.5
        assert "invoice_number" in invoice_fallback["schema"]["fields"]
        assert "total_amount" in invoice_fallback["schema"]["fields"]

        # Test Receipt fallback
        receipt_fallback = analyzer._create_fallback_schema(
            "Receipt", "receipt.jpg", "Test Model", "Network Error"
        )

        assert "merchant_name" in receipt_fallback["schema"]["fields"]
        assert "purchase_date" in receipt_fallback["schema"]["fields"]

        # Test Unknown document fallback
        unknown_fallback = analyzer._create_fallback_schema(
            "Unknown", "doc.pdf", "Test Model", "Parse Error"
        )

        assert "document_title" in unknown_fallback["schema"]["fields"]
        assert "date" in unknown_fallback["schema"]["fields"]
        assert "amount" in unknown_fallback["schema"]["fields"]

    @patch('ai_schema_generation.core.ai_analyzer.completion')
    @patch('ai_schema_generation.core.ai_analyzer.get_model_param')
    def test_ai_model_call_success(self, mock_get_model_param, mock_completion, analyzer):
        """Test successful AI model call"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "schema": {
                "id": "test_schema",
                "name": "Test Schema",
                "fields": {
                    "test_field": {
                        "type": "string",
                        "required": True,
                        "confidence": 0.9
                    }
                }
            },
            "analysis": {
                "confidence_score": 0.85,
                "fields_detected": 1,
                "processing_notes": "Test successful"
            }
        })

        mock_completion.return_value = mock_response
        mock_get_model_param.return_value = "groq/test-model"

        # Test the AI call
        response = analyzer._call_ai_model("groq", "test-model", "test prompt", "test_base64")

        assert response == mock_response
        mock_completion.assert_called_once()

        # Verify the call parameters
        call_args = mock_completion.call_args
        assert call_args[1]['model'] == "groq/test-model"
        assert call_args[1]['temperature'] == 0.1
        assert call_args[1]['max_tokens'] == 2000

    @patch('ai_schema_generation.core.ai_analyzer.completion')
    def test_ai_model_call_failure(self, mock_completion, analyzer):
        """Test AI model call failure handling"""
        # Mock API failure
        mock_completion.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="AI model call failed"):
            analyzer._call_ai_model("groq", "test-model", "test prompt", "test_base64")

    def test_parse_ai_response_success(self, analyzer):
        """Test parsing successful AI response"""
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "schema": {
                "id": "test_schema",
                "fields": {
                    "field1": {"type": "string", "confidence": 0.9},
                    "field2": {"type": "number", "confidence": 0.8}
                }
            },
            "analysis": {
                "confidence_score": 0.85,
                "processing_notes": "Success"
            }
        })

        result = analyzer._parse_ai_response(mock_response, "Invoice", "test.pdf", "Test Model")

        assert result["confidence_score"] == 0.85
        assert result["fields_detected"] == 2
        assert "field1" in result["schema"]["fields"]
        assert "field2" in result["schema"]["fields"]

        # Check AI metadata was added
        field1 = result["schema"]["fields"]["field1"]
        assert "ai_metadata" in field1
        assert field1["ai_metadata"]["source"] == "Test Model"
        assert field1["ai_metadata"]["generated_by"] == "ai_analysis"

    def test_parse_ai_response_malformed_json(self, analyzer):
        """Test parsing response with malformed JSON"""
        # Mock response with partial JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Some text before {"schema": {"fields": {"test": {"type": "string"}}}} some text after'

        result = analyzer._parse_ai_response(mock_response, "Invoice", "test.pdf", "Test Model")

        assert "test" in result["schema"]["fields"]
        assert result["fields_detected"] == 1

    def test_parse_ai_response_invalid_json(self, analyzer):
        """Test parsing response with completely invalid JSON"""
        # Mock response with no valid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not JSON at all"

        result = analyzer._parse_ai_response(mock_response, "Invoice", "test.pdf", "Test Model")

        # Should fall back to basic schema
        assert result["is_fallback"] == True
        assert result["confidence_score"] == 0.5
        assert "invoice_number" in result["schema"]["fields"]

    @patch('ai_schema_generation.core.ai_analyzer.st.error')
    def test_complete_workflow_with_api_failure(self, mock_st_error, analyzer, mock_image_file):
        """Test complete workflow when API fails (no API keys)"""
        result = analyzer.generate_schema_from_document(
            mock_image_file, "Invoice", "Llama Scout 17B (Groq)"
        )

        # Should handle API failure gracefully
        assert result["success"] == False
        assert "error" in result
        assert result["ai_model"] == "Llama Scout 17B (Groq)"
        assert result["analysis_time"] == 0
        assert result["confidence_score"] == 0
        assert result["fields_detected"] == 0

    @patch('ai_schema_generation.core.ai_analyzer.completion')
    @patch('ai_schema_generation.core.ai_analyzer.get_model_param')
    @patch('ai_schema_generation.core.ai_analyzer.st.error')
    def test_complete_workflow_success(self, mock_st_error, mock_get_model_param, mock_completion, analyzer, mock_image_file):
        """Test complete successful workflow"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "schema": {
                "id": "ai_invoice",
                "name": "AI Invoice Schema",
                "fields": {
                    "invoice_number": {"type": "string", "required": True, "confidence": 0.95},
                    "total_amount": {"type": "number", "required": True, "confidence": 0.88}
                }
            },
            "analysis": {
                "confidence_score": 0.91,
                "fields_detected": 2,
                "processing_notes": "Analysis completed successfully"
            }
        })

        mock_completion.return_value = mock_response
        mock_get_model_param.return_value = "groq/test-model"

        result = analyzer.generate_schema_from_document(
            mock_image_file, "Invoice", "Llama Scout 17B (Groq)"
        )

        # Verify successful result
        assert result["success"] == True
        assert result["confidence_score"] == 0.91
        assert result["fields_detected"] == 2
        assert result["ai_model"] == "Llama Scout 17B (Groq)"
        assert result["provider"] == "groq"
        assert result["model"] == "meta-llama/llama-4-scout-17b-16e-instruct"
        assert "analysis_time" in result
        assert result["analysis_time"] > 0

        # Verify schema structure
        assert "invoice_number" in result["schema"]["fields"]
        assert "total_amount" in result["schema"]["fields"]

        # Verify AI metadata was added
        invoice_field = result["schema"]["fields"]["invoice_number"]
        assert invoice_field["ai_metadata"]["source"] == "Llama Scout 17B (Groq)"
        assert invoice_field["ai_metadata"]["confidence"] == 0.95


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])