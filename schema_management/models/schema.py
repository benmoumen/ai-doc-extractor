"""
Schema entity model implementation.
Based on data-model.md specifications.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class SchemaStatus(Enum):
    """Schema lifecycle states"""
    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    EDITING = "editing"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class Schema:
    """
    Complete document schema definition
    
    Represents a document type schema with metadata, fields, and validation rules.
    Supports versioning, lifecycle management, and JSON serialization.
    """
    
    # Core identification
    id: str
    name: str
    description: str = ""
    category: str = "Custom"
    version: str = "v1.0.0"
    
    # Status and flags
    is_active: bool = True
    status: SchemaStatus = SchemaStatus.DRAFT
    
    # Content (stored in JSON files)
    fields: Dict[str, Dict] = field(default_factory=dict)
    validation_rules: List[Dict] = field(default_factory=list)
    
    # Metadata (stored in SQLite)
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    created_by: str = "system"
    usage_count: int = 0
    
    # Versioning
    migration_notes: str = ""
    backward_compatible: bool = True
    
    def __post_init__(self):
        """Initialize timestamps if not provided"""
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.updated_date is None:
            self.updated_date = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "is_active": self.is_active,
            "status": self.status.value if isinstance(self.status, SchemaStatus) else self.status,
            "fields": self.fields,
            "validation_rules": self.validation_rules,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "updated_date": self.updated_date.isoformat() if self.updated_date else None,
            "created_by": self.created_by,
            "usage_count": self.usage_count,
            "migration_notes": self.migration_notes,
            "backward_compatible": self.backward_compatible
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schema':
        """Create schema from dictionary (JSON deserialization)"""
        # Handle datetime parsing
        created_date = None
        updated_date = None
        
        if data.get("created_date"):
            if isinstance(data["created_date"], str):
                created_date = datetime.fromisoformat(data["created_date"].replace('Z', '+00:00'))
            else:
                created_date = data["created_date"]
        
        if data.get("updated_date"):
            if isinstance(data["updated_date"], str):
                updated_date = datetime.fromisoformat(data["updated_date"].replace('Z', '+00:00'))
            else:
                updated_date = data["updated_date"]
        
        # Handle status enum
        status = data.get("status", SchemaStatus.DRAFT)
        if isinstance(status, str):
            try:
                status = SchemaStatus(status)
            except ValueError:
                status = SchemaStatus.DRAFT
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "Custom"),
            version=data.get("version", "v1.0.0"),
            is_active=data.get("is_active", True),
            status=status,
            fields=data.get("fields", {}),
            validation_rules=data.get("validation_rules", []),
            created_date=created_date,
            updated_date=updated_date,
            created_by=data.get("created_by", "system"),
            usage_count=data.get("usage_count", 0),
            migration_notes=data.get("migration_notes", ""),
            backward_compatible=data.get("backward_compatible", True)
        )
    
    def to_json(self) -> str:
        """Convert schema to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Schema':
        """Create schema from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def add_field(self, field_name: str, field_config: Dict[str, Any]) -> None:
        """Add a field to the schema"""
        self.fields[field_name] = field_config
        self.updated_date = datetime.now()
    
    def remove_field(self, field_name: str) -> bool:
        """Remove a field from the schema"""
        if field_name in self.fields:
            del self.fields[field_name]
            self.updated_date = datetime.now()
            return True
        return False
    
    def get_field(self, field_name: str) -> Optional[Dict[str, Any]]:
        """Get a field configuration by name"""
        return self.fields.get(field_name)
    
    def get_required_fields(self) -> List[str]:
        """Get list of required field names"""
        required_fields = []
        for field_name, field_config in self.fields.items():
            if field_config.get("required", False):
                required_fields.append(field_name)
        return required_fields
    
    def get_field_count(self) -> int:
        """Get total number of fields in schema"""
        return len(self.fields)
    
    def update_metadata(self, **kwargs) -> None:
        """Update schema metadata"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_date = datetime.now()
    
    def increment_usage(self) -> None:
        """Increment usage counter"""
        self.usage_count += 1
        self.updated_date = datetime.now()
    
    def validate_structure(self) -> List[Dict[str, str]]:
        """Validate schema structure and return list of errors"""
        errors = []
        
        # Validate required fields
        if not self.id:
            errors.append({"field": "id", "message": "Schema ID is required"})
        
        if not self.name:
            errors.append({"field": "name", "message": "Schema name is required"})
        
        if not self.version:
            errors.append({"field": "version", "message": "Schema version is required"})
        
        # Validate fields
        if not self.fields:
            errors.append({"field": "fields", "message": "Schema must have at least one field"})
        
        # Validate field structure
        for field_name, field_config in self.fields.items():
            if not isinstance(field_config, dict):
                errors.append({"field": f"fields.{field_name}", "message": "Field configuration must be a dictionary"})
                continue
            
            if not field_config.get("name"):
                errors.append({"field": f"fields.{field_name}.name", "message": "Field name is required"})
            
            if not field_config.get("type"):
                errors.append({"field": f"fields.{field_name}.type", "message": "Field type is required"})
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if schema is structurally valid"""
        return len(self.validate_structure()) == 0
    
    def clone(self, new_id: str = None, new_version: str = None) -> 'Schema':
        """Create a copy of the schema with optional new ID/version"""
        schema_dict = self.to_dict()
        
        if new_id:
            schema_dict["id"] = new_id
        
        if new_version:
            schema_dict["version"] = new_version
        
        # Reset metadata for clone
        schema_dict["created_date"] = None
        schema_dict["updated_date"] = None
        schema_dict["usage_count"] = 0
        
        return Schema.from_dict(schema_dict)


class SchemaVersion:
    """
    Schema version tracking
    """
    def __init__(self, schema_id: str, version: str, changes: str = "", 
                 created_by: str = "system", migration_notes: str = ""):
        self.schema_id = schema_id
        self.version = version
        self.changes = changes
        self.created_date = datetime.now()
        self.created_by = created_by
        self.migration_notes = migration_notes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "schema_id": self.schema_id,
            "version": self.version,
            "changes": self.changes,
            "created_date": self.created_date.isoformat(),
            "created_by": self.created_by,
            "migration_notes": self.migration_notes
        }


class SchemaChange:
    """
    Individual change record for schema modifications
    """
    def __init__(self, change_type: str, field_name: str = "", 
                 old_value: Any = None, new_value: Any = None):
        self.change_type = change_type  # "field_added", "field_removed", "field_modified", etc.
        self.field_name = field_name
        self.old_value = old_value
        self.new_value = new_value
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "change_type": self.change_type,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat()
        }