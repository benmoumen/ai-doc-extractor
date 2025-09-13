"""
Schema CRUD operations service implementation.
Based on data-model.md specifications.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import re
from pathlib import Path

from ..models.schema import Schema, SchemaStatus
from ..models.field import Field
from ..storage.schema_storage import SchemaStorage, SchemaStorageError


logger = logging.getLogger(__name__)


class SchemaServiceError(Exception):
    """Custom exception for schema service operations"""
    pass


class SchemaService:
    """
    Service layer for schema CRUD operations
    
    Provides high-level schema management functionality including
    validation, versioning, and business logic enforcement.
    """
    
    def __init__(self, storage: SchemaStorage = None):
        """
        Initialize schema service
        
        Args:
            storage: Storage backend (creates default if None)
        """
        self.storage = storage or SchemaStorage()
    
    def create_schema(self, schema_data: Dict[str, Any], 
                     user_id: str = "system") -> Tuple[bool, str, Optional[Schema]]:
        """
        Create a new schema with validation
        
        Args:
            schema_data: Schema configuration dictionary
            user_id: User creating the schema
            
        Returns:
            Tuple of (success, message, schema_object)
        """
        try:
            # Validate required fields
            if not schema_data.get("id"):
                return False, "Schema ID is required", None
            
            if not schema_data.get("name"):
                return False, "Schema name is required", None
            
            # Check for existing schema
            existing = self.storage.load_schema(schema_data["id"])
            if existing:
                return False, f"Schema with ID '{schema_data['id']}' already exists", None
            
            # Set defaults
            schema_data.setdefault("version", "v1.0.0")
            schema_data.setdefault("status", SchemaStatus.DRAFT.value)
            schema_data.setdefault("created_by", user_id)
            schema_data.setdefault("category", "Custom")
            schema_data.setdefault("is_active", True)
            schema_data.setdefault("fields", {})
            schema_data.setdefault("validation_rules", [])
            
            # Create schema object
            schema = Schema.from_dict(schema_data)
            
            # Validate schema structure
            validation_errors = schema.validate_structure()
            if validation_errors:
                error_messages = [error.get("message", str(error)) for error in validation_errors]
                return False, f"Schema validation failed: {'; '.join(error_messages)}", None
            
            # Save schema
            success = self.storage.save_schema(schema.id, schema)
            if not success:
                return False, "Failed to save schema to storage", None
            
            # Add audit log
            self.storage.add_audit_log(
                schema.id, "schema_created", None, schema.to_dict(), user_id
            )
            
            logger.info(f"Schema {schema.id} created successfully by {user_id}")
            return True, "Schema created successfully", schema
            
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            return False, f"Failed to create schema: {str(e)}", None
    
    def get_schema(self, schema_id: str, version: str = None) -> Optional[Schema]:
        """
        Retrieve a schema by ID and optional version
        
        Args:
            schema_id: Schema identifier
            version: Specific version (latest if None)
            
        Returns:
            Schema object or None if not found
        """
        try:
            schema = self.storage.load_schema(schema_id, version)
            if schema:
                logger.info(f"Schema {schema_id} retrieved successfully")
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get schema {schema_id}: {e}")
            return None
    
    def update_schema(self, schema_id: str, updates: Dict[str, Any], 
                     user_id: str = "system", 
                     increment_version: bool = True) -> Tuple[bool, str, Optional[Schema]]:
        """
        Update an existing schema
        
        Args:
            schema_id: Schema identifier
            updates: Dictionary of fields to update
            user_id: User making the update
            increment_version: Whether to increment version number
            
        Returns:
            Tuple of (success, message, schema_object)
        """
        try:
            # Load existing schema
            existing_schema = self.storage.load_schema(schema_id)
            if not existing_schema:
                return False, f"Schema {schema_id} not found", None
            
            # Store old values for audit
            old_values = existing_schema.to_dict()
            
            # Apply updates
            schema_dict = existing_schema.to_dict()
            schema_dict.update(updates)
            
            # Increment version if requested
            if increment_version:
                new_version = self.increment_version(existing_schema.version)
                schema_dict["version"] = new_version
            
            # Update timestamps
            schema_dict["updated_date"] = datetime.now().isoformat()
            
            # Create updated schema object
            updated_schema = Schema.from_dict(schema_dict)
            
            # Validate updated schema
            validation_errors = updated_schema.validate_structure()
            if validation_errors:
                error_messages = [error.get("message", str(error)) for error in validation_errors]
                return False, f"Updated schema validation failed: {'; '.join(error_messages)}", None
            
            # Check backward compatibility if version changed
            if increment_version:
                compatibility_issues = self.check_backward_compatibility(existing_schema, updated_schema)
                if compatibility_issues:
                    updated_schema.backward_compatible = False
                    updated_schema.migration_notes = f"Breaking changes: {'; '.join(compatibility_issues)}"
            
            # Save updated schema
            success = self.storage.save_schema(schema_id, updated_schema)
            if not success:
                return False, "Failed to save updated schema", None
            
            # Add audit log
            self.storage.add_audit_log(
                schema_id, "schema_updated", old_values, updated_schema.to_dict(), user_id,
                {"fields_changed": list(updates.keys())}
            )
            
            logger.info(f"Schema {schema_id} updated successfully by {user_id}")
            return True, "Schema updated successfully", updated_schema
            
        except Exception as e:
            logger.error(f"Failed to update schema {schema_id}: {e}")
            return False, f"Failed to update schema: {str(e)}", None
    
    def delete_schema(self, schema_id: str, user_id: str = "system", 
                     soft_delete: bool = True) -> Tuple[bool, str]:
        """
        Delete a schema (soft or hard delete)
        
        Args:
            schema_id: Schema identifier
            user_id: User performing deletion
            soft_delete: Whether to soft delete (mark as deleted) or hard delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Load existing schema
            existing_schema = self.storage.load_schema(schema_id)
            if not existing_schema:
                return False, f"Schema {schema_id} not found"
            
            if soft_delete:
                # Soft delete: mark as deleted and inactive
                updates = {
                    "status": SchemaStatus.DELETED.value,
                    "is_active": False,
                    "updated_date": datetime.now().isoformat()
                }
                
                success, message, _ = self.update_schema(
                    schema_id, updates, user_id, increment_version=False
                )
                
                if success:
                    # Add audit log
                    self.storage.add_audit_log(
                        schema_id, "schema_soft_deleted", existing_schema.to_dict(), None, user_id
                    )
                    logger.info(f"Schema {schema_id} soft deleted by {user_id}")
                    return True, "Schema marked as deleted"
                else:
                    return False, f"Failed to soft delete schema: {message}"
            
            else:
                # Hard delete: remove from storage
                success = self.storage.delete_schema(schema_id)
                if success:
                    logger.info(f"Schema {schema_id} hard deleted by {user_id}")
                    return True, "Schema permanently deleted"
                else:
                    return False, "Failed to delete schema from storage"
            
        except Exception as e:
            logger.error(f"Failed to delete schema {schema_id}: {e}")
            return False, f"Failed to delete schema: {str(e)}"
    
    def list_schemas(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        List schemas with optional filtering
        
        Args:
            filters: Optional filters (category, status, active_only, etc.)
            
        Returns:
            List of schema metadata dictionaries
        """
        try:
            filters = filters or {}
            
            schemas = self.storage.list_schemas(
                category=filters.get("category"),
                status=filters.get("status"),
                active_only=filters.get("active_only", True)
            )
            
            # Apply additional filters
            if filters.get("search_term"):
                search_term = filters["search_term"].lower()
                schemas = [
                    s for s in schemas 
                    if search_term in s["name"].lower() or 
                       search_term in s.get("description", "").lower()
                ]
            
            if filters.get("created_by"):
                schemas = [s for s in schemas if s.get("created_by") == filters["created_by"]]
            
            # Sort by specified field
            sort_by = filters.get("sort_by", "updated_date")
            reverse = filters.get("sort_desc", True)
            
            if sort_by in ["name", "category", "version", "created_date", "updated_date", "usage_count"]:
                schemas.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
            
            logger.info(f"Listed {len(schemas)} schemas with filters: {filters}")
            return schemas
            
        except Exception as e:
            logger.error(f"Failed to list schemas: {e}")
            return []
    
    def search_schemas(self, query: str, fields: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search schemas across multiple fields
        
        Args:
            query: Search query
            fields: Fields to search in (default: name, description)
            
        Returns:
            List of matching schema metadata
        """
        try:
            fields = fields or ["name", "description"]
            query = query.lower()
            
            all_schemas = self.storage.list_schemas(active_only=False)
            matching_schemas = []
            
            for schema in all_schemas:
                for field in fields:
                    field_value = str(schema.get(field, "")).lower()
                    if query in field_value:
                        matching_schemas.append(schema)
                        break
            
            logger.info(f"Search for '{query}' found {len(matching_schemas)} schemas")
            return matching_schemas
            
        except Exception as e:
            logger.error(f"Failed to search schemas: {e}")
            return []
    
    def get_schema_versions(self, schema_id: str) -> List[Dict[str, Any]]:
        """
        Get version history for a schema
        
        Args:
            schema_id: Schema identifier
            
        Returns:
            List of version metadata
        """
        try:
            versions = self.storage.get_schema_versions(schema_id)
            logger.info(f"Retrieved {len(versions)} versions for schema {schema_id}")
            return versions
            
        except Exception as e:
            logger.error(f"Failed to get versions for schema {schema_id}: {e}")
            return []
    
    def clone_schema(self, source_schema_id: str, new_schema_id: str, 
                    new_name: str = None, user_id: str = "system") -> Tuple[bool, str, Optional[Schema]]:
        """
        Clone an existing schema
        
        Args:
            source_schema_id: ID of schema to clone
            new_schema_id: ID for new schema
            new_name: Name for new schema (derived from ID if None)
            user_id: User performing the clone
            
        Returns:
            Tuple of (success, message, new_schema)
        """
        try:
            # Load source schema
            source_schema = self.storage.load_schema(source_schema_id)
            if not source_schema:
                return False, f"Source schema {source_schema_id} not found", None
            
            # Check if new ID already exists
            existing = self.storage.load_schema(new_schema_id)
            if existing:
                return False, f"Schema with ID '{new_schema_id}' already exists", None
            
            # Clone schema
            cloned_schema = source_schema.clone(new_schema_id, "v1.0.0")
            
            # Set new name if provided
            if new_name:
                cloned_schema.name = new_name
            else:
                cloned_schema.name = f"{source_schema.name} (Copy)"
            
            # Update metadata
            cloned_schema.created_by = user_id
            cloned_schema.status = SchemaStatus.DRAFT
            cloned_schema.migration_notes = f"Cloned from {source_schema_id}"
            
            # Save cloned schema
            success = self.storage.save_schema(new_schema_id, cloned_schema)
            if not success:
                return False, "Failed to save cloned schema", None
            
            # Add audit logs
            self.storage.add_audit_log(
                new_schema_id, "schema_cloned", None, cloned_schema.to_dict(), user_id,
                {"source_schema_id": source_schema_id}
            )
            
            logger.info(f"Schema {source_schema_id} cloned to {new_schema_id} by {user_id}")
            return True, "Schema cloned successfully", cloned_schema
            
        except Exception as e:
            logger.error(f"Failed to clone schema {source_schema_id}: {e}")
            return False, f"Failed to clone schema: {str(e)}", None
    
    def activate_schema(self, schema_id: str, user_id: str = "system") -> Tuple[bool, str]:
        """
        Activate a schema for use
        
        Args:
            schema_id: Schema identifier
            user_id: User activating the schema
            
        Returns:
            Tuple of (success, message)
        """
        try:
            schema = self.storage.load_schema(schema_id)
            if not schema:
                return False, f"Schema {schema_id} not found"
            
            # Validate schema before activation
            if not schema.is_valid():
                validation_errors = schema.validate_structure()
                error_messages = [error.get("message", str(error)) for error in validation_errors]
                return False, f"Cannot activate invalid schema: {'; '.join(error_messages)}"
            
            # Update status
            updates = {
                "status": SchemaStatus.ACTIVE.value,
                "is_active": True
            }
            
            success, message, _ = self.update_schema(
                schema_id, updates, user_id, increment_version=False
            )
            
            if success:
                logger.info(f"Schema {schema_id} activated by {user_id}")
                return True, "Schema activated successfully"
            else:
                return False, f"Failed to activate schema: {message}"
            
        except Exception as e:
            logger.error(f"Failed to activate schema {schema_id}: {e}")
            return False, f"Failed to activate schema: {str(e)}"
    
    def deactivate_schema(self, schema_id: str, user_id: str = "system") -> Tuple[bool, str]:
        """
        Deactivate a schema
        
        Args:
            schema_id: Schema identifier
            user_id: User deactivating the schema
            
        Returns:
            Tuple of (success, message)
        """
        try:
            updates = {
                "is_active": False,
                "status": SchemaStatus.DEPRECATED.value
            }
            
            success, message, _ = self.update_schema(
                schema_id, updates, user_id, increment_version=False
            )
            
            if success:
                logger.info(f"Schema {schema_id} deactivated by {user_id}")
                return True, "Schema deactivated successfully"
            else:
                return False, f"Failed to deactivate schema: {message}"
            
        except Exception as e:
            logger.error(f"Failed to deactivate schema {schema_id}: {e}")
            return False, f"Failed to deactivate schema: {str(e)}"
    
    def record_usage(self, schema_id: str, operation: str = "extract", 
                    user_id: str = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Record schema usage for analytics
        
        Args:
            schema_id: Schema identifier
            operation: Type of operation
            user_id: User performing operation
            metadata: Additional metadata
            
        Returns:
            bool: True if recorded successfully
        """
        try:
            return self.storage.record_schema_usage(schema_id, operation, user_id, metadata)
            
        except Exception as e:
            logger.error(f"Failed to record usage for schema {schema_id}: {e}")
            return False
    
    def get_usage_analytics(self, schema_id: str = None, days: int = 30) -> Dict[str, Any]:
        """
        Get usage analytics
        
        Args:
            schema_id: Specific schema (all if None)
            days: Number of days to analyze
            
        Returns:
            Analytics data
        """
        try:
            return self.storage.get_usage_analytics(schema_id, days)
            
        except Exception as e:
            logger.error(f"Failed to get usage analytics: {e}")
            return {}
    
    def validate_schema_name(self, name: str, schema_id: str = None) -> List[str]:
        """
        Validate schema name
        
        Args:
            name: Schema name to validate
            schema_id: Current schema ID (for updates)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not name:
            errors.append("Schema name is required")
            return errors
        
        if len(name) < 3:
            errors.append("Schema name must be at least 3 characters")
        
        if len(name) > 100:
            errors.append("Schema name must be less than 100 characters")
        
        # Check for duplicate names (excluding current schema)
        existing_schemas = self.storage.list_schemas(active_only=False)
        for schema in existing_schemas:
            if schema["name"] == name and schema["id"] != schema_id:
                errors.append(f"Schema name '{name}' is already used")
                break
        
        return errors
    
    def validate_schema_id(self, schema_id: str) -> List[str]:
        """
        Validate schema ID format
        
        Args:
            schema_id: Schema ID to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not schema_id:
            errors.append("Schema ID is required")
            return errors
        
        # Check format (alphanumeric, underscore, hyphen)
        if not re.match(r'^[a-zA-Z0-9_-]+$', schema_id):
            errors.append("Schema ID can only contain letters, numbers, underscores, and hyphens")
        
        if len(schema_id) < 3:
            errors.append("Schema ID must be at least 3 characters")
        
        if len(schema_id) > 50:
            errors.append("Schema ID must be less than 50 characters")
        
        return errors
    
    @staticmethod
    def increment_version(current_version: str) -> str:
        """
        Increment version number
        
        Args:
            current_version: Current version string (e.g., "v1.2.3")
            
        Returns:
            New version string
        """
        try:
            # Remove 'v' prefix if present
            version = current_version.lstrip('v')
            
            # Split into parts
            parts = version.split('.')
            if len(parts) != 3:
                # If not semantic versioning, just append .1
                return f"v{current_version}.1"
            
            # Increment patch version
            major, minor, patch = parts
            new_patch = int(patch) + 1
            
            return f"v{major}.{minor}.{new_patch}"
            
        except (ValueError, IndexError):
            # If parsing fails, create new version
            return f"v{current_version}.1"
    
    def check_backward_compatibility(self, old_schema: Schema, new_schema: Schema) -> List[str]:
        """
        Check backward compatibility between schema versions
        
        Args:
            old_schema: Previous schema version
            new_schema: New schema version
            
        Returns:
            List of compatibility issues
        """
        issues = []
        
        # Check for removed required fields
        old_required = set()
        new_required = set()
        
        for field_name, field_config in old_schema.fields.items():
            if field_config.get("required", False):
                old_required.add(field_name)
        
        for field_name, field_config in new_schema.fields.items():
            if field_config.get("required", False):
                new_required.add(field_name)
        
        removed_required = old_required - new_required
        if removed_required:
            issues.append(f"Removed required fields: {', '.join(removed_required)}")
        
        # Check for added required fields
        added_required = new_required - old_required
        if added_required:
            issues.append(f"Added required fields: {', '.join(added_required)}")
        
        # Check for field type changes
        for field_name in old_schema.fields:
            if field_name in new_schema.fields:
                old_type = old_schema.fields[field_name].get("type")
                new_type = new_schema.fields[field_name].get("type")
                if old_type != new_type:
                    issues.append(f"Changed field type for '{field_name}': {old_type} -> {new_type}")
        
        return issues
    
    def export_schema(self, schema_id: str, format: str = "json") -> Optional[str]:
        """
        Export schema in specified format
        
        Args:
            schema_id: Schema identifier
            format: Export format ('json', 'yaml', etc.)
            
        Returns:
            Exported schema string or None if failed
        """
        try:
            schema = self.storage.load_schema(schema_id)
            if not schema:
                return None
            
            if format.lower() == "json":
                return schema.to_json()
            else:
                logger.warning(f"Unsupported export format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to export schema {schema_id}: {e}")
            return None
    
    def import_schema(self, schema_data: str, format: str = "json", 
                     user_id: str = "system") -> Tuple[bool, str, Optional[Schema]]:
        """
        Import schema from string data
        
        Args:
            schema_data: Schema data string
            format: Import format ('json', 'yaml', etc.)
            user_id: User importing the schema
            
        Returns:
            Tuple of (success, message, schema_object)
        """
        try:
            if format.lower() == "json":
                schema = Schema.from_json(schema_data)
            else:
                return False, f"Unsupported import format: {format}", None
            
            # Create the schema
            return self.create_schema(schema.to_dict(), user_id)
            
        except Exception as e:
            logger.error(f"Failed to import schema: {e}")
            return False, f"Failed to import schema: {str(e)}", None