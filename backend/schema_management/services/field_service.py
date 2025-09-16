"""
Field management service implementation.
Based on data-model.md specifications.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import re

from ..models.field import Field, FieldType, FieldStatus
from ..models.validation_rule import ValidationRule, ValidationRuleType
from ..services.schema_service import SchemaService
from ..storage.schema_storage import SchemaStorage


logger = logging.getLogger(__name__)


class FieldServiceError(Exception):
    """Custom exception for field service operations"""
    pass


class FieldService:
    """
    Service layer for field management operations
    
    Provides field-specific operations including validation,
    dependency management, and field templates.
    """
    
    def __init__(self, storage: SchemaStorage = None, schema_service: SchemaService = None):
        """
        Initialize field service
        
        Args:
            storage: Storage backend
            schema_service: Schema service for schema operations
        """
        self.storage = storage or SchemaStorage()
        self.schema_service = schema_service or SchemaService(self.storage)
    
    def create_field(self, schema_id: str, field_data: Dict[str, Any], 
                    user_id: str = "system") -> Tuple[bool, str, Optional[Field]]:
        """
        Create a new field in a schema
        
        Args:
            schema_id: Schema identifier
            field_data: Field configuration dictionary
            user_id: User creating the field
            
        Returns:
            Tuple of (success, message, field_object)
        """
        try:
            # Load schema
            schema = self.schema_service.get_schema(schema_id)
            if not schema:
                return False, f"Schema {schema_id} not found", None
            
            # Validate required field data
            if not field_data.get("name"):
                return False, "Field name is required", None
            
            if not field_data.get("display_name"):
                return False, "Field display name is required", None
            
            if not field_data.get("type"):
                return False, "Field type is required", None
            
            # Check for duplicate field name
            field_name = field_data["name"]
            if field_name in schema.fields:
                return False, f"Field '{field_name}' already exists in schema", None
            
            # Validate field name
            name_errors = self.validate_field_name(field_name, schema.fields)
            if name_errors:
                return False, f"Invalid field name: {'; '.join(name_errors)}", None
            
            # Create field object
            field = Field.from_dict(field_data)
            
            # Validate field structure
            validation_errors = field.validate_structure()
            if validation_errors:
                return False, f"Field validation failed: {'; '.join(validation_errors)}", None
            
            # Add field to schema
            schema.add_field(field_name, field.to_dict())
            
            # Save updated schema
            success = self.storage.save_schema(schema_id, schema)
            if not success:
                return False, "Failed to save schema with new field", None
            
            # Add audit log
            self.storage.add_audit_log(
                schema_id, "field_added", None, field.to_dict(), user_id,
                {"field_name": field_name}
            )
            
            logger.info(f"Field {field_name} added to schema {schema_id} by {user_id}")
            return True, "Field created successfully", field
            
        except Exception as e:
            logger.error(f"Failed to create field in schema {schema_id}: {e}")
            return False, f"Failed to create field: {str(e)}", None
    
    def get_field(self, schema_id: str, field_name: str) -> Optional[Field]:
        """
        Retrieve a field from a schema
        
        Args:
            schema_id: Schema identifier
            field_name: Field name
            
        Returns:
            Field object or None if not found
        """
        try:
            schema = self.schema_service.get_schema(schema_id)
            if not schema:
                return None
            
            field_config = schema.get_field(field_name)
            if not field_config:
                return None
            
            return Field.from_dict(field_config)
            
        except Exception as e:
            logger.error(f"Failed to get field {field_name} from schema {schema_id}: {e}")
            return None
    
    def update_field(self, schema_id: str, field_name: str, updates: Dict[str, Any],
                    user_id: str = "system") -> Tuple[bool, str, Optional[Field]]:
        """
        Update an existing field in a schema
        
        Args:
            schema_id: Schema identifier
            field_name: Field name to update
            updates: Dictionary of field properties to update
            user_id: User making the update
            
        Returns:
            Tuple of (success, message, field_object)
        """
        try:
            # Load schema
            schema = self.schema_service.get_schema(schema_id)
            if not schema:
                return False, f"Schema {schema_id} not found", None
            
            # Check if field exists
            if field_name not in schema.fields:
                return False, f"Field '{field_name}' not found in schema", None
            
            # Get current field
            current_field_config = schema.fields[field_name]
            old_field = Field.from_dict(current_field_config)
            
            # Apply updates
            updated_config = current_field_config.copy()
            updated_config.update(updates)
            updated_config["updated_date"] = datetime.now().isoformat()
            
            # Create updated field object
            updated_field = Field.from_dict(updated_config)
            
            # Validate updated field
            validation_errors = updated_field.validate_structure()
            if validation_errors:
                return False, f"Updated field validation failed: {'; '.join(validation_errors)}", None
            
            # Check for breaking changes
            breaking_changes = self.check_field_breaking_changes(old_field, updated_field)
            if breaking_changes:
                logger.warning(f"Breaking changes detected for field {field_name}: {breaking_changes}")
            
            # Update field in schema
            schema.fields[field_name] = updated_field.to_dict()
            schema.updated_date = datetime.now()
            
            # Save updated schema
            success = self.storage.save_schema(schema_id, schema)
            if not success:
                return False, "Failed to save schema with updated field", None
            
            # Add audit log
            self.storage.add_audit_log(
                schema_id, "field_updated", old_field.to_dict(), updated_field.to_dict(), user_id,
                {"field_name": field_name, "fields_changed": list(updates.keys())}
            )
            
            logger.info(f"Field {field_name} updated in schema {schema_id} by {user_id}")
            return True, "Field updated successfully", updated_field
            
        except Exception as e:
            logger.error(f"Failed to update field {field_name} in schema {schema_id}: {e}")
            return False, f"Failed to update field: {str(e)}", None
    
    def delete_field(self, schema_id: str, field_name: str, 
                    user_id: str = "system") -> Tuple[bool, str]:
        """
        Delete a field from a schema
        
        Args:
            schema_id: Schema identifier
            field_name: Field name to delete
            user_id: User performing deletion
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Load schema
            schema = self.schema_service.get_schema(schema_id)
            if not schema:
                return False, f"Schema {schema_id} not found"
            
            # Check if field exists
            if field_name not in schema.fields:
                return False, f"Field '{field_name}' not found in schema"
            
            # Get field for audit log
            field_config = schema.fields[field_name]
            
            # Check for dependencies
            dependent_fields = self.find_dependent_fields(schema, field_name)
            if dependent_fields:
                return False, f"Cannot delete field '{field_name}' - it has dependent fields: {', '.join(dependent_fields)}"
            
            # Remove field from schema
            success = schema.remove_field(field_name)
            if not success:
                return False, f"Failed to remove field '{field_name}' from schema"
            
            # Save updated schema
            save_success = self.storage.save_schema(schema_id, schema)
            if not save_success:
                return False, "Failed to save schema after field deletion"
            
            # Add audit log
            self.storage.add_audit_log(
                schema_id, "field_deleted", field_config, None, user_id,
                {"field_name": field_name}
            )
            
            logger.info(f"Field {field_name} deleted from schema {schema_id} by {user_id}")
            return True, "Field deleted successfully"
            
        except Exception as e:
            logger.error(f"Failed to delete field {field_name} from schema {schema_id}: {e}")
            return False, f"Failed to delete field: {str(e)}"
    
    def reorder_fields(self, schema_id: str, field_order: List[str],
                      user_id: str = "system") -> Tuple[bool, str]:
        """
        Reorder fields in a schema
        
        Args:
            schema_id: Schema identifier
            field_order: List of field names in desired order
            user_id: User performing reorder
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Load schema
            schema = self.schema_service.get_schema(schema_id)
            if not schema:
                return False, f"Schema {schema_id} not found"
            
            # Validate field order list
            existing_fields = set(schema.fields.keys())
            ordered_fields = set(field_order)
            
            if existing_fields != ordered_fields:
                missing = existing_fields - ordered_fields
                extra = ordered_fields - existing_fields
                
                error_msg = []
                if missing:
                    error_msg.append(f"Missing fields: {', '.join(missing)}")
                if extra:
                    error_msg.append(f"Unknown fields: {', '.join(extra)}")
                
                return False, f"Invalid field order: {'; '.join(error_msg)}"
            
            # Create new ordered fields dictionary
            ordered_fields_dict = {}
            for i, field_name in enumerate(field_order):
                field_config = schema.fields[field_name].copy()
                field_config["order"] = i + 1  # 1-based ordering
                ordered_fields_dict[field_name] = field_config
            
            # Update schema with new field order
            old_fields = schema.fields.copy()
            schema.fields = ordered_fields_dict
            schema.updated_date = datetime.now()
            
            # Save updated schema
            success = self.storage.save_schema(schema_id, schema)
            if not success:
                return False, "Failed to save schema with reordered fields"
            
            # Add audit log
            self.storage.add_audit_log(
                schema_id, "fields_reordered", {"old_order": list(old_fields.keys())}, 
                {"new_order": field_order}, user_id
            )
            
            logger.info(f"Fields reordered in schema {schema_id} by {user_id}")
            return True, "Fields reordered successfully"
            
        except Exception as e:
            logger.error(f"Failed to reorder fields in schema {schema_id}: {e}")
            return False, f"Failed to reorder fields: {str(e)}"
    
    def add_validation_rule(self, schema_id: str, field_name: str, 
                           validation_rule: ValidationRule,
                           user_id: str = "system") -> Tuple[bool, str]:
        """
        Add validation rule to a field
        
        Args:
            schema_id: Schema identifier
            field_name: Field name
            validation_rule: ValidationRule object
            user_id: User adding the rule
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get field
            field = self.get_field(schema_id, field_name)
            if not field:
                return False, f"Field '{field_name}' not found in schema {schema_id}"
            
            # Validate rule
            if not validation_rule.is_valid():
                errors = validation_rule.validate_structure()
                return False, f"Invalid validation rule: {'; '.join(errors)}"
            
            # Add rule to field
            field.add_validation_rule(validation_rule.to_dict())
            
            # Update field in schema
            success, message, _ = self.update_field(
                schema_id, field_name, {"validation_rules": field.validation_rules}, user_id
            )
            
            if success:
                logger.info(f"Validation rule added to field {field_name} in schema {schema_id}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Failed to add validation rule to field {field_name}: {e}")
            return False, f"Failed to add validation rule: {str(e)}"
    
    def remove_validation_rule(self, schema_id: str, field_name: str, 
                              rule_index: int, user_id: str = "system") -> Tuple[bool, str]:
        """
        Remove validation rule from a field
        
        Args:
            schema_id: Schema identifier
            field_name: Field name
            rule_index: Index of rule to remove
            user_id: User removing the rule
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get field
            field = self.get_field(schema_id, field_name)
            if not field:
                return False, f"Field '{field_name}' not found in schema {schema_id}"
            
            # Remove rule
            success = field.remove_validation_rule(rule_index)
            if not success:
                return False, f"Invalid rule index {rule_index}"
            
            # Update field in schema
            update_success, message, _ = self.update_field(
                schema_id, field_name, {"validation_rules": field.validation_rules}, user_id
            )
            
            if update_success:
                logger.info(f"Validation rule removed from field {field_name} in schema {schema_id}")
            
            return update_success, message
            
        except Exception as e:
            logger.error(f"Failed to remove validation rule from field {field_name}: {e}")
            return False, f"Failed to remove validation rule: {str(e)}"
    
    def set_field_dependency(self, schema_id: str, field_name: str, 
                            depends_on: str, condition: str, condition_value: Any,
                            user_id: str = "system") -> Tuple[bool, str]:
        """
        Set field dependency relationship
        
        Args:
            schema_id: Schema identifier
            field_name: Field name
            depends_on: Field this field depends on
            condition: Dependency condition (==, !=, etc.)
            condition_value: Value for condition
            user_id: User setting dependency
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Load schema to validate dependency field exists
            schema = self.schema_service.get_schema(schema_id)
            if not schema:
                return False, f"Schema {schema_id} not found"
            
            if depends_on not in schema.fields:
                return False, f"Dependency field '{depends_on}' not found in schema"
            
            if field_name == depends_on:
                return False, "Field cannot depend on itself"
            
            # Check for circular dependencies
            if self.has_circular_dependency(schema, field_name, depends_on):
                return False, f"Circular dependency detected: {field_name} -> {depends_on}"
            
            # Update field with dependency
            updates = {
                "depends_on": depends_on,
                "condition": condition,
                "condition_value": condition_value
            }
            
            success, message, _ = self.update_field(schema_id, field_name, updates, user_id)
            
            if success:
                logger.info(f"Dependency set for field {field_name} -> {depends_on} in schema {schema_id}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Failed to set field dependency: {e}")
            return False, f"Failed to set field dependency: {str(e)}"
    
    def clear_field_dependency(self, schema_id: str, field_name: str,
                              user_id: str = "system") -> Tuple[bool, str]:
        """
        Clear field dependency
        
        Args:
            schema_id: Schema identifier
            field_name: Field name
            user_id: User clearing dependency
            
        Returns:
            Tuple of (success, message)
        """
        try:
            updates = {
                "depends_on": None,
                "condition": None,
                "condition_value": None
            }
            
            success, message, _ = self.update_field(schema_id, field_name, updates, user_id)
            
            if success:
                logger.info(f"Dependency cleared for field {field_name} in schema {schema_id}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Failed to clear field dependency: {e}")
            return False, f"Failed to clear field dependency: {str(e)}"
    
    def copy_field(self, source_schema_id: str, source_field_name: str,
                  target_schema_id: str, target_field_name: str = None,
                  user_id: str = "system") -> Tuple[bool, str, Optional[Field]]:
        """
        Copy field from one schema to another
        
        Args:
            source_schema_id: Source schema identifier
            source_field_name: Source field name
            target_schema_id: Target schema identifier
            target_field_name: Target field name (uses source name if None)
            user_id: User performing copy
            
        Returns:
            Tuple of (success, message, copied_field)
        """
        try:
            # Get source field
            source_field = self.get_field(source_schema_id, source_field_name)
            if not source_field:
                return False, f"Source field '{source_field_name}' not found", None
            
            # Determine target field name
            if target_field_name is None:
                target_field_name = source_field_name
            
            # Clone field
            copied_field = source_field.clone(target_field_name)
            
            # Create field in target schema
            success, message, created_field = self.create_field(
                target_schema_id, copied_field.to_dict(), user_id
            )
            
            if success:
                logger.info(f"Field copied from {source_schema_id}.{source_field_name} to {target_schema_id}.{target_field_name}")
            
            return success, message, created_field
            
        except Exception as e:
            logger.error(f"Failed to copy field: {e}")
            return False, f"Failed to copy field: {str(e)}", None
    
    def get_field_dependencies(self, schema_id: str, field_name: str) -> List[str]:
        """
        Get list of fields that depend on the specified field
        
        Args:
            schema_id: Schema identifier
            field_name: Field name
            
        Returns:
            List of field names that depend on this field
        """
        try:
            schema = self.schema_service.get_schema(schema_id)
            if not schema:
                return []
            
            return self.find_dependent_fields(schema, field_name)
            
        except Exception as e:
            logger.error(f"Failed to get field dependencies: {e}")
            return []
    
    def validate_field_name(self, field_name: str, existing_fields: Dict[str, Any]) -> List[str]:
        """
        Validate field name
        
        Args:
            field_name: Field name to validate
            existing_fields: Dictionary of existing fields
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not field_name:
            errors.append("Field name is required")
            return errors
        
        # Check format (valid Python identifier)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field_name):
            errors.append("Field name must be a valid Python identifier")
        
        # Check length
        if len(field_name) < 2:
            errors.append("Field name must be at least 2 characters")
        
        if len(field_name) > 50:
            errors.append("Field name must be less than 50 characters")
        
        # Check for reserved keywords
        reserved_keywords = {
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else',
            'except', 'exec', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
            'lambda', 'not', 'or', 'pass', 'print', 'raise', 'return', 'try', 'while', 'with', 'yield'
        }
        
        if field_name.lower() in reserved_keywords:
            errors.append(f"Field name '{field_name}' is a reserved keyword")
        
        # Check for duplicates
        if field_name in existing_fields:
            errors.append(f"Field name '{field_name}' already exists")
        
        return errors
    
    def get_field_suggestions(self, field_type: str, category: str = None) -> List[Dict[str, Any]]:
        """
        Get field suggestions based on type and category
        
        Args:
            field_type: Field type
            category: Schema category for context
            
        Returns:
            List of field suggestions
        """
        suggestions = []
        
        # Common field suggestions by type
        if field_type == "text":
            suggestions.extend([
                {"name": "name", "display_name": "Name", "description": "Person or entity name"},
                {"name": "description", "display_name": "Description", "description": "Text description"},
                {"name": "notes", "display_name": "Notes", "description": "Additional notes"},
                {"name": "title", "display_name": "Title", "description": "Title or heading"},
                {"name": "address", "display_name": "Address", "description": "Physical address"}
            ])
        
        elif field_type == "number":
            suggestions.extend([
                {"name": "amount", "display_name": "Amount", "description": "Monetary amount"},
                {"name": "quantity", "display_name": "Quantity", "description": "Item quantity"},
                {"name": "total", "display_name": "Total", "description": "Total value"},
                {"name": "count", "display_name": "Count", "description": "Count of items"},
                {"name": "percentage", "display_name": "Percentage", "description": "Percentage value"}
            ])
        
        elif field_type == "date":
            suggestions.extend([
                {"name": "created_date", "display_name": "Created Date", "description": "Creation date"},
                {"name": "due_date", "display_name": "Due Date", "description": "Due date"},
                {"name": "issue_date", "display_name": "Issue Date", "description": "Date of issue"},
                {"name": "expiry_date", "display_name": "Expiry Date", "description": "Expiration date"},
                {"name": "birth_date", "display_name": "Birth Date", "description": "Date of birth"}
            ])
        
        elif field_type == "email":
            suggestions.extend([
                {"name": "email", "display_name": "Email Address", "description": "Primary email address"},
                {"name": "contact_email", "display_name": "Contact Email", "description": "Contact email address"},
                {"name": "billing_email", "display_name": "Billing Email", "description": "Billing email address"}
            ])
        
        elif field_type == "phone":
            suggestions.extend([
                {"name": "phone", "display_name": "Phone Number", "description": "Primary phone number"},
                {"name": "mobile", "display_name": "Mobile Number", "description": "Mobile phone number"},
                {"name": "work_phone", "display_name": "Work Phone", "description": "Work phone number"}
            ])
        
        # Category-specific suggestions
        if category == "Government":
            suggestions.extend([
                {"name": "document_number", "display_name": "Document Number", "description": "Official document number"},
                {"name": "agency", "display_name": "Issuing Agency", "description": "Government agency"},
                {"name": "citizen_id", "display_name": "Citizen ID", "description": "Citizen identification number"}
            ])
        
        elif category == "Business":
            suggestions.extend([
                {"name": "invoice_number", "display_name": "Invoice Number", "description": "Invoice identifier"},
                {"name": "vendor_name", "display_name": "Vendor Name", "description": "Vendor or supplier name"},
                {"name": "tax_amount", "display_name": "Tax Amount", "description": "Tax amount"},
                {"name": "subtotal", "display_name": "Subtotal", "description": "Subtotal before tax"}
            ])
        
        return suggestions
    
    def find_dependent_fields(self, schema, field_name: str) -> List[str]:
        """Find fields that depend on the specified field"""
        dependent_fields = []
        
        for fname, field_config in schema.fields.items():
            if field_config.get("depends_on") == field_name:
                dependent_fields.append(fname)
        
        return dependent_fields
    
    def has_circular_dependency(self, schema, field_name: str, depends_on: str) -> bool:
        """Check if adding dependency would create circular dependency"""
        visited = set()
        
        def check_dependency_chain(current_field: str) -> bool:
            if current_field in visited:
                return True  # Circular dependency found
            
            visited.add(current_field)
            
            field_config = schema.fields.get(current_field, {})
            field_depends_on = field_config.get("depends_on")
            
            if field_depends_on:
                if field_depends_on == field_name:
                    return True  # Would create circular dependency
                return check_dependency_chain(field_depends_on)
            
            return False
        
        return check_dependency_chain(depends_on)
    
    def check_field_breaking_changes(self, old_field: Field, new_field: Field) -> List[str]:
        """Check for breaking changes between field versions"""
        breaking_changes = []
        
        # Check if required status changed
        if not old_field.required and new_field.required:
            breaking_changes.append("Field became required")
        
        # Check if field type changed
        if old_field.type != new_field.type:
            breaking_changes.append(f"Field type changed from {old_field.type} to {new_field.type}")
        
        # Check validation rules for breaking changes
        old_rules = {rule.get("type") for rule in old_field.validation_rules}
        new_rules = {rule.get("type") for rule in new_field.validation_rules}
        
        # New required validations are breaking
        if "required" in new_rules and "required" not in old_rules:
            breaking_changes.append("Required validation added")
        
        return breaking_changes