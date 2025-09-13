# Data Model: AI-Powered Schema Generation from Sample Documents

**Feature**: 003-ai-schema-generation
**Date**: 2025-09-13

## Entity Definitions

### SampleDocument

Represents the uploaded file used as input for AI analysis.

```python
@dataclass
class SampleDocument:
    """Sample document uploaded for AI schema generation."""
    id: str                          # Unique identifier
    filename: str                    # Original filename
    file_type: str                   # 'pdf' | 'image'
    file_size: int                   # Size in bytes
    content_hash: str                # Hash of document content
    upload_timestamp: datetime       # When document was uploaded
    processing_status: str           # 'pending' | 'processing' | 'completed' | 'failed'
    page_count: Optional[int]        # Number of pages (PDF only)

    # Content data
    file_data: bytes                 # Raw file content
    processed_images: List[str]      # Base64 encoded images for AI processing

    # Metadata
    metadata: Dict[str, Any]         # Additional file metadata
    user_session_id: Optional[str]   # Associated user session
```

**Relationships**:
- One SampleDocument → One AIAnalysisResult
- One SampleDocument → One or more GeneratedSchema (if re-analyzed)

**State Transitions**:
```
pending → processing → completed
        ↘ failed
```

### AIAnalysisResult

Contains the AI's interpretation of the document including confidence scores and processing metadata.

```python
@dataclass
class AIAnalysisResult:
    """Result of AI analysis on sample document."""
    id: str                          # Unique identifier
    sample_document_id: str          # Reference to source document
    analysis_timestamp: datetime     # When analysis was performed
    model_used: str                  # AI model identifier
    processing_time: float           # Processing duration in seconds

    # Document analysis
    detected_document_type: str      # Identified document type
    document_type_confidence: float  # Confidence in document type (0.0-1.0)
    alternative_types: List[Dict[str, float]]  # Alternative document types with confidence

    # Structure analysis
    layout_description: str          # Description of document layout
    field_locations: Dict[str, Dict] # Field positions and bounding boxes
    text_blocks: List[Dict[str, Any]] # Identified text blocks

    # Processing metadata
    total_fields_detected: int       # Number of fields found
    high_confidence_fields: int      # Fields with confidence ≥ 0.8
    requires_review_count: int       # Fields requiring manual review
    analysis_notes: List[str]        # Additional observations

    # Quality metrics
    overall_quality_score: float     # Overall document quality (0.0-1.0)
    confidence_distribution: Dict[str, int]  # Distribution of confidence levels
```

**Relationships**:
- One AIAnalysisResult → One SampleDocument
- One AIAnalysisResult → One or more ExtractedField
- One AIAnalysisResult → One DocumentTypeSuggestion

### ExtractedField

Individual field definitions derived from sample analysis.

```python
@dataclass
class ExtractedField:
    """Field extracted from document analysis."""
    id: str                          # Unique identifier
    analysis_result_id: str          # Reference to analysis result

    # Field identification
    detected_name: str               # AI-detected field name
    display_name: str                # Human-readable field name
    field_type: str                  # Inferred data type
    source_text: Optional[str]       # Actual text found in document

    # Confidence scoring
    visual_clarity_score: float      # How clear field is visually (0.0-1.0)
    label_confidence_score: float    # Confidence in field label (0.0-1.0)
    value_confidence_score: float    # Confidence in extracted value (0.0-1.0)
    type_confidence_score: float     # Confidence in data type (0.0-1.0)
    context_confidence_score: float  # Fit within document context (0.0-1.0)
    overall_confidence_score: float  # Calculated overall confidence (0.0-1.0)

    # Location and context
    bounding_box: Optional[Dict[str, float]]  # Field location in document
    page_number: Optional[int]       # Page where field was found
    context_description: str         # Surrounding context

    # Field properties
    is_required: bool               # Whether field appears required
    has_validation_hints: bool      # If validation patterns were detected
    field_group: Optional[str]      # Logical grouping (e.g., "address", "contact")

    # Alternative interpretations
    alternative_names: List[str]     # Other possible field names
    alternative_types: List[Dict[str, float]]  # Other possible types with confidence

    # Processing metadata
    extraction_method: str           # How field was extracted
    requires_review: bool           # Flagged for manual review
    review_reason: Optional[str]    # Why review is needed
```

**Relationships**:
- One ExtractedField → One AIAnalysisResult
- One ExtractedField → Zero or more ValidationRuleInference

**Validation Rules**:
- overall_confidence_score = average of individual confidence scores
- field_type must be valid data type
- requires_review = True if overall_confidence_score < 0.6

### ValidationRuleInference

Automatically generated validation rules based on field content patterns.

```python
@dataclass
class ValidationRuleInference:
    """Validation rules inferred from field analysis."""
    id: str                          # Unique identifier
    extracted_field_id: str          # Reference to field

    # Rule definition
    rule_type: str                   # 'pattern' | 'length' | 'range' | 'format' | 'custom'
    rule_value: Any                  # Rule parameter (regex, number, etc.)
    rule_description: str            # Human-readable explanation

    # Confidence and validation
    confidence_score: float          # Confidence in this rule (0.0-1.0)
    sample_matches: List[str]        # Sample values that match rule
    sample_non_matches: List[str]    # Values that would fail rule

    # Rule metadata
    inference_method: str            # How rule was inferred
    is_recommended: bool            # Whether to apply by default
    priority: int                   # Rule application priority

    # Alternative rules
    alternative_rules: List[Dict[str, Any]]  # Other possible rules
```

**Relationships**:
- One ValidationRuleInference → One ExtractedField

**State Transitions**:
```
inferred → recommended → applied
        ↘ rejected
```

### DocumentTypeSuggestion

AI's classification of the document type with confidence score and alternatives.

```python
@dataclass
class DocumentTypeSuggestion:
    """AI suggestion for document type classification."""
    id: str                          # Unique identifier
    analysis_result_id: str          # Reference to analysis result

    # Primary suggestion
    suggested_type: str              # Primary document type
    type_confidence: float           # Confidence in suggestion (0.0-1.0)
    type_description: str            # Description of document type

    # Alternative suggestions
    alternative_types: List[Dict[str, Any]]  # Other possible types
    # Structure: [{"type": str, "confidence": float, "reason": str}]

    # Classification reasoning
    classification_factors: List[str] # Factors that led to classification
    key_indicators: List[str]        # Specific indicators found
    confidence_explanation: str      # Why this confidence level

    # Template matching
    matched_templates: List[str]     # Known templates that match
    template_similarity_scores: Dict[str, float]  # Similarity to known types

    # Metadata
    classification_timestamp: datetime
    model_used: str
    requires_confirmation: bool      # Whether user confirmation needed
```

**Relationships**:
- One DocumentTypeSuggestion → One AIAnalysisResult

### GeneratedSchema

A document schema created from AI analysis, extending the existing Schema model.

```python
@dataclass
class GeneratedSchema:
    """Schema generated from AI analysis, extends existing Schema model."""
    # Inherits all fields from existing Schema model
    # Additional AI-specific fields:

    source_document_id: str          # Reference to source sample document
    analysis_result_id: str          # Reference to analysis result
    generation_method: str           # 'ai_generated' | 'ai_assisted' | 'manual_refined'

    # Generation metadata
    generated_timestamp: datetime    # When schema was generated
    ai_model_used: str              # AI model that generated schema
    generation_confidence: float     # Overall confidence in generated schema

    # Quality metrics
    total_fields_generated: int      # Number of fields AI generated
    high_confidence_fields: int      # Fields with high confidence
    user_modified_fields: List[str]  # Fields user has modified
    validation_status: str           # 'pending' | 'partial' | 'complete' | 'failed'

    # User interaction
    user_review_status: str          # 'pending' | 'in_progress' | 'reviewed' | 'approved'
    review_notes: Optional[str]      # User notes from review
    last_modified_by: str           # 'ai' | 'user'

    # Improvement tracking
    accuracy_feedback: Optional[Dict[str, float]]  # User feedback on accuracy
    suggested_improvements: List[str] # AI suggestions for improvement
```

**Relationships**:
- One GeneratedSchema → One SampleDocument
- One GeneratedSchema → One AIAnalysisResult
- One GeneratedSchema extends existing Schema model

**State Transitions**:
```
draft → under_review → reviewed → approved
      ↘ needs_revision ↙
```

## Database Schema Extensions

### New Tables Required

```sql
-- Sample documents table
CREATE TABLE sample_documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('pdf', 'image')),
    file_size INTEGER NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    page_count INTEGER,
    metadata TEXT, -- JSON
    user_session_id TEXT
);

-- AI analysis results table
CREATE TABLE ai_analysis_results (
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
CREATE TABLE extracted_fields (
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
```

### Extensions to Existing Tables

```sql
-- Extend existing schemas table with AI generation fields
ALTER TABLE schemas ADD COLUMN source_document_id TEXT REFERENCES sample_documents(id);
ALTER TABLE schemas ADD COLUMN analysis_result_id TEXT REFERENCES ai_analysis_results(id);
ALTER TABLE schemas ADD COLUMN generation_method TEXT DEFAULT 'manual';
ALTER TABLE schemas ADD COLUMN generated_timestamp DATETIME;
ALTER TABLE schemas ADD COLUMN ai_model_used TEXT;
ALTER TABLE schemas ADD COLUMN generation_confidence REAL CHECK (generation_confidence BETWEEN 0 AND 1);
ALTER TABLE schemas ADD COLUMN user_review_status TEXT DEFAULT 'pending';
```

## Field Type Mappings

### AI Type Inference → Schema Field Types

```python
AI_TYPE_MAPPINGS = {
    # Text types
    'text': 'string',
    'name': 'string',
    'address': 'string',
    'description': 'string',

    # Numeric types
    'number': 'number',
    'integer': 'number',
    'decimal': 'number',
    'currency': 'number',
    'percentage': 'number',

    # Date/time types
    'date': 'date',
    'datetime': 'date',
    'time': 'date',

    # Specialized types
    'email': 'string',
    'phone': 'string',
    'url': 'string',
    'ssn': 'string',
    'zipcode': 'string',

    # Boolean
    'boolean': 'boolean',
    'checkbox': 'boolean',
    'yes_no': 'boolean'
}
```

## Validation Rules

### Entity Validation

```python
def validate_extracted_field(field: ExtractedField) -> List[str]:
    """Validate extracted field data."""
    errors = []

    if not field.detected_name or len(field.detected_name.strip()) == 0:
        errors.append("Field name cannot be empty")

    if field.overall_confidence_score < 0.0 or field.overall_confidence_score > 1.0:
        errors.append("Confidence score must be between 0.0 and 1.0")

    if field.field_type not in SUPPORTED_FIELD_TYPES:
        errors.append(f"Unsupported field type: {field.field_type}")

    # Confidence scores should average to overall score (within tolerance)
    individual_scores = [
        field.visual_clarity_score,
        field.label_confidence_score,
        field.value_confidence_score,
        field.type_confidence_score,
        field.context_confidence_score
    ]
    calculated_average = sum(individual_scores) / len(individual_scores)
    if abs(calculated_average - field.overall_confidence_score) > 0.1:
        errors.append("Overall confidence score doesn't match individual scores")

    return errors
```

## Storage Strategy

### File Storage
- Sample document content: Temporary storage with automatic cleanup
- Generated schema JSON: Existing schema storage system
- AI analysis cache: Time-limited cache (30 minutes)

### Database Storage
- Metadata and relationships: SQLite database
- Search indexes: On document type, confidence scores, timestamps
- Audit trail: Existing schema versioning system

### Performance Considerations
- Index on sample_document_id, analysis_timestamp for queries
- Partitioning by generation_method for performance
- Automatic cleanup of old analysis results (>30 days)
- Caching of frequently accessed generated schemas

---

**Data Model Status**: Complete
**Next Phase**: Contract Generation