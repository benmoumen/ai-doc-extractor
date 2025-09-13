# Quickstart Guide: Schema Management UI Extension

## Prerequisites

- Python 3.11+ environment
- Existing `001-our-data-extraction` feature implemented and working
- Streamlit application running successfully
- Write access to project directory

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
# Add to requirements.txt
echo "streamlit-elements>=0.1.0" >> requirements.txt
echo "python-jsonschema>=4.0.0" >> requirements.txt

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Test streamlit-elements
python -c "from streamlit_elements import elements, mui; print('✅ streamlit-elements ready')"

# Test jsonschema
python -c "import jsonschema; print('✅ jsonschema ready')"
```

### 3. Create Module Structure

```bash
# Create schema management module
mkdir -p schema_management
touch schema_management/__init__.py
touch schema_management/schema_storage.py
touch schema_management/schema_builder.py
```

### 4. Create Data Directories

```bash
# Create data storage structure
mkdir -p data/schemas data/templates

# Initialize SQLite database
python -c "
import sqlite3
conn = sqlite3.connect('data/schema_metadata.db')
cursor = conn.cursor()
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
conn.commit()
conn.close()
print('✅ Database initialized')
"
```

## Basic Implementation Test (10 minutes)

### 1. Minimal Schema Storage

Create `schema_management/schema_storage.py`:

```python
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class SchemaStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.schemas_dir = self.data_dir / "schemas"
        self.metadata_db = self.data_dir / "schema_metadata.db"
        
        self.schemas_dir.mkdir(parents=True, exist_ok=True)
    
    def save_schema(self, schema_id: str, schema_data: Dict) -> bool:
        try:
            # Add timestamps
            schema_data["updated_date"] = datetime.now().isoformat()
            version = schema_data.get("version", "v1.0.0")
            
            # Save JSON file
            filename = f"{schema_id}_{version}.json"
            filepath = self.schemas_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving schema: {e}")
            return False
    
    def load_schema(self, schema_id: str, version: Optional[str] = None) -> Optional[Dict]:
        try:
            if version is None:
                version = "v1.0.0"  # Default for testing
            
            filename = f"{schema_id}_{version}.json"
            filepath = self.schemas_dir / filename
            
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error loading schema: {e}")
            return None
    
    def list_schemas(self) -> List[Dict]:
        schemas = []
        try:
            for json_file in self.schemas_dir.glob("*.json"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
                    schemas.append({
                        "id": schema_data.get("id"),
                        "name": schema_data.get("name"),
                        "category": schema_data.get("category", "Custom"),
                        "version": schema_data.get("version"),
                        "updated_date": schema_data.get("updated_date")
                    })
        except Exception as e:
            print(f"Error listing schemas: {e}")
        
        return schemas
```

### 2. Minimal UI Integration

Create `schema_management/schema_builder.py`:

```python
import streamlit as st
from .schema_storage import SchemaStorage

def render_schema_management_page():
    """Main schema management interface"""
    st.title("🏗️ Schema Management")
    
    # Initialize storage
    storage = SchemaStorage()
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Basic Info", "🏷️ Fields", "✅ Validation", "👁️ Preview"])
    
    with tab1:
        render_basic_info_tab(storage)
    
    with tab2:
        st.info("Field management coming soon...")
    
    with tab3:
        st.info("Validation builder coming soon...")
    
    with tab4:
        st.info("Schema preview coming soon...")

def render_basic_info_tab(storage: SchemaStorage):
    """Basic schema information form"""
    st.subheader("Schema Information")
    
    # Form inputs
    schema_name = st.text_input("Schema Name", placeholder="e.g., National ID Card")
    schema_description = st.text_area("Description", placeholder="Describe this document type...")
    schema_category = st.selectbox("Category", ["Government", "Business", "Personal", "Custom"])
    
    # Simple create button
    if st.button("Create Schema", type="primary"):
        if schema_name:
            schema_id = schema_name.lower().replace(" ", "_")
            schema_data = {
                "id": schema_id,
                "name": schema_name,
                "description": schema_description,
                "category": schema_category,
                "version": "v1.0.0",
                "is_active": True,
                "fields": {},
                "validation_rules": []
            }
            
            if storage.save_schema(schema_id, schema_data):
                st.success(f"✅ Schema '{schema_name}' created successfully!")
            else:
                st.error("❌ Failed to create schema")
        else:
            st.error("Schema name is required")
    
    # List existing schemas
    st.subheader("Existing Schemas")
    schemas = storage.list_schemas()
    
    if schemas:
        for schema in schemas:
            with st.expander(f"{schema['name']} ({schema['category']})"):
                st.write(f"**ID:** {schema['id']}")
                st.write(f"**Version:** {schema['version']}")
                st.write(f"**Updated:** {schema['updated_date']}")
    else:
        st.info("No schemas created yet. Create your first schema above!")
```

### 3. Integrate with Main App

Update your `app.py` to add navigation:

```python
# Add this after your existing imports
try:
    from schema_management.schema_builder import render_schema_management_page
    SCHEMA_MANAGEMENT_AVAILABLE = True
except ImportError:
    SCHEMA_MANAGEMENT_AVAILABLE = False

# Add navigation in your sidebar (before existing content)
with st.sidebar:
    if SCHEMA_MANAGEMENT_AVAILABLE:
        page = st.selectbox(
            "📍 Navigate",
            ["📊 Document Extraction", "🏗️ Schema Management"],
            index=0
        )
    else:
        page = "📊 Document Extraction"
        st.info("Schema Management: Install dependencies to enable")

# Add page routing (replace your main content area)
if page == "🏗️ Schema Management" and SCHEMA_MANAGEMENT_AVAILABLE:
    render_schema_management_page()
else:
    # Your existing document extraction interface goes here
    st.title("AI Document Data Extractor")
    # ... rest of your existing app.py content
```

## Testing the Implementation (5 minutes)

### 1. Run the Application

```bash
streamlit run app.py
```

### 2. Test Basic Functionality

1. **Navigate to Schema Management**: Use the sidebar navigation
2. **Create a Test Schema**:
   - Name: "Test Document"
   - Description: "A test schema for validation"
   - Category: "Custom"
   - Click "Create Schema"
3. **Verify Storage**: Check that `data/schemas/test_document_v1.0.0.json` was created
4. **View in List**: Confirm the schema appears in the "Existing Schemas" section

### 3. Validate File Structure

```bash
# Check created files
ls -la data/schemas/
ls -la schema_management/

# Verify JSON content
cat data/schemas/test_document_v1.0.0.json
```

Expected JSON structure:
```json
{
  "id": "test_document",
  "name": "Test Document",
  "description": "A test schema for validation",
  "category": "Custom",
  "version": "v1.0.0",
  "is_active": true,
  "fields": {},
  "validation_rules": [],
  "updated_date": "2025-09-12T..."
}
```

## Integration Test (5 minutes)

### Test Schema Integration with Extraction

Update your document type selector in the extraction interface to include custom schemas:

```python
# In your extraction interface, replace the document type selector
def get_available_document_types():
    # Existing built-in types
    built_in_types = {
        "national_id": {"name": "National ID", "category": "Government"},
        "passport": {"name": "Passport", "category": "Government"}
        # ... your existing types
    }
    
    # Add custom schemas
    try:
        from schema_management.schema_storage import SchemaStorage
        storage = SchemaStorage()
        custom_schemas = storage.list_schemas()
        
        for schema in custom_schemas:
            built_in_types[schema["id"]] = {
                "name": schema["name"],
                "category": schema["category"]
            }
    except Exception as e:
        st.warning(f"Custom schemas unavailable: {e}")
    
    return built_in_types

# Use in your document type selector
document_types = get_available_document_types()
selected_type = st.selectbox("Document Type", list(document_types.keys()))
```

## Troubleshooting

### Common Issues

**Import Error for streamlit-elements**:
```bash
pip install streamlit-elements>=0.1.0
# If still failing, try:
pip install --upgrade streamlit-elements
```

**Database Permission Error**:
```bash
# Ensure write permissions
chmod 755 data/
chmod 644 data/schema_metadata.db
```

**Module Import Error**:
```bash
# Ensure __init__.py exists
touch schema_management/__init__.py
```

### Verify Installation

Run this test script to verify everything is working:

```python
# test_quickstart.py
import json
from schema_management.schema_storage import SchemaStorage

def test_basic_functionality():
    storage = SchemaStorage("test_data")
    
    # Test save
    test_schema = {
        "id": "quickstart_test",
        "name": "Quickstart Test",
        "version": "v1.0.0",
        "fields": {}
    }
    
    assert storage.save_schema("quickstart_test", test_schema)
    print("✅ Save test passed")
    
    # Test load
    loaded = storage.load_schema("quickstart_test")
    assert loaded is not None
    assert loaded["name"] == "Quickstart Test"
    print("✅ Load test passed")
    
    # Test list
    schemas = storage.list_schemas()
    assert len(schemas) >= 1
    print("✅ List test passed")
    
    print("🎉 All quickstart tests passed!")

if __name__ == "__main__":
    test_basic_functionality()
```

```bash
python test_quickstart.py
```

## Next Steps

After completing this quickstart:

1. **Run Contract Tests**: Execute the contract tests to guide implementation
2. **Implement Field Management**: Add drag-drop field builder
3. **Add Validation Builder**: Implement validation rule interface
4. **Enhanced Preview**: Add real-time schema preview
5. **Import/Export**: Add schema sharing capabilities

## Expected Outcome

After completing this quickstart, you should have:

- ✅ Schema Management tab in your Streamlit app
- ✅ Basic schema creation interface
- ✅ File-based schema storage working
- ✅ Custom schemas appearing in document type selector
- ✅ Foundation for implementing advanced features

The quickstart provides a minimal but functional schema management system that integrates seamlessly with your existing document extraction workflow.