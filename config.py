"""
Configuration settings and constants for the OCR application.
"""
import os
import streamlit as st

# Default provider and model configuration
DEFAULT_PROVIDER = "groq"
DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Provider and model configuration
PROVIDER_OPTIONS = {
    "Mistral": "mistral",
    "Groq": "groq"
}

MODEL_OPTIONS = {
    "mistral": {
        "Mistral Small 3.2": "mistral-small-2506"
    },
    "groq": {
        "Llama Scout 17B": "meta-llama/llama-4-scout-17b-16e-instruct"
    }
}

# Pricing per 1k tokens (converted from per M tokens)
PRICING_FALLBACK = {
    "groq/meta-llama/llama-4-scout-17b-16e-instruct": {
        "input": 0.00011, "output": 0.00034
    },  # $0.11/$0.34 per M tokens
    "mistral/mistral-small-2506": {
        "input": 0.0001, "output": 0.0003
    },  # $0.1/$0.3 per M tokens
}

# API Configuration
def setup_api_keys():
    """Set up API keys from Streamlit secrets."""
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    if "MISTRAL_API_KEY" in st.secrets:
        os.environ["MISTRAL_API_KEY"] = st.secrets["MISTRAL_API_KEY"]

def get_model_param(provider, model):
    """Get the properly formatted model parameter for LiteLLM."""
    if provider == "mistral":
        return f"mistral/{model}"
    elif provider == "groq":
        return f"groq/{model}"
    else:
        return model

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "DATA EXTRACTION APP",
    "page_icon": "🔎",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}