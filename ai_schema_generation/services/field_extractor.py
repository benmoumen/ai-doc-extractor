"""
T032: FieldExtractor
Service for processing and enhancing extracted fields from AI analysis
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

from ..models.extracted_field import ExtractedField
from ..models.validation_rule_inference import ValidationRuleInference
from ..storage.analysis_storage import AIAnalysisStorage


class FieldExtractionError(Exception):
    """Custom exception for field extraction errors"""
    pass


class FieldExtractor:
    """Service for processing and enhancing extracted fields."""

    # Field type patterns for validation and enhancement
    FIELD_TYPE_PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$',
        'date': r'^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}$|^\d{4}-\d{2}-\d{2}$',
        'url': r'^https?://[^\s<>"{}|\\^`\[\]]+$',
        'currency': r'^\$?[\d,]+\.?\d{0,2}$',
        'ssn': r'^\d{3}-?\d{2}-?\d{4}$',
        'zipcode': r'^\d{5}(-\d{4})?$',
        'number': r'^-?\d+\.?\d*$',
        'boolean': r'^(true|false|yes|no|y|n|1|0)$'
    }

    # Common field name variations
    FIELD_NAME_MAPPINGS = {
        'name': ['full_name', 'customer_name', 'client_name', 'person_name'],
        'first_name': ['fname', 'firstname', 'given_name'],
        'last_name': ['lname', 'lastname', 'surname', 'family_name'],
        'email': ['email_address', 'e_mail', 'electronic_mail'],
        'phone': ['phone_number', 'telephone', 'mobile', 'cell'],
        'address': ['street_address', 'mailing_address', 'billing_address'],
        'city': ['town', 'municipality'],
        'state': ['province', 'region', 'territory'],
        'zip': ['zipcode', 'postal_code', 'zip_code'],
        'amount': ['total', 'sum', 'value', 'price', 'cost'],
        'date': ['date_created', 'created_date', 'issue_date', 'due_date'],
        'id': ['identifier', 'reference', 'number', 'id_number']
    }

    # Required field indicators
    REQUIRED_FIELD_INDICATORS = {
        'invoice': ['invoice_number', 'amount', 'date', 'vendor'],
        'receipt': ['amount', 'date', 'merchant'],
        'form': ['name', 'signature'],
        'drivers_license': ['license_number', 'name', 'date_of_birth'],
        'passport': ['passport_number', 'name', 'date_of_birth'],
        'contract': ['parties', 'date', 'terms'],
        'tax_document': ['tax_year', 'taxpayer_id'],
        'bank_statement': ['account_number', 'statement_date', 'balance']
    }

    def __init__(self, storage: Optional[AIAnalysisStorage] = None):
        """Initialize field extractor"""
        self.storage = storage or AIAnalysisStorage()

    def process_extracted_fields(self, analysis_result_id: str) -> List[ExtractedField]:
        """
        Process and enhance extracted fields from analysis result

        Args:
            analysis_result_id: ID of analysis result

        Returns:
            List of processed ExtractedField instances

        Raises:
            FieldExtractionError: If processing fails
        """
        try:
            # Get extracted fields
            fields = self.storage.get_fields_for_analysis(analysis_result_id)
            if not fields:
                return []

            # Get analysis result for context
            analysis_result = self.storage.get_analysis_result(analysis_result_id)
            if not analysis_result:
                raise FieldExtractionError("Analysis result not found")

            processed_fields = []

            for field in fields:
                # Process individual field
                enhanced_field = self._enhance_field(field, analysis_result.detected_document_type)
                processed_fields.append(enhanced_field)

                # Update field in storage
                self.storage.save_extracted_field(enhanced_field)

            # Perform cross-field analysis
            self._perform_cross_field_analysis(processed_fields, analysis_result.detected_document_type)

            # Group related fields
            self._group_related_fields(processed_fields)

            # Update storage with final enhancements
            for field in processed_fields:
                self.storage.save_extracted_field(field)

            return processed_fields

        except Exception as e:
            raise FieldExtractionError(f"Field processing failed: {str(e)}")

    def _enhance_field(self, field: ExtractedField, document_type: str) -> ExtractedField:
        """Enhance individual field with additional analysis"""
        # Normalize field name
        normalized_name = self._normalize_field_name(field.detected_name)
        if normalized_name != field.detected_name:
            field.add_alternative_name(field.detected_name)
            field.detected_name = normalized_name

        # Validate and enhance field type
        enhanced_type = self._validate_and_enhance_field_type(field)
        if enhanced_type != field.field_type:
            field.add_alternative_type(field.field_type, 0.5)
            field.field_type = enhanced_type

        # Determine if field is required
        field.is_required = self._determine_if_required(field.detected_name, document_type)

        # Add validation hints
        field.has_validation_hints = self._has_validation_patterns(field.field_type)

        # Enhance display name
        field.display_name = self._generate_display_name(field.detected_name, field.field_type)

        # Add context description
        field.context_description = self._generate_context_description(field, document_type)

        # Recalculate confidence based on enhancements
        field.overall_confidence_score = self._recalculate_confidence(field)

        return field

    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name to standard format"""
        # Convert to lowercase and replace spaces/punctuation
        normalized = re.sub(r'[^\w]', '_', field_name.lower().strip())
        normalized = re.sub(r'_+', '_', normalized).strip('_')

        # Check mappings for standard names
        for standard_name, variations in self.FIELD_NAME_MAPPINGS.items():
            if normalized == standard_name or normalized in variations:
                return standard_name

        return normalized

    def _validate_and_enhance_field_type(self, field: ExtractedField) -> str:
        """Validate and potentially enhance field type based on content"""
        if not field.source_text:
            return field.field_type

        source_text = field.source_text.strip()

        # Test against type patterns
        for field_type, pattern in self.FIELD_TYPE_PATTERNS.items():
            if re.match(pattern, source_text, re.IGNORECASE):
                # If it matches a more specific type, use that
                if field_type != 'string' and field.field_type == 'string':
                    return field_type
                # If current type is less specific, upgrade
                elif self._is_more_specific_type(field_type, field.field_type):
                    return field_type

        # Special handling for dates
        if field.field_type in ['string', 'date']:
            if self._looks_like_date(source_text):
                return 'date'

        # Special handling for numbers
        if field.field_type in ['string', 'number']:
            if self._looks_like_number(source_text):
                return 'number'

        # Special handling for currency
        if field.field_type in ['string', 'number', 'currency']:
            if self._looks_like_currency(source_text):
                return 'currency'

        return field.field_type

    def _determine_if_required(self, field_name: str, document_type: str) -> bool:
        """Determine if field should be required based on document type"""
        required_fields = self.REQUIRED_FIELD_INDICATORS.get(document_type, [])

        # Check direct match
        if field_name in required_fields:
            return True

        # Check variations
        for required_field in required_fields:
            variations = self.FIELD_NAME_MAPPINGS.get(required_field, [])
            if field_name in variations:
                return True

        # Special cases
        if 'name' in field_name and document_type in ['form', 'contract', 'drivers_license', 'passport']:
            return True

        if 'amount' in field_name and document_type in ['invoice', 'receipt']:
            return True

        return False

    def _has_validation_patterns(self, field_type: str) -> bool:
        """Check if field type has validation patterns"""
        return field_type in self.FIELD_TYPE_PATTERNS

    def _generate_display_name(self, field_name: str, field_type: str) -> str:
        """Generate human-readable display name"""
        # Convert underscore-separated to title case
        display = field_name.replace('_', ' ').title()

        # Special cases
        display_mappings = {
            'Ssn': 'Social Security Number',
            'Dob': 'Date of Birth',
            'Id': 'ID',
            'Url': 'URL',
            'Email': 'Email Address',
            'Phone': 'Phone Number',
            'Zip': 'ZIP Code'
        }

        for key, value in display_mappings.items():
            if key in display:
                display = display.replace(key, value)

        return display

    def _generate_context_description(self, field: ExtractedField, document_type: str) -> str:
        """Generate context description for field"""
        descriptions = []

        if field.field_type == 'email':
            descriptions.append("Email address field")
        elif field.field_type == 'phone':
            descriptions.append("Phone number field")
        elif field.field_type == 'date':
            descriptions.append("Date field")
        elif field.field_type == 'currency':
            descriptions.append("Currency amount field")

        if field.is_required:
            descriptions.append("Required field")

        if field.overall_confidence_score < 0.6:
            descriptions.append("May require verification")

        document_context = {
            'invoice': f"Invoice {field.field_type} field",
            'receipt': f"Receipt {field.field_type} field",
            'form': f"Form {field.field_type} field"
        }

        if document_type in document_context:
            descriptions.insert(0, document_context[document_type])

        return "; ".join(descriptions) if descriptions else "Extracted field"

    def _recalculate_confidence(self, field: ExtractedField) -> float:
        """Recalculate overall confidence after enhancements"""
        confidence_factors = []

        # Add original scores
        if field.visual_clarity_score > 0:
            confidence_factors.append(field.visual_clarity_score)
        if field.label_confidence_score > 0:
            confidence_factors.append(field.label_confidence_score)
        if field.value_confidence_score > 0:
            confidence_factors.append(field.value_confidence_score)
        if field.type_confidence_score > 0:
            confidence_factors.append(field.type_confidence_score)
        if field.context_confidence_score > 0:
            confidence_factors.append(field.context_confidence_score)

        # Boost for validation patterns
        if field.has_validation_hints and field.source_text:
            pattern = self.FIELD_TYPE_PATTERNS.get(field.field_type)
            if pattern and re.match(pattern, field.source_text, re.IGNORECASE):
                confidence_factors.append(0.9)

        # Boost for required fields
        if field.is_required:
            confidence_factors.append(0.8)

        if not confidence_factors:
            return 0.0

        return sum(confidence_factors) / len(confidence_factors)

    def _perform_cross_field_analysis(self, fields: List[ExtractedField], document_type: str):
        """Perform analysis across all fields"""
        # Group fields by type for consistency checking
        fields_by_type = {}
        for field in fields:
            if field.field_type not in fields_by_type:
                fields_by_type[field.field_type] = []
            fields_by_type[field.field_type].append(field)

        # Check for consistency in similar fields
        self._check_field_consistency(fields_by_type)

        # Validate required fields are present
        self._validate_required_fields_present(fields, document_type)

        # Detect and resolve naming conflicts
        self._resolve_naming_conflicts(fields)

    def _check_field_consistency(self, fields_by_type: Dict[str, List[ExtractedField]]):
        """Check consistency within field types"""
        for field_type, type_fields in fields_by_type.items():
            if len(type_fields) <= 1:
                continue

            # Check for similar field names that might be duplicates
            for i, field1 in enumerate(type_fields):
                for j, field2 in enumerate(type_fields[i+1:], i+1):
                    similarity = self._calculate_name_similarity(field1.detected_name, field2.detected_name)
                    if similarity > 0.8:
                        # Mark lower confidence field for review
                        if field1.overall_confidence_score < field2.overall_confidence_score:
                            field1.mark_for_review("Similar to higher-confidence field")
                        else:
                            field2.mark_for_review("Similar to higher-confidence field")

    def _validate_required_fields_present(self, fields: List[ExtractedField], document_type: str):
        """Validate that required fields are present"""
        required_fields = self.REQUIRED_FIELD_INDICATORS.get(document_type, [])
        if not required_fields:
            return

        present_field_names = {field.detected_name for field in fields}

        for required_field in required_fields:
            if required_field not in present_field_names:
                # Check variations
                variations = self.FIELD_NAME_MAPPINGS.get(required_field, [])
                if not any(var in present_field_names for var in variations):
                    # Required field missing - this affects document quality
                    # Could add metadata or warning here
                    pass

    def _resolve_naming_conflicts(self, fields: List[ExtractedField]):
        """Resolve naming conflicts between fields"""
        name_counts = {}
        for field in fields:
            name_counts[field.detected_name] = name_counts.get(field.detected_name, 0) + 1

        # Handle duplicate names
        for field in fields:
            if name_counts[field.detected_name] > 1:
                # Add field group or location info to make unique
                if field.page_number:
                    field.detected_name = f"{field.detected_name}_page_{field.page_number}"
                elif field.bounding_box:
                    # Use position as differentiator
                    y_pos = int(field.bounding_box.get('y', 0))
                    field.detected_name = f"{field.detected_name}_{y_pos}"

    def _group_related_fields(self, fields: List[ExtractedField]):
        """Group related fields together"""
        # Define field groups
        field_groups = {
            'personal_info': ['name', 'first_name', 'last_name', 'date_of_birth', 'ssn'],
            'contact_info': ['email', 'phone', 'address', 'city', 'state', 'zip'],
            'financial': ['amount', 'total', 'tax', 'subtotal', 'balance'],
            'identification': ['id', 'number', 'reference', 'invoice_number', 'account_number'],
            'dates': ['date', 'due_date', 'issue_date', 'created_date']
        }

        # Assign group names
        for field in fields:
            for group_name, group_fields in field_groups.items():
                if field.detected_name in group_fields:
                    field.set_field_group(group_name)
                    break
                # Check if any part of field name matches
                for group_field in group_fields:
                    if group_field in field.detected_name or field.detected_name in group_field:
                        field.set_field_group(group_name)
                        break

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between field names"""
        if name1 == name2:
            return 1.0

        # Simple Levenshtein-like similarity
        longer = name1 if len(name1) > len(name2) else name2
        shorter = name2 if len(name1) > len(name2) else name1

        if len(longer) == 0:
            return 1.0

        edit_distance = len(longer)
        for i, char in enumerate(shorter):
            if i < len(longer) and char == longer[i]:
                edit_distance -= 1

        return (len(longer) - edit_distance) / len(longer)

    def _is_more_specific_type(self, type1: str, type2: str) -> bool:
        """Check if type1 is more specific than type2"""
        specificity_order = ['string', 'number', 'date', 'email', 'phone', 'url', 'currency', 'ssn']

        try:
            return specificity_order.index(type1) > specificity_order.index(type2)
        except ValueError:
            return False

    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date"""
        date_patterns = [
            r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}'
        ]

        return any(re.search(pattern, text) for pattern in date_patterns)

    def _looks_like_number(self, text: str) -> bool:
        """Check if text looks like a number"""
        # Remove common formatting
        cleaned = re.sub(r'[,\s]', '', text)
        return re.match(r'^-?\d+\.?\d*$', cleaned) is not None

    def _looks_like_currency(self, text: str) -> bool:
        """Check if text looks like currency"""
        currency_patterns = [
            r'^\$[\d,]+\.?\d{0,2}$',
            r'^[\d,]+\.?\d{0,2}\s*USD?$',
            r'^USD?\s*[\d,]+\.?\d{0,2}$'
        ]

        return any(re.match(pattern, text, re.IGNORECASE) for pattern in currency_patterns)

    def get_field_extraction_stats(self) -> Dict[str, Any]:
        """Get field extraction statistics"""
        return {
            'supported_field_types': list(self.FIELD_TYPE_PATTERNS.keys()),
            'field_name_mappings_count': len(self.FIELD_NAME_MAPPINGS),
            'document_type_mappings': list(self.REQUIRED_FIELD_INDICATORS.keys())
        }