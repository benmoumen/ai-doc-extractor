"""
Template management service implementation.
Based on data-model.md specifications.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import re

from ..models.templates import FieldTemplate, SchemaTemplate, TemplateLibrary, TemplateCategory, TemplateStatus
from ..models.field import Field, FieldType
from ..models.schema import Schema
from ..storage.schema_storage import SchemaStorage
from ..services.schema_service import SchemaService


logger = logging.getLogger(__name__)


class TemplateServiceError(Exception):
    """Custom exception for template service operations"""
    pass


class TemplateService:
    """
    Service layer for template management operations
    
    Provides template creation, management, and application functionality
    for both field and schema templates.
    """
    
    def __init__(self, storage: SchemaStorage = None, schema_service: SchemaService = None):
        """
        Initialize template service
        
        Args:
            storage: Storage backend
            schema_service: Schema service for schema operations
        """
        self.storage = storage or SchemaStorage()
        self.schema_service = schema_service or SchemaService(self.storage)
        self.template_library = TemplateLibrary()
        
        # Load existing templates from storage
        self._load_templates()
    
    def _load_templates(self):
        """Load templates from storage into library"""
        try:
            # Load field templates
            field_templates = self.storage.list_templates("field")
            for template_meta in field_templates:
                template = self.storage.load_field_template(template_meta["id"])
                if template:
                    self.template_library.add_field_template(template)
            
            # Load schema templates
            schema_templates = self.storage.list_templates("schema")
            for template_meta in schema_templates:
                template = self.storage.load_schema_template(template_meta["id"])
                if template:
                    self.template_library.add_schema_template(template)
            
            logger.info(f"Loaded {len(self.template_library.field_templates)} field templates and {len(self.template_library.schema_templates)} schema templates")
            
        except Exception as e:
            logger.error(f"Failed to load templates from storage: {e}")
    
    def create_field_template(self, template_data: Dict[str, Any], 
                             user_id: str = "system") -> Tuple[bool, str, Optional[FieldTemplate]]:
        """
        Create a new field template
        
        Args:
            template_data: Template configuration dictionary
            user_id: User creating the template
            
        Returns:
            Tuple of (success, message, template_object)
        """
        try:
            # Validate required fields
            if not template_data.get("id"):
                return False, "Template ID is required", None
            
            if not template_data.get("name"):
                return False, "Template name is required", None
            
            if not template_data.get("field_type"):
                return False, "Field type is required", None
            
            # Check for existing template
            existing = self.template_library.get_field_template(template_data["id"])
            if existing:
                return False, f"Field template with ID '{template_data['id']}' already exists", None
            
            # Set defaults
            template_data.setdefault("created_by", user_id)
            template_data.setdefault("status", TemplateStatus.ACTIVE.value)
            template_data.setdefault("category", "Custom")
            template_data.setdefault("tags", [])
            template_data.setdefault("default_validation_rules", [])
            
            # Create template object
            template = FieldTemplate.from_dict(template_data)
            
            # Validate template
            validation_errors = self.validate_field_template(template)
            if validation_errors:
                return False, f"Template validation failed: {'; '.join(validation_errors)}", None
            
            # Add to library
            success = self.template_library.add_field_template(template)
            if not success:
                return False, "Failed to add template to library", None
            
            # Save to storage
            save_success = self.storage.save_field_template(template)
            if not save_success:
                self.template_library.remove_field_template(template.id)
                return False, "Failed to save template to storage", None
            
            logger.info(f"Field template {template.id} created successfully by {user_id}")
            return True, "Field template created successfully", template
            
        except Exception as e:
            logger.error(f"Failed to create field template: {e}")
            return False, f"Failed to create field template: {str(e)}", None
    
    def create_schema_template(self, template_data: Dict[str, Any],
                              user_id: str = "system") -> Tuple[bool, str, Optional[SchemaTemplate]]:
        """
        Create a new schema template
        
        Args:
            template_data: Template configuration dictionary
            user_id: User creating the template
            
        Returns:
            Tuple of (success, message, template_object)
        """
        try:
            # Validate required fields
            if not template_data.get("id"):
                return False, "Template ID is required", None
            
            if not template_data.get("name"):
                return False, "Template name is required", None
            
            # Check for existing template
            existing = self.template_library.get_schema_template(template_data["id"])
            if existing:
                return False, f"Schema template with ID '{template_data['id']}' already exists", None
            
            # Set defaults
            template_data.setdefault("created_by", user_id)
            template_data.setdefault("status", TemplateStatus.ACTIVE.value)
            template_data.setdefault("category", TemplateCategory.CUSTOM.value)
            template_data.setdefault("field_templates", [])
            template_data.setdefault("tags", [])
            template_data.setdefault("default_validation_rules", [])
            
            # Create template object
            template = SchemaTemplate.from_dict(template_data)
            
            # Validate template
            validation_errors = self.validate_schema_template(template)
            if validation_errors:
                return False, f"Template validation failed: {'; '.join(validation_errors)}", None
            
            # Add to library
            success = self.template_library.add_schema_template(template)
            if not success:
                return False, "Failed to add template to library", None
            
            # Save to storage
            save_success = self.storage.save_schema_template(template)
            if not save_success:
                self.template_library.remove_schema_template(template.id)
                return False, "Failed to save template to storage", None
            
            logger.info(f"Schema template {template.id} created successfully by {user_id}")
            return True, "Schema template created successfully", template
            
        except Exception as e:
            logger.error(f"Failed to create schema template: {e}")
            return False, f"Failed to create schema template: {str(e)}", None
    
    def get_field_template(self, template_id: str) -> Optional[FieldTemplate]:
        """
        Get field template by ID
        
        Args:
            template_id: Template identifier
            
        Returns:
            FieldTemplate object or None if not found
        """
        return self.template_library.get_field_template(template_id)
    
    def get_schema_template(self, template_id: str) -> Optional[SchemaTemplate]:
        """
        Get schema template by ID
        
        Args:
            template_id: Template identifier
            
        Returns:
            SchemaTemplate object or None if not found
        """
        return self.template_library.get_schema_template(template_id)
    
    def list_field_templates(self, category: str = None, tags: List[str] = None,
                            status: TemplateStatus = None, search_term: str = None) -> List[FieldTemplate]:
        """
        List field templates with optional filtering
        
        Args:
            category: Filter by category
            tags: Filter by tags
            status: Filter by status
            search_term: Search in name/description
            
        Returns:
            List of FieldTemplate objects
        """
        templates = self.template_library.list_field_templates(category, tags)
        
        # Apply additional filters
        if status:
            templates = [t for t in templates if t.status == status]
        
        if search_term:
            search_term = search_term.lower()
            templates = [
                t for t in templates
                if search_term in t.name.lower() or search_term in t.description.lower()
            ]
        
        # Sort by usage count and name
        templates.sort(key=lambda t: (-t.usage_count, t.name))
        
        return templates
    
    def list_schema_templates(self, category: TemplateCategory = None, tags: List[str] = None,
                             status: TemplateStatus = None, search_term: str = None) -> List[SchemaTemplate]:
        """
        List schema templates with optional filtering
        
        Args:
            category: Filter by category
            tags: Filter by tags
            status: Filter by status
            search_term: Search in name/description
            
        Returns:
            List of SchemaTemplate objects
        """
        templates = self.template_library.list_schema_templates(category, tags)
        
        # Apply additional filters
        if status:
            templates = [t for t in templates if t.status == status]
        
        if search_term:
            search_term = search_term.lower()
            templates = [
                t for t in templates
                if search_term in t.name.lower() or search_term in t.description.lower()
            ]
        
        # Sort by usage count and name
        templates.sort(key=lambda t: (-t.usage_count, t.name))
        
        return templates
    
    def apply_field_template(self, template_id: str, field_name: str = None,
                            overrides: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Apply field template to create field configuration
        
        Args:
            template_id: Field template identifier
            field_name: Custom field name (uses template name if None)
            overrides: Properties to override from template
            
        Returns:
            Tuple of (success, message, field_config)
        """
        try:
            # Get template
            template = self.template_library.get_field_template(template_id)
            if not template:
                return False, f"Field template '{template_id}' not found", None
            
            # Convert template to field config
            field_config = template.to_field_config()
            
            # Apply custom field name
            if field_name:
                field_config["name"] = field_name
                # Update display name if it was generic
                if field_config["display_name"] == template.name.replace("_", " ").title():
                    field_config["display_name"] = field_name.replace("_", " ").title()
            
            # Apply overrides
            if overrides:
                field_config.update(overrides)
            
            # Increment usage count
            template.increment_usage()
            self.storage.save_field_template(template)
            
            logger.info(f"Field template {template_id} applied to create field {field_config['name']}")
            return True, "Field template applied successfully", field_config
            
        except Exception as e:
            logger.error(f"Failed to apply field template {template_id}: {e}")
            return False, f"Failed to apply field template: {str(e)}", None
    
    def apply_schema_template(self, template_id: str, schema_id: str, schema_name: str = None,
                             user_id: str = "system") -> Tuple[bool, str, Optional[Schema]]:
        """
        Apply schema template to create new schema
        
        Args:
            template_id: Schema template identifier
            schema_id: New schema identifier
            schema_name: Custom schema name (uses template name if None)
            user_id: User applying template
            
        Returns:
            Tuple of (success, message, schema_object)
        """
        try:
            # Get template
            template = self.template_library.get_schema_template(template_id)
            if not template:
                return False, f"Schema template '{template_id}' not found", None
            
            # Create schema data from template
            schema_data = {
                "id": schema_id,
                "name": schema_name or template.name,
                "description": template.description,
                "category": template.category.value if isinstance(template.category, TemplateCategory) else template.category,
                "version": "v1.0.0",
                "is_active": True,
                "status": "draft",
                "fields": {},
                "validation_rules": template.default_validation_rules.copy(),
                "created_by": user_id
            }
            
            # Apply field templates
            for field_template_id in template.field_templates:
                field_template = self.template_library.get_field_template(field_template_id)
                if field_template:
                    field_config = field_template.to_field_config()
                    schema_data["fields"][field_config["name"]] = field_config
                    
                    # Increment field template usage
                    field_template.increment_usage()
                    self.storage.save_field_template(field_template)
                else:
                    logger.warning(f"Field template '{field_template_id}' not found in schema template '{template_id}'")
            
            # Create schema
            success, message, schema = self.schema_service.create_schema(schema_data, user_id)
            
            if success:
                # Increment template usage
                template.increment_usage()
                self.storage.save_schema_template(template)
                
                logger.info(f"Schema template {template_id} applied to create schema {schema_id}")
            
            return success, message, schema
            
        except Exception as e:
            logger.error(f"Failed to apply schema template {template_id}: {e}")
            return False, f"Failed to apply schema template: {str(e)}", None
    
    def create_template_from_field(self, schema_id: str, field_name: str, template_id: str,
                                  template_name: str = None, user_id: str = "system") -> Tuple[bool, str, Optional[FieldTemplate]]:
        """
        Create field template from existing field
        
        Args:
            schema_id: Source schema identifier
            field_name: Source field name
            template_id: New template identifier
            template_name: Template name (derived from field if None)
            user_id: User creating template
            
        Returns:
            Tuple of (success, message, template_object)
        """
        try:
            # Get source schema
            schema = self.schema_service.get_schema(schema_id)
            if not schema:
                return False, f"Schema {schema_id} not found", None
            
            # Get field configuration
            field_config = schema.get_field(field_name)
            if not field_config:
                return False, f"Field '{field_name}' not found in schema", None
            
            # Create template data from field
            template_data = {
                "id": template_id,
                "name": template_name or field_name,
                "display_name": field_config.get("display_name", field_name),
                "field_type": field_config.get("type", "text"),
                "description": field_config.get("description", f"Template created from {field_name} field"),
                "category": schema.category,
                "default_required": field_config.get("required", False),
                "default_validation_rules": field_config.get("validation_rules", []),
                "default_placeholder": field_config.get("placeholder", ""),
                "default_help_text": field_config.get("help_text", ""),
                "created_by": user_id,
                "tags": ["generated", schema.category.lower()]
            }
            
            # Create template
            success, message, template = self.create_field_template(template_data, user_id)
            
            if success:
                logger.info(f"Field template {template_id} created from field {schema_id}.{field_name}")
            
            return success, message, template
            
        except Exception as e:
            logger.error(f"Failed to create template from field: {e}")
            return False, f"Failed to create template from field: {str(e)}", None
    
    def create_template_from_schema(self, schema_id: str, template_id: str, template_name: str = None,
                                   user_id: str = "system") -> Tuple[bool, str, Optional[SchemaTemplate]]:
        """
        Create schema template from existing schema
        
        Args:
            schema_id: Source schema identifier
            template_id: New template identifier
            template_name: Template name (derived from schema if None)
            user_id: User creating template
            
        Returns:
            Tuple of (success, message, template_object)
        """
        try:
            # Get source schema
            schema = self.schema_service.get_schema(schema_id)
            if not schema:
                return False, f"Schema {schema_id} not found", None
            
            # Create field templates for each field
            field_template_ids = []
            for field_name, field_config in schema.fields.items():
                field_template_id = f"{template_id}_{field_name}_template"
                
                # Check if field template already exists
                existing_field_template = self.template_library.get_field_template(field_template_id)
                if not existing_field_template:
                    # Create field template
                    success, _, field_template = self.create_template_from_field(
                        schema_id, field_name, field_template_id, 
                        f"{template_name or schema.name} - {field_name}", user_id
                    )
                    
                    if success:
                        field_template_ids.append(field_template_id)
                else:
                    field_template_ids.append(field_template_id)
            
            # Create schema template data
            template_data = {
                "id": template_id,
                "name": template_name or f"{schema.name} Template",
                "description": f"Template created from {schema.name} schema",
                "category": schema.category,
                "field_templates": field_template_ids,
                "default_validation_rules": schema.validation_rules,
                "tags": ["generated", schema.category.lower()],
                "created_by": user_id
            }
            
            # Create schema template
            success, message, template = self.create_schema_template(template_data, user_id)
            
            if success:
                logger.info(f"Schema template {template_id} created from schema {schema_id}")
            
            return success, message, template
            
        except Exception as e:
            logger.error(f"Failed to create template from schema: {e}")
            return False, f"Failed to create template from schema: {str(e)}", None
    
    def update_field_template(self, template_id: str, updates: Dict[str, Any],
                             user_id: str = "system") -> Tuple[bool, str, Optional[FieldTemplate]]:
        """
        Update field template
        
        Args:
            template_id: Template identifier
            updates: Properties to update
            user_id: User making update
            
        Returns:
            Tuple of (success, message, updated_template)
        """
        try:
            # Get existing template
            template = self.template_library.get_field_template(template_id)
            if not template:
                return False, f"Field template '{template_id}' not found", None
            
            # Apply updates
            template_dict = template.to_dict()
            template_dict.update(updates)
            template_dict["updated_date"] = datetime.now().isoformat()
            
            # Create updated template
            updated_template = FieldTemplate.from_dict(template_dict)
            
            # Validate updated template
            validation_errors = self.validate_field_template(updated_template)
            if validation_errors:
                return False, f"Updated template validation failed: {'; '.join(validation_errors)}", None
            
            # Update in library
            self.template_library.field_templates[template_id] = updated_template
            
            # Save to storage
            save_success = self.storage.save_field_template(updated_template)
            if not save_success:
                return False, "Failed to save updated template", None
            
            logger.info(f"Field template {template_id} updated by {user_id}")
            return True, "Field template updated successfully", updated_template
            
        except Exception as e:
            logger.error(f"Failed to update field template {template_id}: {e}")
            return False, f"Failed to update field template: {str(e)}", None
    
    def update_schema_template(self, template_id: str, updates: Dict[str, Any],
                              user_id: str = "system") -> Tuple[bool, str, Optional[SchemaTemplate]]:
        """
        Update schema template
        
        Args:
            template_id: Template identifier
            updates: Properties to update
            user_id: User making update
            
        Returns:
            Tuple of (success, message, updated_template)
        """
        try:
            # Get existing template
            template = self.template_library.get_schema_template(template_id)
            if not template:
                return False, f"Schema template '{template_id}' not found", None
            
            # Apply updates
            template_dict = template.to_dict()
            template_dict.update(updates)
            template_dict["updated_date"] = datetime.now().isoformat()
            
            # Create updated template
            updated_template = SchemaTemplate.from_dict(template_dict)
            
            # Validate updated template
            validation_errors = self.validate_schema_template(updated_template)
            if validation_errors:
                return False, f"Updated template validation failed: {'; '.join(validation_errors)}", None
            
            # Update in library
            self.template_library.schema_templates[template_id] = updated_template
            
            # Save to storage
            save_success = self.storage.save_schema_template(updated_template)
            if not save_success:
                return False, "Failed to save updated template", None
            
            logger.info(f"Schema template {template_id} updated by {user_id}")
            return True, "Schema template updated successfully", updated_template
            
        except Exception as e:
            logger.error(f"Failed to update schema template {template_id}: {e}")
            return False, f"Failed to update schema template: {str(e)}", None
    
    def delete_field_template(self, template_id: str, user_id: str = "system") -> Tuple[bool, str]:
        """
        Delete field template
        
        Args:
            template_id: Template identifier
            user_id: User performing deletion
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if template exists
            template = self.template_library.get_field_template(template_id)
            if not template:
                return False, f"Field template '{template_id}' not found"
            
            # Check for dependencies (schema templates using this field template)
            dependent_schemas = []
            for schema_template in self.template_library.schema_templates.values():
                if template_id in schema_template.field_templates:
                    dependent_schemas.append(schema_template.id)
            
            if dependent_schemas:
                return False, f"Cannot delete field template - it is used by schema templates: {', '.join(dependent_schemas)}"
            
            # Remove from library
            self.template_library.remove_field_template(template_id)
            
            # Note: We don't delete from storage to maintain history
            # Instead, mark as deleted/archived
            template.status = TemplateStatus.ARCHIVED
            self.storage.save_field_template(template)
            
            logger.info(f"Field template {template_id} deleted by {user_id}")
            return True, "Field template deleted successfully"
            
        except Exception as e:
            logger.error(f"Failed to delete field template {template_id}: {e}")
            return False, f"Failed to delete field template: {str(e)}"
    
    def delete_schema_template(self, template_id: str, user_id: str = "system") -> Tuple[bool, str]:
        """
        Delete schema template
        
        Args:
            template_id: Template identifier
            user_id: User performing deletion
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if template exists
            template = self.template_library.get_schema_template(template_id)
            if not template:
                return False, f"Schema template '{template_id}' not found"
            
            # Remove from library
            self.template_library.remove_schema_template(template_id)
            
            # Mark as archived in storage
            template.status = TemplateStatus.ARCHIVED
            self.storage.save_schema_template(template)
            
            logger.info(f"Schema template {template_id} deleted by {user_id}")
            return True, "Schema template deleted successfully"
            
        except Exception as e:
            logger.error(f"Failed to delete schema template {template_id}: {e}")
            return False, f"Failed to delete schema template: {str(e)}"
    
    def get_template_library_stats(self) -> Dict[str, Any]:
        """
        Get template library statistics
        
        Returns:
            Statistics dictionary
        """
        return self.template_library.get_template_stats()
    
    def get_popular_templates(self, template_type: str = "field", limit: int = 10) -> List[Any]:
        """
        Get popular templates by usage
        
        Args:
            template_type: "field" or "schema"
            limit: Maximum number to return
            
        Returns:
            List of popular templates
        """
        if template_type == "field":
            return self.template_library.get_popular_field_templates(limit)
        elif template_type == "schema":
            return self.template_library.get_popular_schema_templates(limit)
        else:
            return []
    
    def validate_field_template(self, template: FieldTemplate) -> List[str]:
        """
        Validate field template configuration
        
        Args:
            template: FieldTemplate object
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate ID format
        if not re.match(r'^[a-zA-Z0-9_-]+$', template.id):
            errors.append("Template ID can only contain letters, numbers, underscores, and hyphens")
        
        # Validate field type
        try:
            FieldType(template.field_type)
        except ValueError:
            # Allow custom field types
            pass
        
        # Validate validation rules
        for rule_dict in template.default_validation_rules:
            try:
                from ..models.validation_rule import ValidationRule
                rule = ValidationRule.from_dict(rule_dict)
                rule_errors = rule.validate_structure()
                errors.extend(rule_errors)
            except Exception as e:
                errors.append(f"Invalid validation rule: {str(e)}")
        
        return errors
    
    def validate_schema_template(self, template: SchemaTemplate) -> List[str]:
        """
        Validate schema template configuration
        
        Args:
            template: SchemaTemplate object
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Use built-in validation
        errors.extend(template.validate_structure())
        
        # Validate field template references
        for field_template_id in template.field_templates:
            if not self.template_library.get_field_template(field_template_id):
                errors.append(f"Referenced field template '{field_template_id}' not found")
        
        return errors
    
    def suggest_field_templates(self, field_name: str, field_type: str = None,
                               category: str = None) -> List[FieldTemplate]:
        """
        Suggest field templates based on field name and context
        
        Args:
            field_name: Field name for matching
            field_type: Field type filter
            category: Category filter
            
        Returns:
            List of suggested FieldTemplate objects
        """
        suggestions = []
        
        # Get all field templates
        all_templates = self.template_library.list_field_templates()
        
        # Score templates based on relevance
        scored_templates = []
        
        for template in all_templates:
            score = 0
            
            # Name similarity
            if field_name.lower() in template.name.lower():
                score += 10
            
            if template.name.lower() in field_name.lower():
                score += 8
            
            # Type match
            if field_type and template.field_type == field_type:
                score += 5
            
            # Category match
            if category and template.category.lower() == category.lower():
                score += 3
            
            # Tag relevance
            for tag in template.tags:
                if tag.lower() in field_name.lower() or (category and tag.lower() == category.lower()):
                    score += 2
            
            # Usage popularity
            score += min(template.usage_count / 10, 5)
            
            if score > 0:
                scored_templates.append((score, template))
        
        # Sort by score and return top suggestions
        scored_templates.sort(key=lambda x: x[0], reverse=True)
        suggestions = [template for score, template in scored_templates[:10]]
        
        return suggestions
    
    def get_system_templates(self) -> Dict[str, List[Any]]:
        """
        Get built-in system templates
        
        Returns:
            Dictionary with field and schema system templates
        """
        field_templates = [t for t in self.template_library.field_templates.values() if t.is_system_template]
        schema_templates = [t for t in self.template_library.schema_templates.values() if t.is_system_template]
        
        return {
            "field_templates": field_templates,
            "schema_templates": schema_templates
        }
    
    def initialize_system_templates(self) -> bool:
        """
        Initialize built-in system templates
        
        Returns:
            bool: True if successful
        """
        try:
            # Common field templates
            system_field_templates = [
                {
                    "id": "name_field",
                    "name": "name",
                    "display_name": "Name",
                    "field_type": "text",
                    "description": "Standard name field",
                    "category": "Personal",
                    "is_system_template": True,
                    "default_required": True,
                    "default_validation_rules": [
                        {"type": "required", "message": "Name is required"},
                        {"type": "length", "min_length": 2, "max_length": 100, "message": "Name must be 2-100 characters"}
                    ]
                },
                {
                    "id": "email_field",
                    "name": "email",
                    "display_name": "Email Address",
                    "field_type": "email",
                    "description": "Standard email field",
                    "category": "Personal",
                    "is_system_template": True,
                    "default_required": True,
                    "default_validation_rules": [
                        {"type": "required", "message": "Email is required"},
                        {"type": "format", "format": "email", "message": "Must be a valid email address"}
                    ]
                },
                {
                    "id": "phone_field",
                    "name": "phone",
                    "display_name": "Phone Number",
                    "field_type": "phone",
                    "description": "Standard phone field",
                    "category": "Personal",
                    "is_system_template": True,
                    "default_validation_rules": [
                        {"type": "format", "format": "phone", "message": "Must be a valid phone number"}
                    ]
                },
                {
                    "id": "amount_field",
                    "name": "amount",
                    "display_name": "Amount",
                    "field_type": "number",
                    "description": "Standard monetary amount field",
                    "category": "Business",
                    "is_system_template": True,
                    "default_required": True,
                    "default_validation_rules": [
                        {"type": "required", "message": "Amount is required"},
                        {"type": "range", "min_value": 0, "message": "Amount must be positive"}
                    ]
                }
            ]
            
            # Create system field templates
            for template_data in system_field_templates:
                existing = self.template_library.get_field_template(template_data["id"])
                if not existing:
                    self.create_field_template(template_data, "system")
            
            logger.info("System templates initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize system templates: {e}")
            return False