"""
T048: Advanced field editor UI component
Detailed field editing with validation rules and AI metadata
"""

import streamlit as st
from typing import Dict, Any, List, Optional


class FieldEditorUI:
    """Advanced UI component for editing schema fields."""

    FIELD_TYPES = [
        'string', 'number', 'date', 'boolean',
        'email', 'phone', 'url', 'currency'
    ]

    VALIDATION_RULE_TYPES = [
        'pattern', 'length', 'range', 'format', 'custom'
    ]

    def render_field_editor(self, field_name: str, field_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Render advanced field editor

        Args:
            field_name: Name of the field
            field_config: Current field configuration

        Returns:
            Modified field configuration or None if no changes
        """
        st.subheader(f"✏️ Editing Field: {field_name}")

        modifications = {}

        # Field editor tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔧 Basic Properties",
            "✅ Validation Rules",
            "🤖 AI Analysis",
            "📊 Preview"
        ])

        with tab1:
            basic_changes = self._render_basic_properties_tab(field_name, field_config)
            if basic_changes:
                modifications.update(basic_changes)

        with tab2:
            validation_changes = self._render_validation_rules_tab(field_name, field_config)
            if validation_changes:
                modifications.update(validation_changes)

        with tab3:
            self._render_ai_analysis_tab(field_name, field_config)

        with tab4:
            self._render_preview_tab(field_name, field_config, modifications)

        # Save/Cancel buttons
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("💾 Save Changes", type="primary", disabled=not modifications):
                return modifications

        with col2:
            if st.button("↩️ Reset"):
                st.rerun()

        with col3:
            if modifications:
                st.info(f"✏️ {len(modifications)} changes pending")

        return None

    def _render_basic_properties_tab(self, field_name: str, field_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Render basic field properties tab"""
        changes = {}

        st.write("**Field Identification**")

        col1, col2 = st.columns(2)

        with col1:
            new_display_name = st.text_input(
                "Display Name",
                value=field_config.get('display_name', field_name),
                help="Human-readable name for this field"
            )
            if new_display_name != field_config.get('display_name', field_name):
                changes['display_name'] = new_display_name

            new_type = st.selectbox(
                "Field Type",
                self.FIELD_TYPES,
                index=self.FIELD_TYPES.index(field_config.get('type', 'string')),
                help="Data type for this field"
            )
            if new_type != field_config.get('type', 'string'):
                changes['type'] = new_type

        with col2:
            new_required = st.checkbox(
                "Required Field",
                value=field_config.get('required', False),
                help="Whether this field must have a value"
            )
            if new_required != field_config.get('required', False):
                changes['required'] = new_required

            field_group = st.text_input(
                "Field Group",
                value=field_config.get('group', ''),
                help="Logical group for organizing fields (e.g., 'personal_info', 'billing')"
            )
            if field_group != field_config.get('group', ''):
                changes['group'] = field_group

        st.write("**Field Description**")

        new_description = st.text_area(
            "Description",
            value=field_config.get('description', ''),
            help="Detailed description of this field's purpose",
            height=100
        )
        if new_description != field_config.get('description', ''):
            changes['description'] = new_description

        # Examples management
        st.write("**Example Values**")

        current_examples = field_config.get('examples', [])

        # Display current examples
        for i, example in enumerate(current_examples):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.code(example, language=None)
            with col2:
                if st.button("🗑️", key=f"delete_example_{i}", help="Delete example"):
                    new_examples = current_examples.copy()
                    new_examples.pop(i)
                    changes['examples'] = new_examples

        # Add new example
        new_example = st.text_input(
            "Add Example Value",
            placeholder="Enter an example value for this field"
        )
        if new_example and st.button("➕ Add Example"):
            updated_examples = current_examples + [new_example]
            changes['examples'] = updated_examples

        return changes if changes else None

    def _render_validation_rules_tab(self, field_name: str, field_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Render validation rules tab"""
        changes = {}

        st.write("**Validation Rules**")

        current_rules = field_config.get('validation_rules', [])

        if current_rules:
            st.write("**Current Rules:**")

            # Display current rules
            for i, rule in enumerate(current_rules):
                with st.expander(f"📏 {rule.get('type', 'unknown').title()} Rule"):
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.write(f"**Type:** {rule.get('type', 'unknown')}")
                        st.write(f"**Description:** {rule.get('description', 'No description')}")
                        if rule.get('value'):
                            st.code(str(rule['value']), language=None)

                    with col2:
                        priority = rule.get('priority', 1)
                        st.metric("Priority", priority)

                    with col3:
                        if st.button(f"🗑️ Remove", key=f"remove_rule_{i}"):
                            updated_rules = current_rules.copy()
                            updated_rules.pop(i)
                            changes['validation_rules'] = updated_rules
        else:
            st.info("No validation rules defined for this field.")

        # Add new validation rule
        st.write("**Add New Validation Rule**")

        with st.form(f"add_rule_{field_name}"):
            col1, col2 = st.columns(2)

            with col1:
                rule_type = st.selectbox(
                    "Rule Type",
                    self.VALIDATION_RULE_TYPES,
                    help="Type of validation rule"
                )

                rule_priority = st.number_input(
                    "Priority",
                    min_value=1,
                    max_value=10,
                    value=5,
                    help="Rule priority (1-10, higher = more important)"
                )

            with col2:
                rule_description = st.text_input(
                    "Rule Description",
                    placeholder="Describe what this rule validates"
                )

            # Rule-specific configuration
            rule_value = None

            if rule_type == 'pattern':
                rule_value = st.text_input(
                    "Regular Expression Pattern",
                    placeholder="e.g., ^[A-Z]{2}[0-9]{6}$ for license numbers"
                )

            elif rule_type == 'length':
                col1, col2 = st.columns(2)
                with col1:
                    min_length = st.number_input("Minimum Length", min_value=0, value=1)
                with col2:
                    max_length = st.number_input("Maximum Length", min_value=1, value=100)
                rule_value = {'min_length': min_length, 'max_length': max_length}

            elif rule_type == 'range':
                col1, col2 = st.columns(2)
                with col1:
                    min_value = st.number_input("Minimum Value", value=0.0)
                with col2:
                    max_value = st.number_input("Maximum Value", value=100.0)
                rule_value = {'min_value': min_value, 'max_value': max_value}

            elif rule_type == 'format':
                format_type = st.selectbox(
                    "Format Type",
                    ['email', 'phone', 'date', 'url', 'currency', 'ssn', 'zipcode']
                )
                rule_value = {'format': format_type}

            elif rule_type == 'custom':
                rule_value = st.text_area(
                    "Custom Rule Definition",
                    placeholder="Define custom validation logic"
                )

            if st.form_submit_button("➕ Add Rule"):
                if rule_value and rule_description:
                    new_rule = {
                        'type': rule_type,
                        'value': rule_value,
                        'description': rule_description,
                        'priority': rule_priority
                    }
                    updated_rules = current_rules + [new_rule]
                    changes['validation_rules'] = updated_rules
                    st.success("Rule added! Save the field to apply changes.")

        return changes if changes else None

    def _render_ai_analysis_tab(self, field_name: str, field_config: Dict[str, Any]):
        """Render AI analysis information tab"""
        st.write("**AI Analysis Results**")

        ai_metadata = field_config.get('ai_metadata', {})

        if not ai_metadata:
            st.info("No AI analysis data available for this field.")
            return

        # Overall confidence
        confidence = ai_metadata.get('confidence_score', 0)
        confidence_color = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🔴"

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Overall Confidence",
                f"{confidence_color} {confidence:.1%}",
                help="AI's confidence in this field extraction"
            )

        with col2:
            requires_review = ai_metadata.get('requires_review', False)
            review_status = "⚠️ Needs Review" if requires_review else "✅ Auto-approved"
            st.metric("Review Status", review_status)

        with col3:
            source = ai_metadata.get('source', 'unknown')
            st.metric("Extraction Source", source.replace('_', ' ').title())

        # Confidence breakdown
        breakdown = ai_metadata.get('confidence_breakdown', {})
        if breakdown:
            st.write("**Confidence Breakdown:**")

            breakdown_data = [
                ('Visual Clarity', breakdown.get('visual_clarity', 0)),
                ('Label Confidence', breakdown.get('label_confidence', 0)),
                ('Value Confidence', breakdown.get('value_confidence', 0)),
                ('Type Confidence', breakdown.get('type_confidence', 0)),
                ('Context Confidence', breakdown.get('context_confidence', 0))
            ]

            for metric_name, score in breakdown_data:
                if score > 0:
                    progress_color = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
                    st.write(f"• **{metric_name}:** {progress_color} {score:.1%}")
                    st.progress(score)

        # Location information
        location = ai_metadata.get('location', {})
        if location:
            st.write("**Document Location:**")
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"• **X:** {location.get('x', 0):.0f}")
                st.write(f"• **Y:** {location.get('y', 0):.0f}")

            with col2:
                st.write(f"• **Width:** {location.get('width', 0):.0f}")
                st.write(f"• **Height:** {location.get('height', 0):.0f}")

            page_number = ai_metadata.get('page_number')
            if page_number:
                st.write(f"• **Page:** {page_number}")

        # Alternative interpretations
        alt_names = ai_metadata.get('alternative_names', [])
        alt_types = ai_metadata.get('alternative_types', [])

        if alt_names or alt_types:
            st.write("**Alternative Interpretations:**")

            if alt_names:
                st.write("**Alternative Names:**")
                for alt_name in alt_names:
                    st.write(f"• {alt_name}")

            if alt_types:
                st.write("**Alternative Types:**")
                for alt_type in alt_types:
                    type_name = alt_type.get('type', 'unknown')
                    confidence = alt_type.get('confidence', 0)
                    st.write(f"• {type_name} ({confidence:.1%} confidence)")

    def _render_preview_tab(self, field_name: str, field_config: Dict[str, Any], modifications: Dict[str, Any]):
        """Render field preview tab"""
        st.write("**Field Preview**")

        # Show how the field will appear
        preview_config = field_config.copy()
        if modifications:
            preview_config.update(modifications)

        # Field preview card
        with st.container():
            st.markdown("---")

            # Field header
            display_name = preview_config.get('display_name', field_name)
            field_type = preview_config.get('type', 'string')
            required = preview_config.get('required', False)

            required_indicator = " *" if required else ""
            st.write(f"**{display_name}** ({field_type}){required_indicator}")

            # Description
            description = preview_config.get('description', '')
            if description:
                st.caption(description)

            # Example input based on type
            self._render_field_input_preview(field_type, preview_config)

            # Validation rules preview
            validation_rules = preview_config.get('validation_rules', [])
            if validation_rules:
                st.write("**Validation Rules:**")
                for rule in validation_rules:
                    rule_desc = rule.get('description', 'No description')
                    priority = rule.get('priority', 1)
                    st.write(f"• {rule_desc} (Priority: {priority})")

            st.markdown("---")

        # JSON preview
        if modifications:
            st.write("**Changes Preview:**")
            st.json(modifications)

    def _render_field_input_preview(self, field_type: str, field_config: Dict[str, Any]):
        """Render a preview input based on field type"""
        examples = field_config.get('examples', [])
        placeholder = examples[0] if examples else f"Enter {field_type} value"

        if field_type == 'string':
            st.text_input("Value", placeholder=placeholder, disabled=True)
        elif field_type == 'number':
            st.number_input("Value", disabled=True)
        elif field_type == 'date':
            st.date_input("Value", disabled=True)
        elif field_type == 'boolean':
            st.checkbox("Value", disabled=True)
        elif field_type == 'email':
            st.text_input("Email", placeholder="example@email.com", disabled=True)
        elif field_type == 'phone':
            st.text_input("Phone", placeholder="+1 (555) 123-4567", disabled=True)
        elif field_type == 'url':
            st.text_input("URL", placeholder="https://example.com", disabled=True)
        elif field_type == 'currency':
            st.text_input("Currency", placeholder="$123.45", disabled=True)

    def render_bulk_field_editor(self, fields_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Render bulk field editor for multiple fields"""
        st.subheader("⚙️ Bulk Field Editor")

        if not fields_data:
            st.info("No fields available for bulk editing.")
            return None

        # Bulk operations
        st.write("**Bulk Operations:**")

        col1, col2, col3 = st.columns(3)

        bulk_changes = {}

        with col1:
            # Set required status for multiple fields
            if st.button("📝 Mark Selected as Required"):
                bulk_changes['bulk_required'] = True

        with col2:
            # Set field group for multiple fields
            if st.button("📂 Set Field Group"):
                bulk_changes['bulk_group'] = True

        with col3:
            # Apply validation rules to multiple fields
            if st.button("✅ Apply Validation Rules"):
                bulk_changes['bulk_validation'] = True

        # Field selection
        st.write("**Select Fields for Bulk Operations:**")

        selected_fields = []
        for field_name in fields_data.keys():
            if st.checkbox(field_name, key=f"bulk_select_{field_name}"):
                selected_fields.append(field_name)

        if selected_fields and bulk_changes:
            st.write(f"**Selected {len(selected_fields)} fields for bulk operation:**")
            return {
                'selected_fields': selected_fields,
                'operations': bulk_changes
            }

        return None

    def get_field_editor_stats(self) -> Dict[str, Any]:
        """Get field editor statistics"""
        return {
            'supported_field_types': self.FIELD_TYPES,
            'supported_validation_types': self.VALIDATION_RULE_TYPES,
            'features': [
                'Basic properties editing',
                'Validation rules management',
                'AI analysis visualization',
                'Real-time preview',
                'Bulk operations'
            ]
        }