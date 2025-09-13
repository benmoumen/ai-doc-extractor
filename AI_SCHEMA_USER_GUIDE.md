# 🤖 AI Schema Generation - User Guide

## How to Access and Use AI Schema Generation

The AI Schema Generation feature has been integrated into the main Streamlit application. Here's how to use it:

### 🚀 Quick Start

1. **Access the Feature**
   - Open your browser and go to `http://localhost:8503` (enhanced app with AI features)
   - You'll see **three tabs** at the top:
     - 📄 Document Extraction (original feature)
     - 🔧 Schema Management (existing feature)
     - **🤖 AI Schema Generation** (new feature!)

2. **Click on the AI Schema Generation tab** to start using the feature

### 📱 User Interface Overview

The AI Schema Generation tab contains **4 sub-tabs**:

#### 1. 📤 Document Analysis
**Purpose**: Upload documents and generate AI-powered schemas

**How to use**:
- Upload a document (PDF, PNG, JPG, TIFF, BMP)
- Select document type (Auto-detect, Invoice, Receipt, Contract, etc.)
- Set confidence threshold (0.1 to 1.0)
- Click **🤖 Generate AI Schema**
- Wait for AI analysis to complete

**What you'll see**:
- File information and preview
- Analysis progress indicator
- Results summary with confidence scores

#### 2. 📋 Schema Preview
**Purpose**: View and export generated schemas

**Features**:
- Schema overview with metrics (Total Fields, Required Fields, Confidence)
- Detailed field configurations with AI metadata
- Export options:
  - 📄 Export as JSON
  - 📊 Export as CSV
  - 🔧 Add to Schema Manager

#### 3. 🔍 Data Validation
**Purpose**: Test the generated schema with sample data

**How to use**:
- Enter test data for each field in the schema
- Click **🔍 Validate Data**
- Review validation results and error messages

**What you'll see**:
- Dynamic form fields based on schema
- Validation success/failure indicators
- Detailed error messages for failed validations

#### 4. 📊 Performance Monitor
**Purpose**: Monitor AI schema generation performance

**Features**:
- Real-time performance metrics
- System resource monitoring
- Performance issue alerts
- Controls to refresh data or clear history

### 🛠️ Current Implementation Status

**✅ What Works Now:**
- Complete utility infrastructure (validation, caching, monitoring, etc.)
- Full UI interface with mock AI analysis
- Data validation against schemas
- Performance monitoring
- Export capabilities

**🚧 What's Coming Soon:**
- Real AI model integration for document analysis
- Actual field type inference from document content
- Advanced confidence scoring based on real AI analysis
- Integration with existing Schema Manager

### 📋 Step-by-Step Workflow

#### Generating a Schema:

1. **Go to AI Schema Generation tab** → **Document Analysis**

2. **Upload Your Document**
   - Click "Choose a document for AI schema generation"
   - Select a PDF or image file
   - View file information and preview

3. **Configure Analysis**
   - Choose document type (or use Auto-detect)
   - Set confidence threshold (recommend 0.7 for balanced results)

4. **Generate Schema**
   - Click "🤖 Generate AI Schema"
   - Wait for analysis (currently simulated, ~2-3 seconds)
   - View results summary

5. **Review Generated Schema**
   - Switch to **Schema Preview** tab
   - Review field details and AI confidence scores
   - Export schema if satisfied

6. **Test Your Schema**
   - Switch to **Data Validation** tab
   - Enter sample data in the generated form
   - Validate to ensure schema works correctly

#### Performance Monitoring:

1. **Go to Performance Monitor tab**
2. **View Metrics**: Check processing times and system resources
3. **Monitor Issues**: Review any performance warnings
4. **Manage Data**: Refresh or clear performance history

### 💡 Tips for Best Results

1. **Document Quality**: Use high-resolution, clear images for better AI analysis
2. **Document Type**: Select the correct document type when possible
3. **Confidence Threshold**:
   - Higher (0.8+): More strict, fewer fields but higher accuracy
   - Lower (0.5-0.7): More permissive, more fields but may include noise
4. **Validation Testing**: Always test generated schemas with sample data
5. **Export Early**: Export schemas you're happy with to avoid losing work

### 🔧 Integration with Existing Features

**Schema Management Integration**:
- Generated schemas can be exported to the existing Schema Manager
- Use the "🔧 Add to Schema Manager" button in Schema Preview

**Document Extraction Integration**:
- Generated schemas can be used in the Document Extraction tab
- Exported schemas appear in the document type selector

### 🚀 Running the Enhanced App

**To use the AI Schema Generation feature**:

1. **Start the enhanced app**:
   ```bash
   cd /Users/moulaymehdi/PROJECTS/00AI/ai-doc-extractor
   venv/bin/streamlit run app_with_ai_schema.py --server.port=8503
   ```

2. **Open in browser**: http://localhost:8503

3. **Navigate to AI Schema Generation tab**

**To use the original app** (without AI features):
```bash
venv/bin/streamlit run app.py --server.port=8502
```
Open: http://localhost:8502

### 🐛 Troubleshooting

**If AI Schema Generation tab is missing**:
- Make sure you're running `app_with_ai_schema.py`
- Check that the AI schema generation module is properly installed

**If you get import errors**:
- Ensure all dependencies are installed: `venv/bin/pip install email-validator phonenumbers psutil`
- Check that the ai_schema_generation module is in the correct directory

**If performance is slow**:
- Check the Performance Monitor tab for bottlenecks
- Reduce confidence threshold for faster processing
- Clear performance history if needed

### 📚 Example Use Cases

1. **Invoice Processing**:
   - Upload invoice image → Select "Invoice" type → Generate schema
   - Get fields like invoice_number, date, total_amount, customer_name
   - Test with sample invoice data → Export to Schema Manager

2. **Receipt Analysis**:
   - Upload receipt → Select "Receipt" type → Generate schema
   - Get fields like merchant, date, total, payment_method
   - Validate with test data → Use in Document Extraction

3. **Custom Document Types**:
   - Upload any document → Select "Auto-detect" → Generate schema
   - Review AI-detected fields → Refine as needed
   - Create custom schema for your specific document types

### 🎯 Next Steps

To complete the full AI integration:

1. **Implement Core AI Components**: Connect real AI models for document analysis
2. **Add Model Configuration**: Allow users to select AI models (GPT-4, Claude, etc.)
3. **Enhance Field Inference**: Improve field type detection and validation rule generation
4. **Add Learning Features**: Allow schemas to improve over time based on user feedback

The foundation is complete - the utility infrastructure, UI interface, and integration patterns are all ready for the full AI implementation!