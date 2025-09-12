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

# Document Type Schemas Configuration
DOCUMENT_SCHEMAS = {
    "national_id": {
        "id": "national_id",
        "name": "National ID",
        "description": "Government-issued national identification document",
        "fields": {
            "full_name": {
                "name": "full_name",
                "display_name": "Full Name",
                "type": "string",
                "required": True,
                "description": "Complete name as shown on document",
                "examples": ["John Smith", "Maria Garcia", "Ahmed Hassan"],
                "validation_rules": [
                    {
                        "type": "required",
                        "message": "Full name is required and must be visible on document",
                        "severity": "error"
                    },
                    {
                        "type": "length",
                        "min": 2,
                        "max": 100,
                        "message": "Name must be between 2 and 100 characters",
                        "severity": "warning"
                    }
                ]
            },
            "id_number": {
                "name": "id_number",
                "display_name": "ID Number",
                "type": "string",
                "required": True,
                "description": "Unique identification number on the document",
                "examples": ["AB123456789", "CD987654321", "XY555666777"],
                "validation_rules": [
                    {
                        "type": "required",
                        "message": "ID number is mandatory for identification",
                        "severity": "error"
                    },
                    {
                        "type": "pattern",
                        "value": "^[A-Z0-9]{8,15}$",
                        "message": "ID number should be 8-15 alphanumeric characters",
                        "severity": "error"
                    }
                ]
            },
            "date_of_birth": {
                "name": "date_of_birth",
                "display_name": "Date of Birth",
                "type": "date",
                "required": True,
                "description": "Birth date in YYYY-MM-DD format",
                "examples": ["1985-03-15", "1992-11-08", "1978-07-22"],
                "validation_rules": [
                    {
                        "type": "required",
                        "message": "Date of birth is required for age verification",
                        "severity": "error"
                    },
                    {
                        "type": "format",
                        "value": "date",
                        "message": "Date must be in YYYY-MM-DD format",
                        "severity": "error"
                    },
                    {
                        "type": "range",
                        "min": "1900-01-01",
                        "max": "2010-12-31",
                        "message": "Birth date should be between 1900 and 2010",
                        "severity": "warning"
                    }
                ]
            },
            "address": {
                "name": "address",
                "display_name": "Address",
                "type": "string",
                "required": False,
                "description": "Residential address if visible on document",
                "examples": ["123 Main St, City, State", "456 Oak Ave, Town"],
                "validation_rules": [
                    {
                        "type": "length",
                        "min": 10,
                        "max": 200,
                        "message": "Address should be between 10 and 200 characters if provided",
                        "severity": "info"
                    }
                ]
            }
        }
    },
    "passport": {
        "id": "passport",
        "name": "Passport",
        "description": "International travel document",
        "fields": {
            "passport_number": {
                "name": "passport_number",
                "display_name": "Passport Number",
                "type": "string",
                "required": True,
                "description": "Unique passport identification number",
                "examples": ["A1234567", "B9876543", "C5555666"],
                "validation_rules": [
                    {
                        "type": "required",
                        "message": "Passport number is mandatory",
                        "severity": "error"
                    },
                    {
                        "type": "pattern",
                        "value": "^[A-Z][0-9]{7,9}$",
                        "message": "Passport number should start with a letter followed by 7-9 digits",
                        "severity": "error"
                    }
                ]
            },
            "full_name": {
                "name": "full_name",
                "display_name": "Full Name",
                "type": "string",
                "required": True,
                "description": "Complete name as shown on passport",
                "examples": ["SMITH, JOHN", "GARCIA, MARIA ELENA"],
                "validation_rules": [
                    {
                        "type": "required",
                        "message": "Full name is required on passport",
                        "severity": "error"
                    }
                ]
            },
            "nationality": {
                "name": "nationality",
                "display_name": "Nationality",
                "type": "string",
                "required": True,
                "description": "Country of citizenship",
                "examples": ["UNITED STATES OF AMERICA", "CANADA", "MEXICO"],
                "validation_rules": [
                    {
                        "type": "required",
                        "message": "Nationality must be specified on passport",
                        "severity": "error"
                    }
                ]
            },
            "date_of_birth": {
                "name": "date_of_birth",
                "display_name": "Date of Birth",
                "type": "date",
                "required": True,
                "description": "Birth date in DD MMM YYYY format",
                "examples": ["15 MAR 1985", "08 NOV 1992"],
                "validation_rules": [
                    {
                        "type": "required",
                        "message": "Date of birth is required",
                        "severity": "error"
                    }
                ]
            },
            "expiry_date": {
                "name": "expiry_date",
                "display_name": "Expiry Date",
                "type": "date",
                "required": True,
                "description": "Passport expiration date",
                "examples": ["15 MAR 2035", "08 NOV 2032"],
                "validation_rules": [
                    {
                        "type": "required",
                        "message": "Expiry date is required",
                        "severity": "error"
                    }
                ]
            }
        }
    }
}

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "DATA EXTRACTION APP",
    "page_icon": "🔎",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}