"""
Streamlit OCR Application with LiteLLM integration.
Refactored modular version with specialized files for easy maintenance.
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

# Import schema management
from schema_management.schema_builder import render_schema_management_page
from schema_management.state_manager import initialize_schema_builder_state
from schema_compatibility import get_extraction_configuration, handle_extraction_error, validate_schema_for_extraction

# Set up page configuration
st.set_page_config(**PAGE_CONFIG)

# Set up API keys
setup_api_keys()

# Initialize schema builder state
initialize_schema_builder_state()

# Page Navigation
st.markdown("## 🤖 AI Document Data Extractor")

# Navigation tabs
tab1, tab2 = st.tabs(["📄 Document Extraction", "🔧 Schema Management"])

with tab1:
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
                is_json = st.session_state.get('is_json_result', False)
                parsed_data = st.session_state.get('parsed_data', None)
                formatted_result = st.session_state.get('formatted_result', result_text)
                processing_time = st.session_state.get('processing_time', {})
                cost_data = st.session_state.get('cost_data', None)
                provider_used = st.session_state.get('provider_used', None)
                
                # Render results header with metrics
                render_results_header(processing_time, cost_data, provider_used)
                
                # Render main results content
                render_results_content(result_text, is_json, parsed_data, formatted_result)
                
                # Render download buttons
                render_download_buttons(result_text, is_json, formatted_result, parsed_data)
            else:
                st.markdown("### 📊 Results will appear here")
                st.info("Click 'Extract Data' to start processing", icon="⚡")
    
        # Handle data extraction
        if 'extract_data' in locals() and extract_data:
            with st.spinner("Analyzing and Processing..."):
                try:
                    # Start timing the entire process
                    start_time = time.time()
                    
                    # Get the current image (either from file or PDF conversion)
                    current_image = st.session_state.get('current_image', image)
                    
                    # Convert image to base64
                    img_buffer, image_bytes = image_to_base64(current_image)
                    base64_image = base64.b64encode(image_bytes).decode('utf-8')
                    
                    # Get properly formatted model parameter
                    model_param = get_model_param(selected_provider, selected_model)
                    
                    # Get extraction configuration with compatibility layer
                    extraction_config = get_extraction_configuration(selected_doc_type)
                    
                    # Validate schema compatibility if using schema
                    if selected_doc_type:
                        is_valid, issues = validate_schema_for_extraction(selected_doc_type)
                        if not is_valid:
                            st.warning(f"⚠️ Schema compatibility issues detected: {'; '.join(issues[:3])}")
                            if len(issues) > 3:
                                st.warning(f"... and {len(issues) - 3} more issues")
                    
                    # Generate prompt and set parameters
                    if extraction_config['use_schema_prompt']:
                        prompt_text = create_schema_prompt(selected_doc_type)
                        if not prompt_text:
                            # Fallback to generic extraction
                            prompt_text = "Analyze the text in the provided image. Extract all readable content and present it in JSON format"
                            extraction_config['use_schema_prompt'] = False
                    else:
                        prompt_text = "Analyze the text in the provided image. Extract all readable content and present it in JSON format"
                    
                    temperature = extraction_config['temperature']
                    max_tokens = extraction_config['max_tokens']
                    
                    # Time the API call specifically
                    api_start_time = time.time()
                    
                    # Vision request with dynamic prompt
                    response = completion(
                        model=model_param,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text", 
                                        "text": prompt_text
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}",
                                        },
                                    },
                                ],
                            }
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    
                    api_end_time = time.time()
                    response_text = response.choices[0].message.content
                    
                    # Calculate cost and extract token usage
                    cost_data = calculate_cost_and_tokens(response, model_param)
                    token_usage_data = cost_data
                    
                    # Parse and format JSON if present
                    is_json, parsed_data, formatted_text = extract_and_parse_json(response_text)
                    
                    # For schema-aware responses, use enhanced formatting
                    if selected_doc_type and is_json and parsed_data:
                        formatted_text = format_schema_aware_response(parsed_data)
                    
                    # Calculate total processing time
                    end_time = time.time()
                    processing_time = create_timing_data(start_time, api_start_time, api_end_time, end_time)
                    
                    # Store results in session state
                    st.session_state['ocr_result'] = response_text
                    st.session_state['is_json_result'] = is_json
                    st.session_state['parsed_data'] = parsed_data
                    st.session_state['formatted_result'] = formatted_text
                    st.session_state['provider_used'] = f"{selected_provider_name} - {selected_model_name}"
                    st.session_state['processing_time'] = processing_time
                    st.session_state['token_usage'] = token_usage_data
                    st.session_state['cost_data'] = cost_data
                    st.session_state['selected_document_type'] = selected_doc_type
                    st.session_state['selected_document_type_name'] = selected_doc_type_name
                    st.session_state['extraction_config'] = extraction_config
                    st.session_state['schema_compatibility_used'] = True
                    
                    # Update performance history for comparison
                    update_performance_history(
                        selected_provider_name, 
                        selected_model_name, 
                        processing_time, 
                        token_usage_data
                    )
                    
                except Exception as e:
                    # Try schema compatibility error handling
                    should_retry, fallback_config = handle_extraction_error(
                        selected_doc_type, e, fallback_to_generic=True
                    )
                    
                    if should_retry and fallback_config:
                        st.warning(f"⚠️ Schema extraction failed, falling back to generic extraction")
                        
                        try:
                            # Retry with fallback configuration
                            fallback_prompt = "Analyze the text in the provided image. Extract all readable content and present it in JSON format"
                            
                            api_start_time = time.time()
                            response = completion(
                                model=model_param,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": fallback_prompt},
                                            {
                                                "type": "image_url",
                                                "image_url": {
                                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                                },
                                            },
                                        ],
                                    }
                                ],
                                temperature=fallback_config['temperature'],
                                max_tokens=fallback_config['max_tokens'],
                            )
                            
                            api_end_time = time.time()
                            response_text = response.choices[0].message.content
                            
                            # Process fallback results
                            cost_data = calculate_cost_and_tokens(response, model_param)
                            is_json, parsed_data, formatted_text = extract_and_parse_json(response_text)
                            
                            # Calculate timing
                            end_time = time.time()
                            processing_time = create_timing_data(start_time, api_start_time, api_end_time, end_time)
                            
                            # Store fallback results
                            st.session_state['ocr_result'] = response_text
                            st.session_state['is_json_result'] = is_json
                            st.session_state['parsed_data'] = parsed_data
                            st.session_state['formatted_result'] = formatted_text
                            st.session_state['provider_used'] = f"{selected_provider_name} - {selected_model_name} (Fallback)"
                            st.session_state['processing_time'] = processing_time
                            st.session_state['cost_data'] = cost_data
                            st.session_state['selected_document_type'] = None  # No schema used
                            st.session_state['selected_document_type_name'] = "Generic Extraction (Fallback)"
                            st.session_state['extraction_config'] = fallback_config
                            st.session_state['schema_compatibility_used'] = True
                            st.session_state['fallback_used'] = True
                            st.session_state['fallback_reason'] = fallback_config.get('fallback_reason', str(e))
                            
                            st.success("✅ Fallback extraction completed successfully")
                            
                        except Exception as fallback_error:
                            st.error(f"❌ Both schema and fallback extraction failed:")
                            st.error(f"Original error: {str(e)}")
                            st.error(f"Fallback error: {str(fallback_error)}")
                    else:
                        st.error(f"❌ Error processing image: {str(e)}")
                    
                # Force rerun to update results in right column
                st.rerun()

    else:
        render_welcome_message()

with tab2:
    # Schema Management functionality
    render_schema_management_page()