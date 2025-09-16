"""
T029: GeneratedSchemaStorage
Persistence layer for GeneratedSchema models with integration to existing schema system
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..models.generated_schema import GeneratedSchema


class GeneratedSchemaStorage:
    """Storage service for AI-generated schema persistence and management."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize storage with database connection"""
        self.db_path = db_path or "data/app_database.db"
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Ensure database and tables exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Check if generated_schemas table exists
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='generated_schemas'
            """)

            if not cursor.fetchone():
                # Load and execute schema extensions
                schema_file = Path(__file__).parent / "ai_schema_extensions.sql"
                if schema_file.exists():
                    with open(schema_file) as f:
                        conn.executescript(f.read())

    def save(self, schema: GeneratedSchema) -> str:
        """Save generated schema to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO generated_schemas (
                    id, name, description, fields, source_document_id,
                    analysis_result_id, generation_method, generated_timestamp,
                    ai_model_used, generation_confidence, total_fields_generated,
                    high_confidence_fields, user_modified_fields, validation_status,
                    user_review_status, review_notes, last_modified_by,
                    accuracy_feedback, suggested_improvements, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                schema.id,
                schema.name,
                schema.description,
                json.dumps(schema.fields),
                schema.source_document_id,
                schema.analysis_result_id,
                schema.generation_method,
                schema.generated_timestamp.isoformat(),
                schema.ai_model_used,
                schema.generation_confidence,
                schema.total_fields_generated,
                schema.high_confidence_fields,
                json.dumps(schema.user_modified_fields),
                schema.validation_status,
                schema.user_review_status,
                schema.review_notes,
                schema.last_modified_by,
                json.dumps(schema.accuracy_feedback) if schema.accuracy_feedback else None,
                json.dumps(schema.suggested_improvements),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        return schema.id

    def get_by_id(self, schema_id: str) -> Optional[GeneratedSchema]:
        """Retrieve generated schema by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generated_schemas WHERE id = ?
            """, (schema_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_schema(row)

    def get_by_name(self, schema_name: str) -> Optional[GeneratedSchema]:
        """Retrieve generated schema by name"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generated_schemas
                WHERE name = ?
                ORDER BY generated_timestamp DESC
                LIMIT 1
            """, (schema_name,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_schema(row)

    def get_by_source_document(self, document_id: str) -> List[GeneratedSchema]:
        """Get all schemas generated from a specific document"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generated_schemas
                WHERE source_document_id = ?
                ORDER BY generated_timestamp DESC
            """, (document_id,))

            return [self._row_to_schema(row) for row in cursor.fetchall()]

    def get_by_analysis_result(self, analysis_result_id: str) -> List[GeneratedSchema]:
        """Get all schemas generated from a specific analysis result"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generated_schemas
                WHERE analysis_result_id = ?
                ORDER BY generated_timestamp DESC
            """, (analysis_result_id,))

            return [self._row_to_schema(row) for row in cursor.fetchall()]

    def get_by_review_status(self, status: str) -> List[GeneratedSchema]:
        """Get schemas by user review status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generated_schemas
                WHERE user_review_status = ?
                ORDER BY generated_timestamp DESC
            """, (status,))

            return [self._row_to_schema(row) for row in cursor.fetchall()]

    def get_production_ready(self) -> List[GeneratedSchema]:
        """Get schemas ready for production use"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generated_schemas
                WHERE user_review_status = 'approved'
                  AND validation_status = 'complete'
                  AND generation_confidence > 0.7
                ORDER BY generation_confidence DESC, generated_timestamp DESC
            """, ())

            return [self._row_to_schema(row) for row in cursor.fetchall()]

    def get_requiring_review(self) -> List[GeneratedSchema]:
        """Get schemas requiring user review"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generated_schemas
                WHERE user_review_status IN ('pending', 'in_progress')
                   OR generation_confidence < 0.6
                ORDER BY generation_confidence ASC, generated_timestamp DESC
            """, ())

            return [self._row_to_schema(row) for row in cursor.fetchall()]

    def get_recent(self, limit: int = 50) -> List[GeneratedSchema]:
        """Get recent generated schemas"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generated_schemas
                ORDER BY generated_timestamp DESC
                LIMIT ?
            """, (limit,))

            return [self._row_to_schema(row) for row in cursor.fetchall()]

    def get_by_ai_model(self, model_name: str) -> List[GeneratedSchema]:
        """Get schemas generated by specific AI model"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generated_schemas
                WHERE ai_model_used = ?
                ORDER BY generated_timestamp DESC
            """, (model_name,))

            return [self._row_to_schema(row) for row in cursor.fetchall()]

    def search_by_name_pattern(self, pattern: str) -> List[GeneratedSchema]:
        """Search schemas by name pattern"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generated_schemas
                WHERE name LIKE ?
                ORDER BY generated_timestamp DESC
            """, (f"%{pattern}%",))

            return [self._row_to_schema(row) for row in cursor.fetchall()]

    def update_review_status(self, schema_id: str, status: str, notes: Optional[str] = None):
        """Update schema review status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE generated_schemas
                SET user_review_status = ?, review_notes = ?,
                    last_modified_by = 'user', updated_at = ?
                WHERE id = ?
            """, (status, notes, datetime.now().isoformat(), schema_id))

    def update_validation_status(self, schema_id: str, status: str):
        """Update schema validation status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE generated_schemas
                SET validation_status = ?, updated_at = ?
                WHERE id = ?
            """, (status, datetime.now().isoformat(), schema_id))

    def add_user_modification(self, schema_id: str, field_name: str):
        """Track user modification of a field"""
        schema = self.get_by_id(schema_id)
        if schema:
            if field_name not in schema.user_modified_fields:
                schema.user_modified_fields.append(field_name)
                schema.last_modified_by = 'user'

                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE generated_schemas
                        SET user_modified_fields = ?, last_modified_by = 'user', updated_at = ?
                        WHERE id = ?
                    """, (json.dumps(schema.user_modified_fields), datetime.now().isoformat(), schema_id))

    def update_accuracy_feedback(self, schema_id: str, field_name: str, accuracy_score: float):
        """Update accuracy feedback for a field"""
        schema = self.get_by_id(schema_id)
        if schema:
            if schema.accuracy_feedback is None:
                schema.accuracy_feedback = {}

            schema.accuracy_feedback[field_name] = accuracy_score

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE generated_schemas
                    SET accuracy_feedback = ?, updated_at = ?
                    WHERE id = ?
                """, (json.dumps(schema.accuracy_feedback), datetime.now().isoformat(), schema_id))

    def add_improvement_suggestion(self, schema_id: str, suggestion: str):
        """Add improvement suggestion to schema"""
        schema = self.get_by_id(schema_id)
        if schema and suggestion not in schema.suggested_improvements:
            schema.suggested_improvements.append(suggestion)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE generated_schemas
                    SET suggested_improvements = ?, updated_at = ?
                    WHERE id = ?
                """, (json.dumps(schema.suggested_improvements), datetime.now().isoformat(), schema_id))

    def delete(self, schema_id: str) -> bool:
        """Delete generated schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM generated_schemas WHERE id = ?
            """, (schema_id,))

            return cursor.rowcount > 0

    def export_to_standard_schemas(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """Export generated schema to standard schema format for compatibility"""
        schema = self.get_by_id(schema_id)
        if not schema:
            return None

        return schema.convert_to_standard_schema()

    def import_from_standard_schema(self, standard_schema: Dict[str, Any], source_document_id: str = "") -> GeneratedSchema:
        """Import from standard schema format"""
        import uuid

        # Extract generation metadata if present
        generation_metadata = standard_schema.get('generation_metadata', {})

        schema = GeneratedSchema(
            id=standard_schema.get('id', str(uuid.uuid4())),
            name=standard_schema['name'],
            description=standard_schema.get('description', ''),
            fields=standard_schema.get('fields', {}),
            source_document_id=generation_metadata.get('source_document_id', source_document_id),
            analysis_result_id=generation_metadata.get('analysis_result_id', ''),
            generation_method='imported_from_standard',
            ai_model_used=generation_metadata.get('ai_model_used', ''),
            generation_confidence=generation_metadata.get('generation_confidence', 0.8),
            total_fields_generated=len(standard_schema.get('fields', {}))
        )

        # Save and return
        self.save(schema)
        return schema

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total schemas
            cursor.execute("SELECT COUNT(*) FROM generated_schemas")
            total_schemas = cursor.fetchone()[0]

            # By review status
            cursor.execute("""
                SELECT user_review_status, COUNT(*)
                FROM generated_schemas
                GROUP BY user_review_status
            """)
            review_status_counts = dict(cursor.fetchall())

            # By generation method
            cursor.execute("""
                SELECT generation_method, COUNT(*)
                FROM generated_schemas
                GROUP BY generation_method
            """)
            method_counts = dict(cursor.fetchall())

            # By AI model
            cursor.execute("""
                SELECT ai_model_used, COUNT(*)
                FROM generated_schemas
                WHERE ai_model_used != ''
                GROUP BY ai_model_used
            """)
            model_counts = dict(cursor.fetchall())

            # Average confidence by model
            cursor.execute("""
                SELECT ai_model_used, AVG(generation_confidence)
                FROM generated_schemas
                WHERE ai_model_used != ''
                GROUP BY ai_model_used
            """)
            avg_confidence_by_model = dict(cursor.fetchall())

            # Production ready count
            cursor.execute("""
                SELECT COUNT(*) FROM generated_schemas
                WHERE user_review_status = 'approved'
                  AND validation_status = 'complete'
                  AND generation_confidence > 0.7
            """)
            production_ready = cursor.fetchone()[0]

            # User modification stats
            cursor.execute("""
                SELECT AVG(json_array_length(user_modified_fields))
                FROM generated_schemas
                WHERE user_modified_fields != '[]'
            """)
            avg_user_modifications = cursor.fetchone()[0] or 0

            return {
                'total_schemas': total_schemas,
                'review_status_distribution': review_status_counts,
                'generation_method_distribution': method_counts,
                'ai_model_distribution': model_counts,
                'average_confidence_by_model': avg_confidence_by_model,
                'production_ready_schemas': production_ready,
                'average_user_modifications': avg_user_modifications
            }

    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get quality metrics for generated schemas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Confidence distribution
            cursor.execute("""
                SELECT
                    CASE
                        WHEN generation_confidence >= 0.8 THEN 'high'
                        WHEN generation_confidence >= 0.6 THEN 'medium'
                        ELSE 'low'
                    END as confidence_level,
                    COUNT(*)
                FROM generated_schemas
                GROUP BY confidence_level
            """)
            confidence_distribution = dict(cursor.fetchall())

            # Average accuracy by confidence level
            cursor.execute("""
                SELECT
                    CASE
                        WHEN generation_confidence >= 0.8 THEN 'high'
                        WHEN generation_confidence >= 0.6 THEN 'medium'
                        ELSE 'low'
                    END as confidence_level,
                    AVG(generation_confidence) as avg_confidence
                FROM generated_schemas
                GROUP BY confidence_level
            """)
            avg_confidence_by_level = dict(cursor.fetchall())

            # User review success rate
            cursor.execute("""
                SELECT
                    COUNT(CASE WHEN user_review_status = 'approved' THEN 1 END) * 100.0 / COUNT(*) as approval_rate
                FROM generated_schemas
                WHERE user_review_status IN ('approved', 'reviewed')
            """)
            approval_rate = cursor.fetchone()[0] or 0

            return {
                'confidence_distribution': confidence_distribution,
                'average_confidence_by_level': avg_confidence_by_level,
                'user_approval_rate': approval_rate
            }

    def cleanup_old_drafts(self, days_old: int = 7) -> int:
        """Clean up old draft schemas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM generated_schemas
                WHERE generated_timestamp < datetime('now', '-{} days')
                AND user_review_status = 'pending'
                AND generation_confidence < 0.5
            """.format(days_old))

            return cursor.rowcount

    def _row_to_schema(self, row: sqlite3.Row) -> GeneratedSchema:
        """Convert database row to GeneratedSchema model"""
        fields = {}
        if row['fields']:
            try:
                fields = json.loads(row['fields'])
            except json.JSONDecodeError:
                fields = {}

        user_modified_fields = []
        if row['user_modified_fields']:
            try:
                user_modified_fields = json.loads(row['user_modified_fields'])
            except json.JSONDecodeError:
                user_modified_fields = []

        accuracy_feedback = None
        if row['accuracy_feedback']:
            try:
                accuracy_feedback = json.loads(row['accuracy_feedback'])
            except json.JSONDecodeError:
                accuracy_feedback = {}

        suggested_improvements = []
        if row['suggested_improvements']:
            try:
                suggested_improvements = json.loads(row['suggested_improvements'])
            except json.JSONDecodeError:
                suggested_improvements = []

        return GeneratedSchema(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            fields=fields,
            source_document_id=row['source_document_id'],
            analysis_result_id=row['analysis_result_id'],
            generation_method=row['generation_method'],
            generated_timestamp=datetime.fromisoformat(row['generated_timestamp']),
            ai_model_used=row['ai_model_used'],
            generation_confidence=row['generation_confidence'],
            total_fields_generated=row['total_fields_generated'],
            high_confidence_fields=row['high_confidence_fields'],
            user_modified_fields=user_modified_fields,
            validation_status=row['validation_status'],
            user_review_status=row['user_review_status'],
            review_notes=row['review_notes'],
            last_modified_by=row['last_modified_by'],
            accuracy_feedback=accuracy_feedback,
            suggested_improvements=suggested_improvements
        )

    def exists(self, schema_id: str) -> bool:
        """Check if schema exists"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM generated_schemas WHERE id = ?", (schema_id,))
            return cursor.fetchone() is not None

    def get_schema_versions(self, schema_name: str) -> List[GeneratedSchema]:
        """Get all versions of a schema by name"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generated_schemas
                WHERE name = ?
                ORDER BY generated_timestamp DESC
            """, (schema_name,))

            return [self._row_to_schema(row) for row in cursor.fetchall()]