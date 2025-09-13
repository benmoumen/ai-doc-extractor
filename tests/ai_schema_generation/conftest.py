"""
Pytest configuration and fixtures for AI schema generation tests
"""

import pytest
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, List
import json

# Test data fixtures

@pytest.fixture
def sample_pdf_content():
    """Mock PDF content for testing"""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"

@pytest.fixture
def sample_image_content():
    """Mock image content for testing"""
    # Simple PNG header for testing
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"

@pytest.fixture
def sample_document_data():
    """Sample document data for testing"""
    return {
        "id": "test-doc-001",
        "filename": "test_invoice.pdf",
        "file_type": "pdf",
        "file_size": 1024,
        "content_hash": "abc123hash",
        "upload_timestamp": datetime.now(),
        "processing_status": "pending",
        "page_count": 1,
        "metadata": {},
        "user_session_id": "session-123"
    }

@pytest.fixture
def ai_analysis_result_data():
    """AI analysis result data for testing"""
    return {
        "id": "analysis-001",
        "sample_document_id": "test-doc-001",
        "analysis_timestamp": datetime.now(),
        "model_used": "llama-scout-17b",
        "processing_time": 2.5,
        "detected_document_type": "invoice",
        "document_type_confidence": 0.95,
        "alternative_types": [{"type": "receipt", "confidence": 0.7}],
        "layout_description": "Standard business invoice format",
        "field_locations": {"invoice_number": {"x": 100, "y": 50, "width": 120, "height": 20}},
        "text_blocks": [{"text": "Invoice #12345", "confidence": 0.9}],
        "total_fields_detected": 8,
        "high_confidence_fields": 6,
        "requires_review_count": 2,
        "analysis_notes": ["Clear text", "Good quality scan"],
        "overall_quality_score": 0.85,
        "confidence_distribution": {"high": 6, "medium": 2, "low": 0}
    }

@pytest.fixture
def extracted_field_data():
    """Extracted field data for testing"""
    return {
        "id": "field-001",
        "analysis_result_id": "analysis-001",
        "detected_name": "invoice_number",
        "display_name": "Invoice Number",
        "field_type": "string",
        "source_text": "12345",
        "visual_clarity_score": 0.9,
        "label_confidence_score": 0.95,
        "value_confidence_score": 0.85,
        "type_confidence_score": 0.9,
        "context_confidence_score": 0.88,
        "overall_confidence_score": 0.896,
        "bounding_box": {"x": 100, "y": 50, "width": 120, "height": 20},
        "page_number": 0,
        "context_description": "Located in header section",
        "is_required": True,
        "has_validation_hints": True,
        "field_group": "header",
        "alternative_names": ["ref_number", "reference"],
        "alternative_types": [{"type": "number", "confidence": 0.3}],
        "extraction_method": "ai_ocr_analysis",
        "requires_review": False,
        "review_reason": None
    }

@pytest.fixture
def mock_ai_response():
    """Mock AI model response for testing"""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "document_type": "invoice",
                        "confidence": 0.95,
                        "fields": [
                            {
                                "name": "invoice_number",
                                "type": "string",
                                "value": "12345",
                                "confidence": 0.9
                            },
                            {
                                "name": "total_amount",
                                "type": "number",
                                "value": "150.00",
                                "confidence": 0.85
                            }
                        ]
                    })
                }
            }
        ]
    }

@pytest.fixture
def temp_file():
    """Temporary file for testing file operations"""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        yield tmp.name
    os.unlink(tmp.name)

# Database fixtures
@pytest.fixture
def in_memory_db():
    """In-memory SQLite database for testing"""
    import sqlite3
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()

# Mock service fixtures
@pytest.fixture
def mock_litellm_response():
    """Mock LiteLLM response"""
    class MockResponse:
        def __init__(self, content):
            self.choices = [
                type('Choice', (), {
                    'message': type('Message', (), {'content': content})()
                })()
            ]

    return MockResponse

# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()