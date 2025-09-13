"""
Schema Modification Workflow Integration Tests
Tests the complete workflow for data manager modifying existing schemas.
MUST FAIL initially - implementation comes after tests pass.

User Story: As a data manager, I want to modify existing schemas to add new fields 
or update validation rules so I can adapt to changing document formats.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
from datetime import datetime


@pytest.mark.integration
class TestSchemaModificationWorkflow:
    """Integration tests for complete schema modification workflow"""
    
    def setup_method(self):
        """Set up test environment with existing schema"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create base schema for modification
        self.base_schema = {
            "id": "invoice_schema",
            "name": "Invoice Schema",
            "description": "Original invoice schema",
            "category": "Business",
            "version": "v1.0.0",
            "fields": {
                "invoice_number": {
                    "name": "invoice_number",
                    "display_name": "Invoice Number",
                    "type": "text",
                    "required": True,
                    "validation_rules": [
                        {"type": "required", "message": "Invoice number is required"}
                    ]
                },
                "amount": {
                    "name": "amount",
                    "display_name": "Total Amount",
                    "type": "number",
                    "required": True,
                    "validation_rules": [
                        {"type": "required", "message": "Amount is required"},
                        {"type": "range", "min_value": 0, "message": "Amount must be positive"}
                    ]
                }
            },
            "validation_rules": []
        }
        
        self.mock_session_state = {
            'current_schema_id': 'invoice_schema',
            'active_tab': 'fields',
            'unsaved_changes': False,
            'selected_field_id': None,
            'schema_builder': self.base_schema.copy()
        }
    
    def test_load_existing_schema_for_editing(self):
        """Test: Loading existing schema into editor"""
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Save base schema first
        save_result = storage.save_schema("invoice_schema", self.base_schema)
        assert save_result is True
        
        # Load schema for editing
        loaded_schema = storage.load_schema("invoice_schema")
        assert loaded_schema is not None
        assert loaded_schema["name"] == "Invoice Schema"
        assert len(loaded_schema["fields"]) == 2
        assert "invoice_number" in loaded_schema["fields"]
        assert "amount" in loaded_schema["fields"]
    
    def test_add_new_field_to_existing_schema(self):
        """Test: Adding new field to existing schema"""
        from schema_management.ui.field_editor import render_field_editor
        
        # New field to add
        new_field_data = {
            "name": "vendor_name",
            "display_name": "Vendor Name",
            "type": "text",
            "required": False,
            "description": "Name of the invoice vendor"
        }
        
        with patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.checkbox') as mock_checkbox, \
             patch('streamlit.text_area') as mock_text_area:
            
            # Mock field inputs
            mock_text_input.side_effect = ["vendor_name", "Vendor Name"]
            mock_selectbox.return_value = "text"
            mock_checkbox.return_value = False
            mock_text_area.return_value = "Name of the invoice vendor"
            
            result = render_field_editor(new_field_data, [])
            
            # Verify field structure
            assert isinstance(result, dict)
    
    def test_modify_existing_field_validation(self):
        """Test: Modifying validation rules of existing field"""
        from schema_management.ui.validation_builder import render_validation_builder
        
        # Existing field with validation to modify
        existing_field = self.base_schema["fields"]["amount"]
        
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.number_input') as mock_number_input:
            
            # Mock adding length validation to amount field
            mock_selectbox.return_value = "length"
            mock_text_input.return_value = "Amount format invalid"
            mock_number_input.side_effect = [1, 20]
            
            result = render_validation_builder(existing_field, [])
            
            # Verify validation rules structure
            assert isinstance(result, list)
    
    def test_remove_field_from_schema(self):
        """Test: Removing field from existing schema"""
        from schema_management.ui.field_list import render_field_list
        
        fields = list(self.base_schema["fields"].values())
        
        with patch('streamlit_elements.elements') as mock_elements, \
             patch('streamlit.button') as mock_button:
            
            # Mock elements context
            mock_elements.return_value.__enter__ = Mock()
            mock_elements.return_value.__exit__ = Mock()
            
            # Mock delete button click
            mock_button.return_value = True
            
            result = render_field_list(fields)
            
            # Verify field list handling
            assert isinstance(result, list)
    
    def test_schema_version_increment_on_modification(self):
        """Test: Schema version increments when saved with modifications"""
        from schema_management.storage.schema_storage import SchemaStorage
        from schema_management.services.schema_service import increment_schema_version
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Save original schema
        storage.save_schema("invoice_schema", self.base_schema)
        
        # Modify schema (add new field)
        modified_schema = self.base_schema.copy()
        modified_schema["fields"]["new_field"] = {
            "name": "new_field",
            "type": "text",
            "required": False
        }
        
        # Increment version
        new_version = increment_schema_version(self.base_schema["version"])
        modified_schema["version"] = new_version
        
        # Save modified schema
        save_result = storage.save_schema("invoice_schema", modified_schema)
        assert save_result is True
        
        # Verify version changed
        assert new_version != self.base_schema["version"]
        
        # Load and verify new version
        loaded_schema = storage.load_schema("invoice_schema")
        assert loaded_schema["version"] == new_version
        assert "new_field" in loaded_schema["fields"]
    
    def test_schema_modification_history_tracking(self):
        """Test: Modification history is tracked in database"""
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Save original schema
        storage.save_schema("invoice_schema", self.base_schema)
        
        # Create modified version
        modified_schema = self.base_schema.copy()
        modified_schema["version"] = "v1.1.0"
        modified_schema["fields"]["tax_amount"] = {
            "name": "tax_amount",
            "type": "number",
            "required": False
        }
        modified_schema["migration_notes"] = "Added tax amount field"
        
        # Save modified schema
        storage.save_schema("invoice_schema", modified_schema)
        
        # Verify version history
        versions = storage.get_schema_versions("invoice_schema")
        assert len(versions) == 2
        version_strings = [v["version"] for v in versions]
        assert "v1.0.0" in version_strings
        assert "v1.1.0" in version_strings
    
    @patch('streamlit.session_state', new_callable=lambda: MagicMock())
    def test_unsaved_changes_detection(self, mock_session_state):
        """Test: System detects and warns about unsaved changes"""
        from schema_management.state_manager import mark_unsaved_changes, has_unsaved_changes
        
        # Setup session state
        for key, value in self.mock_session_state.items():
            setattr(mock_session_state, key, value)
        
        # Initially no unsaved changes
        assert not has_unsaved_changes()
        
        # Mark changes as unsaved
        mark_unsaved_changes(True)
        assert has_unsaved_changes()
        
        # Clear unsaved changes
        mark_unsaved_changes(False)
        assert not has_unsaved_changes()
    
    def test_field_reordering_workflow(self):
        """Test: Reordering fields in existing schema"""
        from schema_management.ui.field_list import render_field_list
        
        original_fields = [
            {"name": "invoice_number", "display_name": "Invoice Number", "order": 1},
            {"name": "amount", "display_name": "Total Amount", "order": 2},
            {"name": "date", "display_name": "Invoice Date", "order": 3}
        ]
        
        with patch('streamlit_elements.elements') as mock_elements:
            # Mock drag-drop context
            mock_elements.return_value.__enter__ = Mock()
            mock_elements.return_value.__exit__ = Mock()
            
            result = render_field_list(original_fields)
            
            # Verify reordering capability
            assert isinstance(result, list)
            # Actual reordering logic will be implemented
    
    def test_backward_compatibility_validation(self):
        """Test: Modifications maintain backward compatibility when possible"""
        from schema_management.validators import validate_backward_compatibility
        
        # Create modified schema
        modified_schema = self.base_schema.copy()
        modified_schema["fields"]["optional_field"] = {
            "name": "optional_field",
            "type": "text",
            "required": False  # Optional field maintains compatibility
        }
        
        # Test backward compatibility
        is_compatible = validate_backward_compatibility(self.base_schema, modified_schema)
        assert is_compatible is True
        
        # Test breaking change
        breaking_schema = self.base_schema.copy()
        breaking_schema["fields"]["invoice_number"]["required"] = False  # Breaking change
        
        is_breaking = validate_backward_compatibility(self.base_schema, breaking_schema)
        assert is_breaking is False
    
    def test_cross_field_validation_modification(self):
        """Test: Modifying cross-field validation rules"""
        from schema_management.ui.validation_builder import render_cross_field_validation
        
        # Schema with multiple date fields for cross-validation
        schema_with_dates = self.base_schema.copy()
        schema_with_dates["fields"]["issue_date"] = {
            "name": "issue_date",
            "type": "date",
            "required": True
        }
        schema_with_dates["fields"]["due_date"] = {
            "name": "due_date", 
            "type": "date",
            "required": True
        }
        
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            # Mock cross-field validation setup
            mock_selectbox.return_value = "date_range"
            mock_multiselect.return_value = ["issue_date", "due_date"]
            mock_text_input.side_effect = ["issue_date < due_date", "Due date must be after issue date"]
            
            result = render_cross_field_validation(schema_with_dates)
            
            # Verify cross-field validation structure
            assert isinstance(result, list)


@pytest.mark.integration
class TestSchemaModificationValidation:
    """Integration tests for validation during schema modification"""
    
    def setup_method(self):
        """Set up base schema for validation tests"""
        self.base_schema = {
            "id": "test_schema",
            "name": "Test Schema",
            "version": "v1.0.0",
            "fields": {
                "existing_field": {
                    "name": "existing_field",
                    "type": "text",
                    "required": True
                }
            }
        }
    
    def test_field_name_conflict_validation(self):
        """Test: Validation prevents duplicate field names"""
        from schema_management.validators import validate_field_name_uniqueness
        
        new_field = {
            "name": "existing_field",  # Conflicts with existing field
            "type": "number"
        }
        
        existing_fields = list(self.base_schema["fields"].values())
        
        errors = validate_field_name_uniqueness(new_field, existing_fields)
        assert len(errors) > 0
        assert any("duplicate" in error["message"].lower() for error in errors)
    
    def test_required_field_removal_validation(self):
        """Test: Validation warns when removing required fields"""
        from schema_management.validators import validate_field_removal
        
        field_to_remove = self.base_schema["fields"]["existing_field"]
        
        warnings = validate_field_removal(field_to_remove)
        assert len(warnings) > 0  # Should warn about removing required field
    
    def test_type_change_validation(self):
        """Test: Validation handles field type changes"""
        from schema_management.validators import validate_field_type_change
        
        old_field = {"name": "test_field", "type": "text"}
        new_field = {"name": "test_field", "type": "number"}
        
        warnings = validate_field_type_change(old_field, new_field)
        assert len(warnings) > 0  # Should warn about type changes


@pytest.mark.integration
class TestSchemaModificationPersistence:
    """Integration tests for persistence of schema modifications"""
    
    def setup_method(self):
        """Set up temporary storage"""
        self.temp_dir = tempfile.mkdtemp()
    
    def test_atomic_schema_updates(self):
        """Test: Schema updates are atomic (all-or-nothing)"""
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Save original schema
        original_schema = {
            "id": "atomic_test",
            "name": "Atomic Test Schema",
            "version": "v1.0.0",
            "fields": {"field1": {"name": "field1", "type": "text"}}
        }
        storage.save_schema("atomic_test", original_schema)
        
        # Attempt to save invalid modification
        invalid_modification = original_schema.copy()
        invalid_modification["fields"] = {}  # Remove all fields (invalid)
        
        # Should fail and preserve original
        with patch.object(storage, '_validate_schema', return_value=False):
            result = storage.save_schema("atomic_test", invalid_modification)
            assert result is False
        
        # Verify original schema preserved
        loaded_schema = storage.load_schema("atomic_test")
        assert len(loaded_schema["fields"]) == 1
    
    def test_concurrent_modification_handling(self):
        """Test: Handling concurrent modifications to same schema"""
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage1 = SchemaStorage(data_dir=self.temp_dir)
        storage2 = SchemaStorage(data_dir=self.temp_dir)
        
        # Both load same schema
        base_schema = {
            "id": "concurrent_test",
            "name": "Concurrent Test Schema",
            "version": "v1.0.0",
            "fields": {"field1": {"name": "field1", "type": "text"}}
        }
        storage1.save_schema("concurrent_test", base_schema)
        
        schema1 = storage1.load_schema("concurrent_test")
        schema2 = storage2.load_schema("concurrent_test")
        
        # Both modify schema differently
        schema1["fields"]["field2"] = {"name": "field2", "type": "number"}
        schema2["fields"]["field3"] = {"name": "field3", "type": "date"}
        
        # First save succeeds
        result1 = storage1.save_schema("concurrent_test", schema1)
        assert result1 is True
        
        # Second save should detect conflict or handle gracefully
        result2 = storage2.save_schema("concurrent_test", schema2)
        # Implementation will determine exact behavior
        assert isinstance(result2, bool)