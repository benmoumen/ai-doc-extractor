"""
Validation Builder Contract Tests
These tests define the expected behavior of validation rule builder components.
MUST FAIL initially - implementation comes after tests pass.
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.contract
class TestValidationBuilderContract:
    """Contract tests for validation rule builder interface"""
    
    def test_render_validation_builder_contract(self):
        """Contract: Validation builder renders rule creation interface"""
        from schema_management.ui.validation_builder import render_validation_builder
        
        field_data = {"name": "test_field", "type": "text"}
        templates = [
            {"id": "required_template", "name": "Required Field", "rule_config": {"type": "required"}}
        ]
        
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.button') as mock_button:
            
            mock_selectbox.return_value = "required"
            mock_text_input.return_value = "Field is required"
            mock_button.return_value = False
            
            result = render_validation_builder(field_data, templates)
            
            # Contract: Should return list of validation rules
            assert isinstance(result, list)
            
            # Contract: Each rule should have required structure
            for rule in result:
                assert isinstance(rule, dict)
                assert "type" in rule
                assert "message" in rule
    
    def test_validation_rule_type_selector_contract(self):
        """Contract: Rule type selector provides all validation types"""
        from schema_management.ui.validation_builder import render_rule_type_selector
        
        field_type = "text"
        
        with patch('streamlit.selectbox') as mock_selectbox:
            mock_selectbox.return_value = "required"
            
            result = render_rule_type_selector(field_type)
            
            # Contract: Should call selectbox with validation types
            mock_selectbox.assert_called_once()
            call_args = mock_selectbox.call_args[0]
            
            # Contract: Should include core validation types
            validation_types = call_args[1] if len(call_args) > 1 else []
            required_types = ["required", "pattern", "length", "format"]
            for validation_type in required_types:
                assert validation_type in validation_types
            
            assert result == "required"
    
    def test_required_validation_editor_contract(self):
        """Contract: Required validation editor handles simple required rules"""
        from schema_management.ui.validation_builder import render_required_validation_editor
        
        existing_rule = {"type": "required", "message": "Field is required"}
        
        with patch('streamlit.text_input') as mock_text_input:
            mock_text_input.return_value = "Custom required message"
            
            result = render_required_validation_editor(existing_rule)
            
            # Contract: Should return required rule structure
            assert isinstance(result, dict)
            assert result["type"] == "required"
            assert "message" in result
    
    def test_pattern_validation_editor_contract(self):
        """Contract: Pattern validation editor handles regex patterns"""
        from schema_management.ui.validation_builder import render_pattern_validation_editor
        
        existing_rule = {
            "type": "pattern",
            "pattern": "^[A-Za-z]+$",
            "message": "Only letters allowed"
        }
        
        with patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.text_area') as mock_text_area:
            
            mock_text_input.side_effect = ["^[A-Za-z]+$", "Updated message"]
            mock_text_area.return_value = "Test pattern here"
            
            result = render_pattern_validation_editor(existing_rule)
            
            # Contract: Should return pattern rule structure
            assert isinstance(result, dict)
            assert result["type"] == "pattern"
            assert "pattern" in result
            assert "message" in result
    
    def test_length_validation_editor_contract(self):
        """Contract: Length validation editor handles min/max constraints"""
        from schema_management.ui.validation_builder import render_length_validation_editor
        
        existing_rule = {
            "type": "length",
            "min_length": 2,
            "max_length": 50,
            "message": "Length must be between 2 and 50 characters"
        }
        
        with patch('streamlit.number_input') as mock_number_input, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_number_input.side_effect = [2, 50]
            mock_text_input.return_value = "Invalid length"
            
            result = render_length_validation_editor(existing_rule)
            
            # Contract: Should return length rule structure
            assert isinstance(result, dict)
            assert result["type"] == "length"
            assert "min_length" in result
            assert "max_length" in result
            assert "message" in result
    
    def test_range_validation_editor_contract(self):
        """Contract: Range validation editor handles numeric ranges"""
        from schema_management.ui.validation_builder import render_range_validation_editor
        
        existing_rule = {
            "type": "range",
            "min_value": 0,
            "max_value": 100,
            "message": "Value must be between 0 and 100"
        }
        
        with patch('streamlit.number_input') as mock_number_input, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_number_input.side_effect = [0, 100]
            mock_text_input.return_value = "Value out of range"
            
            result = render_range_validation_editor(existing_rule)
            
            # Contract: Should return range rule structure
            assert isinstance(result, dict)
            assert result["type"] == "range"
            assert "min_value" in result
            assert "max_value" in result
            assert "message" in result
    
    def test_format_validation_editor_contract(self):
        """Contract: Format validation editor handles predefined formats"""
        from schema_management.ui.validation_builder import render_format_validation_editor
        
        existing_rule = {
            "type": "format",
            "format": "email",
            "message": "Invalid email format"
        }
        
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_selectbox.return_value = "email"
            mock_text_input.return_value = "Invalid email"
            
            result = render_format_validation_editor(existing_rule)
            
            # Contract: Should return format rule structure
            assert isinstance(result, dict)
            assert result["type"] == "format"
            assert "format" in result
            assert "message" in result
            
            # Contract: Should support common formats
            call_args = mock_selectbox.call_args[0]
            formats = call_args[1] if len(call_args) > 1 else []
            required_formats = ["email", "phone", "url", "date"]
            for fmt in required_formats:
                assert fmt in formats


@pytest.mark.contract
class TestCrossFieldValidationContract:
    """Contract tests for cross-field validation rules"""
    
    def test_render_cross_field_validation_contract(self):
        """Contract: Cross-field validation builder handles multi-field rules"""
        from schema_management.ui.validation_builder import render_cross_field_validation
        
        schema = {
            "fields": {
                "start_date": {"name": "start_date", "type": "date"},
                "end_date": {"name": "end_date", "type": "date"},
                "birth_date": {"name": "birth_date", "type": "date"}
            }
        }
        
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_selectbox.return_value = "date_range"
            mock_multiselect.return_value = ["start_date", "end_date"]
            mock_text_input.side_effect = ["start_date < end_date", "End date must be after start date"]
            
            result = render_cross_field_validation(schema)
            
            # Contract: Should return list of cross-field validation rules
            assert isinstance(result, list)
            
            # Contract: Each rule should have required structure
            for rule in result:
                assert isinstance(rule, dict)
                assert "type" in rule
                assert "fields" in rule
                assert "rule" in rule
                assert "message" in rule
    
    def test_date_range_validation_contract(self):
        """Contract: Date range validation for sequential dates"""
        from schema_management.ui.validation_builder import render_date_range_validation
        
        available_fields = [
            {"name": "birth_date", "type": "date"},
            {"name": "issue_date", "type": "date"},
            {"name": "expiry_date", "type": "date"}
        ]
        
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_selectbox.side_effect = ["birth_date", "issue_date"]
            mock_text_input.return_value = "Issue date must be after birth date"
            
            result = render_date_range_validation(available_fields)
            
            # Contract: Should return date range rule
            assert isinstance(result, dict)
            assert result["type"] == "date_range"
            assert "fields" in result
            assert len(result["fields"]) == 2
    
    def test_conditional_validation_contract(self):
        """Contract: Conditional validation based on field values"""
        from schema_management.ui.validation_builder import render_conditional_validation
        
        available_fields = [
            {"name": "has_middle_name", "type": "boolean"},
            {"name": "middle_name", "type": "text"},
            {"name": "country", "type": "select"},
            {"name": "state", "type": "text"}
        ]
        
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_selectbox.side_effect = ["has_middle_name", "==", "middle_name"]
            mock_text_input.side_effect = ["true", "Middle name is required when has_middle_name is true"]
            
            result = render_conditional_validation(available_fields)
            
            # Contract: Should return conditional rule
            assert isinstance(result, dict)
            assert result["type"] == "conditional"
            assert "condition_field" in result
            assert "condition_value" in result
            assert "target_field" in result


@pytest.mark.contract
class TestValidationTemplatesContract:
    """Contract tests for validation rule templates"""
    
    def test_load_validation_templates_contract(self):
        """Contract: Template loading provides predefined validation patterns"""
        from schema_management.services.template_service import load_validation_templates
        
        # Contract: Should return list of templates
        templates = load_validation_templates()
        assert isinstance(templates, list)
        
        # Contract: Each template should have required structure
        for template in templates:
            assert isinstance(template, dict)
            assert "id" in template
            assert "name" in template
            assert "rule_config" in template
            assert "applicable_types" in template
    
    def test_apply_validation_template_contract(self):
        """Contract: Template application creates valid rule configuration"""
        from schema_management.ui.validation_builder import apply_validation_template
        
        template = {
            "id": "email_validation",
            "name": "Email Validation",
            "rule_config": {
                "type": "format",
                "format": "email",
                "message": "Please enter a valid email address"
            },
            "applicable_types": ["email", "text"]
        }
        
        field_type = "email"
        
        result = apply_validation_template(template, field_type)
        
        # Contract: Should return rule based on template
        assert isinstance(result, dict)
        assert result["type"] == "format"
        assert result["format"] == "email"
        assert "message" in result
    
    def test_get_applicable_templates_contract(self):
        """Contract: Template filtering by field type"""
        from schema_management.ui.validation_builder import get_applicable_templates
        
        all_templates = [
            {"id": "req", "applicable_types": ["text", "number", "email"]},
            {"id": "email", "applicable_types": ["email"]},
            {"id": "numeric", "applicable_types": ["number"]}
        ]
        
        # Contract: Should filter templates by field type
        text_templates = get_applicable_templates(all_templates, "text")
        assert len(text_templates) == 1  # Only 'req' template applies to text
        
        email_templates = get_applicable_templates(all_templates, "email")
        assert len(email_templates) == 2  # Both 'req' and 'email' apply to email
        
        number_templates = get_applicable_templates(all_templates, "number")
        assert len(number_templates) == 2  # Both 'req' and 'numeric' apply to number


@pytest.mark.contract
class TestValidationRuleValidationContract:
    """Contract tests for validation rule validation (meta-validation)"""
    
    def test_validate_validation_rule_contract(self):
        """Contract: Validation rule validation ensures rule integrity"""
        from schema_management.validators import validate_validation_rule
        
        # Contract: Valid rules should pass
        valid_rule = {
            "type": "length",
            "min_length": 2,
            "max_length": 50,
            "message": "Length must be between 2 and 50 characters"
        }
        errors = validate_validation_rule(valid_rule, "text")
        assert len(errors) == 0
        
        # Contract: Invalid rules should fail
        invalid_rule = {
            "type": "length",
            "min_length": 50,  # min > max
            "max_length": 2,
            "message": "Invalid rule"
        }
        errors = validate_validation_rule(invalid_rule, "text")
        assert len(errors) > 0
    
    def test_validate_regex_pattern_contract(self):
        """Contract: Regex pattern validation catches invalid patterns"""
        from schema_management.validators import validate_regex_pattern
        
        # Contract: Valid patterns should pass
        valid_patterns = ["^[A-Za-z]+$", "\\d{3}-\\d{3}-\\d{4}", "[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}"]
        for pattern in valid_patterns:
            errors = validate_regex_pattern(pattern)
            assert len(errors) == 0
        
        # Contract: Invalid patterns should fail
        invalid_patterns = ["[unclosed", "(?P<unclosed", "\\"]
        for pattern in invalid_patterns:
            errors = validate_regex_pattern(pattern)
            assert len(errors) > 0
    
    def test_validate_rule_compatibility_contract(self):
        """Contract: Rule compatibility validation with field types"""
        from schema_management.validators import validate_rule_compatibility
        
        # Contract: Compatible combinations should pass
        compatible_combinations = [
            ("required", "text"),
            ("length", "text"),
            ("pattern", "text"),
            ("range", "number"),
            ("format", "email")
        ]
        for rule_type, field_type in compatible_combinations:
            errors = validate_rule_compatibility(rule_type, field_type)
            assert len(errors) == 0
        
        # Contract: Incompatible combinations should fail
        incompatible_combinations = [
            ("length", "number"),  # length not applicable to numbers
            ("range", "text"),     # range not applicable to text
            ("format", "number")   # format not applicable to numbers
        ]
        for rule_type, field_type in incompatible_combinations:
            errors = validate_rule_compatibility(rule_type, field_type)
            assert len(errors) > 0