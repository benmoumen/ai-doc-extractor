# Implementation Guide: Schema Management UI Extension

## Overview
This guide provides detailed implementation instructions with cross-references to design documents for each task in the schema management UI extension.

## Quick Reference Map

### Design Document Cross-References
- **Data Models**: `/specs/002-schema-management-ui/data-model.md`
- **UI Contracts**: `/specs/002-schema-management-ui/contracts/ui_contracts.md`
- **Storage Architecture**: `/specs/002-schema-management-ui/research.md` (Storage section)
- **Field Type System**: `/specs/002-schema-management-ui/research.md` (Field Types section)
- **UI Structure**: `/specs/002-schema-management-ui/research.md` (UI Components section)
- **Implementation Steps**: `/specs/002-schema-management-ui/quickstart.md`

## Phase 3.1: Setup & Infrastructure

### T001: Schema Management Module Structure
**Reference**: Research.md Storage Architecture
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
├── schema_storage.py        # Core storage interface
├── schema_builder.py        # Main UI page
├── basic_info.py           # Basic info tab
├── field_editor.py         # Field management tab
├── validation_rules.py     # Validation builder
├── preview.py              # Real-time preview
├── import_export.py        # Import/export functionality
├── templates.py            # Field templates
├── validation_templates.py # Validation templates
├── versioning.py           # Version control
├── state_manager.py        # Session state management
├── error_handling.py       # Error handling
├── testing.py              # Schema testing
├── performance.py          # Performance optimization
└── validators.py           # Schema validation
```

### T002: Data Directory Structure
**Reference**: Research.md Storage Architecture
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
**Reference**: Research.md streamlit-elements decision
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

## Phase 3.2: Tests First (TDD)

### T004: Schema Storage CRUD Tests
**Reference**: Data-model.md entities, UI Contracts storage interface
**Implementation Details**:

Create `tests/test_schema_management/test_schema_storage.py`:
```python
"""
Schema storage CRUD tests - MUST FAIL INITIALLY
Tests the SchemaStorage class and related functionality.
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
        
        # This should fail until implementation is complete
        result = self.storage.save_schema("test_doc", schema_data)
        assert result is True
        
    def test_load_existing_schema(self):
        """Test loading an existing schema."""
        # This should fail until implementation is complete
        schema = self.storage.load_schema("test_doc")
        assert schema is not None
        assert schema["id"] == "test_doc"
        
    def test_version_control_functionality(self):
        """Test schema versioning capabilities."""
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
```

## Phase 3.3: Core Implementation

### Schema Storage Implementation
**Reference**: Data-model.md Storage Strategy
**Implementation Details**:

Create `schema_management/schema_storage.py` with hybrid JSON + SQLite approach:
```python
"""
Complete SchemaStorage implementation.
Implements hybrid JSON file + SQLite metadata approach.
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class SchemaStorage:
    """
    Complete implementation of schema storage operations.
    
    Storage Strategy:
    - JSON files for schema data (human-readable, version control friendly)
    - SQLite for metadata, indexing, and version tracking
    """
    
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
    
    def save_schema(self, schema_id: str, schema_data: Dict) -> bool:
        """
        Save schema to JSON file and update metadata.
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
        """Load schema from JSON file."""
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
                        version = "v1.0"
            
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
        """List all available schemas with metadata."""
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
```

## Integration Points

### Navigation Integration
Update `app.py` to include schema management navigation:
```python
"""
Add schema management navigation to main Streamlit app.
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
    # ... continue with existing extraction logic
```

## Performance Considerations

### Lazy Loading
- Load schemas only when needed
- Cache frequently accessed templates
- Use pagination for large schema lists

### Memory Management
- Stream large files instead of loading entirely in memory
- Clear unused session state regularly
- Optimize JSON serialization/deserialization

### UI Responsiveness
- Use debounced updates for real-time preview
- Show loading indicators for long operations
- Implement progressive disclosure for complex forms

This implementation guide provides detailed instructions for implementing the Schema Management UI Extension while maintaining clear separation from the base document extraction feature.