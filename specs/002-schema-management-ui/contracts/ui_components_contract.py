"""
UI Components Contract Tests
These tests define the expected behavior of schema management UI components.
MUST FAIL initially - implementation comes after tests pass.
"""

import pytest
import streamlit as st
from unittest.mock import Mock, patch


class TestSchemaBuilderUIContract:
    """Contract tests for schema builder UI components"""
    
    def setup_method(self):
        """Set up test environment"""
        # Reset Streamlit session state
        if hasattr(st, 'session_state'):
            st.session_state.clear()
    
    def test_render_schema_management_page_contract(self):
        """Contract: Main page renders with navigation tabs"""
        # Import will fail until implementation exists
        from schema_management.schema_builder import render_schema_management_page
        
        # Contract: Function should execute without errors
        with patch('streamlit.tabs') as mock_tabs:
            mock_tabs.return_value = [Mock(), Mock(), Mock(), Mock()]
            
            # Should not raise exceptions
            render_schema_management_page()
            
            # Contract: Should create tabs for main sections
            mock_tabs.assert_called_once()
            call_args = mock_tabs.call_args[0][0]
            assert "Basic Info" in call_args
            assert "Fields" in call_args
            assert "Validation" in call_args
            assert "Preview" in call_args
    
    def test_render_basic_info_tab_contract(self):
        """Contract: Basic info tab renders form elements and validates input"""
        from schema_management.basic_info import render_basic_info_tab
        
        # Contract: Should render form with required fields
        with patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.text_area') as mock_text_area, \
             patch('streamlit.selectbox') as mock_selectbox:
            
            schema_data = {}
            result = render_basic_info_tab(schema_data)
            
            # Contract: Should render name input
            mock_text_input.assert_called()
            name_calls = [call for call in mock_text_input.call_args_list 
                         if 'name' in str(call).lower()]
            assert len(name_calls) > 0
            
            # Contract: Should render description area
            mock_text_area.assert_called()
            
            # Contract: Should render category selector
            mock_selectbox.assert_called()
            
            # Contract: Should return updated schema data
            assert isinstance(result, dict)
    
    def test_render_field_list_contract(self):
        """Contract: Field list supports drag-drop reordering"""
        from schema_management.field_editor import render_field_list
        
        fields = [
            {"name": "field1", "display_name": "Field 1", "type": "text"},
            {"name": "field2", "display_name": "Field 2", "type": "number"}
        ]
        
        # Contract: Should render drag-droppable list
        with patch('streamlit_elements.elements') as mock_elements:
            result = render_field_list(fields)
            
            # Contract: Should use streamlit-elements for drag-drop
            mock_elements.assert_called()
            
            # Contract: Should return reordered field list
            assert isinstance(result, list)
            assert len(result) <= len(fields)  # May be filtered/reordered
    
    def test_render_field_editor_contract(self):
        """Contract: Field editor validates input and returns valid field config"""
        from schema_management.field_editor import render_field_editor
        
        field_data = {
            "name": "test_field",
            "display_name": "Test Field",
            "type": "text",
            "required": True
        }
        templates = []
        
        # Contract: Should render field configuration form
        with patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.checkbox') as mock_checkbox:
            
            result = render_field_editor(field_data, templates)
            
            # Contract: Should render field name input
            mock_text_input.assert_called()
            
            # Contract: Should render field type selector
            mock_selectbox.assert_called()
            
            # Contract: Should render required checkbox
            mock_checkbox.assert_called()
            
            # Contract: Should return valid field configuration
            assert isinstance(result, dict)
            assert "name" in result
            assert "type" in result
            assert "required" in result
    
    def test_render_validation_builder_contract(self):
        """Contract: Validation builder creates rule objects from UI input"""
        from schema_management.validation_rules import render_validation_builder
        
        field_data = {"name": "test_field", "type": "text"}
        templates = []
        
        # Contract: Should render validation rule interface
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.text_input') as mock_text_input:
            
            result = render_validation_builder(field_data, templates)
            
            # Contract: Should render rule type selector
            mock_selectbox.assert_called()
            
            # Contract: Should return list of validation rules
            assert isinstance(result, list)
            
            # Contract: Each rule should have required properties
            for rule in result:
                assert isinstance(rule, dict)
                assert "type" in rule
                assert "message" in rule
    
    def test_render_schema_preview_contract(self):
        """Contract: Preview shows formatted schema and form representation"""
        from schema_management.preview import render_schema_preview
        
        schema_data = {
            "id": "test_schema",
            "name": "Test Schema",
            "fields": {
                "field1": {"name": "field1", "type": "text", "required": True}
            }
        }
        
        # Contract: Should render preview without errors
        with patch('streamlit.json') as mock_json, \
             patch('streamlit.code') as mock_code:
            
            render_schema_preview(schema_data)
            
            # Contract: Should display JSON representation
            mock_json.assert_called()
            
            # Contract: JSON should contain schema data
            json_call_args = mock_json.call_args[0][0] 
            assert isinstance(json_call_args, dict)
    
    def test_render_import_interface_contract(self):
        """Contract: Import interface validates and processes uploaded schemas"""
        from schema_management.import_export import render_import_interface
        
        # Contract: Should render file uploader and options
        with patch('streamlit.file_uploader') as mock_uploader, \
             patch('streamlit.selectbox') as mock_selectbox:
            
            # Mock uploaded file
            mock_uploader.return_value = Mock(name="test.json", read=Mock(return_value=b'{"test": "data"}'))
            
            result = render_import_interface()
            
            # Contract: Should render file uploader
            mock_uploader.assert_called()
            
            # Contract: Should return import result object
            assert hasattr(result, 'success') or isinstance(result, dict)
    
    def test_render_export_interface_contract(self):
        """Contract: Export interface generates downloadable schema files"""
        from schema_management.import_export import render_export_interface
        
        schema_ids = ["schema1", "schema2"]
        
        # Contract: Should render export options and download
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.download_button') as mock_download:
            
            mock_multiselect.return_value = schema_ids
            
            render_export_interface(schema_ids)
            
            # Contract: Should render schema selector
            mock_multiselect.assert_called()
            
            # Contract: Should provide download button
            mock_download.assert_called()


class TestUIStateManagementContract:
    """Contract tests for UI state management"""
    
    def test_session_state_initialization_contract(self):
        """Contract: Session state is properly initialized with schema builder state"""
        from schema_management.state_manager import initialize_session_state
        
        # Contract: Should initialize required state keys
        initialize_session_state()
        
        required_keys = [
            'current_schema_id',
            'active_tab', 
            'unsaved_changes',
            'selected_field_id',
            'schema_builder'
        ]
        
        for key in required_keys:
            assert key in st.session_state
    
    def test_update_navigation_state_contract(self):
        """Contract: Navigation state updates correctly"""
        from schema_management.state_manager import update_navigation_state
        
        # Contract: Should update session state for navigation
        update_navigation_state("test_schema", "fields")
        
        assert st.session_state.current_schema_id == "test_schema"
        assert st.session_state.active_tab == "fields"
    
    def test_mark_unsaved_changes_contract(self):
        """Contract: Unsaved changes are tracked correctly"""
        from schema_management.state_manager import mark_unsaved_changes
        
        # Contract: Should mark changes as unsaved
        mark_unsaved_changes()
        assert st.session_state.unsaved_changes is True
        
        # Contract: Should be able to clear unsaved changes
        mark_unsaved_changes(False)
        assert st.session_state.unsaved_changes is False


class TestErrorHandlingContract:
    """Contract tests for error handling and validation"""
    
    def test_validation_error_display_contract(self):
        """Contract: Validation errors are displayed with appropriate severity"""
        from schema_management.error_handling import render_validation_errors
        
        errors = [
            {"type": "error", "message": "Field name is required", "field": "name"},
            {"type": "warning", "message": "Field type may be inconsistent", "field": "type"}
        ]
        
        # Contract: Should render errors with appropriate styling
        with patch('streamlit.error') as mock_error, \
             patch('streamlit.warning') as mock_warning:
            
            render_validation_errors(errors)
            
            # Contract: Should display errors with correct severity
            mock_error.assert_called()
            mock_warning.assert_called()
    
    def test_schema_validation_contract(self):
        """Contract: Schema validation catches common errors"""
        from schema_management.validators import validate_schema
        
        # Contract: Should validate required fields
        invalid_schema = {"name": "", "fields": {}}
        errors = validate_schema(invalid_schema)
        assert len(errors) > 0
        assert any("name" in error["message"].lower() for error in errors)
        
        # Contract: Should pass valid schemas
        valid_schema = {
            "id": "valid_schema",
            "name": "Valid Schema", 
            "fields": {
                "field1": {"name": "field1", "type": "text", "required": True}
            }
        }
        errors = validate_schema(valid_schema)
        assert len(errors) == 0
    
    def test_field_validation_contract(self):
        """Contract: Field validation catches invalid configurations"""
        from schema_management.validators import validate_field
        
        # Contract: Should catch invalid field names
        invalid_field = {"name": "123invalid", "type": "text"}
        errors = validate_field(invalid_field)
        assert len(errors) > 0
        
        # Contract: Should catch missing required properties
        incomplete_field = {"name": "valid_name"}  # Missing type
        errors = validate_field(incomplete_field)
        assert len(errors) > 0
        
        # Contract: Should pass valid fields
        valid_field = {
            "name": "valid_field",
            "display_name": "Valid Field",
            "type": "text",
            "required": True
        }
        errors = validate_field(valid_field)
        assert len(errors) == 0