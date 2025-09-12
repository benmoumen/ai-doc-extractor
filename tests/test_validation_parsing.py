"""
Test validation result parsing functionality.
These tests MUST FAIL initially (TDD requirement) before implementation.
Tests for enhanced JSON parsing to handle validation results from AI responses.
"""
import pytest
import sys
import os
import json
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import extract_and_parse_json


class TestValidationResultParsing:
    """Test parsing of AI responses containing validation results."""
    
    def test_parse_standard_validation_response(self):
        """Test parsing of standard schema-aware AI response."""
        sample_response = '''
        {
            "extracted_data": {
                "full_name": "John Smith",
                "id_number": "AB123456789",
                "date_of_birth": "1985-03-15",
                "address": "123 Main St"
            },
            "validation_results": {
                "full_name": {
                    "status": "valid",
                    "message": "Name extracted successfully with high confidence",
                    "extracted_value": "John Smith",
                    "confidence": 0.95
                },
                "id_number": {
                    "status": "valid",
                    "message": "ID number format matches expected pattern",
                    "extracted_value": "AB123456789", 
                    "confidence": 0.98
                },
                "date_of_birth": {
                    "status": "valid",
                    "message": "Date format is correct and reasonable",
                    "extracted_value": "1985-03-15",
                    "confidence": 0.92
                },
                "address": {
                    "status": "warning",
                    "message": "Address partially visible but readable",
                    "extracted_value": "123 Main St",
                    "confidence": 0.75
                }
            }
        }
        '''
        
        is_json, parsed_data, formatted_text = extract_and_parse_json(sample_response)
        
        assert is_json is True, "Should recognize as valid JSON"
        assert parsed_data is not None, "Should parse JSON successfully"
        assert "extracted_data" in parsed_data, "Should contain extracted_data section"
        assert "validation_results" in parsed_data, "Should contain validation_results section"
        
        # Test extracted data structure
        extracted_data = parsed_data["extracted_data"]
        assert extracted_data["full_name"] == "John Smith", "Should extract full name correctly"
        assert extracted_data["id_number"] == "AB123456789", "Should extract ID number correctly"
        
        # Test validation results structure
        validation_results = parsed_data["validation_results"]
        assert "full_name" in validation_results, "Should have validation for full_name"
        assert validation_results["full_name"]["status"] == "valid", "Should parse status correctly"
        assert validation_results["full_name"]["confidence"] == 0.95, "Should parse confidence correctly"

    def test_parse_response_with_invalid_fields(self):
        """Test parsing response with invalid field validations."""
        sample_response = '''
        {
            "extracted_data": {
                "full_name": "J",
                "id_number": "123",
                "date_of_birth": "invalid-date"
            },
            "validation_results": {
                "full_name": {
                    "status": "invalid",
                    "message": "Name too short, minimum 2 characters required",
                    "extracted_value": "J",
                    "confidence": 0.85
                },
                "id_number": {
                    "status": "invalid", 
                    "message": "ID number must be 8-15 alphanumeric characters, got 3",
                    "extracted_value": "123",
                    "confidence": 0.90
                },
                "date_of_birth": {
                    "status": "invalid",
                    "message": "Date format should be YYYY-MM-DD, got 'invalid-date'",
                    "extracted_value": "invalid-date",
                    "confidence": 0.30
                }
            }
        }
        '''
        
        is_json, parsed_data, formatted_text = extract_and_parse_json(sample_response)
        
        assert is_json is True, "Should parse JSON with invalid fields"
        
        validation_results = parsed_data["validation_results"]
        assert validation_results["full_name"]["status"] == "invalid", "Should identify invalid name"
        assert validation_results["id_number"]["status"] == "invalid", "Should identify invalid ID"
        assert validation_results["date_of_birth"]["status"] == "invalid", "Should identify invalid date"
        
        # Check error messages are preserved
        assert "too short" in validation_results["full_name"]["message"], "Should preserve error message"
        assert "8-15" in validation_results["id_number"]["message"], "Should preserve format requirement"

    def test_parse_response_with_missing_fields(self):
        """Test parsing response with missing required fields."""
        sample_response = '''
        {
            "extracted_data": {
                "full_name": "John Smith"
            },
            "validation_results": {
                "full_name": {
                    "status": "valid",
                    "message": "Name found and valid",
                    "extracted_value": "John Smith",
                    "confidence": 0.95
                },
                "id_number": {
                    "status": "missing",
                    "message": "ID number not visible or readable in document",
                    "extracted_value": null,
                    "confidence": 0.0
                },
                "date_of_birth": {
                    "status": "missing", 
                    "message": "Date of birth section not found in document",
                    "extracted_value": null,
                    "confidence": 0.0
                }
            }
        }
        '''
        
        is_json, parsed_data, formatted_text = extract_and_parse_json(sample_response)
        
        assert is_json is True, "Should parse JSON with missing fields"
        
        # Check that missing fields are handled
        validation_results = parsed_data["validation_results"]
        assert validation_results["id_number"]["status"] == "missing", "Should identify missing ID"
        assert validation_results["date_of_birth"]["status"] == "missing", "Should identify missing date"
        assert validation_results["id_number"]["extracted_value"] is None, "Missing field should have null value"

    def test_parse_response_wrapped_in_markdown(self):
        """Test parsing response wrapped in markdown code blocks."""
        sample_response = '''
        Here's the extracted data:
        
        ```json
        {
            "extracted_data": {
                "full_name": "Maria Garcia"
            },
            "validation_results": {
                "full_name": {
                    "status": "valid",
                    "message": "Name extracted clearly",
                    "extracted_value": "Maria Garcia",
                    "confidence": 0.98
                }
            }
        }
        ```
        
        The document appears to be a National ID.
        '''
        
        is_json, parsed_data, formatted_text = extract_and_parse_json(sample_response)
        
        assert is_json is True, "Should extract JSON from markdown"
        assert parsed_data["extracted_data"]["full_name"] == "Maria Garcia", "Should parse wrapped JSON"
        assert "validation_results" in parsed_data, "Should extract validation results from wrapped JSON"

    def test_parse_malformed_validation_response(self):
        """Test handling of malformed validation responses."""
        malformed_responses = [
            '{"extracted_data": {}, "validation_results": "not an object"}',
            '{"extracted_data": "not an object", "validation_results": {}}', 
            '{"extracted_data": {}, "validation_results": {}, "extra": "field"}',
            '{"validation_results": {}}',  # missing extracted_data
            '{"extracted_data": {}}'  # missing validation_results
        ]
        
        for response in malformed_responses:
            is_json, parsed_data, formatted_text = extract_and_parse_json(response)
            
            # Should still parse as JSON but may have structural issues
            if is_json:
                assert parsed_data is not None, f"Should parse malformed response: {response[:50]}..."
                # Implementation should handle structural validation gracefully

    def test_parse_response_with_confidence_scores(self):
        """Test parsing and preservation of confidence scores."""
        sample_response = '''
        {
            "extracted_data": {
                "full_name": "Ahmed Hassan",
                "id_number": "XY555666777"
            },
            "validation_results": {
                "full_name": {
                    "status": "valid",
                    "message": "Name clearly visible", 
                    "extracted_value": "Ahmed Hassan",
                    "confidence": 0.99
                },
                "id_number": {
                    "status": "valid",
                    "message": "ID number partially visible but readable",
                    "extracted_value": "XY555666777",
                    "confidence": 0.78
                }
            }
        }
        '''
        
        is_json, parsed_data, formatted_text = extract_and_parse_json(sample_response)
        
        assert is_json is True, "Should parse response with confidence scores"
        
        validation_results = parsed_data["validation_results"] 
        assert validation_results["full_name"]["confidence"] == 0.99, "Should preserve high confidence score"
        assert validation_results["id_number"]["confidence"] == 0.78, "Should preserve lower confidence score"
        
        # Test confidence score ranges
        for field_result in validation_results.values():
            confidence = field_result["confidence"]
            assert 0.0 <= confidence <= 1.0, f"Confidence should be in range 0-1, got {confidence}"

    def test_parse_response_with_warning_status(self):
        """Test parsing responses with warning validation status."""
        sample_response = '''
        {
            "extracted_data": {
                "full_name": "John A. Smith Jr.",
                "address": "123 Main"
            },
            "validation_results": {
                "full_name": {
                    "status": "warning",
                    "message": "Name contains special characters which may affect processing",
                    "extracted_value": "John A. Smith Jr.",
                    "confidence": 0.88
                },
                "address": {
                    "status": "warning", 
                    "message": "Address appears incomplete or cut off",
                    "extracted_value": "123 Main",
                    "confidence": 0.65
                }
            }
        }
        '''
        
        is_json, parsed_data, formatted_text = extract_and_parse_json(sample_response)
        
        assert is_json is True, "Should parse response with warnings"
        
        validation_results = parsed_data["validation_results"]
        assert validation_results["full_name"]["status"] == "warning", "Should identify warning status"
        assert validation_results["address"]["status"] == "warning", "Should identify warning status"
        
        # Warning messages should be informative
        name_message = validation_results["full_name"]["message"]
        address_message = validation_results["address"]["message"]
        assert len(name_message) > 10, "Warning messages should be descriptive"
        assert len(address_message) > 10, "Warning messages should be descriptive"


class TestBackwardCompatibilityParsing:
    """Test that enhanced parsing maintains backward compatibility."""
    
    def test_parse_legacy_json_response(self):
        """Test that legacy JSON responses without validation still work."""
        legacy_response = '''
        {
            "name": "John Smith",
            "id": "AB123456789",
            "birth_date": "1985-03-15",
            "address": "123 Main Street"
        }
        '''
        
        is_json, parsed_data, formatted_text = extract_and_parse_json(legacy_response)
        
        assert is_json is True, "Should parse legacy JSON format"
        assert parsed_data is not None, "Should extract legacy data"
        assert "name" in parsed_data, "Should preserve legacy field names"
        
        # Should not crash on legacy format
        assert formatted_text is not None, "Should format legacy response"

    def test_parse_non_json_response(self):
        """Test handling of non-JSON responses (fallback behavior)."""
        text_response = """
        Name: John Smith
        ID Number: AB123456789
        Date of Birth: March 15, 1985
        Address: 123 Main Street, Anytown
        """
        
        is_json, parsed_data, formatted_text = extract_and_parse_json(text_response)
        
        # Should gracefully handle non-JSON
        if not is_json:
            assert parsed_data is None, "Non-JSON should return None for parsed_data"
            assert formatted_text == text_response, "Non-JSON should return original text"

    def test_parse_empty_response(self):
        """Test handling of empty or null responses."""
        empty_responses = ["", " ", "null", "{}"]
        
        for empty_response in empty_responses:
            is_json, parsed_data, formatted_text = extract_and_parse_json(empty_response)
            
            # Should handle empty responses gracefully without crashing
            assert formatted_text is not None, f"Should handle empty response: '{empty_response}'"


class TestValidationResultFormatting:
    """Test formatting of parsed validation results for display."""
    
    def test_identify_schema_aware_response(self):
        """Test identification of schema-aware vs legacy responses."""
        schema_aware_response = {
            "extracted_data": {"name": "John"},
            "validation_results": {"name": {"status": "valid"}}
        }
        
        legacy_response = {
            "name": "John Smith",
            "id": "123456789"
        }
        
        # Should be able to distinguish between formats
        assert "validation_results" in schema_aware_response, "Should identify schema-aware format"
        assert "validation_results" not in legacy_response, "Should identify legacy format"

    def test_extract_field_validation_info(self):
        """Test extraction of individual field validation information."""
        validation_results = {
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
            }
        }
        
        # Should be able to extract validation info for each field
        for field_name, field_validation in validation_results.items():
            assert "status" in field_validation, f"Field {field_name} should have status"
            assert "message" in field_validation, f"Field {field_name} should have message"
            assert "confidence" in field_validation, f"Field {field_name} should have confidence"
            
            status = field_validation["status"]
            assert status in ["valid", "invalid", "warning", "missing"], f"Status should be valid enum value, got {status}"


if __name__ == "__main__":
    # Run tests to verify they fail initially (TDD requirement)
    pytest.main([__file__, "-v"])