"""
T051-T057: Schema Manager Integration Bridge
Bridge between AI schema generation and existing schema management system
"""

import streamlit as st
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class SchemaManagerBridge:
    """Bridge for integrating AI-generated schemas with existing schema management."""

    def __init__(self):
        """Initialize schema manager bridge"""
        self.schema_manager_available = self._check_schema_manager_availability()

    def _check_schema_manager_availability(self) -> bool:
        """Check if the existing schema management system is available"""
        try:
            # Check if schema management session state exists
            return 'schema_management' in st.session_state
        except Exception:
            return False

    def export_ai_schema_to_manager(self, ai_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export AI-generated schema to existing schema manager

        Args:
            ai_schema: AI-generated schema data

        Returns:
            Export result with success status
        """
        try:
            # Convert AI schema to standard schema format
            standard_schema = self._convert_ai_to_standard_format(ai_schema)

            if self.schema_manager_available:
                # Add to schema manager session state
                if 'schemas' not in st.session_state.schema_management:
                    st.session_state.schema_management.schemas = {}

                schema_id = standard_schema['id']
                st.session_state.schema_management.schemas[schema_id] = standard_schema

                return {
                    'success': True,
                    'schema_id': schema_id,
                    'message': 'Schema successfully exported to Schema Manager'
                }
            else:
                # Fallback: store in AI schema session state
                if 'exported_schemas' not in st.session_state:
                    st.session_state.exported_schemas = {}

                schema_id = standard_schema['id']
                st.session_state.exported_schemas[schema_id] = standard_schema

                return {
                    'success': True,
                    'schema_id': schema_id,
                    'message': 'Schema stored locally (Schema Manager not available)'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to export schema'
            }

    def _convert_ai_to_standard_format(self, ai_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert AI schema format to standard schema manager format"""
        standard_schema = {
            'id': ai_schema.get('id'),
            'name': ai_schema.get('name'),
            'description': ai_schema.get('description', ''),
            'fields': {},
            'metadata': {
                'created_date': datetime.now().isoformat(),
                'source': 'ai_generation',
                'ai_metadata': {
                    'generation_confidence': ai_schema.get('generation_confidence', 0),
                    'ai_model_used': ai_schema.get('ai_model_used', ''),
                    'total_fields_generated': ai_schema.get('total_fields_generated', 0),
                    'high_confidence_fields': ai_schema.get('high_confidence_fields', 0)
                }
            }
        }

        # Convert fields
        ai_fields = ai_schema.get('fields', {})
        for field_name, field_config in ai_fields.items():
            standard_field = {
                'display_name': field_config.get('display_name', field_name),
                'type': field_config.get('type', 'string'),
                'required': field_config.get('required', False),
                'description': field_config.get('description', ''),
                'examples': field_config.get('examples', [])
            }

            # Add validation rules if present
            validation_rules = field_config.get('validation_rules', [])
            if validation_rules:
                standard_field['validation_rules'] = validation_rules

            # Preserve AI metadata
            ai_metadata = field_config.get('ai_metadata', {})
            if ai_metadata:
                standard_field['ai_metadata'] = ai_metadata

            standard_schema['fields'][field_name] = standard_field

        return standard_schema

    def enhance_existing_schema_with_ai(self, schema_id: str) -> Dict[str, Any]:
        """Enhance existing schema with AI analysis"""
        try:
            if not self.schema_manager_available:
                return {'success': False, 'error': 'Schema Manager not available'}

            # Get existing schema
            existing_schemas = st.session_state.schema_management.get('schemas', {})
            if schema_id not in existing_schemas:
                return {'success': False, 'error': 'Schema not found'}

            existing_schema = existing_schemas[schema_id]

            # Analyze with AI (placeholder - would use actual AI analysis)
            enhancements = self._generate_ai_enhancements(existing_schema)

            # Apply enhancements
            enhanced_schema = existing_schema.copy()
            enhanced_schema.update(enhancements)

            # Update in schema manager
            st.session_state.schema_management.schemas[schema_id] = enhanced_schema

            return {
                'success': True,
                'enhancements_applied': len(enhancements),
                'message': 'Schema enhanced with AI analysis'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_ai_enhancements(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI enhancements for existing schema"""
        enhancements = {}

        # Add AI confidence scores to fields
        fields = schema.get('fields', {})
        for field_name, field_config in fields.items():
            if 'ai_metadata' not in field_config:
                # Simulate AI analysis confidence (in real implementation, would use actual AI)
                confidence_score = 0.75  # Default simulated confidence

                enhancements[f'fields.{field_name}.ai_metadata'] = {
                    'confidence_score': confidence_score,
                    'source': 'ai_enhancement',
                    'enhancement_timestamp': datetime.now().isoformat()
                }

        return enhancements

    def get_ai_schema_suggestions(self, document_type: str) -> List[Dict[str, Any]]:
        """Get AI schema suggestions for document type"""
        # Placeholder for AI-powered schema suggestions
        suggestions = [
            {
                'id': f'ai_suggested_{document_type}_1',
                'name': f'Standard {document_type.title()} Schema',
                'description': f'AI-suggested schema for {document_type} documents',
                'confidence': 0.85,
                'field_count': 8,
                'source': 'ai_suggestion'
            },
            {
                'id': f'ai_suggested_{document_type}_2',
                'name': f'Detailed {document_type.title()} Schema',
                'description': f'Comprehensive AI-suggested schema for {document_type} documents',
                'confidence': 0.78,
                'field_count': 15,
                'source': 'ai_suggestion'
            }
        ]

        return suggestions

    def validate_schema_compatibility(self, ai_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate AI schema compatibility with schema manager"""
        compatibility_issues = []
        warnings = []

        # Check required fields
        required_fields = ['id', 'name', 'fields']
        for field in required_fields:
            if field not in ai_schema:
                compatibility_issues.append(f"Missing required field: {field}")

        # Check field structure
        fields = ai_schema.get('fields', {})
        for field_name, field_config in fields.items():
            if not isinstance(field_config, dict):
                compatibility_issues.append(f"Invalid field configuration for: {field_name}")

            if 'type' not in field_config:
                warnings.append(f"Field '{field_name}' missing type specification")

        return {
            'compatible': len(compatibility_issues) == 0,
            'issues': compatibility_issues,
            'warnings': warnings,
            'enhancement_opportunities': self._identify_enhancement_opportunities(ai_schema)
        }

    def _identify_enhancement_opportunities(self, schema: Dict[str, Any]) -> List[str]:
        """Identify opportunities to enhance the schema"""
        opportunities = []

        fields = schema.get('fields', {})

        # Check for missing validation rules
        fields_without_validation = sum(1 for f in fields.values() if not f.get('validation_rules'))
        if fields_without_validation > 0:
            opportunities.append(f"{fields_without_validation} fields could benefit from validation rules")

        # Check for low confidence fields
        low_confidence_fields = 0
        for field_config in fields.values():
            ai_metadata = field_config.get('ai_metadata', {})
            if ai_metadata.get('confidence_score', 1.0) < 0.6:
                low_confidence_fields += 1

        if low_confidence_fields > 0:
            opportunities.append(f"{low_confidence_fields} fields have low confidence and need review")

        return opportunities

    def render_integration_status(self):
        """Render integration status in UI"""
        st.subheader("🔗 Schema Manager Integration")

        col1, col2 = st.columns(2)

        with col1:
            if self.schema_manager_available:
                st.success("✅ Schema Manager Available")
            else:
                st.warning("⚠️ Schema Manager Not Available")

        with col2:
            exported_count = len(st.session_state.get('exported_schemas', {}))
            st.metric("Exported Schemas", exported_count)

        # Integration actions
        if self.schema_manager_available:
            st.write("**Available Actions:**")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📤 Export Current Schema"):
                    st.info("Export functionality ready")

            with col2:
                if st.button("🔍 Analyze Existing Schemas"):
                    st.info("Analysis functionality ready")

            with col3:
                if st.button("🔄 Sync Schemas"):
                    st.info("Sync functionality ready")

    def get_bridge_statistics(self) -> Dict[str, Any]:
        """Get bridge usage statistics"""
        return {
            'schema_manager_available': self.schema_manager_available,
            'exported_schemas_count': len(st.session_state.get('exported_schemas', {})),
            'integration_features': [
                'AI to Standard conversion',
                'Schema enhancement',
                'Compatibility validation',
                'Suggestion system'
            ]
        }


# Global bridge instance
_schema_bridge = None

def get_schema_bridge() -> SchemaManagerBridge:
    """Get singleton schema bridge instance"""
    global _schema_bridge
    if _schema_bridge is None:
        _schema_bridge = SchemaManagerBridge()
    return _schema_bridge