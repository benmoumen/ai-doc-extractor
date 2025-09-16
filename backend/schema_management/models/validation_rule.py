"""
ValidationRule entity model implementation.
Based on data-model.md specifications.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
import re


class ValidationRuleType(Enum):
    """Supported validation rule types"""
    REQUIRED = "required"
    LENGTH = "length"
    RANGE = "range"
    PATTERN = "pattern"
    FORMAT = "format"
    OPTIONS = "options"
    CUSTOM = "custom"
    CROSS_FIELD = "cross_field"
    CONDITIONAL = "conditional"


class ValidationSeverity(Enum):
    """Validation rule severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationRule:
    """
    Individual validation rule for field validation
    
    Represents a single validation constraint with configurable parameters,
    error messages, and conditional application logic.
    """
    
    # Core identification
    rule_type: Union[ValidationRuleType, str]
    message: str
    
    # Rule parameters (stored as dict for flexibility)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Conditional application
    condition: Optional[str] = None  # JavaScript-like condition expression
    applies_when: Optional[Dict[str, Any]] = None  # Field dependencies
    
    # Configuration
    severity: ValidationSeverity = ValidationSeverity.ERROR
    enabled: bool = True
    
    # Metadata
    description: str = ""
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps and normalize rule type"""
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.updated_date is None:
            self.updated_date = datetime.now()
        
        # Normalize rule type
        if isinstance(self.rule_type, str):
            try:
                self.rule_type = ValidationRuleType(self.rule_type)
            except ValueError:
                # Keep as string for custom types
                pass
    
    @property
    def type(self) -> str:
        """Get rule type as string"""
        if isinstance(self.rule_type, ValidationRuleType):
            return self.rule_type.value
        return self.rule_type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation rule to dictionary for JSON serialization"""
        return {
            "type": self.type,
            "message": self.message,
            "parameters": self.parameters,
            "condition": self.condition,
            "applies_when": self.applies_when,
            "severity": self.severity.value if isinstance(self.severity, ValidationSeverity) else self.severity,
            "enabled": self.enabled,
            "description": self.description,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "updated_date": self.updated_date.isoformat() if self.updated_date else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationRule':
        """Create validation rule from dictionary (JSON deserialization)"""
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
        
        # Handle severity enum
        severity = data.get("severity", ValidationSeverity.ERROR)
        if isinstance(severity, str):
            try:
                severity = ValidationSeverity(severity)
            except ValueError:
                severity = ValidationSeverity.ERROR
        
        # Handle rule type
        rule_type = data.get("type", "required")
        try:
            rule_type = ValidationRuleType(rule_type)
        except ValueError:
            # Keep as string for custom types
            pass
        
        return cls(
            rule_type=rule_type,
            message=data["message"],
            parameters=data.get("parameters", {}),
            condition=data.get("condition"),
            applies_when=data.get("applies_when"),
            severity=severity,
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
            created_date=created_date,
            updated_date=updated_date
        )
    
    def to_json(self) -> str:
        """Convert validation rule to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ValidationRule':
        """Create validation rule from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """Set a parameter value"""
        self.parameters[key] = value
        self.updated_date = datetime.now()
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a parameter value"""
        return self.parameters.get(key, default)
    
    def has_parameter(self, key: str) -> bool:
        """Check if parameter exists"""
        return key in self.parameters
    
    def remove_parameter(self, key: str) -> bool:
        """Remove a parameter"""
        if key in self.parameters:
            del self.parameters[key]
            self.updated_date = datetime.now()
            return True
        return False
    
    def is_applicable(self, field_values: Dict[str, Any] = None) -> bool:
        """Check if rule is applicable given current field values"""
        if not self.enabled:
            return False
        
        # Check applies_when conditions
        if self.applies_when and field_values:
            for field_name, expected_value in self.applies_when.items():
                field_value = field_values.get(field_name)
                if field_value != expected_value:
                    return False
        
        # Check custom condition (simplified evaluation)
        if self.condition and field_values:
            # This is a basic implementation - in production you might want
            # a more sophisticated expression evaluator
            try:
                # Simple variable substitution for basic conditions
                condition = self.condition
                for field_name, field_value in field_values.items():
                    condition = condition.replace(f"${field_name}", str(field_value))
                
                # Basic evaluation for simple expressions
                if "==" in condition:
                    left, right = condition.split("==", 1)
                    return left.strip() == right.strip()
                elif "!=" in condition:
                    left, right = condition.split("!=", 1)
                    return left.strip() != right.strip()
                # Add more operators as needed
                
            except Exception:
                # If condition evaluation fails, assume rule applies
                return True
        
        return True
    
    def validate_parameters(self) -> List[str]:
        """Validate rule parameters and return list of errors"""
        errors = []
        
        if self.type == "length":
            if not self.has_parameter("min_length") and not self.has_parameter("max_length"):
                errors.append("Length validation must specify min_length or max_length")
            
            min_length = self.get_parameter("min_length")
            max_length = self.get_parameter("max_length")
            
            if min_length is not None and min_length < 0:
                errors.append("min_length must be non-negative")
            
            if max_length is not None and max_length < 0:
                errors.append("max_length must be non-negative")
            
            if min_length is not None and max_length is not None and min_length > max_length:
                errors.append("min_length must be less than or equal to max_length")
        
        elif self.type == "range":
            if not self.has_parameter("min_value") and not self.has_parameter("max_value"):
                errors.append("Range validation must specify min_value or max_value")
            
            min_value = self.get_parameter("min_value")
            max_value = self.get_parameter("max_value")
            
            if min_value is not None and max_value is not None and min_value > max_value:
                errors.append("min_value must be less than or equal to max_value")
        
        elif self.type == "pattern":
            pattern = self.get_parameter("pattern")
            if not pattern:
                errors.append("Pattern validation must specify a pattern")
            else:
                try:
                    re.compile(pattern)
                except re.error as e:
                    errors.append(f"Invalid regex pattern: {e}")
        
        elif self.type == "options":
            options = self.get_parameter("options")
            if not options or not isinstance(options, list):
                errors.append("Options validation must specify a list of valid options")
            elif len(options) == 0:
                errors.append("Options list cannot be empty")
        
        elif self.type == "format":
            format_type = self.get_parameter("format")
            valid_formats = ["email", "phone", "url", "date", "time", "datetime", "uuid", "ipv4", "ipv6"]
            if not format_type:
                errors.append("Format validation must specify a format type")
            elif format_type not in valid_formats:
                errors.append(f"Invalid format type. Valid formats: {', '.join(valid_formats)}")
        
        return errors
    
    def validate_structure(self) -> List[str]:
        """Validate complete rule structure and return list of errors"""
        errors = []
        
        # Validate required fields
        if not self.message:
            errors.append("Validation rule message is required")
        
        if not self.type:
            errors.append("Validation rule type is required")
        
        # Validate parameters based on rule type
        errors.extend(self.validate_parameters())
        
        # Validate condition syntax (basic check)
        if self.condition:
            if not any(op in self.condition for op in ["==", "!=", ">", "<", ">=", "<="]):
                errors.append("Condition must contain a valid operator (==, !=, >, <, >=, <=)")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if validation rule is structurally valid"""
        return len(self.validate_structure()) == 0
    
    def clone(self) -> 'ValidationRule':
        """Create a copy of the validation rule"""
        rule_dict = self.to_dict()
        
        # Reset metadata for clone
        rule_dict["created_date"] = None
        rule_dict["updated_date"] = None
        
        return ValidationRule.from_dict(rule_dict)
    
    @classmethod
    def create_required_rule(cls, message: str = "This field is required") -> 'ValidationRule':
        """Create a required validation rule"""
        return cls(
            rule_type=ValidationRuleType.REQUIRED,
            message=message,
            description="Ensures field value is provided"
        )
    
    @classmethod
    def create_length_rule(cls, min_length: int = None, max_length: int = None, 
                          message: str = None) -> 'ValidationRule':
        """Create a length validation rule"""
        params = {}
        if min_length is not None:
            params["min_length"] = min_length
        if max_length is not None:
            params["max_length"] = max_length
        
        if message is None:
            if min_length is not None and max_length is not None:
                message = f"Length must be between {min_length} and {max_length} characters"
            elif min_length is not None:
                message = f"Must be at least {min_length} characters"
            elif max_length is not None:
                message = f"Must be no more than {max_length} characters"
            else:
                message = "Invalid length"
        
        return cls(
            rule_type=ValidationRuleType.LENGTH,
            message=message,
            parameters=params,
            description="Validates text length constraints"
        )
    
    @classmethod
    def create_range_rule(cls, min_value: float = None, max_value: float = None,
                         message: str = None) -> 'ValidationRule':
        """Create a range validation rule"""
        params = {}
        if min_value is not None:
            params["min_value"] = min_value
        if max_value is not None:
            params["max_value"] = max_value
        
        if message is None:
            if min_value is not None and max_value is not None:
                message = f"Value must be between {min_value} and {max_value}"
            elif min_value is not None:
                message = f"Value must be at least {min_value}"
            elif max_value is not None:
                message = f"Value must be no more than {max_value}"
            else:
                message = "Invalid range"
        
        return cls(
            rule_type=ValidationRuleType.RANGE,
            message=message,
            parameters=params,
            description="Validates numeric value ranges"
        )
    
    @classmethod
    def create_pattern_rule(cls, pattern: str, message: str = None) -> 'ValidationRule':
        """Create a pattern validation rule"""
        if message is None:
            message = f"Value must match pattern: {pattern}"
        
        return cls(
            rule_type=ValidationRuleType.PATTERN,
            message=message,
            parameters={"pattern": pattern},
            description="Validates value against regex pattern"
        )
    
    @classmethod
    def create_format_rule(cls, format_type: str, message: str = None) -> 'ValidationRule':
        """Create a format validation rule"""
        if message is None:
            message = f"Value must be a valid {format_type}"
        
        return cls(
            rule_type=ValidationRuleType.FORMAT,
            message=message,
            parameters={"format": format_type},
            description=f"Validates {format_type} format"
        )
    
    @classmethod
    def create_options_rule(cls, options: List[Any], message: str = None) -> 'ValidationRule':
        """Create an options validation rule"""
        if message is None:
            message = f"Value must be one of: {', '.join(str(opt) for opt in options)}"
        
        return cls(
            rule_type=ValidationRuleType.OPTIONS,
            message=message,
            parameters={"options": options},
            description="Validates value against list of allowed options"
        )


class ValidationRuleSet:
    """
    Collection of validation rules for a field or schema
    """
    
    def __init__(self, rules: List[ValidationRule] = None):
        self.rules = rules or []
        self.created_date = datetime.now()
        self.updated_date = datetime.now()
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule to the set"""
        self.rules.append(rule)
        self.updated_date = datetime.now()
    
    def remove_rule(self, rule_index: int) -> bool:
        """Remove a validation rule by index"""
        if 0 <= rule_index < len(self.rules):
            del self.rules[rule_index]
            self.updated_date = datetime.now()
            return True
        return False
    
    def get_rules_by_type(self, rule_type: str) -> List[ValidationRule]:
        """Get all rules of a specific type"""
        return [rule for rule in self.rules if rule.type == rule_type]
    
    def has_rule_type(self, rule_type: str) -> bool:
        """Check if rule set contains a rule of specific type"""
        return any(rule.type == rule_type for rule in self.rules)
    
    def get_applicable_rules(self, field_values: Dict[str, Any] = None) -> List[ValidationRule]:
        """Get all rules that are applicable given current field values"""
        return [rule for rule in self.rules if rule.is_applicable(field_values)]
    
    def validate_all(self) -> List[str]:
        """Validate all rules in the set and return list of errors"""
        errors = []
        for i, rule in enumerate(self.rules):
            rule_errors = rule.validate_structure()
            for error in rule_errors:
                errors.append(f"Rule {i}: {error}")
        return errors
    
    def is_valid(self) -> bool:
        """Check if all rules in the set are valid"""
        return len(self.validate_all()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule set to dictionary"""
        return {
            "rules": [rule.to_dict() for rule in self.rules],
            "created_date": self.created_date.isoformat(),
            "updated_date": self.updated_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationRuleSet':
        """Create rule set from dictionary"""
        rules = [ValidationRule.from_dict(rule_data) for rule_data in data.get("rules", [])]
        
        rule_set = cls(rules)
        
        if data.get("created_date"):
            rule_set.created_date = datetime.fromisoformat(data["created_date"].replace('Z', '+00:00'))
        if data.get("updated_date"):
            rule_set.updated_date = datetime.fromisoformat(data["updated_date"].replace('Z', '+00:00'))
        
        return rule_set
    
    def clone(self) -> 'ValidationRuleSet':
        """Create a copy of the rule set"""
        cloned_rules = [rule.clone() for rule in self.rules]
        return ValidationRuleSet(cloned_rules)