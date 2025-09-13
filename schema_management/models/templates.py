"""
Template entities model implementation.
Based on data-model.md specifications.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json


class TemplateCategory(Enum):
    """Template categories for organization"""
    GOVERNMENT = "Government"
    BUSINESS = "Business"
    PERSONAL = "Personal"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    FINANCE = "Finance"
    LEGAL = "Legal"
    CUSTOM = "Custom"


class TemplateStatus(Enum):
    """Template lifecycle states"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class FieldTemplate:
    """
    Template for common field configurations
    
    Represents a reusable field definition that can be applied to multiple schemas.
    Contains common validation rules, UI configurations, and field properties.
    """
    
    # Core identification
    id: str
    name: str
    display_name: str
    field_type: str
    
    # Template properties
    description: str = ""
    category: str = "Custom"
    tags: List[str] = field(default_factory=list)
    
    # Default field configuration
    default_required: bool = False
    default_validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    
    # UI Configuration defaults
    default_placeholder: str = ""
    default_help_text: str = ""
    
    # Usage metadata
    usage_count: int = 0
    is_system_template: bool = False
    
    # Metadata
    status: TemplateStatus = TemplateStatus.ACTIVE
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    created_by: str = "system"
    
    def __post_init__(self):
        """Initialize timestamps if not provided"""
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.updated_date is None:
            self.updated_date = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert field template to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "field_type": self.field_type,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "default_required": self.default_required,
            "default_validation_rules": self.default_validation_rules,
            "default_placeholder": self.default_placeholder,
            "default_help_text": self.default_help_text,
            "usage_count": self.usage_count,
            "is_system_template": self.is_system_template,
            "status": self.status.value if isinstance(self.status, TemplateStatus) else self.status,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "updated_date": self.updated_date.isoformat() if self.updated_date else None,
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldTemplate':
        """Create field template from dictionary (JSON deserialization)"""
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
        status = data.get("status", TemplateStatus.ACTIVE)
        if isinstance(status, str):
            try:
                status = TemplateStatus(status)
            except ValueError:
                status = TemplateStatus.ACTIVE
        
        return cls(
            id=data["id"],
            name=data["name"],
            display_name=data["display_name"],
            field_type=data["field_type"],
            description=data.get("description", ""),
            category=data.get("category", "Custom"),
            tags=data.get("tags", []),
            default_required=data.get("default_required", False),
            default_validation_rules=data.get("default_validation_rules", []),
            default_placeholder=data.get("default_placeholder", ""),
            default_help_text=data.get("default_help_text", ""),
            usage_count=data.get("usage_count", 0),
            is_system_template=data.get("is_system_template", False),
            status=status,
            created_date=created_date,
            updated_date=updated_date,
            created_by=data.get("created_by", "system")
        )
    
    def to_json(self) -> str:
        """Convert field template to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'FieldTemplate':
        """Create field template from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def increment_usage(self) -> None:
        """Increment usage counter"""
        self.usage_count += 1
        self.updated_date = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the template"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_date = datetime.now()
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the template"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_date = datetime.now()
            return True
        return False
    
    def has_tag(self, tag: str) -> bool:
        """Check if template has a specific tag"""
        return tag in self.tags
    
    def to_field_config(self) -> Dict[str, Any]:
        """Convert template to field configuration for schema use"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "type": self.field_type,
            "required": self.default_required,
            "description": self.description,
            "placeholder": self.default_placeholder,
            "help_text": self.default_help_text,
            "validation_rules": self.default_validation_rules.copy(),
            "examples": [],  # Templates don't store examples by default
            "depends_on": None,
            "condition": None,
            "condition_value": None
        }
    
    def clone(self, new_id: str = None, new_name: str = None) -> 'FieldTemplate':
        """Create a copy of the field template"""
        template_dict = self.to_dict()
        
        if new_id:
            template_dict["id"] = new_id
        
        if new_name:
            template_dict["name"] = new_name
            # Update display name if it was based on original name
            if template_dict["display_name"] == self.name.replace("_", " ").title():
                template_dict["display_name"] = new_name.replace("_", " ").title()
        
        # Reset metadata for clone
        template_dict["created_date"] = None
        template_dict["updated_date"] = None
        template_dict["usage_count"] = 0
        template_dict["is_system_template"] = False
        
        return FieldTemplate.from_dict(template_dict)


@dataclass
class SchemaTemplate:
    """
    Template for complete schema configurations
    
    Represents a reusable schema definition with predefined fields,
    validation rules, and configuration that can be used to create new schemas.
    """
    
    # Core identification
    id: str
    name: str
    description: str = ""
    category: TemplateCategory = TemplateCategory.CUSTOM
    
    # Template configuration
    field_templates: List[str] = field(default_factory=list)  # Field template IDs
    default_validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    is_system_template: bool = False
    
    # Lifecycle
    status: TemplateStatus = TemplateStatus.ACTIVE
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    created_by: str = "system"
    
    # Documentation
    documentation_url: str = ""
    example_documents: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize timestamps if not provided"""
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.updated_date is None:
            self.updated_date = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema template to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value if isinstance(self.category, TemplateCategory) else self.category,
            "field_templates": self.field_templates,
            "default_validation_rules": self.default_validation_rules,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "is_system_template": self.is_system_template,
            "status": self.status.value if isinstance(self.status, TemplateStatus) else self.status,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "updated_date": self.updated_date.isoformat() if self.updated_date else None,
            "created_by": self.created_by,
            "documentation_url": self.documentation_url,
            "example_documents": self.example_documents
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchemaTemplate':
        """Create schema template from dictionary (JSON deserialization)"""
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
        
        # Handle category enum
        category = data.get("category", TemplateCategory.CUSTOM)
        if isinstance(category, str):
            try:
                category = TemplateCategory(category)
            except ValueError:
                category = TemplateCategory.CUSTOM
        
        # Handle status enum
        status = data.get("status", TemplateStatus.ACTIVE)
        if isinstance(status, str):
            try:
                status = TemplateStatus(status)
            except ValueError:
                status = TemplateStatus.ACTIVE
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            category=category,
            field_templates=data.get("field_templates", []),
            default_validation_rules=data.get("default_validation_rules", []),
            tags=data.get("tags", []),
            usage_count=data.get("usage_count", 0),
            is_system_template=data.get("is_system_template", False),
            status=status,
            created_date=created_date,
            updated_date=updated_date,
            created_by=data.get("created_by", "system"),
            documentation_url=data.get("documentation_url", ""),
            example_documents=data.get("example_documents", [])
        )
    
    def to_json(self) -> str:
        """Convert schema template to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SchemaTemplate':
        """Create schema template from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def add_field_template(self, field_template_id: str) -> None:
        """Add a field template to the schema template"""
        if field_template_id not in self.field_templates:
            self.field_templates.append(field_template_id)
            self.updated_date = datetime.now()
    
    def remove_field_template(self, field_template_id: str) -> bool:
        """Remove a field template from the schema template"""
        if field_template_id in self.field_templates:
            self.field_templates.remove(field_template_id)
            self.updated_date = datetime.now()
            return True
        return False
    
    def has_field_template(self, field_template_id: str) -> bool:
        """Check if schema template includes a specific field template"""
        return field_template_id in self.field_templates
    
    def get_field_count(self) -> int:
        """Get the number of field templates in this schema template"""
        return len(self.field_templates)
    
    def increment_usage(self) -> None:
        """Increment usage counter"""
        self.usage_count += 1
        self.updated_date = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the template"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_date = datetime.now()
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the template"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_date = datetime.now()
            return True
        return False
    
    def has_tag(self, tag: str) -> bool:
        """Check if template has a specific tag"""
        return tag in self.tags
    
    def add_example_document(self, document_name: str) -> None:
        """Add an example document reference"""
        if document_name not in self.example_documents:
            self.example_documents.append(document_name)
            self.updated_date = datetime.now()
    
    def remove_example_document(self, document_name: str) -> bool:
        """Remove an example document reference"""
        if document_name in self.example_documents:
            self.example_documents.remove(document_name)
            self.updated_date = datetime.now()
            return True
        return False
    
    def validate_structure(self) -> List[str]:
        """Validate schema template structure and return list of errors"""
        errors = []
        
        # Validate required fields
        if not self.id:
            errors.append("Schema template ID is required")
        
        if not self.name:
            errors.append("Schema template name is required")
        
        # Validate field templates
        if not self.field_templates:
            errors.append("Schema template must have at least one field template")
        
        # Validate URLs
        if self.documentation_url and not self.documentation_url.startswith(('http://', 'https://')):
            errors.append("Documentation URL must be a valid HTTP/HTTPS URL")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if schema template is structurally valid"""
        return len(self.validate_structure()) == 0
    
    def clone(self, new_id: str = None, new_name: str = None) -> 'SchemaTemplate':
        """Create a copy of the schema template"""
        template_dict = self.to_dict()
        
        if new_id:
            template_dict["id"] = new_id
        
        if new_name:
            template_dict["name"] = new_name
        
        # Reset metadata for clone
        template_dict["created_date"] = None
        template_dict["updated_date"] = None
        template_dict["usage_count"] = 0
        template_dict["is_system_template"] = False
        
        return SchemaTemplate.from_dict(template_dict)


class TemplateLibrary:
    """
    Collection and management of templates
    """
    
    def __init__(self):
        self.field_templates: Dict[str, FieldTemplate] = {}
        self.schema_templates: Dict[str, SchemaTemplate] = {}
        self.created_date = datetime.now()
        self.updated_date = datetime.now()
    
    def add_field_template(self, template: FieldTemplate) -> bool:
        """Add a field template to the library"""
        if template.id in self.field_templates:
            return False
        
        self.field_templates[template.id] = template
        self.updated_date = datetime.now()
        return True
    
    def remove_field_template(self, template_id: str) -> bool:
        """Remove a field template from the library"""
        if template_id in self.field_templates:
            del self.field_templates[template_id]
            self.updated_date = datetime.now()
            return True
        return False
    
    def get_field_template(self, template_id: str) -> Optional[FieldTemplate]:
        """Get a field template by ID"""
        return self.field_templates.get(template_id)
    
    def list_field_templates(self, category: str = None, tags: List[str] = None) -> List[FieldTemplate]:
        """List field templates with optional filtering"""
        templates = list(self.field_templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        return templates
    
    def add_schema_template(self, template: SchemaTemplate) -> bool:
        """Add a schema template to the library"""
        if template.id in self.schema_templates:
            return False
        
        self.schema_templates[template.id] = template
        self.updated_date = datetime.now()
        return True
    
    def remove_schema_template(self, template_id: str) -> bool:
        """Remove a schema template from the library"""
        if template_id in self.schema_templates:
            del self.schema_templates[template_id]
            self.updated_date = datetime.now()
            return True
        return False
    
    def get_schema_template(self, template_id: str) -> Optional[SchemaTemplate]:
        """Get a schema template by ID"""
        return self.schema_templates.get(template_id)
    
    def list_schema_templates(self, category: TemplateCategory = None, tags: List[str] = None) -> List[SchemaTemplate]:
        """List schema templates with optional filtering"""
        templates = list(self.schema_templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        return templates
    
    def get_popular_field_templates(self, limit: int = 10) -> List[FieldTemplate]:
        """Get most popular field templates by usage count"""
        templates = list(self.field_templates.values())
        templates.sort(key=lambda t: t.usage_count, reverse=True)
        return templates[:limit]
    
    def get_popular_schema_templates(self, limit: int = 10) -> List[SchemaTemplate]:
        """Get most popular schema templates by usage count"""
        templates = list(self.schema_templates.values())
        templates.sort(key=lambda t: t.usage_count, reverse=True)
        return templates[:limit]
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about the template library"""
        field_categories = {}
        schema_categories = {}
        
        for template in self.field_templates.values():
            category = template.category
            field_categories[category] = field_categories.get(category, 0) + 1
        
        for template in self.schema_templates.values():
            category = template.category.value if isinstance(template.category, TemplateCategory) else template.category
            schema_categories[category] = schema_categories.get(category, 0) + 1
        
        return {
            "field_template_count": len(self.field_templates),
            "schema_template_count": len(self.schema_templates),
            "field_categories": field_categories,
            "schema_categories": schema_categories,
            "total_field_usage": sum(t.usage_count for t in self.field_templates.values()),
            "total_schema_usage": sum(t.usage_count for t in self.schema_templates.values())
        }
    
    def validate_references(self) -> List[str]:
        """Validate that all template references are valid"""
        errors = []
        
        # Check that schema templates reference valid field templates
        for schema_template in self.schema_templates.values():
            for field_template_id in schema_template.field_templates:
                if field_template_id not in self.field_templates:
                    errors.append(f"Schema template '{schema_template.id}' references non-existent field template '{field_template_id}'")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template library to dictionary"""
        return {
            "field_templates": {tid: template.to_dict() for tid, template in self.field_templates.items()},
            "schema_templates": {tid: template.to_dict() for tid, template in self.schema_templates.items()},
            "created_date": self.created_date.isoformat(),
            "updated_date": self.updated_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateLibrary':
        """Create template library from dictionary"""
        library = cls()
        
        # Load field templates
        for template_id, template_data in data.get("field_templates", {}).items():
            template = FieldTemplate.from_dict(template_data)
            library.field_templates[template_id] = template
        
        # Load schema templates
        for template_id, template_data in data.get("schema_templates", {}).items():
            template = SchemaTemplate.from_dict(template_data)
            library.schema_templates[template_id] = template
        
        # Set timestamps
        if data.get("created_date"):
            library.created_date = datetime.fromisoformat(data["created_date"].replace('Z', '+00:00'))
        if data.get("updated_date"):
            library.updated_date = datetime.fromisoformat(data["updated_date"].replace('Z', '+00:00'))
        
        return library