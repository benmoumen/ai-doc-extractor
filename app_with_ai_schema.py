"""
Enhanced Streamlit OCR Application with AI Schema Generation
This is the main app.py with AI Schema Generation integrated
"""
import streamlit as st
import base64
import time
from PIL import Image
from litellm import completion

# Import our modular components
from config import setup_api_keys, get_model_param, PAGE_CONFIG
from utils import extract_and_parse_json, image_to_base64, pdf_to_images, format_schema_aware_response
from cost_tracking import calculate_cost_and_tokens
from performance import update_performance_history, create_timing_data
from schema_utils import create_schema_prompt
from ui_components import (
    render_sidebar, render_results_header, render_results_content,
    render_download_buttons, render_pdf_controls, render_welcome_message
)

# Import dynamic structured output for JSON Mode
from dynamic_structured_output import (
    create_response_format_for_document, validate_extraction_with_schema,
    generate_simplified_prompt, get_schema_from_storage
)

# Import schema compatibility functions
from schema_compatibility import get_extraction_configuration, handle_extraction_error, validate_schema_for_extraction

# Import AI Schema Generation
try:
    from ai_schema_ui_integration import render_ai_schema_generation_tab
    AI_SCHEMA_AVAILABLE = True
except ImportError:
    AI_SCHEMA_AVAILABLE = False

# Set up page configuration
st.set_page_config(**PAGE_CONFIG)

# Set up API keys
setup_api_keys()

# Page Navigation
st.markdown("## 🤖 AI Document Data Extractor")

def render_document_extraction():
    # Original extraction functionality
    st.subheader("DATA EXTRACTION", divider='orange')

    # Render sidebar and get selections
    selected_provider, selected_model, selected_provider_name, selected_model_name, uploaded_file, selected_doc_type, selected_doc_type_name = render_sidebar()

    if uploaded_file is not None:
        # Create two-column layout for image and results
        col_img, col_results = st.columns([1, 2])

        with col_img:
            file_type = uploaded_file.type

            if file_type == "application/pdf":
                # Handle PDF files
                success, image, selected_page = render_pdf_controls(uploaded_file)
                if success:
                    # Show compact PDF preview
                    st.image(image, caption=f"PDF Page {selected_page}", width=300)
                    st.session_state['current_image'] = image
                else:
                    image = None
            else:
                # Handle regular image files with compact display
                image = Image.open(uploaded_file)
                st.image(image, caption="Preview", width=300)
                st.session_state['current_image'] = image

            # Move extract button to image column for better UX
            if image is not None and st.button("Extract Data 💫", type="primary", width="stretch"):
                extract_data = True
            else:
                extract_data = False

        with col_results:
            # Display results in the right column
            if 'ocr_result' in st.session_state:
                result_text = st.session_state['ocr_result']
                processing_time = st.session_state.get('processing_time', {})
                cost_data = st.session_state.get('cost_data', None)
                provider_used = st.session_state.get('provider_used', None)
                is_json = st.session_state.get('is_json_result', False)
                parsed_data = st.session_state.get('parsed_data', None)
                formatted_result = st.session_state.get('formatted_result', result_text)

                render_results_header(processing_time, cost_data, provider_used)
                render_results_content(result_text, is_json, parsed_data, formatted_result)
                render_download_buttons(result_text, is_json, formatted_result, parsed_data)
            else:
                st.info("👆 Upload a document and click **Extract Data** to see results here.")

        # Extract data if button was clicked
        if extract_data and image is not None:
            try:
                with st.spinner('🔮 Extracting data with AI...'):
                    start_time = time.time()

                    # Get extraction configuration
                    extraction_config = get_extraction_configuration(selected_doc_type)

                    # Convert image to base64
                    image_base64 = image_to_base64(image)

                    # Create the prompt
                    if selected_doc_type != "generic":
                        # Use schema-aware prompt
                        schema = extraction_config.get("schema", {})
                        validate_schema_for_extraction(selected_doc_type)
                        prompt = create_schema_prompt(selected_doc_type, selected_doc_type_name)
                    else:
                        # Use generic prompt
                        prompt = f"Extract all text, data, and structure from this {selected_doc_type_name} image. Return the data as structured JSON."

                    # Get model parameters
                    model_param = get_model_param(selected_provider, selected_model)

                    # Make API call with timing
                    api_start_time = time.time()

                    # Prepare completion kwargs
                    completion_kwargs = {
                        "model": model_param,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                            ]
                        }],
                        "temperature": 0.1
                    }

                    # Add response_format for structured output (JSON Mode always enabled)
                    if selected_doc_type and selected_doc_type != "generic":
                        # Try to create response format from user-defined schema
                        # Pass provider name for provider-specific formatting
                        response_format = create_response_format_for_document(selected_doc_type, selected_provider)

                        if response_format:
                            completion_kwargs["response_format"] = response_format

                            # Get schema for simplified prompt
                            schema = get_schema_from_storage(selected_doc_type)
                            if schema:
                                # Use simplified prompt for structured output (provider-specific)
                                completion_kwargs["messages"][0]["content"][0]["text"] = generate_simplified_prompt(schema, selected_provider)
                        else:
                            # Fallback to regular extraction if schema not found
                            st.warning("Schema not found for JSON Mode, using regular extraction")

                    response = completion(**completion_kwargs)
                    api_end_time = time.time()

                    end_time = time.time()
                    processing_time = end_time - start_time

                    # Process response
                    raw_content = response.choices[0].message.content

                    # Parse and format JSON if present
                    is_json, parsed_data, formatted_text = extract_and_parse_json(raw_content)

                    # Validate against schema if using structured output
                    validation_passed = True
                    validation_errors = []

                    if selected_doc_type and selected_doc_type != "generic":
                        schema = get_schema_from_storage(selected_doc_type)
                        if schema and is_json and parsed_data:
                            # Validate extraction result against dynamic schema
                            validation_passed, validated_model, validation_errors = validate_extraction_with_schema(
                                schema, parsed_data
                            )

                            if not validation_passed:
                                st.warning(f"⚠️ Schema validation issues: {', '.join(validation_errors[:3])}")

                    if selected_doc_type != "generic":
                        # For schema-aware responses, use enhanced formatting
                        if is_json and parsed_data:
                            result_text = format_schema_aware_response(parsed_data)
                        else:
                            result_text = formatted_text
                    else:
                        # Use generic formatting
                        result_text = formatted_text

                    # Track costs and performance
                    cost_data = calculate_cost_and_tokens(response, model_param)
                    timing_data = create_timing_data(start_time, api_start_time, api_end_time, end_time)
                    update_performance_history(selected_provider_name, selected_model_name, timing_data)

                    # Store results in session state
                    st.session_state['ocr_result'] = result_text
                    st.session_state['is_json_result'] = is_json
                    st.session_state['parsed_data'] = parsed_data
                    st.session_state['formatted_result'] = formatted_text
                    st.session_state['processing_time'] = timing_data
                    st.session_state['cost_data'] = cost_data
                    st.session_state['provider_used'] = f"{selected_provider_name} - {selected_model_name}"

                    # Force refresh to show results
                    st.rerun()

            except Exception as e:
                # Try schema compatibility error handling
                should_retry, fallback_config = handle_extraction_error(
                    selected_doc_type, e, fallback_to_generic=True
                )

                if should_retry and fallback_config:
                    st.warning(f"⚠️ Schema extraction failed, falling back to generic extraction")
                    # Could implement fallback logic here
                else:
                    st.error(f"❌ Extraction failed: {str(e)}")
                    st.error(f"Provider: {selected_provider_name}, Model: {selected_model_name}")

    else:
        # Show welcome message when no file is uploaded
        render_welcome_message()


# Navigation tabs - Add AI Schema Generation if available
if AI_SCHEMA_AVAILABLE:
    tab1, tab2 = st.tabs([
        "📄 Document Extraction",
        "🤖 AI Schema Generation"
    ])

    # Document Extraction Tab
    with tab1:
        render_document_extraction()

    # AI Schema Generation Tab
    with tab2:
        render_ai_schema_generation_tab()
else:
    # Single page mode - just show document extraction
    render_document_extraction()
