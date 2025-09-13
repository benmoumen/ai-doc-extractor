"""
Hybrid storage manager implementation.
Based on data-model.md specifications for JSON+SQLite hybrid storage.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import logging
import threading
from contextlib import contextmanager

from ..models.schema import Schema, SchemaStatus
from ..models.field import Field
from ..models.validation_rule import ValidationRule
from ..models.templates import FieldTemplate, SchemaTemplate, TemplateLibrary


logger = logging.getLogger(__name__)


class SchemaStorageError(Exception):
    """Custom exception for schema storage operations"""
    pass


class SchemaStorage:
    """
    Hybrid storage manager for schema data
    
    Implements the hybrid JSON+SQLite storage strategy:
    - SQLite: Schema metadata, versioning, usage tracking
    - JSON: Complete schema definitions with fields and validation rules
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize storage manager
        
        Args:
            data_dir: Base directory for storage (contains schemas/, db/, templates/)
        """
        self.data_dir = Path(data_dir)
        self.schemas_dir = self.data_dir / "schemas"
        self.templates_dir = self.data_dir / "templates"
        self.db_path = self.data_dir / "db" / "schema_metadata.db"
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Initialize database
        self._init_database()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.schemas_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        (self.data_dir / "db").mkdir(exist_ok=True)
    
    def _init_database(self) -> None:
        """Initialize SQLite database with required tables"""
        with self._get_db_connection() as conn:
            # Schema metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_metadata (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    version TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    status TEXT DEFAULT 'draft',
                    created_date TEXT,
                    updated_date TEXT,
                    created_by TEXT DEFAULT 'system',
                    usage_count INTEGER DEFAULT 0,
                    migration_notes TEXT,
                    backward_compatible BOOLEAN DEFAULT 1
                )
            """)
            
            # Schema versions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schema_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    changes TEXT,
                    created_date TEXT,
                    created_by TEXT,
                    migration_notes TEXT,
                    UNIQUE(schema_id, version)
                )
            """)
            
            # Template metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS template_metadata (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    template_type TEXT NOT NULL, -- 'field' or 'schema'
                    category TEXT,
                    usage_count INTEGER DEFAULT 0,
                    is_system_template BOOLEAN DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    created_date TEXT,
                    updated_date TEXT,
                    created_by TEXT DEFAULT 'system'
                )
            """)
            
            # Usage tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schema_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL, -- 'extract', 'validate', 'edit', etc.
                    user_id TEXT,
                    metadata TEXT -- JSON for additional data
                )
            """)
            
            # Audit trail table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schema_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    details TEXT -- JSON for additional details
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise SchemaStorageError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def _get_schema_file_path(self, schema_id: str, version: str = None) -> Path:
        """Get file path for schema JSON storage"""
        if version:
            filename = f"{schema_id}_v{version.replace('.', '_')}.json"
        else:
            filename = f"{schema_id}.json"
        return self.schemas_dir / filename
    
    def _get_template_file_path(self, template_id: str, template_type: str) -> Path:
        """Get file path for template JSON storage"""
        filename = f"{template_type}_{template_id}.json"
        return self.templates_dir / filename
    
    def save_schema(self, schema_id: str, schema_data: Union[Schema, Dict[str, Any]]) -> bool:
        """
        Save schema with hybrid storage approach
        
        Args:
            schema_id: Unique schema identifier
            schema_data: Schema object or dictionary
            
        Returns:
            bool: True if saved successfully
        """
        with self._lock:
            try:
                # Convert to Schema object if needed
                if isinstance(schema_data, dict):
                    schema = Schema.from_dict(schema_data)
                else:
                    schema = schema_data
                
                # Validate schema structure
                if not schema.is_valid():
                    errors = schema.validate_structure()
                    raise SchemaStorageError(f"Invalid schema structure: {errors}")
                
                # Update timestamps
                if schema.created_date is None:
                    schema.created_date = datetime.now()
                schema.updated_date = datetime.now()
                
                # Save to JSON file
                schema_file = self._get_schema_file_path(schema_id)
                with open(schema_file, 'w', encoding='utf-8') as f:
                    json.dump(schema.to_dict(), f, indent=2, ensure_ascii=False)
                
                # Save metadata to database
                with self._get_db_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO schema_metadata 
                        (id, name, description, category, version, is_active, status,
                         created_date, updated_date, created_by, usage_count, 
                         migration_notes, backward_compatible)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        schema.id, schema.name, schema.description, schema.category,
                        schema.version, schema.is_active, schema.status.value,
                        schema.created_date.isoformat(), schema.updated_date.isoformat(),
                        schema.created_by, schema.usage_count, schema.migration_notes,
                        schema.backward_compatible
                    ))
                    
                    # Add version record
                    conn.execute("""
                        INSERT OR IGNORE INTO schema_versions 
                        (schema_id, version, created_date, created_by, migration_notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        schema.id, schema.version, schema.updated_date.isoformat(),
                        schema.created_by, schema.migration_notes
                    ))
                    
                    conn.commit()
                
                logger.info(f"Schema {schema_id} saved successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to save schema {schema_id}: {e}")
                raise SchemaStorageError(f"Failed to save schema: {e}")
    
    def load_schema(self, schema_id: str, version: str = None) -> Optional[Schema]:
        """
        Load schema from storage
        
        Args:
            schema_id: Schema identifier
            version: Specific version to load (latest if None)
            
        Returns:
            Schema object or None if not found
        """
        with self._lock:
            try:
                # Determine which file to load
                if version:
                    schema_file = self._get_schema_file_path(schema_id, version)
                else:
                    schema_file = self._get_schema_file_path(schema_id)
                
                if not schema_file.exists():
                    logger.warning(f"Schema file not found: {schema_file}")
                    return None
                
                # Load from JSON file
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
                
                schema = Schema.from_dict(schema_data)
                logger.info(f"Schema {schema_id} loaded successfully")
                return schema
                
            except Exception as e:
                logger.error(f"Failed to load schema {schema_id}: {e}")
                return None
    
    def delete_schema(self, schema_id: str) -> bool:
        """
        Delete schema and its metadata
        
        Args:
            schema_id: Schema identifier
            
        Returns:
            bool: True if deleted successfully
        """
        with self._lock:
            try:
                # Delete JSON file
                schema_file = self._get_schema_file_path(schema_id)
                if schema_file.exists():
                    schema_file.unlink()
                
                # Delete from database
                with self._get_db_connection() as conn:
                    conn.execute("DELETE FROM schema_metadata WHERE id = ?", (schema_id,))
                    conn.execute("DELETE FROM schema_versions WHERE schema_id = ?", (schema_id,))
                    conn.execute("DELETE FROM usage_log WHERE schema_id = ?", (schema_id,))
                    conn.execute("DELETE FROM audit_trail WHERE schema_id = ?", (schema_id,))
                    conn.commit()
                
                logger.info(f"Schema {schema_id} deleted successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete schema {schema_id}: {e}")
                return False
    
    def list_schemas(self, category: str = None, status: str = None, 
                    active_only: bool = True) -> List[Dict[str, Any]]:
        """
        List schemas with optional filtering
        
        Args:
            category: Filter by category
            status: Filter by status
            active_only: Only return active schemas
            
        Returns:
            List of schema metadata dictionaries
        """
        with self._lock:
            try:
                with self._get_db_connection() as conn:
                    query = "SELECT * FROM schema_metadata WHERE 1=1"
                    params = []
                    
                    if category:
                        query += " AND category = ?"
                        params.append(category)
                    
                    if status:
                        query += " AND status = ?"
                        params.append(status)
                    
                    if active_only:
                        query += " AND is_active = 1"
                    
                    query += " ORDER BY updated_date DESC"
                    
                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()
                    
                    return [dict(row) for row in rows]
                    
            except Exception as e:
                logger.error(f"Failed to list schemas: {e}")
                return []
    
    def get_schema_versions(self, schema_id: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a schema
        
        Args:
            schema_id: Schema identifier
            
        Returns:
            List of version metadata
        """
        with self._lock:
            try:
                with self._get_db_connection() as conn:
                    cursor = conn.execute("""
                        SELECT * FROM schema_versions 
                        WHERE schema_id = ? 
                        ORDER BY created_date DESC
                    """, (schema_id,))
                    
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                    
            except Exception as e:
                logger.error(f"Failed to get versions for schema {schema_id}: {e}")
                return []
    
    def record_schema_usage(self, schema_id: str, operation: str = "extract", 
                           user_id: str = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Record schema usage for analytics
        
        Args:
            schema_id: Schema identifier
            operation: Type of operation performed
            user_id: User performing the operation
            metadata: Additional operation metadata
            
        Returns:
            bool: True if recorded successfully
        """
        with self._lock:
            try:
                with self._get_db_connection() as conn:
                    # Record usage log
                    conn.execute("""
                        INSERT INTO usage_log 
                        (schema_id, timestamp, operation, user_id, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        schema_id, datetime.now().isoformat(), operation,
                        user_id, json.dumps(metadata) if metadata else None
                    ))
                    
                    # Increment usage counter
                    conn.execute("""
                        UPDATE schema_metadata 
                        SET usage_count = usage_count + 1,
                            updated_date = ?
                        WHERE id = ?
                    """, (datetime.now().isoformat(), schema_id))
                    
                    conn.commit()
                    return True
                    
            except Exception as e:
                logger.error(f"Failed to record usage for schema {schema_id}: {e}")
                return False
    
    def get_usage_analytics(self, schema_id: str = None, 
                           days: int = 30) -> Dict[str, Any]:
        """
        Get usage analytics for schemas
        
        Args:
            schema_id: Specific schema (all if None)
            days: Number of days to analyze
            
        Returns:
            Analytics data dictionary
        """
        with self._lock:
            try:
                with self._get_db_connection() as conn:
                    # Get usage data
                    query = """
                        SELECT schema_id, operation, COUNT(*) as count,
                               DATE(timestamp) as date
                        FROM usage_log 
                        WHERE timestamp > datetime('now', '-{} days')
                    """.format(days)
                    
                    params = []
                    if schema_id:
                        query += " AND schema_id = ?"
                        params.append(schema_id)
                    
                    query += " GROUP BY schema_id, operation, DATE(timestamp)"
                    
                    cursor = conn.execute(query, params)
                    usage_data = [dict(row) for row in cursor.fetchall()]
                    
                    # Get schema metadata
                    if schema_id:
                        metadata_query = "SELECT * FROM schema_metadata WHERE id = ?"
                        metadata_params = [schema_id]
                    else:
                        metadata_query = "SELECT * FROM schema_metadata"
                        metadata_params = []
                    
                    cursor = conn.execute(metadata_query, metadata_params)
                    schema_metadata = [dict(row) for row in cursor.fetchall()]
                    
                    return {
                        "usage_data": usage_data,
                        "schema_metadata": schema_metadata,
                        "analysis_period_days": days
                    }
                    
            except Exception as e:
                logger.error(f"Failed to get usage analytics: {e}")
                return {}
    
    def save_field_template(self, template: FieldTemplate) -> bool:
        """Save field template"""
        with self._lock:
            try:
                # Save to JSON file
                template_file = self._get_template_file_path(template.id, "field")
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)
                
                # Save metadata to database
                with self._get_db_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO template_metadata 
                        (id, name, template_type, category, usage_count, 
                         is_system_template, status, created_date, updated_date, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        template.id, template.name, "field", template.category,
                        template.usage_count, template.is_system_template,
                        template.status.value, template.created_date.isoformat(),
                        template.updated_date.isoformat(), template.created_by
                    ))
                    conn.commit()
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to save field template {template.id}: {e}")
                return False
    
    def load_field_template(self, template_id: str) -> Optional[FieldTemplate]:
        """Load field template"""
        with self._lock:
            try:
                template_file = self._get_template_file_path(template_id, "field")
                if not template_file.exists():
                    return None
                
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                return FieldTemplate.from_dict(template_data)
                
            except Exception as e:
                logger.error(f"Failed to load field template {template_id}: {e}")
                return None
    
    def save_schema_template(self, template: SchemaTemplate) -> bool:
        """Save schema template"""
        with self._lock:
            try:
                # Save to JSON file
                template_file = self._get_template_file_path(template.id, "schema")
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)
                
                # Save metadata to database
                with self._get_db_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO template_metadata 
                        (id, name, template_type, category, usage_count, 
                         is_system_template, status, created_date, updated_date, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        template.id, template.name, "schema", template.category.value,
                        template.usage_count, template.is_system_template,
                        template.status.value, template.created_date.isoformat(),
                        template.updated_date.isoformat(), template.created_by
                    ))
                    conn.commit()
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to save schema template {template.id}: {e}")
                return False
    
    def load_schema_template(self, template_id: str) -> Optional[SchemaTemplate]:
        """Load schema template"""
        with self._lock:
            try:
                template_file = self._get_template_file_path(template_id, "schema")
                if not template_file.exists():
                    return None
                
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                return SchemaTemplate.from_dict(template_data)
                
            except Exception as e:
                logger.error(f"Failed to load schema template {template_id}: {e}")
                return None
    
    def list_templates(self, template_type: str = None) -> List[Dict[str, Any]]:
        """List templates"""
        with self._lock:
            try:
                with self._get_db_connection() as conn:
                    query = "SELECT * FROM template_metadata WHERE 1=1"
                    params = []
                    
                    if template_type:
                        query += " AND template_type = ?"
                        params.append(template_type)
                    
                    query += " ORDER BY usage_count DESC, updated_date DESC"
                    
                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()
                    
                    return [dict(row) for row in rows]
                    
            except Exception as e:
                logger.error(f"Failed to list templates: {e}")
                return []
    
    def add_audit_log(self, schema_id: str, action: str, old_value: Any = None,
                     new_value: Any = None, user_id: str = None, 
                     details: Dict[str, Any] = None) -> bool:
        """Add audit trail entry"""
        with self._lock:
            try:
                with self._get_db_connection() as conn:
                    conn.execute("""
                        INSERT INTO audit_trail 
                        (schema_id, action, old_value, new_value, timestamp, user_id, details)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        schema_id, action,
                        json.dumps(old_value) if old_value is not None else None,
                        json.dumps(new_value) if new_value is not None else None,
                        datetime.now().isoformat(), user_id,
                        json.dumps(details) if details else None
                    ))
                    conn.commit()
                    return True
                    
            except Exception as e:
                logger.error(f"Failed to add audit log: {e}")
                return False
    
    def get_audit_trail(self, schema_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit trail for schema"""
        with self._lock:
            try:
                with self._get_db_connection() as conn:
                    cursor = conn.execute("""
                        SELECT * FROM audit_trail 
                        WHERE schema_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (schema_id, limit))
                    
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                    
            except Exception as e:
                logger.error(f"Failed to get audit trail: {e}")
                return []
    
    def clear_all_schemas(self) -> bool:
        """Clear all schemas (for testing/reset)"""
        with self._lock:
            try:
                # Delete all JSON files
                for file_path in self.schemas_dir.glob("*.json"):
                    file_path.unlink()
                
                # Clear database tables
                with self._get_db_connection() as conn:
                    conn.execute("DELETE FROM schema_metadata")
                    conn.execute("DELETE FROM schema_versions")
                    conn.execute("DELETE FROM usage_log")
                    conn.execute("DELETE FROM audit_trail")
                    conn.commit()
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to clear schemas: {e}")
                return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        with self._lock:
            try:
                stats = {
                    "json_files": len(list(self.schemas_dir.glob("*.json"))),
                    "template_files": len(list(self.templates_dir.glob("*.json"))),
                    "db_size_bytes": os.path.getsize(self.db_path) if self.db_path.exists() else 0
                }
                
                with self._get_db_connection() as conn:
                    # Count database records
                    stats["total_schemas"] = conn.execute("SELECT COUNT(*) FROM schema_metadata").fetchone()[0]
                    stats["active_schemas"] = conn.execute("SELECT COUNT(*) FROM schema_metadata WHERE is_active = 1").fetchone()[0]
                    stats["total_versions"] = conn.execute("SELECT COUNT(*) FROM schema_versions").fetchone()[0]
                    stats["usage_records"] = conn.execute("SELECT COUNT(*) FROM usage_log").fetchone()[0]
                    stats["audit_records"] = conn.execute("SELECT COUNT(*) FROM audit_trail").fetchone()[0]
                    stats["templates"] = conn.execute("SELECT COUNT(*) FROM template_metadata").fetchone()[0]
                
                return stats
                
            except Exception as e:
                logger.error(f"Failed to get storage stats: {e}")
                return {}
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            with self._get_db_connection() as conn:
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            backup_conn = sqlite3.connect(backup_path)
            with self._get_db_connection() as conn:
                backup_conn.backup(conn)
            backup_conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False