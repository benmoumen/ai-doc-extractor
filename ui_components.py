"""
UI components and display functions for the Streamlit app.
"""
import streamlit as st
from config import PROVIDER_OPTIONS, MODEL_OPTIONS
from utils import format_time_display, clear_session_state
from cost_tracking import format_cost_display, should_show_cost
from performance import get_provider_stats, format_performance_stats_display


def render_sidebar():
    """
    Render the sidebar with enhanced provider/model selection and performance stats.
    
    Returns:
        tuple: (selected_provider, selected_model, selected_provider_name, selected_model_name, uploaded_file)
    """
    with st.sidebar:
        # Enhanced header
        st.markdown("### ⚙️ Configuration")
        
        # Provider selection with enhanced styling
        st.markdown("**🤖 AI Provider**")
        selected_provider_name = st.selectbox(
            "Choose your AI provider",
            options=list(PROVIDER_OPTIONS.keys()),
            index=0,
            help="Select the AI service provider for processing"
        )
        
        selected_provider = PROVIDER_OPTIONS[selected_provider_name]
        
        # Model selection based on provider
        model_options = MODEL_OPTIONS.get(selected_provider, {})
        
        st.markdown("**🧠 AI Model**")
        selected_model_name = st.selectbox(
            "Choose the AI model",
            options=list(model_options.keys()),
            index=0,
            help="Select the specific AI model for text extraction"
        )
        
        selected_model = model_options[selected_model_name]
        
        # Show model info
        if selected_provider_name == "Mistral" and "Small" in selected_model_name:
            st.info("💡 Optimized for fast, cost-effective processing")
        elif selected_provider_name == "Groq" and "Scout" in selected_model_name:
            st.info("🚀 High-performance processing with detailed extraction")
        
        st.divider()
        
        # Enhanced file upload section
        st.markdown("### 📁 Upload Document")
        uploaded_file = st.file_uploader(
            "Select an image or PDF file",
            type=['png', 'jpg', 'jpeg', 'pdf'],
            help="Supported formats: PNG, JPG, JPEG, PDF"
        )
        
        # File info if uploaded
        if uploaded_file:
            file_size = len(uploaded_file.getvalue()) / 1024  # KB
            st.success(f"✅ **{uploaded_file.name}** ({file_size:.1f} KB)")
        
        # Performance comparison section
        render_performance_stats()
        
        # Enhanced action buttons
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("♻️ Clear", width="stretch", help="Clear all results and start over"):
                clear_session_state()
                st.rerun()
                
        with col2:
            if st.button("📊 Stats", width="stretch", help="View detailed performance statistics"):
                st.session_state['show_detailed_stats'] = not st.session_state.get('show_detailed_stats', False)
                st.rerun()
            
        return selected_provider, selected_model, selected_provider_name, selected_model_name, uploaded_file


def render_performance_stats():
    """Render performance statistics in the sidebar."""
    provider_stats = get_provider_stats()
    if provider_stats:
        st.divider()
        st.subheader("📊 Performance")
        
        # Sort by average time (fastest first)
        sorted_stats = sorted(provider_stats.items(), key=lambda x: x[1]['avg_time'])
        
        # Show performance stats for each provider+model combination
        for key, stats in sorted_stats:
            display_data = format_performance_stats_display(stats)
            
            st.metric(
                label=display_data['provider'],
                value=display_data['time_display'],
                delta=display_data['delta_text'],
                help=display_data['help_text']
            )


def render_results_header(processing_time, cost_data, provider_used):
    """
    Render the results header with provider info, timing, and cost metrics.
    
    Args:
        processing_time: Dictionary with timing data
        cost_data: Dictionary with cost and token data  
        provider_used: String with provider and model info
    """
    # Enhanced header with better visual hierarchy
    st.markdown("### 📊 Processing Results")
    
    # Main metrics in a clean row - removed quality score column
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if provider_used:
            # More prominent provider display with dark text
            provider_parts = provider_used.split(" - ")
            if len(provider_parts) == 2:
                st.markdown(f"""
                <div style="padding: 10px; background-color: #f0f8ff; border-left: 4px solid #1f77b4; border-radius: 5px; margin-bottom: 10px; color: #333333;">
                    <strong style="color: #333333;">🤖 Provider:</strong> <span style="color: #333333;">{provider_parts[0]}</span><br>
                    <strong style="color: #333333;">🧠 Model:</strong> <span style="color: #333333;">{provider_parts[1]}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"✨ Processed with: {provider_used}")
    
    with col2:
        render_timing_metrics(processing_time)
    
    with col3:
        render_cost_metrics(cost_data)

def render_timing_metrics(processing_time):
    """Render timing metrics with better formatting."""
    if processing_time:
        total_time = processing_time.get('total', 0)
        api_time = processing_time.get('api_call', 0)
        
        time_str = format_time_display(total_time)
        api_str = format_time_display(api_time)
        
        # Color-coded timing based on performance
        if total_time < 2:
            delta_color = "normal"
        elif total_time < 5:
            delta_color = "normal"
        else:
            delta_color = "inverse"
        
        st.metric(
            label="⏱️ Processing Time",
            value=time_str,
            delta=f"API: {api_str}",
            delta_color=delta_color,
            help=(
                f"**Breakdown:**\n"
                f"• Total: {total_time:.3f}s\n"
                f"• API Call: {api_time:.3f}s\n"
                f"• Preprocessing: {processing_time.get('preprocessing', 0):.3f}s\n"
                f"• Postprocessing: {processing_time.get('postprocessing', 0):.3f}s"
            )
        )


def render_cost_metrics(cost_data):
    """
    Render cost and token usage metrics with enhanced formatting.
    
    Args:
        cost_data: Dictionary with cost and token data
    """
    # Debug output
    print(f"[DEBUG] UI - cost_data: {cost_data}")
    
    if should_show_cost(cost_data):
        display_data = format_cost_display(cost_data)
        total_cost = cost_data.get('total_cost', 0)
        
        # Color-code based on cost
        if total_cost < 0.001:
            delta_color = "normal"
        elif total_cost < 0.01:
            delta_color = "normal" 
        else:
            delta_color = "inverse"
        
        st.metric(
            label="💰 API Cost",
            value=display_data['cost_str'],
            delta=display_data['delta_str'],
            delta_color=delta_color,
            help=f"**Cost Breakdown:**\n{display_data['help_text']}"
        )
    elif cost_data:
        # Show token count even without cost data
        display_data = format_cost_display(cost_data)
        input_tokens = cost_data.get('input_tokens', 0)
        output_tokens = cost_data.get('output_tokens', 0)
        
        st.metric(
            label="🔢 Tokens",
            value=display_data['token_str'],
            delta=display_data['breakdown_str'],
            help=(
                f"**Token Usage:**\n"
                f"• Input: {input_tokens:,} tokens\n"
                f"• Output: {output_tokens:,} tokens\n"
                f"• Total: {input_tokens + output_tokens:,} tokens"
            )
        )

# Removed render_quality_score function as it was taking unnecessary horizontal space


def render_results_content(result_text, is_json, parsed_data, formatted_result):
    """
    Render compact results content for testing/benchmarking focus.
    
    Args:
        result_text: Raw result text from API
        is_json: Boolean indicating if result is JSON
        parsed_data: Parsed JSON data (if applicable)
        formatted_result: Formatted result text
    """
    # Compact format indicator
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Content statistics in compact format
        char_count = len(result_text)
        word_count = len(result_text.split())
        format_type = "JSON" if is_json else "Text"
        
        st.caption(f"📊 {format_type} • {word_count:,} words • {char_count:,} chars")
    
    with col2:
        if is_json:
            display_mode = st.selectbox(
                "View",
                ["JSON", "Text"],
                key="display_mode",
                label_visibility="collapsed"
            )
        else:
            display_mode = "Text"
    
    # Compact content display
    current_mode = st.session_state.get('display_mode', 'JSON')
    
    if is_json and current_mode == 'JSON':
        # Compact JSON display
        with st.expander("📋 Extracted Data", expanded=True):
            st.code(formatted_result, language='json', line_numbers=False)
    else:
        # Compact text display  
        with st.expander("📄 Extracted Text", expanded=True):
            st.text_area(
                "Content",
                value=result_text,
                height=200,
                label_visibility="collapsed"
            )

def render_json_content(formatted_result):
    """Render JSON content with better styling."""
    st.markdown("#### 🔧 Formatted JSON Output")
    
    # Create tabs for different JSON views
    tab1, tab2 = st.tabs(["📋 Pretty Print", "🌳 Tree View"])
    
    with tab1:
        st.code(formatted_result, language='json')
    
    with tab2:
        try:
            import json
            data = json.loads(formatted_result)
            st.json(data)
        except:
            st.code(formatted_result, language='json')

def render_data_explorer(parsed_data):
    """Render interactive data explorer for JSON content."""
    if not isinstance(parsed_data, dict):
        st.warning("Data explorer is only available for JSON objects")
        return
        
    st.markdown("#### 🗄️ Interactive Data Explorer")
    
    # Create expandable sections with better styling
    for key, value in parsed_data.items():
        with st.expander(f"📁 {key.title()} ({type(value).__name__})", expanded=False):
            if isinstance(value, dict):
                st.json(value)
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    st.dataframe(value)
                else:
                    st.json(value)
            else:
                st.markdown(f"**Value:** `{value}`")
                st.markdown(f"**Type:** {type(value).__name__}")

def render_text_content(formatted_result, result_text):
    """Render text content with better formatting."""
    st.markdown("#### 📄 Extracted Text Content")
    
    # Create tabs for different text views
    tab1, tab2 = st.tabs(["📖 Formatted", "📝 Raw Text"])
    
    with tab1:
        # Enhanced markdown rendering
        st.markdown(formatted_result)
    
    with tab2:
        # Raw text in a code block for copy-paste
        st.text_area(
            "Raw Text Output",
            value=result_text,
            height=400,
            help="Raw text output - easy to copy and paste"
        )


def render_download_buttons(result_text, is_json, formatted_result, parsed_data):
    """
    Render compact download buttons focused on essential formats.
    
    Args:
        result_text: Raw result text
        is_json: Boolean indicating if result is JSON
        formatted_result: Formatted result text
        parsed_data: Parsed JSON data
    """
    st.caption("💾 Export:")
    
    # Compact download options
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📄 TXT",
            data=result_text,
            file_name="data.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        if is_json and parsed_data:
            st.download_button(
                label="📋 JSON",
                data=formatted_result,
                file_name="data.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.button(
                label="📋 JSON",
                disabled=True,
                use_container_width=True
            )


def render_pdf_controls(uploaded_file):
    """
    Render compact PDF-specific controls for page selection.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        tuple: (success, image, selected_page) or (False, None, 0) if error
    """
    from utils import pdf_to_images
    
    success, image, total_pages = pdf_to_images(uploaded_file, 0)
    
    if success and total_pages > 0:
        # Compact PDF info
        st.caption(f"📄 PDF • {total_pages} page(s)")
        
        # Page selection for multi-page PDFs
        if total_pages > 1:
            selected_page = st.selectbox(
                "Page",
                options=list(range(1, total_pages + 1)),
                format_func=lambda x: f"Page {x}",
                key="pdf_page_selector"
            )
            
            # Convert to 0-based index and get the selected page
            success, image, _ = pdf_to_images(uploaded_file, selected_page - 1)
        else:
            selected_page = 1
        
        if success:
            return True, image, selected_page
    else:
        st.error("Unable to process PDF")
    
    return False, None, 0


def render_welcome_message():
    """Render a minimal welcome message focused on testing and benchmarking."""
    st.info("📄 Upload a document to start testing and benchmarking AI providers", icon="⚡")