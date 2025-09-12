# Implementation Guide: Schema Management UI Extension

## Overview
This guide provides detailed implementation instructions with cross-references to design documents for each task in the schema management UI extension.

## Quick Reference Map

### Design Document Cross-References
- **Data Models**: `/specs/001-our-data-extraction/data-model.md` (lines 181-372)
- **UI Contracts**: `/specs/001-our-data-extraction/contracts/ui_contracts.md`
- **Storage Architecture**: `/specs/001-our-data-extraction/research.md` (lines 156-174)
- **Field Type System**: `/specs/001-our-data-extraction/research.md` (lines 207-222)
- **UI Structure**: `/specs/001-our-data-extraction/research.md` (lines 183-197)
- **Implementation Steps**: `/specs/001-our-data-extraction/quickstart.md` (lines 266-404)

## Phase 3.1: Setup & Infrastructure

### T001: Schema Management Module Structure
**Reference**: Research.md Storage Architecture (lines 164-174)
**Implementation Details**:

```bash
# Create module structure
mkdir -p schema_management
cd schema_management

# Create module files with proper imports
cat > __init__.py << 'EOF'
"""
Schema Management UI Extension
Provides rich UI for creating, editing, and managing document schemas.
"""

from .schema_storage import SchemaStorage
from .schema_builder import render_schema_management_page
from .templates import FieldTemplateManager, ValidationTemplateManager
from .versioning import SchemaVersionControl

__version__ = "1.0.0"
__all__ = [
    "SchemaStorage",
    "render_schema_management_page", 
    "FieldTemplateManager",
    "ValidationTemplateManager",
    "SchemaVersionControl"
]
EOF
```

**Directory Structure to Create**:
```
schema_management/
├── __init__.py              # Module initialization
├── schema_storage.py        # Core storage interface (T004, T012)
├── schema_builder.py        # Main UI page (T016)
├── basic_info.py           # Basic info tab (T017)
├── field_editor.py         # Field management tab (T018)
├── validation_rules.py     # Validation builder (T019)
├── preview.py              # Real-time preview (T020)
├── import_export.py        # Import/export functionality (T021)
├── templates.py            # Field templates (T013)
├── validation_templates.py # Validation templates (T014)
├── versioning.py           # Version control (T015)
├── state_manager.py        # Session state management (T026)
├── error_handling.py       # Error handling (T027)
├── testing.py              # Schema testing (T029)
├── performance.py          # Performance optimization (T030)
└── validators.py           # Schema validation (T032)
```

### T002: Data Directory Structure
**Reference**: Research.md Storage Architecture (lines 164-174)
**Implementation Details**:

```bash
# Create data directory structure
mkdir -p data/schemas data/templates

# Initialize directory structure with placeholders
cat > data/schemas/README.md << 'EOF'
# Dynamic Schema Storage
This directory contains user-created document schemas in JSON format.

Format: {schema_id}_v{version}.json
Examples:
- custom_national_id_v1.json
- custom_passport_v2.json
- business_license_v1.json
EOF

cat > data/templates/README.md << 'EOF'
# Template Storage
This directory contains reusable field and validation templates.

Files:
- field_types.json: Field configuration templates
- validation_presets.json: Common validation patterns
EOF

# Create SQLite database structure
python3 << 'EOF'
import sqlite3
import json
from datetime import datetime

# Initialize SQLite database
conn = sqlite3.connect('data/schema_metadata.db')
cursor = conn.cursor()

# Schema metadata table
cursor.execute('''
CREATE TABLE IF NOT EXISTS schema_metadata (
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

# Schema versions table
cursor.execute('''
CREATE TABLE IF NOT EXISTS schema_versions (
    schema_id TEXT,
    version TEXT,
    changes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    migration_notes TEXT,
    FOREIGN KEY (schema_id) REFERENCES schema_metadata (id)
)
''')

# Template usage tracking
cursor.execute('''
CREATE TABLE IF NOT EXISTS template_usage (
    template_id TEXT PRIMARY KEY,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()
print("SQLite database initialized successfully")
EOF
```

### T003: Streamlit Elements Dependency
**Reference**: Research.md streamlit-elements decision (lines 143-154)
**Implementation Details**:

```bash
# Add dependencies to requirements.txt
cat >> requirements.txt << 'EOF'
# Schema Management UI Dependencies
streamlit-elements>=0.1.0    # Advanced UI components for drag-drop
python-jsonschema>=4.0.0     # JSON schema validation
sqlite3                      # Built-in Python, no install needed
EOF

# Test streamlit-elements installation
python3 << 'EOF'
try:
    from streamlit_elements import elements, mui, html
    print("✅ streamlit-elements installed successfully")
except ImportError as e:
    print(f"❌ Failed to import streamlit-elements: {e}")
    print("Run: pip install streamlit-elements>=0.1.0")

try:
    import jsonschema
    print("✅ python-jsonschema installed successfully") 
except ImportError as e:
    print(f"❌ Failed to import jsonschema: {e}")
    print("Run: pip install python-jsonschema>=4.0.0")
EOF
```

### T004: Schema Storage Utilities
**Reference**: Data-model.md SchemaStorage interface (lines 325-346)
**Implementation Details**:

Create `schema_management/schema_storage.py`:
```python
"""
Base schema storage interface and utilities.
Implements hybrid JSON file + SQLite metadata approach.

Reference: research.md lines 156-174 (Storage Architecture)
Reference: data-model.md lines 325-346 (Storage Strategy)
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class SchemaStorageInterface:
    """Base interface for schema storage operations."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.schemas_dir = self.data_dir / "schemas"
        self.templates_dir = self.data_dir / "templates"  
        self.metadata_db = self.data_dir / "schema_metadata.db"
        
        # Ensure directories exist
        self.schemas_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
    def get_db_connection(self) -> sqlite3.Connection:
        """Get SQLite database connection."""
        return sqlite3.connect(str(self.metadata_db))
        
    # Method stubs - to be implemented in T012
    def save_schema(self, schema_id: str, schema_data: Dict) -> bool:
        """Save schema to JSON file and update metadata."""
        raise NotImplementedError("Implement in T012")
        
    def load_schema(self, schema_id: str, version: Optional[str] = None) -> Optional[Dict]:
        """Load schema from JSON file."""
        raise NotImplementedError("Implement in T012")
        
    def list_schemas(self) -> List[Dict]:
        """List all available schemas."""
        raise NotImplementedError("Implement in T012")
        
    def delete_schema(self, schema_id: str) -> bool:
        """Delete schema and its versions."""
        raise NotImplementedError("Implement in T012")
```

## Phase 3.2: Tests First (TDD)

### T005: Schema Storage CRUD Tests
**Reference**: Data-model.md entities (lines 181-307), UI Contracts storage interface
**Implementation Details**:

Create `tests/test_schema_management/test_schema_storage.py`:
```python
"""
Schema storage CRUD tests - MUST FAIL INITIALLY
Tests the SchemaStorage class and related functionality.

Reference: data-model.md FieldTemplate (lines 181-209)
Reference: data-model.md ValidationTemplate (lines 212-235)
Reference: data-model.md SchemaVersion (lines 238-262)
"""

import pytest
import tempfile
import json
from pathlib import Path
from schema_management.schema_storage import SchemaStorage

class TestSchemaStorageCRUD:
    """Test schema storage CRUD operations."""
    
    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.storage = SchemaStorage(data_dir=self.test_dir)
        
    def test_save_new_schema(self):
        """Test saving a new schema."""
        schema_data = {
            "id": "test_doc",
            "name": "Test Document",
            "description": "Test document type",
            "fields": {
                "test_field": {
                    "name": "test_field",
                    "display_name": "Test Field",
                    "type": "string",
                    "required": True
                }
            }
        }
        
        # This should fail until T012 is implemented
        result = self.storage.save_schema("test_doc", schema_data)
        assert result is True
        
    def test_load_existing_schema(self):
        """Test loading an existing schema."""
        # This should fail until T012 is implemented
        schema = self.storage.load_schema("test_doc")
        assert schema is not None
        assert schema["id"] == "test_doc"
        
    def test_version_control_functionality(self):
        """Test schema versioning capabilities."""
        # Reference: data-model.md SchemaVersion (lines 238-262)
        
        # Create initial version
        schema_v1 = {"id": "versioned_doc", "version": "v1.0", "fields": {}}
        self.storage.save_schema("versioned_doc", schema_v1)
        
        # Update to new version
        schema_v2 = {"id": "versioned_doc", "version": "v1.1", "fields": {"new_field": {}}}
        self.storage.save_schema("versioned_doc", schema_v2)
        
        # Should be able to retrieve both versions
        current = self.storage.load_schema("versioned_doc")
        previous = self.storage.load_schema("versioned_doc", version="v1.0")
        
        assert current["version"] == "v1.1"
        assert previous["version"] == "v1.0"
        
    def test_template_storage_integration(self):
        """Test field and validation template storage."""
        # Reference: data-model.md FieldTemplate (lines 181-209)
        
        field_template = {
            "id": "personal_name",
            "name": "Personal Name Field", 
            "description": "Standard configuration for person's full name",
            "field_config": {
                "type": "string",
                "required": True,
                "validation_rules": [
                    {"type": "required", "message": "Name is required"}
                ]
            },
            "category": "personal"
        }
        
        # This should fail until template system is implemented
        result = self.storage.save_field_template("personal_name", field_template)
        assert result is True
        
        loaded_template = self.storage.load_field_template("personal_name")
        assert loaded_template["id"] == "personal_name"
```

### T006: Schema Builder UI Tests
**Reference**: UI Contracts render_schema_management_page (lines 15-28)
**Implementation Details**:

Create `tests/test_schema_management/test_schema_builder.py`:
```python
"""
Schema builder UI component tests - MUST FAIL INITIALLY
Tests the main schema management interface.

Reference: contracts/ui_contracts.md Main Interface Contract (lines 15-28)
Reference: research.md UI Structure (lines 183-197)
"""

import pytest
import streamlit as st
from unittest.mock import Mock, patch
from schema_management.schema_builder import render_schema_management_page

class TestSchemaBuilderUI:
    """Test main schema management UI components."""
    
    @patch('streamlit.title')
    @patch('streamlit.tabs')
    def test_main_page_layout(self, mock_tabs, mock_title):
        """Test main page renders with correct tab structure."""
        # Reference: research.md UI Structure (lines 183-197)
        
        # Mock tab structure
        mock_tabs.return_value = [Mock(), Mock(), Mock(), Mock()]
        
        # This should fail until T016 is implemented
        render_schema_management_page()
        
        # Verify correct tab structure
        mock_title.assert_called_with("🏗️ Schema Management")
        mock_tabs.assert_called_with(["📝 Basic Info", "🔧 Fields", "✅ Validation", "👁️ Preview"])
        
    def test_session_state_management(self):
        """Test session state handling for schema builder."""
        # Reference: contracts/ui_contracts.md Session State Dependencies (lines 23-27)
        
        expected_keys = [
            "current_schema_id",
            "active_tab", 
            "unsaved_changes"
        ]
        
        with patch('streamlit.session_state') as mock_session:
            # This should fail until session state management is implemented
            render_schema_management_page()
            
            # Verify session state keys are properly managed
            for key in expected_keys:
                assert key in mock_session
                
    def test_navigation_integration(self):
        """Test navigation to schema management page."""
        # This should fail until navigation integration is complete
        
        with patch('streamlit.sidebar.selectbox') as mock_select:
            mock_select.return_value = "Schema Management"
            
            # Should handle page selection properly
            result = render_schema_management_page()
            assert result is not None
```

### T007: Field Editor Component Tests  
**Reference**: UI Contracts Field Editor Contract (lines 94-131)
**Implementation Details**:

Create `tests/test_schema_management/test_field_editor.py`:
```python
"""
Field editor component tests - MUST FAIL INITIALLY
Tests drag-drop field management and field configuration.

Reference: contracts/ui_contracts.md Field Editor Contract (lines 94-131)
Reference: contracts/ui_contracts.md Field List Component (lines 68-92)
"""

import pytest
from unittest.mock import Mock, patch
from schema_management.field_editor import render_field_list, render_field_editor

class TestFieldEditorComponents:
    """Test field editing UI components."""
    
    def test_drag_drop_field_list(self):
        """Test drag-droppable field list functionality."""
        # Reference: contracts/ui_contracts.md Field List Component (lines 68-92)
        
        sample_fields = [
            {"name": "field1", "type": "string", "required": True},
            {"name": "field2", "type": "number", "required": False}
        ]
        
        with patch('streamlit_elements.elements'):
            # This should fail until T018 is implemented
            result = render_field_list(sample_fields)
            
            # Should return reordered field list
            assert isinstance(result, list)
            assert len(result) == 2
            
    def test_field_configuration_editor(self):
        """Test field configuration editor interface."""
        # Reference: contracts/ui_contracts.md Field Editor Contract (lines 94-131)
        
        field_data = {
            "name": "test_field",
            "display_name": "Test Field",
            "type": "string",
            "required": True,
            "description": "Test field description"
        }
        
        field_templates = [
            {"id": "personal_name", "name": "Personal Name"}
        ]
        
        # This should fail until field editor is implemented
        result = render_field_editor(field_data, field_templates)
        
        # Should return updated field configuration
        expected_keys = ["name", "display_name", "type", "required", "description", "examples", "validation_rules"]
        for key in expected_keys:
            assert key in result
            
    def test_field_type_validation(self):
        """Test field type selection and validation."""
        # Reference: contracts/ui_contracts.md Field Type Selector (line 410-435)
        
        valid_types = ["string", "number", "date", "boolean", "email", "phone"]
        
        for field_type in valid_types:
            field_data = {"name": "test", "type": field_type}
            
            # Should accept valid field types
            result = render_field_editor(field_data, [])
            assert result["type"] == field_type
            
        # Should reject invalid field types
        invalid_field = {"name": "test", "type": "invalid_type"}
        with pytest.raises(ValueError):
            render_field_editor(invalid_field, [])
```

## Phase 3.3: Core Implementation

### T012: SchemaStorage Implementation
**Reference**: Data-model.md Storage Strategy (lines 324-346)
**Implementation Details**:

Update `schema_management/schema_storage.py` with full implementation:
```python
"""
Complete SchemaStorage implementation.
Implements hybrid JSON file + SQLite metadata approach.

Reference: research.md Storage Architecture (lines 164-174)
Reference: data-model.md Storage Strategy (lines 324-346)
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class SchemaStorage(SchemaStorageInterface):
    """
    Complete implementation of schema storage operations.
    
    Storage Strategy:
    - JSON files for schema data (human-readable, version control friendly)
    - SQLite for metadata, indexing, and version tracking
    """
    
    def save_schema(self, schema_id: str, schema_data: Dict) -> bool:
        """
        Save schema to JSON file and update metadata.
        
        Reference: data-model.md Schema entity (lines 32-52)
        """
        try:
            # Add metadata
            schema_data["created_date"] = datetime.now().isoformat()
            schema_data["updated_date"] = datetime.now().isoformat()
            version = schema_data.get("version", "v1.0")
            
            # Save JSON file
            filename = f"{schema_id}_{version}.json"
            filepath = self.schemas_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=2, ensure_ascii=False)
            
            # Update metadata database
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT OR REPLACE INTO schema_metadata 
                (id, name, description, category, version, updated_date)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    schema_id,
                    schema_data.get("name", schema_id),
                    schema_data.get("description", ""),
                    schema_data.get("category", "custom"),
                    version,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Error saving schema {schema_id}: {e}")
            return False
    
    def load_schema(self, schema_id: str, version: Optional[str] = None) -> Optional[Dict]:
        """
        Load schema from JSON file.
        
        Args:
            schema_id: Schema identifier
            version: Specific version to load (defaults to latest)
            
        Returns:
            Schema dictionary or None if not found
        """
        try:
            if version is None:
                # Get latest version from metadata
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        'SELECT version FROM schema_metadata WHERE id = ? AND is_active = 1',
                        (schema_id,)
                    )
                    result = cursor.fetchone()
                    if result:
                        version = result[0]
                    else:
                        version = "v1.0"  # fallback
            
            # Load JSON file
            filename = f"{schema_id}_{version}.json"
            filepath = self.schemas_dir / filename
            
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return None
                
        except Exception as e:
            print(f"Error loading schema {schema_id}: {e}")
            return None
    
    def list_schemas(self) -> List[Dict]:
        """
        List all available schemas with metadata.
        
        Returns:
            List of schema summary dictionaries
        """
        schemas = []
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, name, description, category, version, created_date, updated_date, usage_count
                FROM schema_metadata 
                WHERE is_active = 1
                ORDER BY updated_date DESC
                ''')
                
                for row in cursor.fetchall():
                    schemas.append({
                        "id": row[0],
                        "name": row[1], 
                        "description": row[2],
                        "category": row[3],
                        "version": row[4],
                        "created_date": row[5],
                        "updated_date": row[6],
                        "usage_count": row[7]
                    })
                    
        except Exception as e:
            print(f"Error listing schemas: {e}")
            
        return schemas
    
    def delete_schema(self, schema_id: str) -> bool:
        """
        Delete schema and mark as inactive in metadata.
        
        Args:
            schema_id: Schema to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Mark as inactive in metadata (soft delete)
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE schema_metadata SET is_active = 0 WHERE id = ?',
                    (schema_id,)
                )
                conn.commit()
                
            return True
            
        except Exception as e:
            print(f"Error deleting schema {schema_id}: {e}")
            return False
```

### T013: Field Template System
**Reference**: Data-model.md FieldTemplate (lines 181-209)
**Implementation Details**:

Create `schema_management/templates.py`:
```python
"""
Field template system implementation.
Provides reusable field configurations organized by categories.

Reference: data-model.md FieldTemplate entity (lines 181-209)
Reference: research.md Field Type System (lines 207-222)
"""

import json
from typing import Dict, List, Optional
from pathlib import Path

class FieldTemplateManager:
    """
    Manages field configuration templates.
    
    Field templates provide pre-configured field settings for common use cases.
    Reference: data-model.md FieldTemplate (lines 181-209)
    """
    
    def __init__(self, templates_dir: str = "data/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_file = self.templates_dir / "field_types.json"
        self._templates_cache = None
        
    def get_field_templates(self) -> Dict[str, Dict]:
        """
        Get all available field templates organized by category.
        
        Returns:
            Dictionary of field templates by category
            
        Reference: data-model.md FieldTemplate structure (lines 181-209)
        """
        if self._templates_cache is None:
            self._load_templates()
        
        return self._templates_cache
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        """
        Get specific field template by ID.
        
        Args:
            template_id: Template identifier (e.g., "personal_name")
            
        Returns:
            Template configuration or None if not found
        """
        templates = self.get_field_templates()
        
        for category, category_templates in templates.items():
            if template_id in category_templates:
                return category_templates[template_id]
        
        return None
    
    def get_templates_by_category(self, category: str) -> Dict[str, Dict]:
        """
        Get all templates for a specific category.
        
        Args:
            category: Template category (e.g., "personal", "contact", "identification")
            
        Returns:
            Dictionary of templates for the category
        """
        templates = self.get_field_templates()
        return templates.get(category, {})
    
    def _load_templates(self):
        """Load templates from JSON file."""
        try:
            if self.templates_file.exists():
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._templates_cache = data.get("templates", {})
            else:
                # Create default templates if file doesn't exist
                self._create_default_templates()
        except Exception as e:
            print(f"Error loading field templates: {e}")
            self._templates_cache = {}
    
    def _create_default_templates(self):
        """
        Create default field templates.
        
        Reference: data-model.md FieldTemplate examples (lines 192-209)
        """
        default_templates = {
            "personal": {
                "personal_name": {
                    "id": "personal_name",
                    "name": "Personal Name Field",
                    "description": "Standard configuration for person's full name",
                    "field_config": {
                        "type": "string",
                        "required": True,
                        "validation_rules": [
                            {"type": "required", "message": "Name is required"},
                            {"type": "length", "min": 2, "max": 100, "message": "Name must be 2-100 characters"}
                        ]
                    },
                    "category": "personal",
                    "usage_count": 0
                }
            },
            "identification": {
                "government_id": {
                    "id": "government_id",
                    "name": "Government ID Field", 
                    "description": "Standard government-issued ID number",
                    "field_config": {
                        "type": "string",
                        "required": True,
                        "validation_rules": [
                            {"type": "pattern", "value": "^[A-Z0-9]{8,12}$", "message": "Must be 8-12 alphanumeric characters"}
                        ]
                    },
                    "category": "identification",
                    "usage_count": 0
                }
            },
            "contact": {
                "email_address": {
                    "id": "email_address",
                    "name": "Email Address Field",
                    "description": "Standard email address with validation",
                    "field_config": {
                        "type": "email",
                        "required": False,
                        "validation_rules": [
                            {"type": "format", "value": "email", "message": "Must be valid email format"}
                        ]
                    },
                    "category": "contact",
                    "usage_count": 0
                }
            }
        }
        
        # Save default templates
        self.templates_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump({"templates": default_templates}, f, indent=2, ensure_ascii=False)
        
        self._templates_cache = default_templates
```

## Integration Points

### T022: Navigation Integration
**Reference**: Quickstart.md Navigation Setup (lines 309-321)
**Implementation Details**:

Update `app.py` to include schema management navigation:
```python
"""
Add schema management navigation to main Streamlit app.

Reference: quickstart.md Navigation Setup (lines 309-321)
"""

# Add after existing imports
from schema_management import render_schema_management_page

# Add navigation selector to sidebar (before existing sidebar content)
with st.sidebar:
    # Add page navigation
    page = st.selectbox(
        "Navigation",
        ["📊 Document Extraction", "🏗️ Schema Management"],
        index=0,
        help="Select application feature"
    )

# Add page routing logic (replace existing main content)
if page == "🏗️ Schema Management":
    render_schema_management_page()
else:
    # Existing document extraction interface
    st.subheader("DATA EXTRACTION APP", divider='orange')
    
    # Rest of existing app.py content continues here...
    selected_provider, selected_model, selected_provider_name, selected_model_name, uploaded_file, selected_doc_type, selected_doc_type_name = render_sidebar()
    # ... continue with existing extraction logic
```

### T023: Dynamic Schema Integration
**Reference**: Data-model.md Schema Loading Priority (lines 342-346)
**Implementation Details**:

Update `ui_components.py` render_sidebar function:
```python
"""
Update document type selector to use dynamic schemas.

Reference: data-model.md Schema Loading Priority (lines 342-346)
Reference: quickstart.md Document Type Selection (lines 116-137)
"""

def render_sidebar():
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # Add document type selection with dynamic loading
        st.subheader("📋 Document Type")
        
        # Load schemas from both static config and dynamic storage
        from config import DOCUMENT_SCHEMAS
        from schema_management.schema_storage import SchemaStorage
        
        # Combine static and dynamic schemas
        document_types = {}
        
        # 1. Load static schemas (backward compatibility)
        for schema_id, schema in DOCUMENT_SCHEMAS.items():
            document_types[schema['name']] = {
                'id': schema_id,
                'source': 'static',
                'schema': schema
            }
        
        # 2. Load dynamic schemas (user-created)
        try:
            storage = SchemaStorage()
            dynamic_schemas = storage.list_schemas()
            
            for schema_info in dynamic_schemas:
                schema_data = storage.load_schema(schema_info['id'])
                if schema_data:
                    display_name = f"{schema_data['name']} (Custom)"
                    document_types[display_name] = {
                        'id': schema_info['id'],
                        'source': 'dynamic',
                        'schema': schema_data
                    }
        except Exception as e:
            st.warning(f"Could not load dynamic schemas: {e}")
        
        # Document type selector
        if document_types:
            selected_doc_type_name = st.selectbox(
                "Select document type:",
                options=list(document_types.keys()),
                help="Choose the type of document you're uploading"
            )
            
            selected_doc_info = document_types[selected_doc_type_name]
            selected_doc_type = selected_doc_info['id']
            schema = selected_doc_info['schema']
            
            # Display schema preview with source indicator
            with st.expander(f"📝 Expected Fields ({selected_doc_info['source']})"):
                for field_name, field_def in schema['fields'].items():
                    required_marker = "🔴" if field_def['required'] else "⚪"
                    st.write(f"{required_marker} **{field_def['display_name']}**: {field_def['description']}")
        else:
            selected_doc_type = None
            selected_doc_type_name = "None"
            st.info("No document types available. Create schemas in Schema Management.")
        
        # Continue with existing provider/model selection...
        # ... rest of function remains the same
        
        return selected_provider, selected_model, selected_provider_name, selected_model_name, uploaded_file, selected_doc_type, selected_doc_type_name
```

## Implementation Sequence

### Recommended Implementation Order:
1. **Setup Phase (T001-T004)**: Create infrastructure and interfaces
2. **Test Phase (T005-T011)**: Write failing tests for all components  
3. **Storage Phase (T012-T015)**: Implement core storage and template systems
4. **UI Phase (T016-T021)**: Build schema management interface components
5. **Integration Phase (T022-T027)**: Connect with existing extraction workflow
6. **Polish Phase (T028-T033)**: Add advanced features and optimization

### Cross-Reference Validation:
Each task now includes specific references to design documents with line numbers, ensuring implementers can quickly find the relevant specifications and examples.

### Missing Implementation Details Identified:
1. **UI Component Internals**: Specific streamlit-elements usage patterns
2. **Error Handling Strategies**: Specific error cases and user feedback
3. **Performance Optimization Details**: Caching strategies and loading patterns  
4. **Testing Data**: Sample schemas and test cases for validation
5. **Migration Strategies**: How to handle schema version changes

This implementation guide provides the detailed cross-references and step-by-step instructions missing from the original tasks.md file.