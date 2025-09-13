# Research: AI-Powered Schema Generation from Sample Documents

**Date**: 2025-09-13
**Feature**: 003-ai-schema-generation

## Overview

Research conducted to identify optimal approaches for implementing AI-powered schema generation from sample documents, integrating with the existing schema management system while maintaining performance targets and user experience quality.

## AI Prompt Engineering for Schema Field Extraction

### Decision: Multi-Stage Extraction with Model-Specific Optimization

**Selected Approach**: Two-stage extraction process with model-specific configurations:
1. **Document Analysis Stage**: Identify document type, field labels, and structure patterns
2. **Schema Generation Stage**: Create comprehensive schema with validation rules and confidence scores

**Model Configurations**:
- **Llama Scout 17B**: Temperature 0.1, detailed analysis-first approach for complex documents
- **Mistral Small 3.2**: Temperature 0.2, direct extraction for simpler documents

**Rationale**:
- Multi-stage approach provides better accuracy for field identification and type inference
- Model-specific optimization leverages strengths of each AI model
- Allows for progressive enhancement and fallback strategies
- Maintains compatibility with existing LiteLLM infrastructure

**Alternatives Considered**:
- Single-stage extraction: Rejected due to lower accuracy for complex documents
- Fixed prompt templates: Rejected due to lack of flexibility for different document types
- Human-in-the-loop during analysis: Rejected due to performance impact

## Confidence Scoring Methods

### Decision: Multi-Dimensional Confidence Scoring

**Selected Approach**: Five-dimensional confidence scoring system:
1. Visual Clarity (0.0-1.0): Field visibility in document
2. Label Confidence (0.0-1.0): Certainty of field label identification
3. Value Confidence (0.0-1.0): Confidence in extracted value
4. Type Confidence (0.0-1.0): Certainty of inferred data type
5. Context Confidence (0.0-1.0): Fit within document context

**Confidence Thresholds**:
- Overall confidence ≥ 0.8: Auto-accept with minimal review
- Overall confidence 0.6-0.8: Suggest review with guidance
- Overall confidence < 0.6: Require manual review

**Rationale**:
- Provides granular insight into AI certainty levels
- Enables intelligent UI prioritization for user review
- Supports progressive enhancement workflows
- Allows for quality-based batch operations

**Alternatives Considered**:
- Single overall confidence score: Rejected due to lack of actionable granularity
- Binary confidence (high/low): Rejected due to insufficient nuance for UX optimization
- Self-reported confidence only: Rejected due to potential inconsistency across models

## Performance Optimization for Document Processing

### Decision: Adaptive Processing with Multi-Level Caching

**Selected Optimizations**:

1. **Memory Management**:
   - PyMuPDF memoryview (`samples_mv`) for large documents
   - Generator-based processing for multi-page documents
   - Adaptive zoom calculation based on page complexity
   - Proactive cache cleanup at 80% memory usage

2. **Caching Strategy**:
   - Document hash caching (30 min TTL, 50 documents)
   - Page-level field extraction caching (15 min TTL, 200 pages)
   - Pattern-based validation rule caching (1 hour TTL, 1000 patterns)
   - Predictive preloading based on user patterns

3. **Processing Pipeline**:
   - Direct PyMuPDF JPEG output for AI analysis
   - Intelligent image resizing based on content complexity
   - Batch validation processing for multiple fields
   - Async schema generation with progress tracking

**Performance Targets**:
- Simple documents: <2 seconds (fast path with Mistral)
- Complex documents: <5 seconds (accurate path with Llama Scout)
- Memory usage: <200MB per document processing session
- Cache hit rate: >70% for repeated document types

**Rationale**:
- Maintains existing <500ms response time targets for core operations
- Leverages existing performance infrastructure and patterns
- Provides scalable foundation for larger document processing
- Enables responsive user experience with progress indicators

**Alternatives Considered**:
- Synchronous processing only: Rejected due to UX impact for complex documents
- Unlimited caching: Rejected due to memory constraints
- Single-level caching: Rejected due to missed optimization opportunities

## Integration with Schema Management System

### Decision: Seamless Extension with AI Metadata Layer

**Selected Integration Pattern**:

1. **Storage Extension**:
   - Extend existing Schema model with AI metadata fields
   - Use existing hybrid JSON+SQLite storage system
   - Add AI-specific audit trail entries
   - Maintain backward compatibility with manual workflows

2. **Workflow Integration**:
   - Automatic transition to edit mode after AI generation
   - Preserve AI metadata (confidence scores, source analysis) during editing
   - Support iterative AI→Manual→AI improvement cycles
   - Maintain existing schema management features

3. **Version Control Enhancement**:
   - Tag AI-generated versions with generation method and confidence
   - Track lineage from AI base version through manual refinements
   - Support confidence-based version validation
   - Enable rollback to AI-generated baseline

4. **Error Handling Strategy**:
   - Multi-model fallback (Llama Scout ↔ Mistral Small)
   - Template-based generation for common document types
   - Graceful degradation to manual creation
   - Partial success handling with field-level confidence flags

**Rationale**:
- Leverages existing robust architecture without major changes
- Maintains compatibility with current schema management workflows
- Provides foundation for future AI enhancement capabilities
- Ensures seamless user experience across manual and AI-assisted creation

**Alternatives Considered**:
- Separate AI schema system: Rejected due to fragmentation and maintenance overhead
- Complete workflow replacement: Rejected due to user training and compatibility issues
- AI-only approach: Rejected due to need for human review and refinement

## UI/UX Patterns for AI Review

### Decision: Progressive Disclosure with Confidence-Based Prioritization

**Selected UI Patterns**:

1. **Confidence Visualization**:
   - Color-coded confidence indicators (green ≥80%, orange 60-80%, red <60%)
   - Progressive disclosure based on confidence levels
   - Confidence dashboard with overall metrics

2. **Review Workflow**:
   - One-click acceptance for high-confidence fields (≥80%)
   - Guided editing interface for medium-confidence fields (60-80%)
   - Mandatory review for low-confidence fields (<60%)
   - Batch operations for similar field types

3. **Context Preservation**:
   - Show source document regions that informed each field
   - Maintain AI reasoning context during editing
   - Highlight areas of uncertainty with explanations
   - Provide alternative interpretations for ambiguous fields

4. **Integration with Existing UI**:
   - Extend existing streamlit-elements field editor
   - Add AI-specific review modes to schema management interface
   - Maintain existing drag-drop and real-time preview capabilities
   - Support existing import/export and versioning features

**Rationale**:
- Builds on existing proven UI architecture
- Provides clear guidance for user review priorities
- Maintains context and transparency in AI decision-making
- Enables efficient review of AI-generated content

**Alternatives Considered**:
- Binary accept/reject interface: Rejected due to lack of granular control
- Separate AI review interface: Rejected due to workflow fragmentation
- Auto-accept high confidence: Rejected due to user trust and control requirements

## Implementation Recommendations

### High Priority (Phase 1)
1. Implement multi-stage AI extraction with confidence scoring
2. Extend existing schema storage with AI metadata support
3. Create seamless transition from AI generation to edit mode
4. Add performance optimizations for document processing

### Medium Priority (Phase 2)
1. Implement predictive caching and batch processing
2. Add comprehensive error handling and fallback strategies
3. Create specialized UI components for AI review workflow
4. Enhance version control with AI provenance tracking

### Low Priority (Future Enhancement)
1. Machine learning from user corrections to improve AI accuracy
2. Advanced pattern recognition for specialized document types
3. Cross-document learning and template suggestions
4. Integration with external document type libraries

---

**Research Status**: Complete
**Next Phase**: Design & Contracts (Phase 1)