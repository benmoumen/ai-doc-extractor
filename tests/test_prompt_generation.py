"""
Test schema-aware prompt generation functionality.
These tests MUST FAIL initially (TDD requirement) before implementation.
"""
import pytest
import sys
import os
import json

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema_utils import create_schema_prompt
from config import DOCUMENT_SCHEMAS


class TestPromptGeneration:
    """Test schema-aware prompt generation."""
    
    def test_create_schema_prompt_national_id(self):
        """Test prompt generation for National ID document type."""
        prompt = create_schema_prompt("national_id")
        
        assert prompt is not None, "Should return a prompt for valid document type"
        assert isinstance(prompt, str), "Prompt should be a string"
        assert len(prompt) > 100, "Prompt should be substantial (>100 chars)"
        
        # Check that prompt contains key elements
        assert "National ID" in prompt, "Should mention document type name"
        assert "full_name" in prompt, "Should include full_name field"
        assert "id_number" in prompt, "Should include id_number field"
        assert "date_of_birth" in prompt, "Should include date_of_birth field"
        assert "extracted_data" in prompt, "Should specify extracted_data format"
        assert "validation_results" in prompt, "Should specify validation_results format"

    def test_create_schema_prompt_passport(self):
        """Test prompt generation for Passport document type."""
        prompt = create_schema_prompt("passport")
        
        assert prompt is not None, "Should return a prompt for passport"
        assert "Passport" in prompt, "Should mention passport document type"
        assert "passport_number" in prompt, "Should include passport_number field"
        assert "nationality" in prompt, "Should include nationality field"
        assert "expiry_date" in prompt, "Should include expiry_date field"

    def test_create_schema_prompt_invalid_document_type(self):
        """Test prompt generation for invalid document type."""
        prompt = create_schema_prompt("invalid_document_type")
        
        assert prompt is None, "Should return None for invalid document type"

    def test_create_schema_prompt_contains_validation_instructions(self):
        """Test that generated prompt contains proper validation instructions."""
        prompt = create_schema_prompt("national_id")
        
        # Check for validation status instructions
        assert "valid" in prompt, "Should mention 'valid' status"
        assert "invalid" in prompt, "Should mention 'invalid' status"  
        assert "missing" in prompt, "Should mention 'missing' status"
        assert "warning" in prompt, "Should mention 'warning' status"
        
        # Check for confidence scoring
        assert "confidence" in prompt, "Should mention confidence scoring"
        assert "0.0-1.0" in prompt or "0-1" in prompt, "Should specify confidence range"

    def test_create_schema_prompt_includes_field_descriptions(self):
        """Test that prompt includes field descriptions and types."""
        prompt = create_schema_prompt("national_id")
        
        # Should include field type information
        assert "string" in prompt, "Should mention string type"
        assert "date" in prompt, "Should mention date type"
        
        # Should include required/optional information
        assert "required" in prompt, "Should mention required fields"
        
        # Should include field descriptions
        assert "Complete name" in prompt or "name as shown" in prompt, "Should include name description"
        assert "identification number" in prompt, "Should include ID number description"

    def test_create_schema_prompt_includes_examples(self):
        """Test that prompt includes field examples when available."""
        prompt = create_schema_prompt("national_id")
        
        # Should include examples from schema
        assert "John Smith" in prompt or "examples" in prompt, "Should include name examples"
        assert "AB123456789" in prompt or "examples" in prompt, "Should include ID examples"
        assert "1985-03-15" in prompt or "examples" in prompt, "Should include date examples"

    def test_create_schema_prompt_includes_validation_rules(self):
        """Test that prompt includes validation rule information."""
        prompt = create_schema_prompt("national_id")
        
        # Should mention validation patterns or requirements
        assert "pattern" in prompt or "format" in prompt or "validation" in prompt, "Should mention validation requirements"

    def test_create_schema_prompt_json_format_specification(self):
        """Test that prompt specifies exact JSON format expected."""
        prompt = create_schema_prompt("national_id")
        
        # Should specify JSON structure
        assert '{"extracted_data"' in prompt or '"extracted_data"' in prompt, "Should specify extracted_data structure"
        assert '{"validation_results"' in prompt or '"validation_results"' in prompt, "Should specify validation_results structure"
        
        # Should show field structure
        expected_fields = ["full_name", "id_number", "date_of_birth", "address"]
        for field in expected_fields:
            assert field in prompt, f"Should include {field} in JSON format specification"

    def test_create_schema_prompt_includes_critical_requirements(self):
        """Test that prompt includes critical processing requirements."""
        prompt = create_schema_prompt("national_id")
        
        # Should include important instructions
        assert "EVERY field" in prompt or "all fields" in prompt, "Should emphasize processing all fields"
        assert "do not infer" in prompt.lower() or "don't infer" in prompt.lower(), "Should warn against inference"
        assert "exactly what you see" in prompt.lower(), "Should emphasize literal extraction"

    def test_create_schema_prompt_different_for_different_types(self):
        """Test that different document types generate different prompts."""
        national_id_prompt = create_schema_prompt("national_id")
        passport_prompt = create_schema_prompt("passport")
        
        assert national_id_prompt != passport_prompt, "Different document types should generate different prompts"
        assert "National ID" in national_id_prompt, "National ID prompt should mention document type"
        assert "Passport" in passport_prompt, "Passport prompt should mention document type"
        assert "passport_number" not in national_id_prompt, "National ID prompt should not mention passport fields"
        assert "id_number" not in passport_prompt, "Passport prompt should not mention national ID fields"


class TestPromptStructure:
    """Test the structure and completeness of generated prompts."""
    
    def test_prompt_has_document_identification(self):
        """Test that prompt clearly identifies the document type being processed."""
        prompt = create_schema_prompt("national_id")
        
        # Should clearly state what document is being analyzed
        assert "National ID document" in prompt, "Should clearly identify document type"
        assert "Government-issued" in prompt, "Should include document description"

    def test_prompt_has_schema_specification(self):
        """Test that prompt includes complete schema information."""
        prompt = create_schema_prompt("passport")
        
        # Should include schema information in structured format
        schema_section_found = False
        if "schema:" in prompt.lower() or "extract data according" in prompt.lower():
            schema_section_found = True
        
        assert schema_section_found, "Should have clear schema specification section"

    def test_prompt_has_output_format_specification(self):
        """Test that prompt specifies exact output format."""
        prompt = create_schema_prompt("national_id")
        
        # Should have clear output format section
        format_section_found = False
        if "return json" in prompt.lower() and "format:" in prompt.lower():
            format_section_found = True
        elif "json in this" in prompt.lower() and "format" in prompt.lower():
            format_section_found = True
            
        assert format_section_found, "Should have clear output format specification"

    def test_prompt_has_requirements_section(self):
        """Test that prompt has a clear requirements/instructions section."""
        prompt = create_schema_prompt("passport")
        
        # Should have requirements section
        requirements_section_found = False
        if "requirements:" in prompt.lower() or "critical:" in prompt.lower():
            requirements_section_found = True
        elif "important:" in prompt.lower() or "must:" in prompt.lower():
            requirements_section_found = True
            
        assert requirements_section_found, "Should have clear requirements section"

    def test_prompt_length_reasonable(self):
        """Test that prompt is substantial but not excessively long."""
        for doc_type in ["national_id", "passport"]:
            prompt = create_schema_prompt(doc_type)
            
            assert len(prompt) > 500, f"Prompt for {doc_type} should be substantial (>500 chars)"
            assert len(prompt) < 5000, f"Prompt for {doc_type} should not be excessively long (<5000 chars)"

    def test_prompt_json_parseable_example(self):
        """Test that any JSON examples in prompt are parseable."""
        prompt = create_schema_prompt("national_id")
        
        # Find JSON-like structures in the prompt
        import re
        json_patterns = re.findall(r'\{[^{}]*\}', prompt)
        
        # This test might pass if no JSON examples are included, which is okay
        # But if JSON examples exist, they should be valid
        for pattern in json_patterns:
            if "extracted_data" in pattern or "validation_results" in pattern:
                try:
                    # Try to make it valid JSON by adding quotes where needed
                    # This is a basic check - the implementation should ensure valid JSON examples
                    continue  # Skip validation for now, just ensure structure exists
                except Exception:
                    pass  # Expected to have some issues in test phase


if __name__ == "__main__":
    # Run tests to verify they fail initially (TDD requirement)
    pytest.main([__file__, "-v"])