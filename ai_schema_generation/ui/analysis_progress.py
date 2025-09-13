"""
T045: Analysis progress tracking UI component
Real-time progress tracking for AI analysis pipeline
"""

import streamlit as st
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class AnalysisProgressUI:
    """UI component for tracking analysis progress."""

    PIPELINE_STAGES = [
        {'key': 'document_processing', 'name': '📄 Document Processing', 'description': 'Validating and preparing document'},
        {'key': 'ai_analysis', 'name': '🤖 AI Analysis', 'description': 'Running AI analysis on document'},
        {'key': 'field_enhancement', 'name': '🔍 Field Enhancement', 'description': 'Processing and enhancing extracted fields'},
        {'key': 'validation_inference', 'name': '✅ Validation Rules', 'description': 'Inferring validation rules'},
        {'key': 'schema_generation', 'name': '📋 Schema Generation', 'description': 'Generating complete schema'},
        {'key': 'confidence_analysis', 'name': '📊 Confidence Analysis', 'description': 'Calculating confidence scores'}
    ]

    def __init__(self):
        """Initialize progress tracking UI"""
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state for progress tracking"""
        if 'analysis_progress' not in st.session_state:
            st.session_state.analysis_progress = {
                'active': False,
                'current_stage': None,
                'stages': {},
                'start_time': None,
                'estimated_completion': None,
                'last_update': None
            }

    def start_progress_tracking(self, document_name: str, model_name: str):
        """Start progress tracking for new analysis"""
        st.session_state.analysis_progress.update({
            'active': True,
            'document_name': document_name,
            'model_name': model_name,
            'current_stage': None,
            'stages': {},
            'start_time': datetime.now(),
            'estimated_completion': datetime.now() + timedelta(seconds=60),  # 1 minute estimate
            'last_update': datetime.now()
        })

    def update_stage_progress(self, stage_key: str, status: str, details: Optional[Dict[str, Any]] = None):
        """Update progress for specific stage"""
        if not st.session_state.analysis_progress['active']:
            return

        st.session_state.analysis_progress['current_stage'] = stage_key
        st.session_state.analysis_progress['stages'][stage_key] = {
            'status': status,  # 'running', 'completed', 'failed'
            'details': details or {},
            'timestamp': datetime.now()
        }
        st.session_state.analysis_progress['last_update'] = datetime.now()

        # Update estimated completion based on progress
        self._update_time_estimate()

    def complete_progress_tracking(self, success: bool, final_results: Optional[Dict[str, Any]] = None):
        """Complete progress tracking"""
        st.session_state.analysis_progress.update({
            'active': False,
            'completed': True,
            'success': success,
            'final_results': final_results,
            'end_time': datetime.now()
        })

    def render_progress_interface(self) -> bool:
        """
        Render progress tracking interface

        Returns:
            True if analysis is active, False otherwise
        """
        if not st.session_state.analysis_progress['active']:
            return False

        progress_data = st.session_state.analysis_progress

        # Progress header
        st.subheader("🔄 Analysis in Progress")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Document:** {progress_data.get('document_name', 'Unknown')}")
            st.write(f"**Model:** {progress_data.get('model_name', 'Unknown')}")

        with col2:
            elapsed = datetime.now() - progress_data['start_time']
            st.write(f"**Elapsed Time:** {elapsed.total_seconds():.1f}s")

            if progress_data.get('estimated_completion'):
                remaining = progress_data['estimated_completion'] - datetime.now()
                if remaining.total_seconds() > 0:
                    st.write(f"**Est. Remaining:** {remaining.total_seconds():.1f}s")
                else:
                    st.write("**Status:** Almost complete...")

        # Overall progress bar
        completed_stages = sum(1 for stage in progress_data['stages'].values() if stage['status'] == 'completed')
        failed_stages = sum(1 for stage in progress_data['stages'].values() if stage['status'] == 'failed')
        total_stages = len(self.PIPELINE_STAGES)

        if failed_stages > 0:
            st.error(f"❌ {failed_stages} stage(s) failed")
            overall_progress = 0
        else:
            overall_progress = completed_stages / total_stages

        st.progress(overall_progress)

        # Detailed stage progress
        st.write("**Pipeline Stages:**")

        for i, stage_info in enumerate(self.PIPELINE_STAGES):
            stage_key = stage_info['key']
            stage_data = progress_data['stages'].get(stage_key)

            col1, col2, col3 = st.columns([3, 1, 2])

            with col1:
                # Stage name and description
                if stage_data:
                    if stage_data['status'] == 'completed':
                        icon = "✅"
                        color = "green"
                    elif stage_data['status'] == 'running':
                        icon = "🔄"
                        color = "blue"
                    elif stage_data['status'] == 'failed':
                        icon = "❌"
                        color = "red"
                    else:
                        icon = "⏸️"
                        color = "gray"
                else:
                    if progress_data['current_stage'] == stage_key:
                        icon = "🔄"
                        color = "blue"
                    elif i < self._get_current_stage_index():
                        icon = "✅"
                        color = "green"
                    else:
                        icon = "⏳"
                        color = "gray"

                st.markdown(f"{icon} **{stage_info['name']}**")
                st.caption(stage_info['description'])

            with col2:
                # Status
                if stage_data:
                    if stage_data['status'] == 'completed':
                        st.success("Done")
                    elif stage_data['status'] == 'running':
                        st.info("Running")
                    elif stage_data['status'] == 'failed':
                        st.error("Failed")
                else:
                    if progress_data['current_stage'] == stage_key:
                        st.info("Active")
                    else:
                        st.write("Pending")

            with col3:
                # Details
                if stage_data and stage_data.get('details'):
                    details = stage_data['details']

                    if 'duration' in details:
                        st.write(f"⏱️ {details['duration']:.1f}s")

                    if 'fields_detected' in details:
                        st.write(f"📝 {details['fields_detected']} fields")

                    if 'confidence' in details:
                        st.write(f"📊 {details['confidence']:.1%}")

        return True

    def render_compact_progress(self) -> bool:
        """
        Render compact progress indicator

        Returns:
            True if analysis is active, False otherwise
        """
        if not st.session_state.analysis_progress['active']:
            return False

        progress_data = st.session_state.analysis_progress

        # Compact progress display
        completed_stages = sum(1 for stage in progress_data['stages'].values() if stage['status'] == 'completed')
        total_stages = len(self.PIPELINE_STAGES)
        progress = completed_stages / total_stages

        current_stage_name = "Initializing..."
        if progress_data.get('current_stage'):
            stage_info = next((s for s in self.PIPELINE_STAGES if s['key'] == progress_data['current_stage']), None)
            if stage_info:
                current_stage_name = stage_info['name']

        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"🔄 **{current_stage_name}**")
                st.progress(progress)

            with col2:
                elapsed = datetime.now() - progress_data['start_time']
                st.metric("Time", f"{elapsed.total_seconds():.0f}s")

        return True

    def render_progress_history(self):
        """Render analysis progress history"""
        st.subheader("📜 Analysis History")

        # This would typically load from storage
        # For now, show placeholder
        st.info("Analysis history will be displayed here once multiple analyses are completed.")

        # Example history entry
        with st.expander("📄 Previous Analysis - invoice.pdf"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Document:** invoice.pdf")
                st.write("**Model:** Llama 3.1 70B")
                st.write("**Status:** ✅ Completed")

            with col2:
                st.write("**Duration:** 45.2s")
                st.write("**Fields:** 12 detected")
                st.write("**Confidence:** 89%")

            with col3:
                st.write("**Started:** 14:30:15")
                st.write("**Completed:** 14:31:00")
                st.write("**Schema ID:** abc123...")

    def _get_current_stage_index(self) -> int:
        """Get index of current stage"""
        current_stage = st.session_state.analysis_progress.get('current_stage')
        if not current_stage:
            return 0

        for i, stage in enumerate(self.PIPELINE_STAGES):
            if stage['key'] == current_stage:
                return i

        return 0

    def _update_time_estimate(self):
        """Update estimated completion time based on progress"""
        progress_data = st.session_state.analysis_progress
        completed_stages = sum(1 for stage in progress_data['stages'].values() if stage['status'] == 'completed')
        total_stages = len(self.PIPELINE_STAGES)

        if completed_stages > 0:
            elapsed = datetime.now() - progress_data['start_time']
            estimated_total_time = elapsed.total_seconds() * (total_stages / completed_stages)
            estimated_completion = progress_data['start_time'] + timedelta(seconds=estimated_total_time)
            st.session_state.analysis_progress['estimated_completion'] = estimated_completion

    def get_progress_status(self) -> Dict[str, Any]:
        """Get current progress status"""
        return {
            'active': st.session_state.analysis_progress['active'],
            'current_stage': st.session_state.analysis_progress.get('current_stage'),
            'completed_stages': len([s for s in st.session_state.analysis_progress['stages'].values() if s['status'] == 'completed']),
            'total_stages': len(self.PIPELINE_STAGES),
            'elapsed_time': (datetime.now() - st.session_state.analysis_progress['start_time']).total_seconds() if st.session_state.analysis_progress.get('start_time') else 0
        }