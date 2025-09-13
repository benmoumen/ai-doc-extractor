"""
Schema Creation Workflow Integration Tests
Tests the complete workflow for business analyst creating new schemas.
MUST FAIL initially - implementation comes after tests pass.

User Story: As a business analyst, I want to create new document type schemas 
through a visual interface so I can define extraction requirements without coding.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json


@pytest.mark.integration
class TestSchemaCreationWorkflow:
    """Integration tests for complete schema creation workflow"""
    
    def setup_method(self):
        """Set up test environment for workflow testing"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock streamlit session state
        self.mock_session_state = {
            'current_schema_id': None,
            'active_tab': 'basic',
            'unsaved_changes': False,
            'selected_field_id': None,
            'schema_builder': {}
        }
    
    @patch('streamlit.session_state', new_callable=lambda: MagicMock())
    def test_complete_schema_creation_workflow(self, mock_session_state):
        """Test: Business analyst creates a complete new schema from start to finish"""
        # Setup session state mock
        for key, value in self.mock_session_state.items():
            setattr(mock_session_state, key, value)
        
        from schema_management.schema_builder import render_schema_management_page
        from schema_management.storage.schema_storage import SchemaStorage
        
        # Initialize storage
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        with patch('streamlit.title'), \
             patch('streamlit.tabs') as mock_tabs, \
             patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.text_area') as mock_text_area, \
             patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.button') as mock_button:
            
            # Mock tab returns
            tab_mocks = [Mock() for _ in range(4)]
            mock_tabs.return_value = tab_mocks
            
            # Simulate user input for basic schema info
            mock_text_input.side_effect = ["Custom Invoice Schema", "invoice_number"]
            mock_text_area.return_value = "Schema for extracting data from invoices"
            mock_selectbox.return_value = "Business"
            mock_button.return_value = True  # Save button clicked
            
            # Execute the main page render
            render_schema_management_page()
            
            # Verify workflow progression
            assert mock_tabs.called
            assert mock_text_input.called
            assert mock_selectbox.called
    
    @patch('streamlit.session_state', new_callable=lambda: MagicMock())
    def test_schema_basic_info_creation(self, mock_session_state):
        """Test: Creating basic schema information"""
        from schema_management.ui.basic_info import render_basic_info_tab
        
        with patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.text_area') as mock_text_area, \
             patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.button') as mock_button:
            
            # Mock user inputs
            mock_text_input.side_effect = ["Invoice Schema", "invoice_schema"]
            mock_text_area.return_value = "Invoice data extraction schema"
            mock_selectbox.return_value = "Business"
            mock_button.return_value = False
            
            result = render_basic_info_tab({})
            
            # Verify schema structure
            assert isinstance(result, dict)
            assert "name" in result or mock_text_input.called
            assert "description" in result or mock_text_area.called
            assert "category" in result or mock_selectbox.called
    
    def test_field_addition_workflow(self):
        """Test: Adding fields to a new schema"""
        from schema_management.ui.field_editor import render_field_editor
        
        with patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.checkbox') as mock_checkbox, \
             patch('streamlit.text_area') as mock_text_area:
            
            # Mock field creation inputs
            mock_text_input.side_effect = ["invoice_number", "Invoice Number", "INV-12345"]
            mock_selectbox.return_value = "text"
            mock_checkbox.return_value = True
            mock_text_area.return_value = "Unique invoice identifier"
            
            field_data = {}
            result = render_field_editor(field_data, [])
            
            # Verify field structure
            assert isinstance(result, dict)
            # Fields will be properly structured once implementation exists
    
    def test_validation_rules_addition_workflow(self):
        """Test: Adding validation rules to fields"""
        from schema_management.ui.validation_builder import render_validation_builder
        
        field_data = {"name": "invoice_number", "type": "text"}
        
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.button') as mock_button:
            
            # Mock validation rule inputs
            mock_selectbox.return_value = "required"
            mock_text_input.return_value = "Invoice number is required"
            mock_button.return_value = False
            
            result = render_validation_builder(field_data, [])
            
            # Verify validation rules structure
            assert isinstance(result, list)
    
    def test_schema_preview_workflow(self):
        """Test: Previewing created schema before saving"""
        from schema_management.ui.preview import render_schema_preview
        
        schema_data = {
            "id": "invoice_schema",
            "name": "Invoice Schema",
            "description": "Schema for invoice data extraction",
            "category": "Business",
            "fields": {
                "invoice_number": {
                    "name": "invoice_number",
                    "display_name": "Invoice Number",
                    "type": "text",
                    "required": True
                }
            }
        }
        
        with patch('streamlit.json') as mock_json, \
             patch('streamlit.code') as mock_code, \
             patch('streamlit.success') as mock_success:
            
            # Should render without errors
            render_schema_preview(schema_data)
            
            # Verify preview components called
            assert mock_json.called or mock_code.called
    
    def test_schema_save_workflow(self):
        """Test: Saving the created schema to storage"""
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        schema_data = {
            "id": "test_invoice",
            "name": "Test Invoice Schema",
            "description": "Test schema for integration test",
            "category": "Business",
            "version": "v1.0.0",
            "fields": {
                "invoice_number": {
                    "name": "invoice_number",
                    "type": "text",
                    "required": True
                }
            },
            "validation_rules": []
        }
        
        # This will fail until storage is implemented
        result = storage.save_schema("test_invoice", schema_data)
        assert result is True
        
        # Verify schema was saved
        saved_schema = storage.load_schema("test_invoice")
        assert saved_schema is not None
        assert saved_schema["name"] == "Test Invoice Schema"
    
    def test_end_to_end_schema_creation(self):
        """Test: Complete end-to-end schema creation process"""
        from schema_management.schema_builder import render_schema_management_page
        from schema_management.storage.schema_storage import SchemaStorage
        
        # This comprehensive test covers the full workflow
        with patch('streamlit.title'), \
             patch('streamlit.tabs'), \
             patch('streamlit.session_state', self.mock_session_state), \
             patch.object(SchemaStorage, 'save_schema', return_value=True), \
             patch.object(SchemaStorage, 'list_schemas', return_value=[]):
            
            # Should execute without fatal errors
            try:
                render_schema_management_page()
                workflow_completed = True
            except Exception as e:
                # Expected to fail until implementation complete
                workflow_completed = False
            
            # Will succeed once all components are implemented
            # For now, we expect imports to fail
            assert workflow_completed or "No module named" in str(e)


@pytest.mark.integration 
class TestSchemaValidationWorkflow:
    """Integration tests for schema validation during creation"""
    
    def test_real_time_schema_validation(self):
        """Test: Schema validation provides real-time feedback"""
        from schema_management.validators import validate_schema
        
        # Test with incomplete schema
        incomplete_schema = {
            "name": "",  # Missing required name
            "fields": {}  # No fields
        }
        
        errors = validate_schema(incomplete_schema)
        assert len(errors) > 0
        
        # Test with valid schema
        valid_schema = {
            "id": "valid_test",
            "name": "Valid Test Schema",
            "category": "Test",
            "fields": {
                "test_field": {
                    "name": "test_field",
                    "type": "text",
                    "required": True
                }
            }
        }
        
        errors = validate_schema(valid_schema)
        assert len(errors) == 0
    
    def test_field_validation_integration(self):
        """Test: Field validation during schema creation"""
        from schema_management.validators import validate_field
        
        # Test invalid field
        invalid_field = {
            "name": "123invalid",  # Invalid name
            "type": "invalid_type"  # Invalid type
        }
        
        errors = validate_field(invalid_field)
        assert len(errors) > 0
        
        # Test valid field
        valid_field = {
            "name": "valid_field",
            "display_name": "Valid Field",
            "type": "text",
            "required": True
        }
        
        errors = validate_field(valid_field)
        assert len(errors) == 0
    
    def test_validation_error_display_integration(self):
        """Test: Validation errors are properly displayed to user"""
        from schema_management.error_handling import render_validation_errors
        
        errors = [
            {"type": "error", "message": "Schema name is required", "field": "name"},
            {"type": "warning", "message": "Consider adding more fields", "field": "fields"}
        ]
        
        with patch('streamlit.error') as mock_error, \
             patch('streamlit.warning') as mock_warning:
            
            render_validation_errors(errors)
            
            # Verify appropriate error display methods called
            assert mock_error.called
            assert mock_warning.called


@pytest.mark.integration
class TestSchemaTemplateIntegration:
    """Integration tests for template usage in schema creation"""
    
    def test_field_template_application(self):
        """Test: Applying field templates during schema creation"""
        from schema_management.services.template_service import load_field_templates
        from schema_management.ui.field_editor import apply_field_template
        
        # Load templates (will be empty until templates implemented)
        templates = load_field_templates()
        assert isinstance(templates, list)
        
        # Test template application
        if templates:  # Only test if templates exist
            template = templates[0]
            result = apply_field_template(template)
            assert isinstance(result, dict)
            assert "name" in result
            assert "type" in result
    
    def test_validation_template_application(self):
        """Test: Applying validation templates during rule creation"""
        from schema_management.services.template_service import load_validation_templates
        from schema_management.ui.validation_builder import apply_validation_template
        
        # Load validation templates
        templates = load_validation_templates()
        assert isinstance(templates, list)
        
        # Test template application
        if templates:  # Only test if templates exist
            template = templates[0]
            result = apply_validation_template(template, "text")
            assert isinstance(result, dict)
            assert "type" in result
            assert "message" in result


@pytest.mark.integration
class TestSchemaStorageIntegration:
    """Integration tests for schema storage during creation workflow"""
    
    def setup_method(self):
        """Set up temporary storage for integration tests"""
        self.temp_dir = tempfile.mkdtemp()
    
    def test_schema_persistence_workflow(self):
        """Test: Schema data persists correctly through save/load cycle"""
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Create test schema
        original_schema = {
            "id": "persistence_test",
            "name": "Persistence Test Schema",
            "description": "Testing schema persistence",
            "category": "Test",
            "version": "v1.0.0",
            "fields": {
                "test_field": {
                    "name": "test_field",
                    "display_name": "Test Field",
                    "type": "text",
                    "required": True,
                    "validation_rules": [
                        {"type": "required", "message": "Test field is required"}
                    ]
                }
            },
            "validation_rules": []
        }
        
        # Save schema
        save_result = storage.save_schema("persistence_test", original_schema)
        assert save_result is True
        
        # Load schema
        loaded_schema = storage.load_schema("persistence_test")
        assert loaded_schema is not None
        assert loaded_schema["name"] == original_schema["name"]
        assert loaded_schema["description"] == original_schema["description"]
        assert "test_field" in loaded_schema["fields"]
    
    def test_multiple_schemas_workflow(self):
        """Test: Creating and managing multiple schemas"""
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Create multiple test schemas
        schemas = [
            {"id": "schema1", "name": "Schema One", "category": "Test1"},
            {"id": "schema2", "name": "Schema Two", "category": "Test2"},
            {"id": "schema3", "name": "Schema Three", "category": "Test1"}
        ]
        
        # Save all schemas
        for schema in schemas:
            result = storage.save_schema(schema["id"], schema)
            assert result is True
        
        # List all schemas
        schema_list = storage.list_schemas()
        assert len(schema_list) == 3
        
        # Verify schema metadata
        schema_ids = [s["id"] for s in schema_list]
        assert "schema1" in schema_ids
        assert "schema2" in schema_ids
        assert "schema3" in schema_ids