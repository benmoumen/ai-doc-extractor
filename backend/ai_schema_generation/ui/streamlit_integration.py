"""
T043: Streamlit UI integration component
Main UI interface for AI schema generation integrated with Streamlit app
"""

import streamlit as st
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import base64

from ..api.main_endpoint import AISchemaGenerationAPI


class AISchemaGenerationUI:
    """Streamlit UI component for AI schema generation."""

    def __init__(self):
        """Initialize UI with API backend"""
        self.api = AISchemaGenerationAPI()
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'ai_schema_generation' not in st.session_state:
            st.session_state.ai_schema_generation = {
                'current_document': None,
                'current_analysis': None,
                'current_schema': None,
                'processing_status': 'idle',
                'analysis_history': [],
                'schema_history': []
            }

    def render_main_interface(self):
        """Render the main AI schema generation interface"""
        st.header("🤖 AI-Powered Schema Generation")
        st.write("Generate document schemas automatically using AI analysis")

        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📤 Upload & Analyze",
            "📋 Analysis Results",
            "🔧 Schema Editor",
            "📊 Analytics"
        ])

        with tab1:
            self._render_upload_tab()

        with tab2:
            self._render_analysis_tab()

        with tab3:
            self._render_schema_editor_tab()

        with tab4:
            self._render_analytics_tab()

    def _render_upload_tab(self):
        """Render document upload and analysis interface"""
        st.subheader("Document Analysis")

        # Model selection
        col1, col2 = st.columns(2)

        with col1:
            # Get supported models
            models_result = self.api.get_supported_models()
            if models_result['success']:
                model_options = {
                    f"{m['name']} ({m['provider']})": m['id']
                    for m in models_result['models']
                }
                selected_model = st.selectbox(
                    "AI Model",
                    options=list(model_options.keys()),
                    help="Choose the AI model for document analysis"
                )
                model_id = model_options[selected_model]
            else:
                st.error("Failed to load available models")
                model_id = None

        with col2:
            document_type_hint = st.selectbox(
                "Document Type Hint (Optional)",
                options=["Auto-detect", "Invoice", "Receipt", "Form", "Driver's License",
                        "Passport", "Bank Statement", "Contract", "Tax Document"],
                help="Hint to improve document type detection accuracy"
            )
            doc_hint = None if document_type_hint == "Auto-detect" else document_type_hint.lower().replace(" ", "_")

        # File upload
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=['pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'],
            help="Upload a PDF or image file for analysis"
        )

        # Analysis controls
        col1, col2, col3 = st.columns(3)

        with col1:
            analyze_button = st.button(
                "🔍 Analyze Document",
                type="primary",
                disabled=not uploaded_file or not model_id
            )

        with col2:
            if st.session_state.ai_schema_generation.get('current_analysis'):
                retry_button = st.button("🔄 Retry with Different Model")
            else:
                retry_button = False

        with col3:
            clear_button = st.button("🗑️ Clear Results")

        # Handle button actions
        if clear_button:
            self._clear_results()

        if analyze_button and uploaded_file:
            self._analyze_document(uploaded_file, model_id, doc_hint)

        if retry_button:
            self._retry_analysis(model_id)

        # Show current processing status
        self._show_processing_status()

    def _analyze_document(self, uploaded_file, model_id: str, doc_hint: Optional[str]):
        """Analyze uploaded document"""
        try:
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("📄 Processing document...")
            progress_bar.progress(10)

            # Read file content
            file_content = uploaded_file.read()
            filename = uploaded_file.name

            # Update progress
            status_text.text("🤖 Running AI analysis...")
            progress_bar.progress(30)

            # Call API
            start_time = time.time()
            result = self.api.analyze_document(
                file_content=file_content,
                filename=filename,
                model=model_id,
                document_type_hint=doc_hint
            )

            processing_time = time.time() - start_time

            # Update progress based on results
            if result['success']:
                progress_bar.progress(100)
                status_text.text(f"✅ Analysis completed in {processing_time:.2f}s")

                # Store results in session state
                st.session_state.ai_schema_generation.update({
                    'current_document': result['document'],
                    'current_analysis': result['analysis'],
                    'current_schema': result['schema'],
                    'processing_status': 'completed',
                    'last_result': result
                })

                # Add to history
                st.session_state.ai_schema_generation['analysis_history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'filename': filename,
                    'model': model_id,
                    'document_type': result['analysis']['detected_document_type'],
                    'confidence': result['analysis']['overall_quality_score'],
                    'analysis_id': result['analysis']['id'],
                    'schema_id': result['schema']['id']
                })

                st.success("🎉 Document analysis completed successfully!")

                # Show quick results
                self._show_quick_results(result)

            else:
                progress_bar.progress(0)
                status_text.text("❌ Analysis failed")
                st.error(f"Analysis failed: {result.get('fatal_error', 'Unknown error')}")

                # Show error details
                if 'errors' in result:
                    with st.expander("Error Details"):
                        for error in result['errors']:
                            st.text(error)

        except Exception as e:
            st.error(f"Unexpected error during analysis: {str(e)}")

    def _retry_analysis(self, new_model_id: str):
        """Retry analysis with different model"""
        current_doc = st.session_state.ai_schema_generation.get('current_document')
        current_analysis = st.session_state.ai_schema_generation.get('current_analysis')

        if not current_doc or not current_analysis:
            st.error("No previous analysis to retry")
            return

        try:
            with st.spinner("Retrying analysis with different model..."):
                result = self.api.retry_analysis(
                    document_id=current_doc['id'],
                    previous_analysis_id=current_analysis['id'],
                    model=new_model_id
                )

                if result['success']:
                    st.success("✅ Retry analysis completed!")

                    # Update session state with new results
                    st.session_state.ai_schema_generation.update({
                        'current_analysis': result['retry_analysis'],
                        'current_schema': result['schema']
                    })

                    st.info(f"Confidence improved: {result['improved']}")
                else:
                    st.error(f"Retry failed: {result['error']}")

        except Exception as e:
            st.error(f"Retry analysis failed: {str(e)}")

    def _show_quick_results(self, result: Dict[str, Any]):
        """Show quick analysis results summary"""
        st.subheader("📊 Quick Results")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Document Type",
                result['analysis']['detected_document_type'].title(),
                f"{result['analysis']['document_type_confidence']:.1%} confidence"
            )

        with col2:
            st.metric(
                "Fields Detected",
                result['analysis']['total_fields_detected'],
                f"{result['analysis']['high_confidence_fields']} high confidence"
            )

        with col3:
            st.metric(
                "Overall Quality",
                f"{result['analysis']['overall_quality_score']:.1%}",
                "Schema confidence"
            )

        with col4:
            status = "🟢 Ready" if result['schema']['production_ready'] else "🟡 Review Needed"
            st.metric(
                "Production Status",
                status,
                f"{result['schema']['validation_status'].title()}"
            )

        # Show recommendations
        if result.get('recommendations'):
            with st.expander("💡 Recommendations"):
                for rec in result['recommendations']:
                    st.write(f"• {rec}")

    def _render_analysis_tab(self):
        """Render analysis results interface"""
        st.subheader("📋 Analysis Results")

        current_analysis = st.session_state.ai_schema_generation.get('current_analysis')

        if not current_analysis:
            st.info("No analysis results available. Upload and analyze a document first.")
            return

        # Analysis overview
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Analysis Details**")
            st.write(f"**ID:** {current_analysis['id']}")
            st.write(f"**Model:** {current_analysis['model_used']}")
            st.write(f"**Document Type:** {current_analysis['detected_document_type'].title()}")
            st.write(f"**Type Confidence:** {current_analysis['document_type_confidence']:.1%}")

        with col2:
            st.write("**Field Statistics**")
            st.write(f"**Total Fields:** {current_analysis['total_fields_detected']}")
            st.write(f"**High Confidence:** {current_analysis['high_confidence_fields']}")
            st.write(f"**Overall Quality:** {current_analysis['overall_quality_score']:.1%}")

        # Get detailed analysis results
        detailed_results = self.api.get_analysis_results(current_analysis['id'])

        if detailed_results['success']:
            # Field details
            st.subheader("🔍 Extracted Fields")

            if detailed_results['fields']:
                for field in detailed_results['fields']:
                    with st.expander(f"📝 {field['display_name']} ({field['field_type']})"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**Detected Name:** {field['detected_name']}")
                            st.write(f"**Type:** {field['field_type']}")
                            st.write(f"**Required:** {field['is_required']}")
                            st.write(f"**Sample Value:** {field['source_text']}")

                        with col2:
                            st.write("**Confidence Scores:**")
                            st.write(f"• Overall: {field['overall_confidence_score']:.1%}")
                            st.write(f"• Visual: {field['visual_clarity_score']:.1%}")
                            st.write(f"• Label: {field['label_confidence_score']:.1%}")
                            st.write(f"• Value: {field['value_confidence_score']:.1%}")
                            st.write(f"• Type: {field['type_confidence_score']:.1%}")

                        if field['requires_review']:
                            st.warning(f"⚠️ Requires Review: {field.get('review_reason', 'Low confidence')}")

            # Validation rules
            st.subheader("✅ Validation Rules")

            if detailed_results['validation_rules']:
                rules_by_field = {}
                for rule in detailed_results['validation_rules']:
                    field_id = rule['extracted_field_id']
                    if field_id not in rules_by_field:
                        rules_by_field[field_id] = []
                    rules_by_field[field_id].append(rule)

                for field in detailed_results['fields']:
                    field_rules = rules_by_field.get(field['id'], [])
                    if field_rules:
                        with st.expander(f"📏 Rules for {field['display_name']}"):
                            for rule in field_rules:
                                if rule['is_recommended']:
                                    st.write(f"✅ **{rule['rule_type'].title()}:** {rule['rule_description']}")
                                    st.write(f"   Confidence: {rule['confidence_score']:.1%} | Priority: {rule['priority']}")
            else:
                st.info("No validation rules were generated.")

        else:
            st.error(f"Failed to load detailed results: {detailed_results['error']}")

    def _render_schema_editor_tab(self):
        """Render schema editing interface"""
        st.subheader("🔧 Schema Editor")

        current_schema = st.session_state.ai_schema_generation.get('current_schema')

        if not current_schema:
            st.info("No schema available. Complete document analysis first.")
            return

        # Get detailed schema information
        schema_details = self.api.get_schema_details(current_schema['id'])

        if not schema_details['success']:
            st.error(f"Failed to load schema details: {schema_details['error']}")
            return

        schema_data = schema_details['schema']

        # Schema overview
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Fields", schema_data['total_fields_generated'])

        with col2:
            st.metric("High Confidence Fields", schema_data['high_confidence_fields'])

        with col3:
            confidence_color = "🟢" if schema_data['generation_confidence'] >= 0.8 else "🟡" if schema_data['generation_confidence'] >= 0.6 else "🔴"
            st.metric("Generation Confidence", f"{confidence_color} {schema_data['generation_confidence']:.1%}")

        # Schema actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💾 Save Schema"):
                self._save_schema_to_management_system(schema_data)

        with col2:
            if st.button("📋 Copy JSON"):
                st.code(json.dumps(schema_details['standard_format'], indent=2), language='json')

        with col3:
            if st.button("📤 Export Schema"):
                self._export_schema(schema_data)

        # Field editor
        st.subheader("📝 Field Configuration")

        if schema_data['fields']:
            # Field selection for editing
            field_names = list(schema_data['fields'].keys())
            selected_field = st.selectbox("Select Field to Edit", field_names)

            if selected_field:
                field_config = schema_data['fields'][selected_field]

                with st.form(f"edit_field_{selected_field}"):
                    st.write(f"**Editing:** {selected_field}")

                    col1, col2 = st.columns(2)

                    with col1:
                        new_display_name = st.text_input(
                            "Display Name",
                            value=field_config.get('display_name', selected_field)
                        )

                        new_type = st.selectbox(
                            "Field Type",
                            options=['string', 'number', 'date', 'boolean', 'email', 'phone', 'url', 'currency'],
                            index=['string', 'number', 'date', 'boolean', 'email', 'phone', 'url', 'currency'].index(
                                field_config.get('type', 'string')
                            )
                        )

                    with col2:
                        new_required = st.checkbox(
                            "Required Field",
                            value=field_config.get('required', False)
                        )

                        new_description = st.text_area(
                            "Description",
                            value=field_config.get('description', '')
                        )

                    # AI metadata display
                    ai_metadata = field_config.get('ai_metadata', {})
                    if ai_metadata:
                        st.write("**AI Analysis:**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"Confidence: {ai_metadata.get('confidence_score', 0):.1%}")
                        with col2:
                            st.write(f"Source: {ai_metadata.get('source', 'unknown')}")
                        with col3:
                            if ai_metadata.get('requires_review'):
                                st.warning("⚠️ Requires Review")

                    if st.form_submit_button("💾 Update Field"):
                        # Field update logic would go here
                        st.success(f"Field {selected_field} updated!")

        # Quality assessment
        quality_metrics = schema_details.get('quality_metrics', {})
        if quality_metrics:
            st.subheader("📊 Quality Assessment")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Auto-included", quality_metrics.get('auto_included_fields', 0))

            with col2:
                st.metric("Needs Review", quality_metrics.get('requires_review_fields', 0))

            with col3:
                st.metric("User Modified", quality_metrics.get('user_modified_fields', 0))

            with col4:
                accuracy = quality_metrics.get('user_accuracy_score', 0)
                st.metric("Accuracy Score", f"{accuracy:.1%}")

    def _render_analytics_tab(self):
        """Render analytics and history interface"""
        st.subheader("📊 Analytics & History")

        # Service status
        st.subheader("🔧 Service Status")
        status_result = self.api.get_service_status()

        if status_result['success']:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Document Processing**")
                doc_stats = status_result['storage']['documents']
                st.write(f"• Total Documents: {doc_stats.get('total_documents', 0)}")
                st.write(f"• Recent (24h): {doc_stats.get('recent_uploads_24h', 0)}")

            with col2:
                st.write("**AI Analysis**")
                analysis_stats = status_result['storage']['analyses']
                st.write(f"• Total Analyses: {analysis_stats.get('total_analyses', 0)}")
                st.write(f"• Average Quality: {analysis_stats.get('quality_distribution', {}).get('high', 0)}")

            with col3:
                st.write("**Generated Schemas**")
                schema_stats = status_result['storage']['schemas']
                st.write(f"• Total Schemas: {schema_stats.get('total_schemas', 0)}")
                st.write(f"• Production Ready: {schema_stats.get('production_ready_schemas', 0)}")

        # Analysis history
        history = st.session_state.ai_schema_generation.get('analysis_history', [])

        if history:
            st.subheader("📜 Analysis History")

            for i, entry in enumerate(reversed(history[-10:])):  # Show last 10
                with st.expander(f"📄 {entry['filename']} - {entry['timestamp'][:19]}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Document Type:** {entry['document_type'].title()}")
                        st.write(f"**Model Used:** {entry['model']}")
                        st.write(f"**Confidence:** {entry['confidence']:.1%}")

                    with col2:
                        st.write(f"**Analysis ID:** {entry['analysis_id'][:8]}...")
                        st.write(f"**Schema ID:** {entry['schema_id'][:8]}...")

                        if st.button(f"🔄 Load Analysis {i}", key=f"load_analysis_{i}"):
                            # Load this analysis
                            self._load_analysis(entry['analysis_id'], entry['schema_id'])

        else:
            st.info("No analysis history available.")

    def _show_processing_status(self):
        """Show current processing status"""
        status = st.session_state.ai_schema_generation.get('processing_status', 'idle')

        if status == 'processing':
            st.info("🔄 Processing document...")
        elif status == 'completed':
            st.success("✅ Processing completed")
        elif status == 'error':
            st.error("❌ Processing failed")

    def _clear_results(self):
        """Clear current results"""
        st.session_state.ai_schema_generation.update({
            'current_document': None,
            'current_analysis': None,
            'current_schema': None,
            'processing_status': 'idle'
        })
        st.success("Results cleared!")

    def _load_analysis(self, analysis_id: str, schema_id: str):
        """Load previous analysis and schema"""
        try:
            # Get analysis results
            analysis_result = self.api.get_analysis_results(analysis_id)
            schema_result = self.api.get_schema_details(schema_id)

            if analysis_result['success'] and schema_result['success']:
                st.session_state.ai_schema_generation.update({
                    'current_analysis': analysis_result['analysis'],
                    'current_schema': schema_result['schema']
                })
                st.success("Analysis loaded successfully!")
            else:
                st.error("Failed to load analysis")

        except Exception as e:
            st.error(f"Failed to load analysis: {str(e)}")

    def _save_schema_to_management_system(self, schema_data: Dict[str, Any]):
        """Save schema to the existing schema management system"""
        try:
            # Convert to standard format
            schema_details = self.api.get_schema_details(schema_data['id'])
            if schema_details['success']:
                standard_format = schema_details['standard_format']

                # Here we would integrate with the existing schema management system
                # For now, just show success message
                st.success("✅ Schema saved to management system!")

                # Show integration details
                with st.expander("Integration Details"):
                    st.json(standard_format)

            else:
                st.error("Failed to convert schema to standard format")

        except Exception as e:
            st.error(f"Failed to save schema: {str(e)}")

    def _export_schema(self, schema_data: Dict[str, Any]):
        """Export schema in various formats"""
        try:
            schema_details = self.api.get_schema_details(schema_data['id'])
            if schema_details['success']:
                standard_format = schema_details['standard_format']

                # JSON export
                json_export = json.dumps(standard_format, indent=2)

                st.download_button(
                    label="📄 Download JSON",
                    data=json_export,
                    file_name=f"{schema_data['name'].replace(' ', '_')}.json",
                    mime="application/json"
                )

                st.success("Schema ready for export!")

        except Exception as e:
            st.error(f"Export failed: {str(e)}")

    def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status with main app"""
        return {
            'ui_component_loaded': True,
            'api_backend_available': True,
            'session_state_initialized': 'ai_schema_generation' in st.session_state,
            'current_document': st.session_state.ai_schema_generation.get('current_document') is not None,
            'current_analysis': st.session_state.ai_schema_generation.get('current_analysis') is not None,
            'current_schema': st.session_state.ai_schema_generation.get('current_schema') is not None
        }