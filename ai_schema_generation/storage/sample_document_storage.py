"""
T027: SampleDocumentStorage
Persistence layer for SampleDocument models with database operations
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..models.sample_document import SampleDocument


class SampleDocumentStorage:
    """Storage service for SampleDocument persistence and retrieval."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize storage with database connection"""
        self.db_path = db_path or "data/app_database.db"
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Ensure database and tables exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Check if sample_documents table exists
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='sample_documents'
            """)

            table_exists = cursor.fetchone()

            if not table_exists:
                # Load and execute schema extensions
                schema_file = Path(__file__).parent / "ai_schema_extensions.sql"
                if schema_file.exists():
                    with open(schema_file) as f:
                        conn.executescript(f.read())
            else:
                # Table exists, check for and add missing columns
                self._migrate_schema(conn)

    def _migrate_schema(self, conn):
        """Migrate existing database schema to include missing columns"""
        cursor = conn.cursor()

        # Get current table schema
        cursor.execute("PRAGMA table_info(sample_documents)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Define required columns with their SQL definitions
        required_columns = {
            'file_path': 'TEXT',
            'error_message': 'TEXT',
            'analysis_count': 'INTEGER DEFAULT 0',
            'page_count': 'INTEGER',
            'user_session_id': 'TEXT',
            'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP'
        }

        # Add missing columns
        for column_name, column_def in required_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE sample_documents ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Added missing column: {column_name}")
                except Exception as e:
                    print(f"⚠️  Failed to add column {column_name}: {e}")

        # Update existing rows to have proper timestamps if they're missing
        cursor.execute("""
            UPDATE sample_documents
            SET created_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL OR updated_at IS NULL
        """)

        conn.commit()

    def save(self, document: SampleDocument) -> str:
        """Save document to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sample_documents (
                    id, filename, file_type, file_size, file_path,
                    content_hash, upload_timestamp, processing_status,
                    metadata, error_message, analysis_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document.id,
                document.filename,
                document.file_type,
                document.file_size,
                document.file_path,
                document.content_hash,
                document.upload_timestamp.isoformat(),
                document.processing_status,
                json.dumps(document.metadata) if document.metadata else None,
                document.metadata.get('error_message'),
                document.analysis_count,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        return document.id

    def get_by_id(self, document_id: str) -> Optional[SampleDocument]:
        """Retrieve document by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sample_documents WHERE id = ?
            """, (document_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_document(row)

    def get_by_content_hash(self, content_hash: str) -> Optional[SampleDocument]:
        """Retrieve document by content hash"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sample_documents WHERE content_hash = ?
            """, (content_hash,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_document(row)

    def get_by_status(self, status: str) -> List[SampleDocument]:
        """Get documents by processing status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sample_documents
                WHERE processing_status = ?
                ORDER BY upload_timestamp DESC
            """, (status,))

            return [self._row_to_document(row) for row in cursor.fetchall()]

    def get_recent(self, limit: int = 50) -> List[SampleDocument]:
        """Get recent documents"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sample_documents
                ORDER BY upload_timestamp DESC
                LIMIT ?
            """, (limit,))

            return [self._row_to_document(row) for row in cursor.fetchall()]

    def get_by_file_type(self, file_type: str) -> List[SampleDocument]:
        """Get documents by file type"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sample_documents
                WHERE file_type = ?
                ORDER BY upload_timestamp DESC
            """, (file_type,))

            return [self._row_to_document(row) for row in cursor.fetchall()]

    def search_by_filename(self, filename_pattern: str) -> List[SampleDocument]:
        """Search documents by filename pattern"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sample_documents
                WHERE filename LIKE ?
                ORDER BY upload_timestamp DESC
            """, (f"%{filename_pattern}%",))

            return [self._row_to_document(row) for row in cursor.fetchall()]

    def update_status(self, document_id: str, status: str, error_message: Optional[str] = None):
        """Update document processing status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sample_documents
                SET processing_status = ?, error_message = ?, updated_at = ?
                WHERE id = ?
            """, (status, error_message, datetime.now().isoformat(), document_id))

    def increment_analysis_count(self, document_id: str):
        """Increment analysis count for document"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sample_documents
                SET analysis_count = analysis_count + 1, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), document_id))

    def update_metadata(self, document_id: str, metadata: Dict[str, Any]):
        """Update document metadata"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sample_documents
                SET metadata = ?, updated_at = ?
                WHERE id = ?
            """, (json.dumps(metadata), datetime.now().isoformat(), document_id))

    def delete(self, document_id: str) -> bool:
        """Delete document and related data"""
        with sqlite3.connect(self.db_path) as conn:
            # Delete related analysis results first
            conn.execute("""
                DELETE FROM ai_analysis_results
                WHERE sample_document_id = ?
            """, (document_id,))

            # Delete the document
            cursor = conn.execute("""
                DELETE FROM sample_documents WHERE id = ?
            """, (document_id,))

            return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total documents
            cursor.execute("SELECT COUNT(*) FROM sample_documents")
            total_documents = cursor.fetchone()[0]

            # By status
            cursor.execute("""
                SELECT processing_status, COUNT(*)
                FROM sample_documents
                GROUP BY processing_status
            """)
            status_counts = dict(cursor.fetchall())

            # By file type
            cursor.execute("""
                SELECT file_type, COUNT(*)
                FROM sample_documents
                GROUP BY file_type
            """)
            type_counts = dict(cursor.fetchall())

            # Total file size
            cursor.execute("SELECT SUM(file_size) FROM sample_documents")
            total_size = cursor.fetchone()[0] or 0

            # Recent activity (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM sample_documents
                WHERE upload_timestamp > datetime('now', '-1 day')
            """)
            recent_uploads = cursor.fetchone()[0]

            return {
                'total_documents': total_documents,
                'status_distribution': status_counts,
                'file_type_distribution': type_counts,
                'total_file_size_bytes': total_size,
                'recent_uploads_24h': recent_uploads
            }

    def cleanup_old_documents(self, days_old: int = 30) -> int:
        """Clean up old documents based on age"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM sample_documents
                WHERE upload_timestamp < datetime('now', '-{} days')
                AND processing_status IN ('completed', 'failed')
            """.format(days_old))

            return cursor.rowcount

    def get_duplicate_candidates(self) -> List[Dict[str, Any]]:
        """Find potential duplicate documents by content hash"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT content_hash, COUNT(*) as count,
                       GROUP_CONCAT(id) as document_ids,
                       GROUP_CONCAT(filename) as filenames
                FROM sample_documents
                GROUP BY content_hash
                HAVING COUNT(*) > 1
            """)

            duplicates = []
            for row in cursor.fetchall():
                duplicates.append({
                    'content_hash': row['content_hash'],
                    'count': row['count'],
                    'document_ids': row['document_ids'].split(','),
                    'filenames': row['filenames'].split(',')
                })

            return duplicates

    def _row_to_document(self, row: sqlite3.Row) -> SampleDocument:
        """Convert database row to SampleDocument model"""
        if row['metadata']:
            try:
                metadata = json.loads(row['metadata'])
            except json.JSONDecodeError:
                metadata = {}
        else:
            metadata = {}

        # Add error_message from database to metadata if it exists
        if row['error_message']:
            metadata['error_message'] = row['error_message']

        return SampleDocument(
            id=row['id'],
            filename=row['filename'],
            file_type=row['file_type'],
            file_size=row['file_size'],
            content_hash=row['content_hash'],
            upload_timestamp=datetime.fromisoformat(row['upload_timestamp']),
            processing_status=row['processing_status'],
            file_data=b'',  # File data loaded separately
            metadata=metadata,
            file_path=row['file_path'],
            analysis_count=row['analysis_count']
        )

    @staticmethod
    def calculate_content_hash(file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()

    def exists(self, document_id: str) -> bool:
        """Check if document exists"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM sample_documents WHERE id = ?", (document_id,))
            return cursor.fetchone() is not None

    def get_analysis_candidates(self, limit: int = 10) -> List[SampleDocument]:
        """Get documents ready for analysis"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sample_documents
                WHERE processing_status = 'uploaded'
                ORDER BY upload_timestamp ASC
                LIMIT ?
            """, (limit,))

            return [self._row_to_document(row) for row in cursor.fetchall()]