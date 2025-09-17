"""
Database service for persistent storage of schemas and application data
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager

from config import settings

logger = logging.getLogger(__name__)

class DatabaseService:
    """SQLite database service for schema storage"""

    def __init__(self, db_path: str = "data/schemas.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create schemas table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schemas (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT DEFAULT 'Other',
                    fields TEXT NOT NULL,  -- JSON string
                    metadata TEXT,         -- JSON string for additional data
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_schemas_category
                ON schemas(category)
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def save_schema(self, schema_id: str, schema_data: Dict[str, Any]) -> bool:
        """Save or update a schema"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Prepare data
                fields_json = json.dumps(schema_data.get("fields", {}))
                metadata_json = json.dumps({
                    "overall_confidence": schema_data.get("overall_confidence"),
                    "document_quality": schema_data.get("document_quality"),
                    "extraction_difficulty": schema_data.get("extraction_difficulty"),
                    "document_specific_notes": schema_data.get("document_specific_notes", []),
                    "quality_recommendations": schema_data.get("quality_recommendations", [])
                })

                # Insert or update
                cursor.execute("""
                    INSERT OR REPLACE INTO schemas
                    (id, name, description, category, fields, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    schema_id,
                    schema_data.get("name", "Unknown Schema"),
                    schema_data.get("description", ""),
                    schema_data.get("category", "Other"),
                    fields_json,
                    metadata_json
                ))

                conn.commit()
                logger.info(f"Schema saved: {schema_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to save schema {schema_id}: {e}")
            return False

    def get_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """Get a schema by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM schemas WHERE id = ?
                """, (schema_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                # Parse JSON fields
                fields = json.loads(row["fields"])
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}

                schema = {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "category": row["category"],
                    "fields": fields,
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }

                # Add metadata fields
                schema.update(metadata)

                return schema

        except Exception as e:
            logger.error(f"Failed to get schema {schema_id}: {e}")
            return None

    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get all schemas"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description, category,
                           fields, created_at, updated_at
                    FROM schemas
                    ORDER BY updated_at DESC
                """)

                schemas = {}
                for row in cursor.fetchall():
                    # Parse fields JSON to count fields
                    try:
                        fields = json.loads(row["fields"])
                        field_count = len(fields) if isinstance(fields, dict) else 0
                    except (json.JSONDecodeError, TypeError):
                        field_count = 0

                    schemas[row["id"]] = {
                        "id": row["id"],
                        "name": row["name"],
                        "description": row["description"],
                        "category": row["category"],
                        "field_count": field_count,
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"]
                    }

                return schemas

        except Exception as e:
            logger.error(f"Failed to get all schemas: {e}")
            return {}

    def delete_schema(self, schema_id: str) -> bool:
        """Delete a schema"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM schemas WHERE id = ?", (schema_id,))

                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Schema deleted: {schema_id}")
                    return True
                else:
                    logger.warning(f"Schema not found for deletion: {schema_id}")
                    return False

        except Exception as e:
            logger.error(f"Failed to delete schema {schema_id}: {e}")
            return False

    def get_schemas_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Get schemas by category"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description, category,
                           fields, created_at, updated_at
                    FROM schemas
                    WHERE category = ?
                    ORDER BY updated_at DESC
                """, (category,))

                schemas = {}
                for row in cursor.fetchall():
                    # Parse fields JSON to count fields
                    try:
                        fields = json.loads(row["fields"])
                        field_count = len(fields) if isinstance(fields, dict) else 0
                    except (json.JSONDecodeError, TypeError):
                        field_count = 0

                    schemas[row["id"]] = {
                        "id": row["id"],
                        "name": row["name"],
                        "description": row["description"],
                        "category": row["category"],
                        "field_count": field_count,
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"]
                    }

                return schemas

        except Exception as e:
            logger.error(f"Failed to get schemas by category {category}: {e}")
            return {}

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total schemas
                cursor.execute("SELECT COUNT(*) as total FROM schemas")
                total_schemas = cursor.fetchone()["total"]

                # Schemas by category
                cursor.execute("""
                    SELECT category, COUNT(*) as count
                    FROM schemas
                    GROUP BY category
                """)
                by_category = {row["category"]: row["count"] for row in cursor.fetchall()}

                return {
                    "total_schemas": total_schemas,
                    "by_category": by_category,
                    "database_path": str(self.db_path),
                    "database_size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                }

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}

# Global database service instance
db_service = DatabaseService()

def load_default_schemas():
    """Load default schemas into database"""
    # This can be expanded to load predefined schemas
    logger.info("Default schemas loading (none defined yet)")
    pass