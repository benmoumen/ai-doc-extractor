"""
T050: Main app integration point
Integration with the main Streamlit application (app.py)
"""

import streamlit as st
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add the project root to the path to enable imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ai_schema_generation.ui.main_integration import AISchemaMainIntegration


class AppIntegration:
    """Main integration point for AI schema generation with the existing app."""

    def __init__(self):
        """Initialize app integration"""
        self.ai_schema_ui = AISchemaMainIntegration()
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if all required dependencies are available"""
        try:
            # Check for required packages
            import litellm
            import PIL
            import fitz  # PyMuPDF

            # Check if session state is properly initialized
            if 'ai_schema_integration' not in st.session_state:
                st.session_state.ai_schema_integration = {
                    'enabled': True,
                    'initialized': True,
                    'last_check': str(pd.Timestamp.now()) if 'pd' in globals() else 'unknown'
                }

        except ImportError as e:
            st.error(f"AI Schema Generation: Missing dependency - {str(e)}")
            st.session_state.ai_schema_integration = {'enabled': False, 'error': str(e)}

    def add_to_sidebar(self):
        """Add AI schema generation option to the main app sidebar"""
        if not st.session_state.get('ai_schema_integration', {}).get('enabled', False):
            return

        st.sidebar.markdown("---")
        st.sidebar.subheader("🤖 AI Schema Generation")

        if st.sidebar.button("🚀 Generate Schema from Document"):
            st.session_state.main_app_mode = 'ai_schema_generation'
            st.rerun()

        # Quick status indicator
        try:
            status = self.ai_schema_ui.get_integration_status()
            if status['services_online']:
                st.sidebar.success("✅ AI Services Online")
            else:
                st.sidebar.warning("⚠️ Services Checking...")
        except Exception:
            st.sidebar.error("❌ Service Error")

    def render_in_main_app(self):
        """Render AI schema generation interface in main app"""
        if st.session_state.get('main_app_mode') != 'ai_schema_generation':
            return False

        # Check if properly enabled
        if not st.session_state.get('ai_schema_integration', {}).get('enabled', False):
            st.error("AI Schema Generation is not properly configured")
            error = st.session_state.get('ai_schema_integration', {}).get('error', 'Unknown error')
            st.write(f"Error: {error}")
            return False

        # Render the main AI schema generation interface
        try:
            # Add navigation back to main app
            col1, col2 = st.columns([1, 4])

            with col1:
                if st.button("← Back to Main App"):
                    st.session_state.main_app_mode = 'document_extraction'
                    st.rerun()

            with col2:
                st.markdown("### 🤖 AI-Powered Schema Generation")

            # Render the full AI schema interface
            self.ai_schema_ui.render_main_application()

            return True

        except Exception as e:
            st.error(f"Failed to render AI Schema Generation interface: {str(e)}")
            st.exception(e)
            return False

    def add_to_extraction_results(self, extraction_results: Dict[str, Any]):
        """Add AI schema generation option to extraction results"""
        if not st.session_state.get('ai_schema_integration', {}).get('enabled', False):
            return

        if not extraction_results or not extraction_results.get('success', False):
            return

        st.markdown("---")
        st.subheader("🤖 Generate Schema from This Document")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Generate a reusable schema based on this document structure:**")
            st.write("• Automatic field detection")
            st.write("• Validation rule inference")
            st.write("• Confidence scoring")
            st.write("• Integration with Schema Manager")

        with col2:
            if st.button("🚀 Generate Schema", type="primary"):
                # Store current extraction results for schema generation
                st.session_state.ai_schema_source_data = {
                    'extraction_results': extraction_results,
                    'timestamp': str(pd.Timestamp.now()) if 'pd' in globals() else 'unknown',
                    'source': 'main_app_extraction'
                }

                # Switch to AI schema generation mode
                st.session_state.main_app_mode = 'ai_schema_generation'
                st.rerun()

    def enhance_schema_management_integration(self):
        """Enhance integration with existing schema management system"""
        # This would integrate with the 002-schema-management-ui feature
        # For now, provide integration hooks

        integration_info = {
            'ai_generated_schemas_supported': True,
            'confidence_metadata_preserved': True,
            'validation_rules_compatible': True,
            'import_export_enhanced': True
        }

        return integration_info

    def add_ai_enhancement_to_existing_schemas(self):
        """Add AI enhancement options to existing schema management"""
        if not st.session_state.get('ai_schema_integration', {}).get('enabled', False):
            return

        # This would be called from the existing schema management interface
        st.markdown("### 🤖 AI Enhancement Options")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔍 AI Field Analysis"):
                st.info("Analyze existing schema fields with AI for validation suggestions")

        with col2:
            if st.button("✅ Auto-generate Validation"):
                st.info("Generate validation rules based on field patterns")

        with col3:
            if st.button("📊 Confidence Scoring"):
                st.info("Add confidence scores to existing schema fields")

    def get_integration_metrics(self) -> Dict[str, Any]:
        """Get integration metrics and status"""
        try:
            ai_status = self.ai_schema_ui.get_integration_status()

            return {
                'integration_enabled': st.session_state.get('ai_schema_integration', {}).get('enabled', False),
                'ai_services_online': ai_status.get('services_online', False),
                'ui_components_loaded': ai_status.get('ui_components_loaded', False),
                'session_state_ready': ai_status.get('session_state_initialized', False),
                'last_activity': st.session_state.get('ai_schema_integration', {}).get('last_check', 'never')
            }
        except Exception as e:
            return {
                'integration_enabled': False,
                'error': str(e),
                'status': 'error'
            }

    def cleanup_integration(self):
        """Cleanup integration resources if needed"""
        # Clean up any temporary files or session data
        cleanup_keys = [
            'ai_schema_source_data',
            'ai_schema_generation',
            'ai_schema_main',
            'analysis_progress'
        ]

        for key in cleanup_keys:
            if key in st.session_state:
                del st.session_state[key]

    def check_compatibility(self) -> Dict[str, Any]:
        """Check compatibility with existing app components"""
        compatibility = {
            'streamlit_version': st.__version__,
            'existing_schema_manager': True,  # Assumes 002-schema-management-ui is present
            'litellm_available': False,
            'pymupdf_available': False,
            'pil_available': False
        }

        try:
            import litellm
            compatibility['litellm_available'] = True
        except ImportError:
            pass

        try:
            import fitz
            compatibility['pymupdf_available'] = True
        except ImportError:
            pass

        try:
            import PIL
            compatibility['pil_available'] = True
        except ImportError:
            pass

        compatibility['all_dependencies_met'] = all([
            compatibility['litellm_available'],
            compatibility['pymupdf_available'],
            compatibility['pil_available']
        ])

        return compatibility


# Global integration instance
_app_integration = None

def get_app_integration() -> AppIntegration:
    """Get singleton app integration instance"""
    global _app_integration
    if _app_integration is None:
        _app_integration = AppIntegration()
    return _app_integration


def integrate_with_main_app():
    """Main integration function to be called from app.py"""
    integration = get_app_integration()

    # Add to sidebar
    integration.add_to_sidebar()

    # Handle AI schema generation mode
    if st.session_state.get('main_app_mode') == 'ai_schema_generation':
        return integration.render_in_main_app()

    return False


def enhance_extraction_results(extraction_results: Dict[str, Any]):
    """Enhance extraction results with AI schema generation option"""
    integration = get_app_integration()
    integration.add_to_extraction_results(extraction_results)


def get_integration_status() -> Dict[str, Any]:
    """Get current integration status"""
    integration = get_app_integration()
    return integration.get_integration_metrics()