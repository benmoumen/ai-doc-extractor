"""
T049: Main integration component
Central integration point for all AI schema generation UI components
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime

from .streamlit_integration import AISchemaGenerationUI
from .document_upload import DocumentUploadUI
from .analysis_progress import AnalysisProgressUI
from .schema_preview import SchemaPreviewUI
from .confidence_display import ConfidenceDisplayUI
from .field_editor import FieldEditorUI

from ..api.main_endpoint import AISchemaGenerationAPI


class AISchemaMainIntegration:
    """Main integration component for AI schema generation UI."""

    def __init__(self):
        """Initialize main integration component"""
        # Initialize API and UI components
        self.api = AISchemaGenerationAPI()
        self.main_ui = AISchemaGenerationUI()
        self.upload_ui = DocumentUploadUI()
        self.progress_ui = AnalysisProgressUI()
        self.preview_ui = SchemaPreviewUI()
        self.confidence_ui = ConfidenceDisplayUI()
        self.field_editor_ui = FieldEditorUI()

        # Initialize session state
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize comprehensive session state"""
        if 'ai_schema_main' not in st.session_state:
            st.session_state.ai_schema_main = {
                'active_workflow': None,
                'current_step': 'upload',
                'workflow_data': {},
                'ui_preferences': {
                    'show_advanced_options': False,
                    'auto_proceed': True,
                    'show_confidence_details': True
                }
            }

    def render_main_application(self):
        """Render the complete AI schema generation application"""
        # Application header
        self._render_app_header()

        # Check for active analysis
        if self.progress_ui.render_compact_progress():
            # Analysis is running, show progress interface
            self._render_analysis_in_progress()
        else:
            # Normal workflow interface
            self._render_workflow_interface()

        # Application footer
        self._render_app_footer()

    def _render_app_header(self):
        """Render application header with navigation"""
        st.title("🤖 AI-Powered Schema Generation")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.caption("Automatically generate document schemas using AI analysis")

        with col2:
            # Service status indicator
            status_result = self.api.get_service_status()
            if status_result['success']:
                st.success("🟢 Services Online")
            else:
                st.error("🔴 Service Error")

        with col3:
            # Settings menu
            if st.button("⚙️ Settings"):
                self._show_settings_modal()

    def _render_workflow_interface(self):
        """Render main workflow interface"""
        # Workflow tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📤 Upload",
            "📋 Analysis",
            "🔧 Schema Editor",
            "📊 Analytics",
            "📜 History"
        ])

        with tab1:
            self._render_upload_workflow()

        with tab2:
            self._render_analysis_workflow()

        with tab3:
            self._render_schema_editor_workflow()

        with tab4:
            self._render_analytics_workflow()

        with tab5:
            self._render_history_workflow()

    def _render_upload_workflow(self):
        """Render document upload workflow"""
        st.header("📤 Document Upload & Analysis")

        # Upload interface
        upload_result = self.upload_ui.render_upload_interface()

        if upload_result and upload_result['success']:
            # Document uploaded successfully
            document = upload_result['document']

            # Show analysis options
            st.subheader("🤖 Analysis Options")

            col1, col2 = st.columns(2)

            with col1:
                # Model selection
                models_result = self.api.get_supported_models()
                if models_result['success']:
                    model_options = {
                        f"{m['name']} ({m['provider']})": m['id']
                        for m in models_result['models']
                    }
                    selected_model = st.selectbox(
                        "AI Model",
                        options=list(model_options.keys())
                    )
                    model_id = model_options[selected_model]
                else:
                    model_id = None

            with col2:
                # Document type hint
                document_type_hint = st.selectbox(
                    "Document Type Hint",
                    ["Auto-detect", "Invoice", "Receipt", "Form", "Driver's License",
                     "Passport", "Bank Statement", "Contract"]
                )
                doc_hint = None if document_type_hint == "Auto-detect" else document_type_hint.lower().replace(" ", "_")

            # Analysis button
            if st.button("🚀 Start AI Analysis", type="primary", disabled=not model_id):
                self._start_analysis_workflow(document, model_id, doc_hint)

        # Bulk upload option
        with st.expander("📦 Bulk Upload"):
            bulk_results = self.upload_ui.render_bulk_upload_interface()
            if bulk_results:
                st.success(f"Uploaded {len(bulk_results)} documents")

    def _render_analysis_workflow(self):
        """Render analysis results workflow"""
        current_analysis = st.session_state.ai_schema_generation.get('current_analysis')

        if not current_analysis:
            st.info("No analysis results available. Upload and analyze a document first.")
            return

        st.header("📋 Analysis Results")

        # Analysis overview
        self._render_analysis_overview(current_analysis)

        # Confidence analysis
        confidence_data = st.session_state.ai_schema_generation.get('last_result', {}).get('confidence', {})
        if confidence_data:
            self.confidence_ui.render_confidence_overview(confidence_data)

        # Detailed analysis results
        detailed_results = self.api.get_analysis_results(current_analysis['id'])
        if detailed_results['success']:
            # Fields analysis
            st.subheader("🔍 Extracted Fields")
            self._render_fields_analysis(detailed_results['fields'])

            # Document type analysis
            if detailed_results['document_type_suggestion']:
                st.subheader("🏷️ Document Type Classification")
                self._render_document_type_analysis(detailed_results['document_type_suggestion'])

    def _render_schema_editor_workflow(self):
        """Render schema editor workflow"""
        current_schema = st.session_state.ai_schema_generation.get('current_schema')

        if not current_schema:
            st.info("No schema available. Complete document analysis first.")
            return

        st.header("🔧 Schema Editor")

        # Schema preview and editing
        schema_details = self.api.get_schema_details(current_schema['id'])
        if schema_details['success']:
            modified_schema = self.preview_ui.render_schema_preview(
                schema_details['schema'],
                interactive=True
            )

            if modified_schema:
                st.success("Schema modifications saved!")
                # Here you would update the schema via API

        # Advanced field editor
        if st.checkbox("🔧 Advanced Field Editor"):
            fields_data = schema_details['schema']['fields'] if schema_details['success'] else {}
            if fields_data:
                field_names = list(fields_data.keys())
                selected_field = st.selectbox("Select field to edit", field_names)

                if selected_field:
                    field_config = fields_data[selected_field]
                    field_changes = self.field_editor_ui.render_field_editor(selected_field, field_config)

                    if field_changes:
                        st.success(f"Field '{selected_field}' updated!")

    def _render_analytics_workflow(self):
        """Render analytics workflow"""
        st.header("📊 Analytics & Insights")

        # Service status
        status_result = self.api.get_service_status()
        if status_result['success']:
            st.subheader("🔧 Service Status")

            col1, col2, col3 = st.columns(3)

            with col1:
                doc_stats = status_result['storage']['documents']
                st.metric(
                    "Total Documents",
                    doc_stats.get('total_documents', 0),
                    f"{doc_stats.get('recent_uploads_24h', 0)} recent"
                )

            with col2:
                analysis_stats = status_result['storage']['analyses']
                st.metric(
                    "Total Analyses",
                    analysis_stats.get('total_analyses', 0)
                )

            with col3:
                schema_stats = status_result['storage']['schemas']
                st.metric(
                    "Generated Schemas",
                    schema_stats.get('total_schemas', 0),
                    f"{schema_stats.get('production_ready_schemas', 0)} ready"
                )

        # Performance analytics
        current_analysis = st.session_state.ai_schema_generation.get('current_analysis')
        if current_analysis:
            confidence_data = st.session_state.ai_schema_generation.get('last_result', {}).get('confidence', {})
            if confidence_data:
                self.confidence_ui.render_confidence_insights(confidence_data)

    def _render_history_workflow(self):
        """Render analysis history workflow"""
        st.header("📜 Analysis History")

        history = st.session_state.ai_schema_generation.get('analysis_history', [])

        if history:
            for i, entry in enumerate(reversed(history[-20:])):  # Show last 20
                with st.expander(f"📄 {entry['filename']} - {entry['timestamp'][:19]}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Document:** {entry['filename']}")
                        st.write(f"**Type:** {entry['document_type'].title()}")

                    with col2:
                        st.write(f"**Model:** {entry['model']}")
                        st.write(f"**Confidence:** {entry['confidence']:.1%}")

                    with col3:
                        if st.button(f"🔄 Load", key=f"load_{i}"):
                            self._load_historical_analysis(entry)

        else:
            st.info("No analysis history available.")

    def _render_analysis_in_progress(self):
        """Render interface when analysis is in progress"""
        st.header("🔄 Analysis in Progress")

        # Full progress interface
        self.progress_ui.render_progress_interface()

        # Option to cancel (if supported)
        if st.button("⏹️ Cancel Analysis", type="secondary"):
            self._cancel_analysis()

    def _start_analysis_workflow(self, document, model_id: str, doc_hint: Optional[str]):
        """Start the analysis workflow"""
        try:
            # Start progress tracking
            self.progress_ui.start_progress_tracking(
                document_name=document.filename,
                model_name=model_id
            )

            # Read document file
            with open(document.file_path, 'rb') as f:
                file_content = f.read()

            # Start analysis with progress updates
            with st.spinner("Starting AI analysis..."):
                result = self.api.analyze_document(
                    file_content=file_content,
                    filename=document.filename,
                    model=model_id,
                    document_type_hint=doc_hint
                )

                # Complete progress tracking
                self.progress_ui.complete_progress_tracking(
                    success=result['success'],
                    final_results=result
                )

                if result['success']:
                    # Store results
                    st.session_state.ai_schema_generation.update({
                        'current_document': result['document'],
                        'current_analysis': result['analysis'],
                        'current_schema': result['schema'],
                        'last_result': result
                    })

                    # Add to history
                    history_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'filename': document.filename,
                        'model': model_id,
                        'document_type': result['analysis']['detected_document_type'],
                        'confidence': result['analysis']['overall_quality_score'],
                        'analysis_id': result['analysis']['id'],
                        'schema_id': result['schema']['id']
                    }

                    if 'analysis_history' not in st.session_state.ai_schema_generation:
                        st.session_state.ai_schema_generation['analysis_history'] = []

                    st.session_state.ai_schema_generation['analysis_history'].append(history_entry)

                    st.success("🎉 Analysis completed successfully!")
                    st.rerun()

                else:
                    st.error(f"Analysis failed: {result.get('fatal_error', 'Unknown error')}")

        except Exception as e:
            st.error(f"Analysis workflow failed: {str(e)}")
            self.progress_ui.complete_progress_tracking(success=False)

    def _render_analysis_overview(self, analysis_data: Dict[str, Any]):
        """Render analysis overview"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Document Type",
                analysis_data['detected_document_type'].title(),
                f"{analysis_data['document_type_confidence']:.1%}"
            )

        with col2:
            st.metric(
                "Fields Detected",
                analysis_data['total_fields_detected'],
                f"{analysis_data['high_confidence_fields']} high conf."
            )

        with col3:
            st.metric(
                "Quality Score",
                f"{analysis_data['overall_quality_score']:.1%}",
                "Overall quality"
            )

        with col4:
            st.metric(
                "Model Used",
                analysis_data['model_used'].split('/')[-1],
                "AI Model"
            )

    def _render_fields_analysis(self, fields_data: List[Dict[str, Any]]):
        """Render fields analysis"""
        if not fields_data:
            st.info("No fields were extracted.")
            return

        # Fields summary
        high_conf_fields = sum(1 for f in fields_data if f['overall_confidence_score'] >= 0.8)
        review_fields = sum(1 for f in fields_data if f['requires_review'])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Fields", len(fields_data))

        with col2:
            st.metric("High Confidence", high_conf_fields)

        with col3:
            st.metric("Need Review", review_fields)

        # Field confidence visualization
        if st.session_state.ai_schema_main['ui_preferences']['show_confidence_details']:
            self.confidence_ui.render_field_confidence_matrix(fields_data)

    def _render_document_type_analysis(self, doc_type_data: Dict[str, Any]):
        """Render document type analysis"""
        primary_type = doc_type_data['suggested_type']
        confidence = doc_type_data['type_confidence']

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Primary Type:** {primary_type.title()}")
            st.write(f"**Confidence:** {confidence:.1%}")

        with col2:
            alternatives = doc_type_data.get('alternative_types', [])
            if alternatives:
                st.write("**Alternatives:**")
                for alt in alternatives[:3]:
                    st.write(f"• {alt['type']} ({alt['confidence']:.1%})")

    def _load_historical_analysis(self, entry: Dict[str, Any]):
        """Load historical analysis"""
        try:
            analysis_result = self.api.get_analysis_results(entry['analysis_id'])
            schema_result = self.api.get_schema_details(entry['schema_id'])

            if analysis_result['success'] and schema_result['success']:
                st.session_state.ai_schema_generation.update({
                    'current_analysis': analysis_result['analysis'],
                    'current_schema': schema_result['schema']
                })
                st.success("Historical analysis loaded!")
                st.rerun()
            else:
                st.error("Failed to load historical analysis")

        except Exception as e:
            st.error(f"Error loading analysis: {str(e)}")

    def _cancel_analysis(self):
        """Cancel ongoing analysis"""
        # Reset progress tracking
        self.progress_ui.complete_progress_tracking(success=False)
        st.warning("Analysis cancelled")
        st.rerun()

    def _show_settings_modal(self):
        """Show settings modal"""
        with st.expander("⚙️ Application Settings", expanded=True):
            st.write("**UI Preferences:**")

            # UI preferences
            show_advanced = st.checkbox(
                "Show Advanced Options",
                value=st.session_state.ai_schema_main['ui_preferences']['show_advanced_options']
            )

            auto_proceed = st.checkbox(
                "Auto-proceed After Analysis",
                value=st.session_state.ai_schema_main['ui_preferences']['auto_proceed']
            )

            show_confidence = st.checkbox(
                "Show Detailed Confidence",
                value=st.session_state.ai_schema_main['ui_preferences']['show_confidence_details']
            )

            if st.button("💾 Save Settings"):
                st.session_state.ai_schema_main['ui_preferences'].update({
                    'show_advanced_options': show_advanced,
                    'auto_proceed': auto_proceed,
                    'show_confidence_details': show_confidence
                })
                st.success("Settings saved!")

    def _render_app_footer(self):
        """Render application footer"""
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.caption("🤖 AI Schema Generation v1.0")

        with col2:
            integration_status = self.main_ui.get_integration_status()
            if all(integration_status.values()):
                st.caption("✅ All systems operational")
            else:
                st.caption("⚠️ Some components not ready")

        with col3:
            st.caption(f"Session: {datetime.now().strftime('%H:%M:%S')}")

    def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status"""
        return {
            'api_available': True,
            'ui_components_loaded': True,
            'session_state_initialized': 'ai_schema_main' in st.session_state,
            'services_online': self.api.get_service_status()['success'],
            'workflow_active': st.session_state.ai_schema_main.get('active_workflow') is not None
        }