"""
Field entity model implementation.
Based on data-model.md specifications.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
import re


class FieldType(Enum):
    """Supported field data types"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    BOOLEAN = "boolean"
    SELECT = "select"
    CURRENCY = "currency"
    URL = "url"
    CUSTOM = "custom"


class FieldStatus(Enum):
    """Field lifecycle states"""
    NEW = "new"
    CONFIGURED = "configured"
    VALIDATED = "validated"
    ACTIVE = "active"
    EDITING = "editing"


@dataclass
class Field:
    """
    Individual field configuration within a schema
    
    Represents a single field with its type, validation rules, and UI configuration.
    """
    
    # Core identification
    name: str
    display_name: str
    field_type: Union[FieldType, str]
    
    # Field properties
    required: bool = False
    description: str = ""
    examples: List[str] = field(default_factory=list)
    
    # UI Configuration
    placeholder: str = ""
    help_text: str = ""
    
    # Dependencies
    depends_on: Optional[str] = None
    condition: Optional[str] = None  # "==", "!=", ">", "<", etc.
    condition_value: Optional[Any] = None
    
    # Validation
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    status: FieldStatus = FieldStatus.NEW
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps and normalize field type"""
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.updated_date is None:
            self.updated_date = datetime.now()
        
        # Normalize field type
        if isinstance(self.field_type, str):
            try:
                self.field_type = FieldType(self.field_type)
            except ValueError:
                # Keep as string for custom types
                pass
    
    @property
    def type(self) -> str:
        """Get field type as string"""
        if isinstance(self.field_type, FieldType):
            return self.field_type.value
        return self.field_type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert field to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "examples": self.examples,
            "placeholder": self.placeholder,
            "help_text": self.help_text,
            "depends_on": self.depends_on,
            "condition": self.condition,
            "condition_value": self.condition_value,
            "validation_rules": self.validation_rules,
            "status": self.status.value if isinstance(self.status, FieldStatus) else self.status,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "updated_date": self.updated_date.isoformat() if self.updated_date else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Field':
        """Create field from dictionary (JSON deserialization)"""
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
        status = data.get("status", FieldStatus.NEW)
        if isinstance(status, str):
            try:
                status = FieldStatus(status)
            except ValueError:
                status = FieldStatus.NEW
        
        # Handle field type
        field_type = data.get("type", "text")
        try:
            field_type = FieldType(field_type)
        except ValueError:
            # Keep as string for custom types
            pass
        
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            field_type=field_type,
            required=data.get("required", False),
            description=data.get("description", ""),
            examples=data.get("examples", []),
            placeholder=data.get("placeholder", ""),
            help_text=data.get("help_text", ""),
            depends_on=data.get("depends_on"),
            condition=data.get("condition"),
            condition_value=data.get("condition_value"),
            validation_rules=data.get("validation_rules", []),
            status=status,
            created_date=created_date,
            updated_date=updated_date
        )
    
    def to_json(self) -> str:
        """Convert field to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Field':
        """Create field from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def add_validation_rule(self, rule: Dict[str, Any]) -> None:
        """Add a validation rule to the field"""
        self.validation_rules.append(rule)
        self.updated_date = datetime.now()
    
    def remove_validation_rule(self, rule_index: int) -> bool:
        """Remove a validation rule by index"""
        if 0 <= rule_index < len(self.validation_rules):
            del self.validation_rules[rule_index]
            self.updated_date = datetime.now()
            return True
        return False
    
    def get_validation_rules_by_type(self, rule_type: str) -> List[Dict[str, Any]]:
        """Get validation rules of a specific type"""
        return [rule for rule in self.validation_rules if rule.get("type") == rule_type]
    
    def has_validation_rule(self, rule_type: str) -> bool:
        """Check if field has a validation rule of specific type"""
        return any(rule.get("type") == rule_type for rule in self.validation_rules)
    
    def add_example(self, example: str) -> None:
        """Add an example value"""
        if example not in self.examples:
            self.examples.append(example)
            self.updated_date = datetime.now()
    
    def remove_example(self, example: str) -> bool:
        """Remove an example value"""
        if example in self.examples:
            self.examples.remove(example)
            self.updated_date = datetime.now()
            return True
        return False
    
    def set_dependency(self, depends_on: str, condition: str, condition_value: Any) -> None:
        """Set field dependency"""
        self.depends_on = depends_on
        self.condition = condition
        self.condition_value = condition_value
        self.updated_date = datetime.now()
    
    def clear_dependency(self) -> None:
        """Clear field dependency"""
        self.depends_on = None
        self.condition = None
        self.condition_value = None
        self.updated_date = datetime.now()
    
    def has_dependency(self) -> bool:
        """Check if field has dependency"""
        return self.depends_on is not None
    
    def validate_name(self) -> List[str]:
        """Validate field name and return list of errors"""
        errors = []
        
        if not self.name:
            errors.append("Field name is required")
            return errors
        
        # Check if name is valid Python identifier
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.name):
            errors.append("Field name must be a valid Python identifier (letters, numbers, underscore)")
        
        # Check for reserved keywords
        reserved_keywords = {
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else',
            'except', 'exec', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
            'lambda', 'not', 'or', 'pass', 'print', 'raise', 'return', 'try', 'while', 'with', 'yield'
        }
        
        if self.name.lower() in reserved_keywords:
            errors.append(f"Field name '{self.name}' is a reserved keyword")
        
        return errors
    
    def validate_type(self) -> List[str]:
        """Validate field type and return list of errors"""
        errors = []
        
        if not self.type:
            errors.append("Field type is required")
            return errors
        
        # Check if type is valid
        valid_types = [ft.value for ft in FieldType] + ["custom"]
        if self.type not in valid_types:
            errors.append(f"Invalid field type '{self.type}'. Valid types: {', '.join(valid_types)}")
        
        return errors
    
    def validate_validation_rules(self) -> List[str]:
        """Validate validation rules and return list of errors"""
        errors = []
        
        for i, rule in enumerate(self.validation_rules):
            if not isinstance(rule, dict):
                errors.append(f"Validation rule {i} must be a dictionary")
                continue
            
            if not rule.get("type"):
                errors.append(f"Validation rule {i} must have a 'type' field")
            
            if not rule.get("message"):
                errors.append(f"Validation rule {i} must have a 'message' field")
            
            # Type-specific validation
            rule_type = rule.get("type")
            if rule_type == "length":
                if "min_length" not in rule and "max_length" not in rule:
                    errors.append(f"Length validation rule {i} must specify min_length or max_length")
                
                if rule.get("min_length", 0) < 0:
                    errors.append(f"Length validation rule {i} min_length must be non-negative")
                
                if rule.get("max_length", 0) < 0:
                    errors.append(f"Length validation rule {i} max_length must be non-negative")
                
                if (rule.get("min_length", 0) > rule.get("max_length", float('inf'))):
                    errors.append(f"Length validation rule {i} min_length must be <= max_length")
            
            elif rule_type == "range":
                if "min_value" not in rule and "max_value" not in rule:
                    errors.append(f"Range validation rule {i} must specify min_value or max_value")
                
                if (rule.get("min_value", float('-inf')) > rule.get("max_value", float('inf'))):
                    errors.append(f"Range validation rule {i} min_value must be <= max_value")
            
            elif rule_type == "pattern":
                pattern = rule.get("pattern")
                if not pattern:
                    errors.append(f"Pattern validation rule {i} must specify a pattern")
                else:
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        errors.append(f"Pattern validation rule {i} has invalid regex: {e}")
        
        return errors
    
    def validate_structure(self) -> List[str]:
        """Validate complete field structure and return list of errors"""
        errors = []
        
        errors.extend(self.validate_name())
        errors.extend(self.validate_type())
        errors.extend(self.validate_validation_rules())
        
        # Validate display name
        if not self.display_name:
            errors.append("Field display name is required")
        
        # Validate examples match field type
        if self.examples and self.type:
            type_errors = self._validate_examples_for_type()
            errors.extend(type_errors)
        
        return errors
    
    def _validate_examples_for_type(self) -> List[str]:
        """Validate that examples match the field type"""
        errors = []
        
        for i, example in enumerate(self.examples):
            if self.type == "number":
                try:
                    float(example)
                except (ValueError, TypeError):
                    errors.append(f"Example {i} '{example}' is not a valid number")
            
            elif self.type == "email":
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, str(example)):
                    errors.append(f"Example {i} '{example}' is not a valid email address")
            
            elif self.type == "url":
                url_pattern = r'^https?://[^\s]+$'
                if not re.match(url_pattern, str(example)):
                    errors.append(f"Example {i} '{example}' is not a valid URL")
            
            elif self.type == "boolean":
                if str(example).lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                    errors.append(f"Example {i} '{example}' is not a valid boolean value")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if field is structurally valid"""
        return len(self.validate_structure()) == 0
    
    def get_applicable_validation_types(self) -> List[str]:
        """Get list of validation types applicable to this field type"""
        # All field types support required validation
        applicable = ["required"]
        
        if self.type in ["text", "email", "phone", "url"]:
            applicable.extend(["length", "pattern", "format"])
        
        if self.type == "number":
            applicable.extend(["range"])
        
        if self.type == "select":
            applicable.extend(["options"])
        
        if self.type == "email":
            applicable.extend(["format"])
        
        if self.type == "phone":
            applicable.extend(["format", "pattern"])
        
        if self.type == "url":
            applicable.extend(["format"])
        
        # Custom validation always available
        applicable.append("custom")
        
        return applicable
    
    def clone(self, new_name: str = None) -> 'Field':
        """Create a copy of the field with optional new name"""
        field_dict = self.to_dict()
        
        if new_name:
            field_dict["name"] = new_name
            # Update display name if it was based on original name
            if field_dict["display_name"] == self.name.replace("_", " ").title():
                field_dict["display_name"] = new_name.replace("_", " ").title()
        
        # Reset metadata for clone
        field_dict["created_date"] = None
        field_dict["updated_date"] = None
        field_dict["status"] = FieldStatus.NEW.value
        
        return Field.from_dict(field_dict)