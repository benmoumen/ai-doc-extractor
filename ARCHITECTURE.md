# AI Data Extraction Tool - System Architecture

## 📋 Overview

This application is a multi-provider AI benchmarking tool for document data extraction, built with a modular architecture that separates concerns for maintainability, extensibility, and testing efficiency.

---

## 🏗️ System Architecture

### **Core Design Principles**
- **Modular separation**: Each module handles a specific domain
- **Provider agnostic**: Easy integration of new AI providers  
- **Cost transparency**: Real-time tracking of API costs and token usage
- **Performance focused**: Optimized for testing and benchmarking workflows
- **Streamlit native**: Leverages Streamlit's component system for responsive UI

### **Technology Stack**
- **Frontend**: Streamlit web framework
- **LLM Integration**: LiteLLM for multi-provider API calls
- **Image Processing**: Pillow (PIL) for image manipulation
- **PDF Processing**: PyMuPDF for PDF page extraction
- **Data Encoding**: Base64 for API-compatible image encoding
- **Configuration**: TOML-based secrets management

---

## 📁 Module Structure

```
OCR_App/
├── app.py                 # Main application orchestrator
├── config.py              # Configuration and constants
├── cost_tracking.py       # Cost calculation and token analysis
├── utils.py               # Image processing and data utilities
├── performance.py         # Performance metrics and statistics
├── ui_components.py       # Streamlit UI component library
├── requirements.txt       # Python dependencies
└── .streamlit/
    ├── secrets.toml       # API keys (user-created)
    └── secrets.toml.example  # Configuration template
```

---

## 🔧 Module Specifications

### **app.py** - Application Orchestrator
**Purpose**: Main application flow and coordination

**Responsibilities**:
- Streamlit page configuration and setup
- API key initialization
- User interface rendering coordination
- File upload and processing workflow
- Session state management
- API call execution and response handling
- Results storage and display coordination

**Key Functions**:
- Main application logic and user interaction handling
- Integration of all modular components
- Error handling and user feedback

---

### **config.py** - Configuration Management
**Purpose**: Centralized configuration and constants

**Core Components**:
```python
# Provider definitions
PROVIDER_OPTIONS = {"Provider Name": "api_key"}
MODEL_OPTIONS = {"provider": {"Model Name": "model_id"}}

# Cost fallback data
PRICING_FALLBACK = {"provider/model": {"input": rate, "output": rate}}

# Functions
setup_api_keys()      # Initialize API keys from secrets
get_model_param()     # Format model parameters for LiteLLM
```

**Configuration Areas**:
- **Provider mappings**: UI names to API identifiers
- **Model definitions**: Available models per provider
- **Pricing data**: Fallback rates when API doesn't provide costs
- **Page settings**: Streamlit configuration parameters

---

### **cost_tracking.py** - Financial Analytics
**Purpose**: API cost calculation and token usage analysis

**Core Functions**:
```python
calculate_cost_and_tokens(response, model_param)
format_cost_display(cost_data)  
should_show_cost(cost_data)
```

**Features**:
- **LiteLLM integration**: Native cost extraction from API responses
- **Fallback pricing**: Manual calculation when API costs unavailable
- **Token breakdown**: Input/output token analysis
- **Display formatting**: User-friendly cost and token presentation
- **Validation**: Cost data completeness checking

---

### **utils.py** - Data Processing Utilities
**Purpose**: File processing and data manipulation

**Core Functions**:
```python
extract_and_parse_json(text)         # Parse JSON from LLM responses
pdf_to_images(pdf_file, page_num)    # Convert PDF pages to images
image_to_base64(image)               # Encode images for API calls
format_time_display(seconds)         # Human-readable time formatting
clear_session_state()               # Reset application state
```

**Processing Capabilities**:
- **JSON extraction**: Intelligent parsing of structured data from text
- **PDF handling**: Page-by-page image conversion with error handling
- **Image encoding**: Base64 conversion optimized for API transmission
- **Time formatting**: Consistent duration display across UI
- **State management**: Clean session reset functionality

---

### **performance.py** - Analytics Engine
**Purpose**: Performance tracking and statistical analysis

**Core Functions**:
```python
update_performance_history(provider, model, timing, tokens)
get_provider_stats()
format_performance_stats_display(stats)
create_timing_data(start, api_start, api_end, total_end)
```

**Analytics Features**:
- **Historical tracking**: Performance data over time per provider
- **Statistical analysis**: Averages, minimums, maximums, totals
- **Timing breakdown**: Detailed processing phase measurements
- **Comparative metrics**: Provider performance comparison
- **Display optimization**: Formatted statistics for UI presentation

---

### **ui_components.py** - User Interface Library
**Purpose**: Streamlit component library for consistent UI

**Component Categories**:

#### **Layout Components**:
- `render_sidebar()`: Configuration panel with provider selection
- `render_results_header()`: Metrics display with performance indicators
- `render_results_content()`: Content display with format detection

#### **Control Components**:
- `render_pdf_controls()`: PDF page selection interface
- `render_download_buttons()`: Export functionality for multiple formats
- `render_performance_stats()`: Provider comparison display

#### **Content Components**:
- `render_welcome_message()`: Minimal onboarding for testing focus
- `render_timing_metrics()`: Processing time breakdown
- `render_cost_metrics()`: Cost and token usage display

**Design Philosophy**:
- **Compact layout**: Side-by-side display eliminates scrolling
- **Testing focused**: Streamlined interface for benchmarking workflows
- **Consistent styling**: Uniform component design language
- **Responsive metrics**: Real-time performance feedback

---

## 🔄 Data Flow Architecture

### **Processing Pipeline**:
```
User Upload → File Processing → API Call → Cost Analysis → Performance Tracking → UI Display
```

### **Detailed Flow**:
1. **Input Processing**:
   - File upload (image/PDF) via `ui_components.py`
   - PDF page conversion via `utils.py`
   - Image encoding via `utils.py`

2. **API Execution**:
   - Provider/model selection from `config.py`
   - LiteLLM API call coordination in `app.py`
   - Response processing and JSON extraction via `utils.py`

3. **Analysis Phase**:
   - Cost calculation via `cost_tracking.py`
   - Performance measurement via `performance.py`
   - Historical data update via `performance.py`

4. **Display Rendering**:
   - Results presentation via `ui_components.py`
   - Metrics display via `ui_components.py`
   - Export options via `ui_components.py`

---

## 🎯 Extension Architecture

### **Adding New Providers**:
1. **Configuration**: Update `PROVIDER_OPTIONS` and `MODEL_OPTIONS` in `config.py`
2. **Pricing**: Add fallback rates to `PRICING_FALLBACK` in `config.py`  
3. **Formatting**: Extend `get_model_param()` if custom formatting needed
4. **Testing**: Validate cost tracking and performance measurement

### **Adding New Features**:
1. **UI Components**: Add functions to `ui_components.py`
2. **Data Processing**: Extend utilities in `utils.py`
3. **Analytics**: Add metrics to `performance.py`
4. **Integration**: Update main flow in `app.py`

### **Customizing UI**:
1. **Component Modification**: Edit specific functions in `ui_components.py`
2. **Layout Changes**: Adjust column ratios and component placement
3. **Styling Updates**: Modify HTML/CSS in component render functions
4. **New Displays**: Add new metric or content display functions

---

## 📊 Performance Considerations

### **Efficiency Optimizations**:
- **Session state**: Minimal data storage in Streamlit session
- **Component isolation**: Independent rendering prevents unnecessary updates
- **Lazy loading**: Components render only when data available
- **Compact UI**: Side-by-side layout reduces render overhead

### **Scalability Design**:
- **Provider agnostic**: Easy addition of new AI providers
- **Modular metrics**: New performance indicators via isolated functions
- **Extensible config**: Simple addition of models and pricing
- **Component reuse**: UI components work across different contexts

---

## 🔐 Security Architecture

### **API Key Management**:
- **Secrets isolation**: API keys stored in `.streamlit/secrets.toml`
- **Environment injection**: Keys loaded into environment variables
- **Git protection**: Secrets file excluded via `.gitignore`
- **Template provision**: Example file for easy setup

### **Data Handling**:
- **Temporary processing**: Images encoded and processed in memory
- **No persistent storage**: No user data stored on disk
- **Session isolation**: Each user session independent
- **Secure transmission**: Base64 encoding for API compatibility

---

This architecture provides a robust foundation for AI provider testing and benchmarking, with clear separation of concerns and straightforward extension points for future enhancements.