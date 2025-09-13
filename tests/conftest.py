"""
Pytest configuration and fixtures for schema management tests.
"""

import pytest
import tempfile
import sqlite3
import shutil
from pathlib import Path
from unittest.mock import Mock

@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create subdirectories
    schemas_dir = Path(temp_dir) / "schemas"
    templates_dir = Path(temp_dir) / "templates"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def temp_database(temp_data_dir):
    """Create temporary SQLite database for testing."""
    db_path = Path(temp_data_dir) / "test_schema_metadata.db"
    
    # Initialize database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create tables (same as production)
    cursor.execute('''
    CREATE TABLE schema_metadata (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT,
        version TEXT NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT DEFAULT 'system',
        usage_count INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE schema_versions (
        schema_id TEXT,
        version TEXT,
        changes TEXT,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT DEFAULT 'system',
        migration_notes TEXT,
        FOREIGN KEY (schema_id) REFERENCES schema_metadata (id),
        PRIMARY KEY (schema_id, version)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    yield str(db_path)

@pytest.fixture
def sample_schema():
    """Sample schema data for testing."""
    return {
        "id": "test_schema",
        "name": "Test Document Schema",
        "description": "A test schema for unit testing",
        "category": "Test",
        "version": "v1.0.0",
        "is_active": True,
        "fields": {
            "test_field": {
                "name": "test_field",
                "display_name": "Test Field",
                "type": "text",
                "required": True,
                "description": "A test field",
                "examples": ["Test value"],
                "validation_rules": [
                    {
                        "type": "required",
                        "message": "Test field is required"
                    }
                ]
            }
        },
        "validation_rules": []
    }

@pytest.fixture
def sample_field():
    """Sample field data for testing."""
    return {
        "name": "sample_field",
        "display_name": "Sample Field",
        "type": "text",
        "required": True,
        "description": "A sample field for testing",
        "examples": ["Sample value 1", "Sample value 2"],
        "validation_rules": [
            {
                "type": "required",
                "message": "Field is required"
            },
            {
                "type": "length",
                "min_length": 2,
                "max_length": 50,
                "message": "Field must be between 2 and 50 characters"
            }
        ]
    }

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components for UI testing."""
    import sys
    from unittest.mock import MagicMock
    
    # Mock streamlit module
    mock_st = MagicMock()
    sys.modules['streamlit'] = mock_st
    
    # Mock common streamlit functions
    mock_st.text_input.return_value = "test_input"
    mock_st.text_area.return_value = "test_area"
    mock_st.selectbox.return_value = "test_option"
    mock_st.checkbox.return_value = True
    mock_st.button.return_value = False
    mock_st.tabs.return_value = [Mock(), Mock(), Mock(), Mock()]
    mock_st.session_state = {}
    
    yield mock_st
    
    # Cleanup
    if 'streamlit' in sys.modules:
        del sys.modules['streamlit']

@pytest.fixture 
def mock_streamlit_elements():
    """Mock streamlit-elements for UI testing."""
    import sys
    from unittest.mock import MagicMock
    
    # Mock streamlit_elements module
    mock_elements = MagicMock()
    sys.modules['streamlit_elements'] = mock_elements
    sys.modules['streamlit_elements.elements'] = MagicMock()
    sys.modules['streamlit_elements.mui'] = MagicMock()
    
    yield mock_elements
    
    # Cleanup
    modules_to_remove = [m for m in sys.modules.keys() if m.startswith('streamlit_elements')]
    for module in modules_to_remove:
        del sys.modules[module]

# Test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "contract: Contract tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")