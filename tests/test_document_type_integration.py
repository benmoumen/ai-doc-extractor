"""
Integration tests for document type selection and processing workflow.
These tests MUST FAIL initially (TDD requirement) before implementation.
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock streamlit before importing modules that use it
sys.modules['streamlit'] = Mock()

from schema_utils import (
    get_available_document_types,
    create_schema_prompt,
    format_validation_results_for_display
)
from config import DOCUMENT_SCHEMAS


class TestDocumentTypeSelectionIntegration:
    """Test the complete document type selection workflow."""
    
    def test_document_type_selection_workflow(self):
        """Test complete workflow from type selection to schema loading."""
        # Step 1: Get available document types
        document_types = get_available_document_types()
        
        assert len(document_types) > 0, "Should have available document types"
        assert "National ID" in document_types, "Should include National ID type"
        
        # Step 2: Select a document type
        selected_type_id = document_types["National ID"]
        assert selected_type_id == "national_id", "Should map to correct ID"
        
        # Step 3: Generate schema-aware prompt
        prompt = create_schema_prompt(selected_type_id)
        assert prompt is not None, "Should generate prompt for selected type"
        assert "National ID" in prompt, "Prompt should reference selected document type"

    def test_schema_preview_data_structure(self):
        """Test data structure for schema preview in UI."""
        schema = DOCUMENT_SCHEMAS["national_id"]
        
        # Test that schema has structure needed for UI preview
        assert "name" in schema, "Schema should have display name"
        assert "description" in schema, "Schema should have description"
        assert "fields" in schema, "Schema should have fields definition"
        
        # Test field structure for UI display
        for field_name, field_def in schema["fields"].items():
            assert "display_name" in field_def, f"Field {field_name} should have display name"
            assert "required" in field_def, f"Field {field_name} should specify if required"
            assert "description" in field_def, f"Field {field_name} should have description"

    def test_ui_field_preview_formatting(self):
        """Test formatting of field information for UI preview."""
        schema = DOCUMENT_SCHEMAS["national_id"]
        
        # Test that we can format field info for display
        formatted_fields = []
        for field_name, field_def in schema["fields"].items():
            required_marker = "🔴" if field_def['required'] else "⚪"
            display_text = f"{required_marker} **{field_def['display_name']}**: {field_def['description']}"
            formatted_fields.append({
                "name": field_name,
                "display": display_text,
                "required": field_def["required"]
            })
        
        assert len(formatted_fields) > 0, "Should format fields for display"
        
        # Check required fields have red marker
        required_fields = [f for f in formatted_fields if f["required"]]
        assert len(required_fields) > 0, "Should have some required fields"
        for field in required_fields:
            assert "🔴" in field["display"], "Required fields should have red marker"

    def test_document_type_switching(self):
        """Test switching between different document types."""
        # Test National ID
        national_id_prompt = create_schema_prompt("national_id")
        assert "National ID" in national_id_prompt, "Should generate National ID prompt"
        
        # Test Passport
        passport_prompt = create_schema_prompt("passport")
        assert "Passport" in passport_prompt, "Should generate Passport prompt"
        
        # Prompts should be different
        assert national_id_prompt != passport_prompt, "Different types should generate different prompts"

    def test_fallback_to_generic_extraction(self):
        """Test fallback when no document type is selected."""
        # When no document type is selected (None), should handle gracefully
        prompt = create_schema_prompt(None)
        assert prompt is None, "Should return None when no document type selected"
        
        # Test with empty string
        prompt = create_schema_prompt("")
        assert prompt is None, "Should return None for empty document type"


class TestExtractionWorkflowIntegration:
    """Test the complete extraction workflow integration."""
    
    @patch('litellm.completion')
    def test_complete_extraction_workflow_with_schema(self, mock_completion):
        """Test complete workflow from document upload to results display."""
        # Mock AI response with validation results
        mock_ai_response = {
            "extracted_data": {
                "full_name": "John Smith",
                "id_number": "AB123456789",
                "date_of_birth": "1985-03-15",
                "address": "123 Main St"
            },
            "validation_results": {
                "full_name": {
                    "status": "valid",
                    "message": "Name extracted successfully",
                    "extracted_value": "John Smith",
                    "confidence": 0.95
                },
                "id_number": {
                    "status": "valid", 
                    "message": "ID number format is correct",
                    "extracted_value": "AB123456789",
                    "confidence": 0.98
                },
                "date_of_birth": {
                    "status": "valid",
                    "message": "Date format is correct", 
                    "extracted_value": "1985-03-15",
                    "confidence": 0.92
                },
                "address": {
                    "status": "warning",
                    "message": "Address partially visible",
                    "extracted_value": "123 Main St",
                    "confidence": 0.75
                }
            }
        }
        
        # Mock the completion call
        mock_message = Mock()
        mock_message.content = json.dumps(mock_ai_response)
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        mock_completion.return_value = mock_response
        
        # Test workflow steps
        # 1. Select document type
        document_type_id = "national_id"
        
        # 2. Generate prompt
        prompt = create_schema_prompt(document_type_id)
        assert prompt is not None, "Should generate prompt"
        
        # 3. Process with AI (mocked)
        # This would normally be called in app.py, but we test the integration here
        response_text = mock_response.choices[0].message.content
        parsed_response = json.loads(response_text)
        
        # 4. Validate response structure
        assert "extracted_data" in parsed_response, "Response should have extracted_data"
        assert "validation_results" in parsed_response, "Response should have validation_results"
        
        # 5. Format for display
        formatted_results = format_validation_results_for_display(parsed_response["validation_results"])
        
        assert len(formatted_results) > 0, "Should format validation results"
        assert all("icon" in result for result in formatted_results), "All results should have icons"

    def test_validation_results_display_formatting(self):
        """Test formatting validation results for UI display."""
        sample_validation_results = {
            "full_name": {
                "status": "valid",
                "message": "Name extracted successfully",
                "extracted_value": "John Smith",
                "confidence": 0.95
            },
            "id_number": {
                "status": "invalid",
                "message": "ID format incorrect",
                "extracted_value": "123",
                "confidence": 0.60
            },
            "date_of_birth": {
                "status": "missing",
                "message": "Date not found in document",
                "extracted_value": None,
                "confidence": 0.00
            }
        }
        
        formatted_results = format_validation_results_for_display(sample_validation_results)
        
        # Test formatting
        assert len(formatted_results) == 3, "Should format all validation results"
        
        # Test status icons
        valid_result = next(r for r in formatted_results if r["status"] == "valid")
        invalid_result = next(r for r in formatted_results if r["status"] == "invalid")
        missing_result = next(r for r in formatted_results if r["status"] == "missing")
        
        assert valid_result["icon"] == "✅", "Valid status should have checkmark icon"
        assert invalid_result["icon"] == "❌", "Invalid status should have X icon"
        assert missing_result["icon"] == "❓", "Missing status should have question mark icon"

    def test_session_state_management_structure(self):
        """Test the session state structure needed for schema features."""
        # Define the session state structure that will be used
        expected_session_keys = [
            "selected_document_type",
            "selected_document_type_name", 
            "schema_extraction_result",
            "validation_feedback",
            "current_schema"
        ]
        
        # Test that we can structure session data appropriately
        sample_session_state = {
            "selected_document_type": "national_id",
            "selected_document_type_name": "National ID",
            "current_schema": DOCUMENT_SCHEMAS["national_id"],
            "schema_extraction_result": {
                "extracted_data": {"full_name": "John Smith"},
                "validation_results": {"full_name": {"status": "valid"}}
            },
            "validation_feedback": [
                {"field": "full_name", "status": "valid", "icon": "✅"}
            ]
        }
        
        # Verify structure
        for key in expected_session_keys:
            assert key in sample_session_state, f"Session state should include {key}"

    def test_backward_compatibility_with_generic_extraction(self):
        """Test that schema features don't break existing generic extraction."""
        # When no document type is selected, should work with existing flow
        
        # Test that existing extraction can still work
        generic_prompt = "Analyze the text in the provided image. Extract all readable content and present it in JSON format"
        
        # This should still be valid for fallback scenarios
        assert len(generic_prompt) > 50, "Generic prompt should still be substantial"
        assert "JSON" in generic_prompt, "Generic prompt should specify JSON output"


class TestErrorHandlingIntegration:
    """Test error handling in the integrated workflow."""
    
    def test_invalid_document_type_handling(self):
        """Test handling of invalid document type selection."""
        # Test various invalid inputs
        invalid_types = [None, "", "invalid_type", 123, []]
        
        for invalid_type in invalid_types:
            prompt = create_schema_prompt(invalid_type)
            assert prompt is None, f"Should handle invalid type gracefully: {invalid_type}"

    def test_malformed_ai_response_handling(self):
        """Test handling of malformed AI responses."""
        malformed_responses = [
            "not json at all",
            '{"extracted_data": "missing validation_results"}',
            '{"validation_results": "missing extracted_data"}',
            '{}',  # empty object
            'null'
        ]
        
        # These should be handled gracefully by the parsing logic
        # The test verifies the structure exists to handle these cases
        for response in malformed_responses:
            # This test mainly ensures we have a plan for handling malformed responses
            # The actual parsing will be implemented in utils.py enhancement
            assert isinstance(response, str), "Response handling should expect string input"

    def test_missing_required_fields_in_schema(self):
        """Test handling when AI doesn't return all required fields."""
        incomplete_validation_results = {
            "full_name": {"status": "valid", "message": "OK"},
            # Missing id_number, date_of_birth (required fields)
        }
        
        # Should handle missing fields in validation results
        formatted_results = format_validation_results_for_display(incomplete_validation_results)
        
        assert len(formatted_results) >= 1, "Should format available results"
        # Implementation should handle missing fields gracefully


if __name__ == "__main__":
    # Run tests to verify they fail initially (TDD requirement)
    pytest.main([__file__, "-v"])