"""
AI Schema Generation UI Integration
Adds AI-powered schema generation to the main Streamlit app
"""

import streamlit as st
from typing import Optional, Dict, Any
import tempfile
import base64
from pathlib import Path
import uuid
from datetime import datetime

def render_ai_schema_generation_tab():
    """Render the AI Schema Generation tab in the main app"""
    st.subheader("🤖 AI SCHEMA GENERATION", divider='blue')

    # Check if AI schema generation utilities are available
    try:
        from ai_schema_generation import (
            get_data_validator, get_schema_validator, get_confidence_calculator,
            get_performance_monitor, get_logger
        )
        ai_available = True
    except ImportError:
        ai_available = False

    if not ai_available:
        st.error("🚫 AI Schema Generation module is not fully available. Please check the installation.")
        st.info("💡 The utility components are implemented, but the core AI analysis components need to be added.")
        return

    # Initialize components
    if 'ai_schema_validator' not in st.session_state:
        st.session_state.ai_schema_validator = get_data_validator()
        st.session_state.ai_schema_checker = get_schema_validator()
        st.session_state.ai_confidence_calc = get_confidence_calculator()
        st.session_state.ai_perf_monitor = get_performance_monitor()
        st.session_state.ai_logger = get_logger()

    # Create tabs for different AI schema functionalities
    ai_tab1, ai_tab2, ai_tab3, ai_tab4 = st.tabs([
        "📤 Document Analysis",
        "📋 Schema Preview",
        "🔍 Data Validation",
        "📊 Performance Monitor"
    ])

    with ai_tab1:
        render_document_analysis_tab()

    with ai_tab2:
        render_schema_preview_tab()

    with ai_tab3:
        render_data_validation_tab()

    with ai_tab4:
        render_performance_monitor_tab()


def render_document_analysis_tab():
    """Document analysis and AI schema generation"""
    st.write("### 📄 Upload Document for AI Analysis")

    # Check if real AI analyzer is available
    try:
        from ai_schema_generation.core import get_ai_analyzer
        ai_analyzer = get_ai_analyzer()
        real_ai_available = True
        available_models = ai_analyzer.get_available_models()
    except ImportError:
        real_ai_available = False
        available_models = ["Llama Scout 17B (Groq)", "Mistral Small 3.2"]

    # Document upload
    uploaded_file = st.file_uploader(
        "Choose a document for AI schema generation",
        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
        key="ai_schema_upload"
    )

    if uploaded_file is not None:
        # Display file info and preview side by side
        col1, col2 = st.columns([1, 1])

        with col1:
            st.write("**📋 File Information:**")
            st.write(f"• **Name:** {uploaded_file.name}")
            st.write(f"• **Type:** {uploaded_file.type}")
            st.write(f"• **Size:** {uploaded_file.size / 1024:.1f} KB")

        with col2:
            # Show preview
            if uploaded_file.type.startswith('image/'):
                from PIL import Image
                image = Image.open(uploaded_file)
                st.image(image, caption="📄 Document Preview", width=250)
            elif uploaded_file.type == 'application/pdf':
                st.write("📄 **PDF Document**")
                st.info("💡 PDF analysis will process the first page")

        # AI Model Configuration
        st.write("### 🤖 AI Configuration")

        if real_ai_available:
            st.success("✅ **Real AI Analysis Available** - Using LiteLLM with Groq/Mistral")
        else:
            st.warning("⚠️ **Simulation Mode** - Real AI analysis not available")

        ai_model = st.selectbox(
            "Select AI Model",
            available_models,
            help="Select the AI model for document analysis"
        )

        st.info("🔍 The AI will automatically detect the document type and extract relevant fields")

        # Show the prompt that will be used
        st.write("### 📝 AI Prompt Preview")
        if real_ai_available:
            # Use real AI analyzer prompt generation - always auto-detect
            prompt = ai_analyzer._generate_schema_prompt("Auto-detect", uploaded_file.name)
        else:
            # Fallback to simulation prompt
            prompt = generate_ai_prompt("Auto-detect", uploaded_file.name)

        with st.expander("👁️ View AI Prompt", expanded=False):
            st.text_area("AI Prompt", prompt, height=200, disabled=True)
            st.caption(f"🤖 Model: **{ai_model}** | 🔍 Mode: **Auto-detect Document Type**")
            if real_ai_available:
                st.caption("🔥 **REAL AI ANALYSIS** - This will call the actual LiteLLM API")

        # Simple generate button
        st.write("### 🚀 Generate Schema")

        if st.button("🤖 **Analyze Document & Generate Schema**", type="primary", use_container_width=True):
            if real_ai_available:
                # Use real AI analysis
                with st.spinner(f"🔥 Calling {ai_model} via LiteLLM..."):
                    # Show progress steps
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    status_text.text("📄 Converting document to base64...")
                    progress_bar.progress(20)

                    status_text.text("🔗 Calling LiteLLM API...")
                    progress_bar.progress(40)

                    status_text.text(f"🤖 Processing with {ai_model}...")
                    progress_bar.progress(70)

                    # Call real AI analyzer - always use auto-detect
                    result = ai_analyzer.generate_schema_from_document(
                        uploaded_file, "Auto-detect", ai_model
                    )

                    status_text.text("✅ AI Analysis Complete!")
                    progress_bar.progress(100)

                    # Store results
                    st.session_state.ai_analysis_result = result
                    st.session_state.ai_model_used = ai_model
                    st.session_state.ai_prompt_used = prompt

                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()

                    if result.get("success"):
                        st.success(f"🔥 **Real AI Analysis Complete!** Schema generated using **{ai_model}** via LiteLLM")
                    else:
                        st.error(f"❌ AI Analysis Failed: {result.get('error', 'Unknown error')}")
                        if result.get("is_fallback"):
                            st.info("💡 Showing fallback schema for demonstration")

            else:
                # Fallback to simulation
                with st.spinner(f"🧠 Simulating analysis with {ai_model}..."):
                    # Show progress steps
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    status_text.text("📄 Processing document...")
                    progress_bar.progress(25)

                    status_text.text("🔍 Analyzing structure...")
                    progress_bar.progress(50)

                    status_text.text("🤖 Generating schema...")
                    progress_bar.progress(75)

                    # Real AI analysis - always use auto-detect
                    if real_ai_available:
                        result = ai_analyzer.generate_schema_from_document(uploaded_file, "Auto-detect", ai_model)
                    else:
                        st.error("❌ AI analyzer not available - check installation")
                        return

                    status_text.text("✅ Complete!")
                    progress_bar.progress(100)

                    # Store results
                    st.session_state.ai_analysis_result = result
                    st.session_state.ai_model_used = ai_model
                    st.session_state.ai_prompt_used = prompt

                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()

                    # Show success message
                    st.success(f"✅ Schema generated successfully using **{ai_model}**!")

        # Show results if available
        if 'ai_analysis_result' in st.session_state:
            show_ai_analysis_results(st.session_state.ai_analysis_result)


def show_ai_analysis_results(result: Dict[str, Any]):
    """Display AI analysis results"""

    # Results summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Fields Detected", result.get('fields_detected', 0))

    with col2:
        confidence = result.get('confidence_score', 0)
        st.metric("Confidence Score", f"{confidence:.1%}")

    with col3:
        time_taken = result.get('analysis_time', 0)
        st.metric("Analysis Time", f"{time_taken:.2f}s")

    with col4:
        st.metric("Document Type", result.get('document_type', 'Unknown'))

    # Show AI details in expander
    with st.expander("🤖 AI Analysis Details", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**AI Model Used:**")
            st.code(result.get('ai_model', 'Unknown'))

            if result.get('provider'):
                st.write("**Provider:**")
                st.code(result.get('provider', 'Unknown'))

        with col2:
            st.write("**Processing Details:**")
            st.write(f"- Document Type: {result.get('document_type', 'Unknown')}")
            st.write(f"- Analysis Time: {result.get('analysis_time', 0):.2f}s")
            st.write(f"- Fields Detected: {result.get('fields_detected', 0)}")

        if result.get('prompt_used'):
            st.write("**AI Prompt Used:**")
            st.text_area("Prompt", result.get('prompt_used', ''), height=150, disabled=True)

    # Error handling
    if result.get('success') == False:
        st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
        st.info("💡 The system will use a fallback schema appropriate for your document type.")

    # Schema preview
    if result.get('schema'):
        st.write("### 📋 Generated Schema")

        schema = result['schema']
        fields = schema.get('fields', {})

        if fields:
            # Create a dataframe for better visualization
            import pandas as pd

            field_data = []
            for field_name, field_config in fields.items():
                field_data.append({
                    'Field Name': field_name,
                    'Type': field_config.get('type', 'string'),
                    'Required': '✅' if field_config.get('required', False) else '❌',
                    'Display Name': field_config.get('display_name', field_name),
                    'Confidence': f"{field_config.get('confidence', 0.5):.1%}" if 'confidence' in field_config else 'N/A'
                })

            df = pd.DataFrame(field_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("No fields detected in the schema.")

    # Raw response for debugging (optional)
    if result.get('raw_response'):
        with st.expander("🔍 Raw AI Response", expanded=False):
            st.code(result.get('raw_response', ''), language='json')


def render_schema_preview_tab():
    """Preview generated schemas"""
    st.write("### 📋 Generated Schema Preview")

    if 'ai_analysis_result' not in st.session_state:
        st.info("📋 No schema generated yet. Please use the Document Analysis tab to generate a schema first.")
        return

    result = st.session_state.ai_analysis_result
    schema = result.get('schema', {})

    if not schema:
        st.warning("⚠️ No schema data available.")
        return

    # Schema summary with AI info
    st.write("#### 🤖 Generated Schema Summary")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"**📄 Schema:** {schema.get('name', 'Unnamed Schema')}")
        st.write(f"**📝 Description:** {schema.get('description', 'No description')}")

    with col2:
        ai_model = st.session_state.get('ai_model_used', result.get('ai_model', 'Unknown'))
        st.write(f"**🤖 Generated by:** {ai_model}")
        st.write(f"**📊 Confidence:** {result.get('confidence_score', 0):.1%}")

    # Schema metrics
    st.write("#### 📊 Schema Metrics")
    col1, col2, col3, col4 = st.columns(4)

    fields = schema.get('fields', {})
    with col1:
        st.metric("Total Fields", len(fields))
    with col2:
        required_fields = sum(1 for f in fields.values() if f.get('required', False))
        st.metric("Required Fields", required_fields)
    with col3:
        confidence = result.get('confidence_score', 0)
        st.metric("Overall Confidence", f"{confidence:.1%}")
    with col4:
        validated_fields = sum(1 for f in fields.values() if f.get('validation_rules'))
        st.metric("Validated Fields", validated_fields)

    # Field details
    st.write("#### 🔍 Field Details")

    if fields:
        for field_name, field_config in fields.items():
            with st.expander(f"🏷️ {field_name} ({field_config.get('type', 'unknown')})"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Configuration:**")
                    st.write(f"• Type: {field_config.get('type', 'unknown')}")
                    st.write(f"• Required: {field_config.get('required', False)}")
                    st.write(f"• Display: {field_config.get('display_name', field_name)}")

                    if field_config.get('description'):
                        st.write(f"• Description: {field_config['description']}")

                with col2:
                    st.write("**AI Analysis:**")
                    ai_meta = field_config.get('ai_metadata', {})
                    if ai_meta:
                        st.write(f"• Confidence: {ai_meta.get('confidence', 0):.1%}")
                        st.write(f"• Source: {ai_meta.get('source', 'unknown')}")

                    validation_rules = field_config.get('validation_rules', [])
                    if validation_rules:
                        st.write("• Validation Rules:")
                        for rule in validation_rules[:3]:  # Show first 3 rules
                            st.write(f"  - {rule.get('type', 'unknown')}")

    # Export options
    st.write("#### 📤 Export Schema")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Export as JSON"):
            export_schema_json(schema)

    with col2:
        if st.button("📊 Export as CSV"):
            export_schema_csv(schema)

    with col3:
        if st.button("🔧 Add to Schema Manager"):
            export_to_schema_manager(schema)


def render_data_validation_tab():
    """Data validation utilities"""
    st.write("### 🔍 Data Validation Testing")

    if 'ai_analysis_result' not in st.session_state:
        st.info("📋 No schema available for validation. Please generate a schema first.")
        return

    schema = st.session_state.ai_analysis_result.get('schema', {})
    validator = st.session_state.ai_schema_validator

    st.write("#### 📝 Test Data Validation")
    st.write("Enter sample data to test against the generated schema:")

    # Create input fields for each schema field
    test_data = {}
    fields = schema.get('fields', {})

    if fields:
        for field_name, field_config in fields.items():
            field_type = field_config.get('type', 'string')
            required = field_config.get('required', False)
            display_name = field_config.get('display_name', field_name)

            label = f"{display_name} ({field_type})"
            if required:
                label += " *"

            # Create appropriate input widget based on field type
            if field_type == 'string':
                test_data[field_name] = st.text_input(label, key=f"test_{field_name}")
            elif field_type == 'number':
                test_data[field_name] = st.number_input(label, key=f"test_{field_name}")
            elif field_type == 'email':
                test_data[field_name] = st.text_input(label, placeholder="user@example.com", key=f"test_{field_name}")
            elif field_type == 'date':
                test_data[field_name] = st.date_input(label, key=f"test_{field_name}")
            elif field_type == 'boolean':
                test_data[field_name] = st.checkbox(label, key=f"test_{field_name}")
            else:
                test_data[field_name] = st.text_input(label, key=f"test_{field_name}")

        if st.button("🔍 Validate Data", type="primary"):
            with st.spinner("Validating data..."):
                # Validate the data
                validation_results = validator.validate_schema_data(test_data, schema)
                summary = validator.get_validation_summary(validation_results)

                # Show results
                st.write("#### ✅ Validation Results")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Valid Fields", summary['valid_fields'])
                with col2:
                    st.metric("Invalid Fields", summary['invalid_fields'])
                with col3:
                    st.metric("Validation Rate", f"{summary['validation_rate']:.1%}")

                if summary['is_valid']:
                    st.success("✅ All data validates successfully!")
                else:
                    st.error("❌ Validation errors found:")
                    for error in summary['errors']:
                        st.write(f"• {error}")

                if summary['warnings']:
                    st.warning("⚠️ Warnings:")
                    for warning in summary['warnings']:
                        st.write(f"• {warning}")


def render_performance_monitor_tab():
    """Performance monitoring dashboard"""
    st.write("### 📊 Performance Monitoring")

    monitor = st.session_state.ai_perf_monitor

    # Performance summary
    st.write("#### 📈 Recent Performance")
    summary = monitor.get_performance_summary()

    if summary.get('metrics'):
        # Show performance metrics
        metrics = summary['metrics']

        # Create columns for key metrics
        if metrics:
            col1, col2, col3 = st.columns(3)

            # Get some sample metrics to display
            metric_names = list(metrics.keys())[:6]  # Show up to 6 metrics

            for i, metric_name in enumerate(metric_names):
                metric_data = metrics[metric_name]
                col_idx = i % 3

                if col_idx == 0:
                    with col1:
                        st.metric(
                            metric_name.replace('_', ' ').title(),
                            f"{metric_data.get('average', 0):.2f} {metric_data.get('unit', '')}"
                        )
                elif col_idx == 1:
                    with col2:
                        st.metric(
                            metric_name.replace('_', ' ').title(),
                            f"{metric_data.get('average', 0):.2f} {metric_data.get('unit', '')}"
                        )
                else:
                    with col3:
                        st.metric(
                            metric_name.replace('_', ' ').title(),
                            f"{metric_data.get('average', 0):.2f} {metric_data.get('unit', '')}"
                        )
    else:
        st.info("📊 No performance data available yet. Run some AI schema generation operations to see metrics.")

    # Performance issues
    issues = summary.get('performance_issues', [])
    if issues:
        st.write("#### ⚠️ Performance Issues")
        for issue in issues:
            st.warning(f"• {issue}")
    else:
        st.success("✅ No performance issues detected")

    # System monitoring controls
    st.write("#### ⚙️ Monitoring Controls")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Refresh Performance Data"):
            st.rerun()

    with col2:
        if st.button("🗑️ Clear Performance History"):
            monitor.cleanup_old_metrics(days=0)
            st.success("Performance history cleared!")


def generate_ai_prompt(document_type: str, filename: str) -> str:
    """Generate AI prompt based on document type"""

    if document_type == "Invoice":
        return f"""Analyze this {document_type.lower()} document ({filename}) and extract a structured schema.

Focus on identifying these common invoice fields:
- Invoice number/ID
- Date (invoice date, due date)
- Company information (vendor, customer)
- Financial data (subtotal, tax, total amount)
- Line items and descriptions
- Payment terms

Return a JSON schema with field names, types (string, number, date, email),
whether each field is required, and validation rules where appropriate.

Provide high confidence scores for clearly visible fields and lower scores for inferred or partially visible fields."""

    elif document_type == "Receipt":
        return f"""Analyze this {document_type.lower()} document ({filename}) and extract a structured schema.

Focus on identifying these common receipt fields:
- Merchant name and location
- Purchase date and time
- Items purchased with prices
- Payment method
- Total amount, tax, subtotal
- Receipt number

Return a JSON schema with appropriate field types and confidence scores."""

    elif document_type == "Contract":
        return f"""Analyze this {document_type.lower()} document ({filename}) and extract a structured schema.

Focus on identifying these common contract fields:
- Contract parties (names, addresses)
- Contract dates (execution, effective, expiration)
- Key terms and conditions
- Financial obligations
- Signatures and witness information

Return a JSON schema with appropriate field types and confidence scores."""

    elif document_type == "Bank Statement":
        return f"""Analyze this {document_type.lower()} document ({filename}) and extract a structured schema.

Focus on identifying these common bank statement fields:
- Account holder information
- Account number and type
- Statement period
- Opening and closing balance
- Transaction details (date, description, amount)
- Bank information

Return a JSON schema with appropriate field types and confidence scores."""

    else:  # Auto-detect or other types
        return f"""Analyze this document ({filename}) and automatically detect its type and structure.

Extract a structured schema by identifying:
- Key data fields and their types (string, number, date, email, phone, etc.)
- Which fields appear to be required vs optional
- Validation patterns for structured data (emails, phone numbers, dates)
- Relationships between fields

Return a JSON schema with field definitions, types, requirements, and confidence scores based on how clearly each field is visible and identifiable in the document."""




def export_schema_csv(schema: Dict[str, Any]):
    """Export schema as CSV"""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Field Name', 'Type', 'Required', 'Display Name', 'Description'])

    # Write fields
    fields = schema.get('fields', {})
    for field_name, field_config in fields.items():
        writer.writerow([
            field_name,
            field_config.get('type', ''),
            field_config.get('required', False),
            field_config.get('display_name', ''),
            field_config.get('description', '')
        ])

    st.download_button(
        label="📊 Download CSV",
        data=output.getvalue(),
        file_name=f"ai_generated_schema_{schema.get('id', 'unknown')}.csv",
        mime="text/csv"
    )


def export_to_schema_manager(schema: Dict[str, Any]):
    """Export schema to the existing schema manager"""
    try:
        # Import the schema management components
        from schema_management.services.schema_service import SchemaService
        from schema_management.models.schema import SchemaStatus

        # Initialize the service
        schema_service = SchemaService()

        # Transform fields to match Schema Manager format
        transformed_fields = {}
        for field_name, field_config in schema.get("fields", {}).items():
            # Map AI field types to Schema Manager field types
            field_type_mapping = {
                "string": "text",
                "number": "number",
                "date": "date",
                "email": "email",
                "phone": "phone",
                "boolean": "boolean",
                "currency": "currency",
                "url": "url"
            }

            ai_field_type = field_config.get("type", "string")
            schema_field_type = field_type_mapping.get(ai_field_type, "text")

            transformed_fields[field_name] = {
                "name": field_name,
                "display_name": field_config.get("display_name", field_name),
                "field_type": schema_field_type,
                "type": schema_field_type,  # Include both for compatibility
                "required": field_config.get("required", False),
                "description": field_config.get("description", ""),
                "validation_rules": field_config.get("validation_rules", []),
                "examples": field_config.get("examples", []),
                "confidence": field_config.get("confidence", 0.7),
                "ai_metadata": {
                    "confidence": field_config.get("confidence", 0.7),
                    "source": "AI Generated",
                    "examples": field_config.get("examples", [])
                }
            }

        # Prepare the schema data for the Schema Manager
        schema_data = {
            "id": schema.get("id", f"ai_{uuid.uuid4().hex[:8]}"),
            "name": schema.get("name", "AI Generated Schema"),
            "description": schema.get("description", "Schema generated by AI analysis"),
            "category": "AI Generated",
            "version": "v1.0.0",
            "is_active": True,
            "status": SchemaStatus.VALIDATED.value,
            "fields": transformed_fields,
            "validation_rules": [],
            "metadata": {
                "source": "AI Schema Generation",
                "detected_type": schema.get("detected_type", "Unknown"),
                "confidence_score": schema.get("confidence_score", 0),
                "ai_model": st.session_state.get("ai_model_used", "Unknown"),
                "generated_date": datetime.now().isoformat()
            }
        }

        # Create the schema in the Schema Manager
        success, message, created_schema = schema_service.create_schema(
            schema_data,
            user_id="ai_generator"
        )

        if success:
            st.success(f"✅ Schema successfully added to Schema Manager!")
            st.info(f"📋 Schema ID: {created_schema.id}")
            st.write(f"You can now find '{created_schema.name}' in the Schema Management tab.")

            # Add a button to go to Schema Management tab
            if st.button("🔧 Go to Schema Management", type="secondary"):
                st.session_state.active_tab = "schema_management"
                st.rerun()
        else:
            st.error(f"❌ Failed to add schema: {message}")

    except ImportError as e:
        st.error("❌ Schema Management module not found. Please ensure it's properly installed.")
        st.write(f"Error: {e}")
    except Exception as e:
        st.error(f"❌ Error exporting to Schema Manager: {str(e)}")
        import traceback
        st.write("Debug info:")
        st.code(traceback.format_exc())


# Integration function for app.py
def add_ai_schema_generation_tab():
    """
    Add AI Schema Generation as a third tab in the main app
    Call this function in app.py to integrate AI schema generation
    """
    return render_ai_schema_generation_tab