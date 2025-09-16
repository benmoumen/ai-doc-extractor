-- T002: Database schema extensions for AI schema generation
-- Extends existing schema management database with AI-specific tables

-- Sample documents table
CREATE TABLE IF NOT EXISTS sample_documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('pdf', 'image')),
    file_size INTEGER NOT NULL,
    file_path TEXT,
    content_hash TEXT NOT NULL UNIQUE,
    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    metadata TEXT, -- JSON
    error_message TEXT,
    analysis_count INTEGER DEFAULT 0,
    page_count INTEGER,
    user_session_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- AI analysis results table
CREATE TABLE IF NOT EXISTS ai_analysis_results (
    id TEXT PRIMARY KEY,
    sample_document_id TEXT NOT NULL REFERENCES sample_documents(id) ON DELETE CASCADE,
    analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    model_used TEXT NOT NULL,
    processing_time REAL NOT NULL,
    detected_document_type TEXT NOT NULL,
    document_type_confidence REAL NOT NULL CHECK (document_type_confidence BETWEEN 0 AND 1),
    alternative_types TEXT, -- JSON array
    layout_description TEXT,
    field_locations TEXT, -- JSON
    text_blocks TEXT, -- JSON array
    total_fields_detected INTEGER DEFAULT 0,
    high_confidence_fields INTEGER DEFAULT 0,
    requires_review_count INTEGER DEFAULT 0,
    analysis_notes TEXT, -- JSON array
    overall_quality_score REAL CHECK (overall_quality_score BETWEEN 0 AND 1),
    confidence_distribution TEXT -- JSON
);

-- Extracted fields table
CREATE TABLE IF NOT EXISTS extracted_fields (
    id TEXT PRIMARY KEY,
    analysis_result_id TEXT NOT NULL REFERENCES ai_analysis_results(id) ON DELETE CASCADE,
    detected_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    field_type TEXT NOT NULL,
    source_text TEXT,
    visual_clarity_score REAL CHECK (visual_clarity_score BETWEEN 0 AND 1),
    label_confidence_score REAL CHECK (label_confidence_score BETWEEN 0 AND 1),
    value_confidence_score REAL CHECK (value_confidence_score BETWEEN 0 AND 1),
    type_confidence_score REAL CHECK (type_confidence_score BETWEEN 0 AND 1),
    context_confidence_score REAL CHECK (context_confidence_score BETWEEN 0 AND 1),
    overall_confidence_score REAL CHECK (overall_confidence_score BETWEEN 0 AND 1),
    bounding_box TEXT, -- JSON
    page_number INTEGER,
    context_description TEXT,
    is_required BOOLEAN DEFAULT FALSE,
    has_validation_hints BOOLEAN DEFAULT FALSE,
    field_group TEXT,
    alternative_names TEXT, -- JSON array
    alternative_types TEXT, -- JSON array
    extraction_method TEXT NOT NULL,
    requires_review BOOLEAN DEFAULT FALSE,
    review_reason TEXT
);

-- Validation rule inference table
CREATE TABLE IF NOT EXISTS validation_rule_inferences (
    id TEXT PRIMARY KEY,
    extracted_field_id TEXT NOT NULL REFERENCES extracted_fields(id) ON DELETE CASCADE,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('pattern', 'length', 'range', 'format', 'custom')),
    rule_value TEXT NOT NULL, -- JSON or string
    rule_description TEXT NOT NULL,
    confidence_score REAL NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
    sample_matches TEXT, -- JSON array
    sample_non_matches TEXT, -- JSON array
    inference_method TEXT NOT NULL,
    is_recommended BOOLEAN DEFAULT FALSE,
    priority INTEGER DEFAULT 1,
    alternative_rules TEXT -- JSON array
);

-- Document type suggestions table
CREATE TABLE IF NOT EXISTS document_type_suggestions (
    id TEXT PRIMARY KEY,
    analysis_result_id TEXT NOT NULL REFERENCES ai_analysis_results(id) ON DELETE CASCADE,
    suggested_type TEXT NOT NULL,
    type_confidence REAL NOT NULL CHECK (type_confidence BETWEEN 0 AND 1),
    type_description TEXT NOT NULL,
    alternative_types TEXT, -- JSON array
    classification_factors TEXT, -- JSON array
    key_indicators TEXT, -- JSON array
    confidence_explanation TEXT,
    matched_templates TEXT, -- JSON array
    template_similarity_scores TEXT, -- JSON
    classification_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    model_used TEXT NOT NULL,
    requires_confirmation BOOLEAN DEFAULT FALSE
);

-- Generated schemas table for AI-generated schema persistence
CREATE TABLE IF NOT EXISTS generated_schemas (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    fields TEXT NOT NULL, -- JSON
    source_document_id TEXT REFERENCES sample_documents(id),
    analysis_result_id TEXT REFERENCES ai_analysis_results(id),
    generation_method TEXT NOT NULL DEFAULT 'ai_extraction',
    generated_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ai_model_used TEXT NOT NULL,
    generation_confidence REAL NOT NULL CHECK (generation_confidence BETWEEN 0 AND 1),
    total_fields_generated INTEGER DEFAULT 0,
    high_confidence_fields INTEGER DEFAULT 0,
    user_modified_fields TEXT DEFAULT '[]', -- JSON array
    validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN ('pending', 'in_progress', 'complete', 'failed')),
    user_review_status TEXT DEFAULT 'pending' CHECK (user_review_status IN ('pending', 'in_progress', 'reviewed', 'approved', 'rejected')),
    review_notes TEXT,
    last_modified_by TEXT DEFAULT 'ai',
    accuracy_feedback TEXT, -- JSON
    suggested_improvements TEXT DEFAULT '[]', -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_sample_documents_processing_status ON sample_documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_sample_documents_upload_timestamp ON sample_documents(upload_timestamp);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_results_sample_document_id ON ai_analysis_results(sample_document_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_results_analysis_timestamp ON ai_analysis_results(analysis_timestamp);
CREATE INDEX IF NOT EXISTS idx_extracted_fields_analysis_result_id ON extracted_fields(analysis_result_id);
CREATE INDEX IF NOT EXISTS idx_extracted_fields_overall_confidence ON extracted_fields(overall_confidence_score);
CREATE INDEX IF NOT EXISTS idx_validation_rules_extracted_field_id ON validation_rule_inferences(extracted_field_id);
CREATE INDEX IF NOT EXISTS idx_document_type_suggestions_analysis_result_id ON document_type_suggestions(analysis_result_id);
CREATE INDEX IF NOT EXISTS idx_generated_schemas_analysis_result_id ON generated_schemas(analysis_result_id);
CREATE INDEX IF NOT EXISTS idx_generated_schemas_generated_timestamp ON generated_schemas(generated_timestamp);
CREATE INDEX IF NOT EXISTS idx_generated_schemas_review_status ON generated_schemas(user_review_status);