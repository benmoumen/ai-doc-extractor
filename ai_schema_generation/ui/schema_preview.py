"""
T046: Schema preview UI component
Interactive schema preview with field details and validation
"""

import streamlit as st
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..models.generated_schema import GeneratedSchema


class SchemaPreviewUI:
    """UI component for schema preview and validation."""

    def __init__(self):
        """Initialize schema preview UI"""
        pass

    def render_schema_preview(self, schema_data: Dict[str, Any], interactive: bool = True) -> Optional[Dict[str, Any]]:
        """
        Render schema preview interface

        Args:
            schema_data: Schema data dictionary
            interactive: Whether to show interactive controls

        Returns:
            Modified schema data if changes made, None otherwise
        """
        st.subheader("📋 Schema Preview")

        # Schema header
        self._render_schema_header(schema_data)

        # Schema tabs
        if interactive:
            tab1, tab2, tab3, tab4 = st.tabs([
                "📝 Fields",
                "🔧 Settings",
                "📊 Quality",
                "💾 Export"
            ])

            with tab1:
                modified_fields = self._render_fields_tab(schema_data, editable=True)

            with tab2:
                modified_settings = self._render_settings_tab(schema_data)

            with tab3:
                self._render_quality_tab(schema_data)

            with tab4:
                self._render_export_tab(schema_data)

            # Check if modifications were made
            if modified_fields or modified_settings:
                return self._apply_modifications(schema_data, modified_fields, modified_settings)

        else:
            # Read-only preview
            self._render_fields_tab(schema_data, editable=False)
            self._render_quality_summary(schema_data)

        return None

    def _render_schema_header(self, schema_data: Dict[str, Any]):
        """Render schema header with key information"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Fields",
                schema_data.get('total_fields_generated', 0),
                help="Total number of fields in the schema"
            )

        with col2:
            high_conf = schema_data.get('high_confidence_fields', 0)
            total = schema_data.get('total_fields_generated', 1)
            confidence_ratio = high_conf / total if total > 0 else 0
            st.metric(
                "High Confidence",
                f"{high_conf} ({confidence_ratio:.1%})",
                help="Fields with high confidence scores"
            )

        with col3:
            confidence = schema_data.get('generation_confidence', 0)
            confidence_color = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🔴"
            st.metric(
                "Overall Confidence",
                f"{confidence_color} {confidence:.1%}",
                help="Overall schema generation confidence"
            )

        with col4:
            status = schema_data.get('user_review_status', 'pending')
            status_icons = {
                'pending': '🟡 Pending',
                'in_progress': '🔄 In Progress',
                'reviewed': '✅ Reviewed',
                'approved': '🟢 Approved'
            }
            st.metric(
                "Review Status",
                status_icons.get(status, status.title()),
                help="Current review status"
            )

        # Schema name and description
        st.write(f"**Schema Name:** {schema_data.get('name', 'Untitled Schema')}")
        if schema_data.get('description'):
            st.write(f"**Description:** {schema_data['description']}")

    def _render_fields_tab(self, schema_data: Dict[str, Any], editable: bool = True) -> Optional[Dict[str, Any]]:
        """Render fields tab with field details"""
        fields = schema_data.get('fields', {})

        if not fields:
            st.info("No fields found in this schema.")
            return None

        modifications = {}

        # Field filter and sort options
        if editable:
            col1, col2, col3 = st.columns(3)

            with col1:
                show_filter = st.selectbox(
                    "Show Fields",
                    ["All Fields", "High Confidence", "Low Confidence", "Required", "Optional"]
                )

            with col2:
                sort_by = st.selectbox(
                    "Sort By",
                    ["Name", "Confidence", "Type", "Required"]
                )

            with col3:
                sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)

        # Filter and sort fields
        filtered_fields = self._filter_and_sort_fields(
            fields,
            show_filter if editable else "All Fields",
            sort_by if editable else "Name",
            sort_order if editable else "Ascending"
        )

        # Render fields
        for field_name, field_config in filtered_fields.items():
            with st.expander(f"📝 {field_config.get('display_name', field_name)} ({field_config.get('type', 'unknown')})"):
                if editable:
                    field_modifications = self._render_editable_field(field_name, field_config)
                    if field_modifications:
                        modifications[field_name] = field_modifications
                else:
                    self._render_readonly_field(field_name, field_config)

        return modifications if modifications else None

    def _render_editable_field(self, field_name: str, field_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Render editable field configuration"""
        modifications = {}

        col1, col2 = st.columns(2)

        with col1:
            # Basic field properties
            new_display_name = st.text_input(
                "Display Name",
                value=field_config.get('display_name', field_name),
                key=f"display_name_{field_name}"
            )
            if new_display_name != field_config.get('display_name', field_name):
                modifications['display_name'] = new_display_name

            new_type = st.selectbox(
                "Field Type",
                ['string', 'number', 'date', 'boolean', 'email', 'phone', 'url', 'currency'],
                index=['string', 'number', 'date', 'boolean', 'email', 'phone', 'url', 'currency'].index(
                    field_config.get('type', 'string')
                ),
                key=f"type_{field_name}"
            )
            if new_type != field_config.get('type', 'string'):
                modifications['type'] = new_type

            new_required = st.checkbox(
                "Required Field",
                value=field_config.get('required', False),
                key=f"required_{field_name}"
            )
            if new_required != field_config.get('required', False):
                modifications['required'] = new_required

        with col2:
            # Field description and examples
            new_description = st.text_area(
                "Description",
                value=field_config.get('description', ''),
                key=f"description_{field_name}",
                height=80
            )
            if new_description != field_config.get('description', ''):
                modifications['description'] = new_description

            # Examples
            examples = field_config.get('examples', [])
            if examples:
                st.write("**Examples:**")
                for example in examples[:3]:  # Show first 3 examples
                    st.code(example, language=None)

        # AI metadata display
        ai_metadata = field_config.get('ai_metadata', {})
        if ai_metadata:
            st.write("**AI Analysis:**")

            col1, col2, col3 = st.columns(3)

            with col1:
                confidence = ai_metadata.get('confidence_score', 0)
                confidence_color = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🔴"
                st.write(f"**Confidence:** {confidence_color} {confidence:.1%}")

            with col2:
                if ai_metadata.get('requires_review'):
                    st.warning("⚠️ Requires Review")
                else:
                    st.success("✅ Auto-approved")

            with col3:
                source = ai_metadata.get('source', 'unknown')
                st.write(f"**Source:** {source}")

            # Confidence breakdown
            breakdown = ai_metadata.get('confidence_breakdown', {})
            if breakdown:
                with st.expander("📊 Confidence Breakdown"):
                    for metric, score in breakdown.items():
                        if score > 0:
                            st.write(f"• {metric.replace('_', ' ').title()}: {score:.1%}")

        # Validation rules
        validation_rules = field_config.get('validation_rules', [])
        if validation_rules:
            st.write(f"**Validation Rules ({len(validation_rules)}):**")
            for rule in validation_rules:
                rule_type = rule.get('type', 'unknown')
                description = rule.get('description', 'No description')
                priority = rule.get('priority', 1)
                st.write(f"• **{rule_type.title()}:** {description} (Priority: {priority})")

        return modifications if modifications else None

    def _render_readonly_field(self, field_name: str, field_config: Dict[str, Any]):
        """Render read-only field information"""
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Display Name:** {field_config.get('display_name', field_name)}")
            st.write(f"**Type:** {field_config.get('type', 'unknown')}")
            st.write(f"**Required:** {'Yes' if field_config.get('required', False) else 'No'}")

        with col2:
            ai_metadata = field_config.get('ai_metadata', {})
            if ai_metadata:
                confidence = ai_metadata.get('confidence_score', 0)
                st.write(f"**Confidence:** {confidence:.1%}")
                st.write(f"**Source:** {ai_metadata.get('source', 'unknown')}")

        if field_config.get('description'):
            st.write(f"**Description:** {field_config['description']}")

        examples = field_config.get('examples', [])
        if examples:
            st.write("**Examples:** " + ", ".join(str(ex) for ex in examples[:3]))

    def _render_settings_tab(self, schema_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Render schema settings tab"""
        st.write("**Schema Configuration**")

        modifications = {}

        # Schema name and description
        new_name = st.text_input(
            "Schema Name",
            value=schema_data.get('name', ''),
            help="Descriptive name for this schema"
        )
        if new_name != schema_data.get('name', ''):
            modifications['name'] = new_name

        new_description = st.text_area(
            "Schema Description",
            value=schema_data.get('description', ''),
            help="Detailed description of what this schema represents"
        )
        if new_description != schema_data.get('description', ''):
            modifications['description'] = new_description

        # Schema metadata
        st.write("**Generation Settings**")

        col1, col2 = st.columns(2)

        with col1:
            generation_method = st.selectbox(
                "Generation Method",
                ['ai_generated', 'ai_assisted', 'manual_refined'],
                index=['ai_generated', 'ai_assisted', 'manual_refined'].index(
                    schema_data.get('generation_method', 'ai_generated')
                )
            )
            if generation_method != schema_data.get('generation_method', 'ai_generated'):
                modifications['generation_method'] = generation_method

        with col2:
            validation_status = st.selectbox(
                "Validation Status",
                ['pending', 'partial', 'complete', 'failed'],
                index=['pending', 'partial', 'complete', 'failed'].index(
                    schema_data.get('validation_status', 'pending')
                )
            )
            if validation_status != schema_data.get('validation_status', 'pending'):
                modifications['validation_status'] = validation_status

        # Review settings
        st.write("**Review Settings**")

        review_status = st.selectbox(
            "Review Status",
            ['pending', 'in_progress', 'reviewed', 'approved'],
            index=['pending', 'in_progress', 'reviewed', 'approved'].index(
                schema_data.get('user_review_status', 'pending')
            )
        )
        if review_status != schema_data.get('user_review_status', 'pending'):
            modifications['user_review_status'] = review_status

        review_notes = st.text_area(
            "Review Notes",
            value=schema_data.get('review_notes', '') or '',
            help="Notes about the review process"
        )
        if review_notes != (schema_data.get('review_notes', '') or ''):
            modifications['review_notes'] = review_notes

        return modifications if modifications else None

    def _render_quality_tab(self, schema_data: Dict[str, Any]):
        """Render quality analysis tab"""
        st.write("**Schema Quality Metrics**")

        # Quality overview
        col1, col2, col3 = st.columns(3)

        with col1:
            total_fields = schema_data.get('total_fields_generated', 0)
            high_conf_fields = schema_data.get('high_confidence_fields', 0)
            quality_ratio = high_conf_fields / total_fields if total_fields > 0 else 0

            st.metric(
                "Field Quality",
                f"{quality_ratio:.1%}",
                help="Ratio of high confidence fields"
            )

        with col2:
            generation_conf = schema_data.get('generation_confidence', 0)
            st.metric(
                "Generation Confidence",
                f"{generation_conf:.1%}",
                help="Overall generation confidence"
            )

        with col3:
            user_modified = len(schema_data.get('user_modified_fields', []))
            st.metric(
                "User Modifications",
                user_modified,
                help="Number of user-modified fields"
            )

        # Detailed quality breakdown
        st.write("**Quality Breakdown**")

        fields = schema_data.get('fields', {})
        if fields:
            confidence_distribution = {'high': 0, 'medium': 0, 'low': 0}

            for field_config in fields.values():
                ai_metadata = field_config.get('ai_metadata', {})
                confidence = ai_metadata.get('confidence_score', 0)

                if confidence >= 0.8:
                    confidence_distribution['high'] += 1
                elif confidence >= 0.6:
                    confidence_distribution['medium'] += 1
                else:
                    confidence_distribution['low'] += 1

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("🟢 High Confidence", confidence_distribution['high'])

            with col2:
                st.metric("🟡 Medium Confidence", confidence_distribution['medium'])

            with col3:
                st.metric("🔴 Low Confidence", confidence_distribution['low'])

        # Quality recommendations
        self._show_quality_recommendations(schema_data)

    def _render_export_tab(self, schema_data: Dict[str, Any]):
        """Render export options tab"""
        st.write("**Export Options**")

        # Export formats
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📄 Export JSON", use_container_width=True):
                self._export_json(schema_data)

            if st.button("📋 Copy to Clipboard", use_container_width=True):
                self._copy_to_clipboard(schema_data)

        with col2:
            if st.button("💾 Save to Schema Manager", use_container_width=True):
                self._save_to_schema_manager(schema_data)

            if st.button("📤 Export CSV", use_container_width=True):
                self._export_csv(schema_data)

        # Preview export formats
        with st.expander("👁️ Preview JSON Export"):
            st.json(schema_data)

    def _filter_and_sort_fields(self, fields: Dict[str, Any], show_filter: str, sort_by: str, sort_order: str) -> Dict[str, Any]:
        """Filter and sort fields based on criteria"""
        filtered_fields = {}

        for field_name, field_config in fields.items():
            # Apply filter
            include = True

            if show_filter == "High Confidence":
                ai_metadata = field_config.get('ai_metadata', {})
                confidence = ai_metadata.get('confidence_score', 0)
                include = confidence >= 0.8
            elif show_filter == "Low Confidence":
                ai_metadata = field_config.get('ai_metadata', {})
                confidence = ai_metadata.get('confidence_score', 0)
                include = confidence < 0.6
            elif show_filter == "Required":
                include = field_config.get('required', False)
            elif show_filter == "Optional":
                include = not field_config.get('required', False)

            if include:
                filtered_fields[field_name] = field_config

        # Sort fields
        if sort_by == "Confidence":
            sorted_items = sorted(
                filtered_fields.items(),
                key=lambda x: x[1].get('ai_metadata', {}).get('confidence_score', 0),
                reverse=(sort_order == "Descending")
            )
        elif sort_by == "Type":
            sorted_items = sorted(
                filtered_fields.items(),
                key=lambda x: x[1].get('type', ''),
                reverse=(sort_order == "Descending")
            )
        elif sort_by == "Required":
            sorted_items = sorted(
                filtered_fields.items(),
                key=lambda x: x[1].get('required', False),
                reverse=(sort_order == "Descending")
            )
        else:  # Name
            sorted_items = sorted(
                filtered_fields.items(),
                key=lambda x: x[0],
                reverse=(sort_order == "Descending")
            )

        return dict(sorted_items)

    def _show_quality_recommendations(self, schema_data: Dict[str, Any]):
        """Show quality recommendations"""
        st.write("**Recommendations**")

        recommendations = []

        # Analyze schema and generate recommendations
        total_fields = schema_data.get('total_fields_generated', 0)
        high_conf_fields = schema_data.get('high_confidence_fields', 0)
        generation_conf = schema_data.get('generation_confidence', 0)

        if generation_conf < 0.6:
            recommendations.append("🔴 Overall confidence is low - consider re-analyzing with different model")

        if total_fields > 0:
            low_conf_ratio = (total_fields - high_conf_fields) / total_fields
            if low_conf_ratio > 0.3:
                recommendations.append("🟡 Many fields have low confidence - review individually")

        if schema_data.get('user_review_status') == 'pending':
            recommendations.append("🟡 Schema pending review - review and approve before production use")

        fields = schema_data.get('fields', {})
        required_fields = sum(1 for f in fields.values() if f.get('required', False))
        if required_fields == 0 and total_fields > 0:
            recommendations.append("🟡 No required fields defined - consider marking important fields as required")

        if recommendations:
            for rec in recommendations:
                st.write(f"• {rec}")
        else:
            st.success("✅ Schema quality looks good!")

    def _apply_modifications(self, schema_data: Dict[str, Any], field_modifications: Optional[Dict],
                           settings_modifications: Optional[Dict]) -> Dict[str, Any]:
        """Apply modifications to schema data"""
        modified_schema = schema_data.copy()

        # Apply field modifications
        if field_modifications:
            for field_name, modifications in field_modifications.items():
                if field_name in modified_schema.get('fields', {}):
                    modified_schema['fields'][field_name].update(modifications)

        # Apply settings modifications
        if settings_modifications:
            modified_schema.update(settings_modifications)

        return modified_schema

    def _export_json(self, schema_data: Dict[str, Any]):
        """Export schema as JSON"""
        json_str = json.dumps(schema_data, indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_str,
            file_name=f"{schema_data.get('name', 'schema').replace(' ', '_')}.json",
            mime="application/json"
        )

    def _copy_to_clipboard(self, schema_data: Dict[str, Any]):
        """Copy schema to clipboard"""
        st.success("Schema copied to clipboard! (Feature would be implemented with JavaScript)")

    def _save_to_schema_manager(self, schema_data: Dict[str, Any]):
        """Save schema to schema manager"""
        st.success("Schema saved to Schema Manager! (Integration point)")

    def _export_csv(self, schema_data: Dict[str, Any]):
        """Export schema fields as CSV"""
        st.info("CSV export would generate field list with properties")

    def _render_quality_summary(self, schema_data: Dict[str, Any]):
        """Render quality summary for read-only mode"""
        st.write("**Quality Summary**")

        total_fields = schema_data.get('total_fields_generated', 0)
        high_conf = schema_data.get('high_confidence_fields', 0)
        quality_ratio = high_conf / total_fields if total_fields > 0 else 0

        if quality_ratio >= 0.8:
            st.success(f"🟢 High quality schema ({quality_ratio:.1%} high confidence fields)")
        elif quality_ratio >= 0.6:
            st.warning(f"🟡 Medium quality schema ({quality_ratio:.1%} high confidence fields)")
        else:
            st.error(f"🔴 Low quality schema ({quality_ratio:.1%} high confidence fields)")

    def get_preview_statistics(self) -> Dict[str, Any]:
        """Get preview component statistics"""
        return {
            'supported_field_types': ['string', 'number', 'date', 'boolean', 'email', 'phone', 'url', 'currency'],
            'filter_options': ["All Fields", "High Confidence", "Low Confidence", "Required", "Optional"],
            'sort_options': ["Name", "Confidence", "Type", "Required"],
            'export_formats': ['JSON', 'CSV', 'Schema Manager']
        }