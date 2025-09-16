"""
T028: AIAnalysisStorage
Persistence layer for AI analysis results with complex querying capabilities
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..models.analysis_result import AIAnalysisResult
from ..models.extracted_field import ExtractedField
from ..models.validation_rule_inference import ValidationRuleInference
from ..models.document_type_suggestion import DocumentTypeSuggestion


class AIAnalysisStorage:
    """Storage service for AI analysis results and related models."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize storage with database connection"""
        self.db_path = db_path or "data/app_database.db"
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Ensure database and tables exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Check if ai_analysis_results table exists
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='ai_analysis_results'
            """)

            if not cursor.fetchone():
                # Load and execute schema extensions
                schema_file = Path(__file__).parent / "ai_schema_extensions.sql"
                if schema_file.exists():
                    with open(schema_file) as f:
                        conn.executescript(f.read())

    # === AI Analysis Results ===

    def save_analysis_result(self, result: AIAnalysisResult) -> str:
        """Save analysis result to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO ai_analysis_results (
                    id, sample_document_id, model_used, analysis_timestamp,
                    detected_document_type, document_type_confidence,
                    total_fields_detected, high_confidence_fields,
                    processing_time, overall_quality_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.id,
                result.sample_document_id,
                result.model_used,
                result.analysis_timestamp.isoformat(),
                result.detected_document_type,
                result.document_type_confidence,
                result.total_fields_detected,
                result.high_confidence_fields,
                result.processing_time,
                result.overall_quality_score
            ))

        return result.id

    def get_analysis_result(self, result_id: str) -> Optional[AIAnalysisResult]:
        """Retrieve analysis result by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM ai_analysis_results WHERE id = ?
            """, (result_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_analysis_result(row)

    def get_analysis_results_for_document(self, document_id: str) -> List[AIAnalysisResult]:
        """Get all analysis results for a document"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM ai_analysis_results
                WHERE sample_document_id = ?
                ORDER BY analysis_timestamp DESC
            """, (document_id,))

            return [self._row_to_analysis_result(row) for row in cursor.fetchall()]

    def get_latest_analysis_for_document(self, document_id: str) -> Optional[AIAnalysisResult]:
        """Get most recent analysis result for a document"""
        results = self.get_analysis_results_for_document(document_id)
        return results[0] if results else None

    def get_analysis_results_by_model(self, model_name: str) -> List[AIAnalysisResult]:
        """Get analysis results by model used"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM ai_analysis_results
                WHERE model_used = ?
                ORDER BY analysis_timestamp DESC
            """, (model_name,))

            return [self._row_to_analysis_result(row) for row in cursor.fetchall()]

    def get_high_quality_analyses(self, min_quality_score: float = 0.8) -> List[AIAnalysisResult]:
        """Get high-quality analysis results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM ai_analysis_results
                WHERE overall_quality_score >= ?
                ORDER BY overall_quality_score DESC, analysis_timestamp DESC
            """, (min_quality_score,))

            return [self._row_to_analysis_result(row) for row in cursor.fetchall()]

    # === Extracted Fields ===

    def save_extracted_field(self, field: ExtractedField) -> str:
        """Save extracted field to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO extracted_fields (
                    id, analysis_result_id, detected_name, display_name,
                    field_type, source_text, visual_clarity_score,
                    label_confidence_score, value_confidence_score,
                    type_confidence_score, context_confidence_score,
                    overall_confidence_score, bounding_box, page_number,
                    context_description, is_required, has_validation_hints,
                    field_group, alternative_names, alternative_types,
                    extraction_method, requires_review, review_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                field.id,
                field.analysis_result_id,
                field.detected_name,
                field.display_name,
                field.field_type,
                field.source_text,
                field.visual_clarity_score,
                field.label_confidence_score,
                field.value_confidence_score,
                field.type_confidence_score,
                field.context_confidence_score,
                field.overall_confidence_score,
                json.dumps(field.bounding_box) if field.bounding_box else None,
                field.page_number,
                field.context_description,
                field.is_required,
                field.has_validation_hints,
                field.field_group,
                json.dumps(field.alternative_names),
                json.dumps(field.alternative_types),
                field.extraction_method,
                field.requires_review,
                field.review_reason
            ))

        return field.id

    def get_extracted_field(self, field_id: str) -> Optional[ExtractedField]:
        """Retrieve extracted field by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM extracted_fields WHERE id = ?
            """, (field_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_extracted_field(row)

    def get_fields_for_analysis(self, analysis_result_id: str) -> List[ExtractedField]:
        """Get all extracted fields for an analysis result"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM extracted_fields
                WHERE analysis_result_id = ?
                ORDER BY overall_confidence_score DESC, detected_name
            """, (analysis_result_id,))

            return [self._row_to_extracted_field(row) for row in cursor.fetchall()]

    def get_fields_requiring_review(self, analysis_result_id: str) -> List[ExtractedField]:
        """Get fields that require manual review"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM extracted_fields
                WHERE analysis_result_id = ? AND requires_review = 1
                ORDER BY overall_confidence_score ASC
            """, (analysis_result_id,))

            return [self._row_to_extracted_field(row) for row in cursor.fetchall()]

    def get_high_confidence_fields(self, analysis_result_id: str, min_confidence: float = 0.8) -> List[ExtractedField]:
        """Get high-confidence fields"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM extracted_fields
                WHERE analysis_result_id = ? AND overall_confidence_score >= ?
                ORDER BY overall_confidence_score DESC
            """, (analysis_result_id, min_confidence))

            return [self._row_to_extracted_field(row) for row in cursor.fetchall()]

    # === Validation Rule Inferences ===

    def save_validation_rule(self, rule: ValidationRuleInference) -> str:
        """Save validation rule inference to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO validation_rule_inferences (
                    id, extracted_field_id, rule_type, rule_value,
                    rule_description, confidence_score, sample_matches,
                    sample_non_matches, inference_method, is_recommended,
                    priority, alternative_rules
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule.id,
                rule.extracted_field_id,
                rule.rule_type,
                json.dumps(rule.rule_value),
                rule.rule_description,
                rule.confidence_score,
                json.dumps(rule.sample_matches),
                json.dumps(rule.sample_non_matches),
                rule.inference_method,
                rule.is_recommended,
                rule.priority,
                json.dumps(rule.alternative_rules)
            ))

        return rule.id

    def get_validation_rule(self, rule_id: str) -> Optional[ValidationRuleInference]:
        """Retrieve validation rule by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM validation_rule_inferences WHERE id = ?
            """, (rule_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_validation_rule(row)

    def get_rules_for_field(self, field_id: str) -> List[ValidationRuleInference]:
        """Get all validation rules for a field"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM validation_rule_inferences
                WHERE extracted_field_id = ?
                ORDER BY priority DESC, confidence_score DESC
            """, (field_id,))

            return [self._row_to_validation_rule(row) for row in cursor.fetchall()]

    def get_recommended_rules(self, field_id: str) -> List[ValidationRuleInference]:
        """Get recommended validation rules for a field"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM validation_rule_inferences
                WHERE extracted_field_id = ? AND is_recommended = 1
                ORDER BY priority DESC, confidence_score DESC
            """, (field_id,))

            return [self._row_to_validation_rule(row) for row in cursor.fetchall()]

    # === Document Type Suggestions ===

    def save_document_type_suggestion(self, suggestion: DocumentTypeSuggestion) -> str:
        """Save document type suggestion to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO document_type_suggestions (
                    id, analysis_result_id, suggested_type, type_confidence,
                    type_description, alternative_types, classification_factors,
                    key_indicators, confidence_explanation, matched_templates,
                    template_similarity_scores, classification_timestamp,
                    model_used, requires_confirmation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                suggestion.id,
                suggestion.analysis_result_id,
                suggestion.suggested_type,
                suggestion.type_confidence,
                suggestion.type_description,
                json.dumps(suggestion.alternative_types),
                json.dumps(suggestion.classification_factors),
                json.dumps(suggestion.key_indicators),
                suggestion.confidence_explanation,
                json.dumps(suggestion.matched_templates),
                json.dumps(suggestion.template_similarity_scores),
                suggestion.classification_timestamp.isoformat(),
                suggestion.model_used,
                suggestion.requires_confirmation
            ))

        return suggestion.id

    def get_document_type_suggestion(self, suggestion_id: str) -> Optional[DocumentTypeSuggestion]:
        """Retrieve document type suggestion by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM document_type_suggestions WHERE id = ?
            """, (suggestion_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_document_type_suggestion(row)

    def get_suggestion_for_analysis(self, analysis_result_id: str) -> Optional[DocumentTypeSuggestion]:
        """Get document type suggestion for analysis result"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM document_type_suggestions
                WHERE analysis_result_id = ?
                ORDER BY classification_timestamp DESC
                LIMIT 1
            """, (analysis_result_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_document_type_suggestion(row)

    # === Analytics and Statistics ===

    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get comprehensive analysis statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total analyses
            cursor.execute("SELECT COUNT(*) FROM ai_analysis_results")
            total_analyses = cursor.fetchone()[0]

            # By model
            cursor.execute("""
                SELECT model_used, COUNT(*)
                FROM ai_analysis_results
                GROUP BY model_used
            """)
            model_counts = dict(cursor.fetchall())

            # Quality distribution
            cursor.execute("""
                SELECT
                    CASE
                        WHEN overall_quality_score >= 0.8 THEN 'high'
                        WHEN overall_quality_score >= 0.6 THEN 'medium'
                        ELSE 'low'
                    END as quality_level,
                    COUNT(*)
                FROM ai_analysis_results
                GROUP BY quality_level
            """)
            quality_distribution = dict(cursor.fetchall())

            # Average processing time
            cursor.execute("SELECT AVG(processing_time) FROM ai_analysis_results")
            avg_processing_time = cursor.fetchone()[0] or 0

            # Fields requiring review
            cursor.execute("SELECT COUNT(*) FROM extracted_fields WHERE requires_review = 1")
            fields_needing_review = cursor.fetchone()[0]

            # Document type distribution
            cursor.execute("""
                SELECT detected_document_type, COUNT(*)
                FROM ai_analysis_results
                GROUP BY detected_document_type
                ORDER BY COUNT(*) DESC
            """)
            document_type_distribution = dict(cursor.fetchall())

            return {
                'total_analyses': total_analyses,
                'model_distribution': model_counts,
                'quality_distribution': quality_distribution,
                'average_processing_time_seconds': avg_processing_time,
                'fields_requiring_review': fields_needing_review,
                'document_type_distribution': document_type_distribution
            }

    def delete_analysis_result(self, result_id: str) -> bool:
        """Delete analysis result and all related data"""
        with sqlite3.connect(self.db_path) as conn:
            # Delete validation rules first
            conn.execute("""
                DELETE FROM validation_rule_inferences
                WHERE extracted_field_id IN (
                    SELECT id FROM extracted_fields
                    WHERE analysis_result_id = ?
                )
            """, (result_id,))

            # Delete extracted fields
            conn.execute("""
                DELETE FROM extracted_fields
                WHERE analysis_result_id = ?
            """, (result_id,))

            # Delete document type suggestions
            conn.execute("""
                DELETE FROM document_type_suggestions
                WHERE analysis_result_id = ?
            """, (result_id,))

            # Delete analysis result
            cursor = conn.execute("""
                DELETE FROM ai_analysis_results WHERE id = ?
            """, (result_id,))

            return cursor.rowcount > 0

    # === Helper Methods ===

    def _row_to_analysis_result(self, row: sqlite3.Row) -> AIAnalysisResult:
        """Convert database row to AIAnalysisResult model"""
        result = AIAnalysisResult(
            id=row['id'],
            sample_document_id=row['sample_document_id'],
            model_used=row['model_used'],
            analysis_timestamp=datetime.fromisoformat(row['analysis_timestamp']),
            detected_document_type=row['detected_document_type'],
            document_type_confidence=row['document_type_confidence'],
            total_fields_detected=row['total_fields_detected'],
            high_confidence_fields=row['high_confidence_fields'],
            processing_time=row['processing_time'],
            overall_quality_score=row['overall_quality_score']
        )

        # Load analysis_notes from database if they exist
        if row['analysis_notes']:
            try:
                notes = json.loads(row['analysis_notes'])
                for note in notes:
                    result.add_analysis_note(note)
            except json.JSONDecodeError:
                # If it's not valid JSON, treat as a single note
                result.add_analysis_note(row['analysis_notes'])

        return result

    def _row_to_extracted_field(self, row: sqlite3.Row) -> ExtractedField:
        """Convert database row to ExtractedField model"""
        bounding_box = None
        if row['bounding_box']:
            try:
                bounding_box = json.loads(row['bounding_box'])
            except json.JSONDecodeError:
                pass

        alternative_names = []
        if row['alternative_names']:
            try:
                alternative_names = json.loads(row['alternative_names'])
            except json.JSONDecodeError:
                pass

        alternative_types = []
        if row['alternative_types']:
            try:
                alternative_types = json.loads(row['alternative_types'])
            except json.JSONDecodeError:
                pass

        return ExtractedField(
            id=row['id'],
            analysis_result_id=row['analysis_result_id'],
            detected_name=row['detected_name'],
            display_name=row['display_name'],
            field_type=row['field_type'],
            source_text=row['source_text'],
            visual_clarity_score=row['visual_clarity_score'],
            label_confidence_score=row['label_confidence_score'],
            value_confidence_score=row['value_confidence_score'],
            type_confidence_score=row['type_confidence_score'],
            context_confidence_score=row['context_confidence_score'],
            overall_confidence_score=row['overall_confidence_score'],
            bounding_box=bounding_box,
            page_number=row['page_number'],
            context_description=row['context_description'],
            is_required=bool(row['is_required']),
            has_validation_hints=bool(row['has_validation_hints']),
            field_group=row['field_group'],
            alternative_names=alternative_names,
            alternative_types=alternative_types,
            extraction_method=row['extraction_method'],
            requires_review=bool(row['requires_review']),
            review_reason=row['review_reason']
        )

    def _row_to_validation_rule(self, row: sqlite3.Row) -> ValidationRuleInference:
        """Convert database row to ValidationRuleInference model"""
        rule_value = None
        if row['rule_value']:
            try:
                rule_value = json.loads(row['rule_value'])
            except json.JSONDecodeError:
                rule_value = row['rule_value']

        sample_matches = []
        if row['sample_matches']:
            try:
                sample_matches = json.loads(row['sample_matches'])
            except json.JSONDecodeError:
                pass

        sample_non_matches = []
        if row['sample_non_matches']:
            try:
                sample_non_matches = json.loads(row['sample_non_matches'])
            except json.JSONDecodeError:
                pass

        alternative_rules = []
        if row['alternative_rules']:
            try:
                alternative_rules = json.loads(row['alternative_rules'])
            except json.JSONDecodeError:
                pass

        return ValidationRuleInference(
            id=row['id'],
            extracted_field_id=row['extracted_field_id'],
            rule_type=row['rule_type'],
            rule_value=rule_value,
            rule_description=row['rule_description'],
            confidence_score=row['confidence_score'],
            sample_matches=sample_matches,
            sample_non_matches=sample_non_matches,
            inference_method=row['inference_method'],
            is_recommended=bool(row['is_recommended']),
            priority=row['priority'],
            alternative_rules=alternative_rules
        )

    def _row_to_document_type_suggestion(self, row: sqlite3.Row) -> DocumentTypeSuggestion:
        """Convert database row to DocumentTypeSuggestion model"""
        alternative_types = []
        if row['alternative_types']:
            try:
                alternative_types = json.loads(row['alternative_types'])
            except json.JSONDecodeError:
                pass

        classification_factors = []
        if row['classification_factors']:
            try:
                classification_factors = json.loads(row['classification_factors'])
            except json.JSONDecodeError:
                pass

        key_indicators = []
        if row['key_indicators']:
            try:
                key_indicators = json.loads(row['key_indicators'])
            except json.JSONDecodeError:
                pass

        matched_templates = []
        if row['matched_templates']:
            try:
                matched_templates = json.loads(row['matched_templates'])
            except json.JSONDecodeError:
                pass

        template_similarity_scores = {}
        if row['template_similarity_scores']:
            try:
                template_similarity_scores = json.loads(row['template_similarity_scores'])
            except json.JSONDecodeError:
                pass

        return DocumentTypeSuggestion(
            id=row['id'],
            analysis_result_id=row['analysis_result_id'],
            suggested_type=row['suggested_type'],
            type_confidence=row['type_confidence'],
            type_description=row['type_description'],
            alternative_types=alternative_types,
            classification_factors=classification_factors,
            key_indicators=key_indicators,
            confidence_explanation=row['confidence_explanation'],
            matched_templates=matched_templates,
            template_similarity_scores=template_similarity_scores,
            classification_timestamp=datetime.fromisoformat(row['classification_timestamp']),
            model_used=row['model_used'],
            requires_confirmation=bool(row['requires_confirmation'])
        )

    def _extract_metadata_from_notes(self, result) -> Dict[str, Any]:
        """Extract metadata from analysis notes that contain metadata JSON"""
        metadata = {}
        for note in result.analysis_notes:
            if note.startswith("Analysis metadata: "):
                try:
                    metadata_str = note[len("Analysis metadata: "):]
                    metadata = json.loads(metadata_str)
                    break
                except json.JSONDecodeError:
                    pass
        return metadata