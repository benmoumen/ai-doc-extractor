# Quickstart Guide: AI-Powered Schema Generation

**Feature**: 003-ai-schema-generation
**Date**: 2025-09-13

## Overview

This quickstart guide demonstrates the complete workflow for AI-powered schema generation from sample documents, from initial upload through final schema creation and integration with the existing schema management system.

## Prerequisites

### System Requirements
- ✅ Existing schema management system (002-schema-management-ui) operational
- ✅ LiteLLM integration with Llama Scout 17B and Mistral Small 3.2
- ✅ Document processing capabilities (PyMuPDF, PIL)
- ✅ Streamlit web interface with file upload support
- ✅ Hybrid JSON+SQLite storage system

### Test Data Requirements
- Sample PDF documents (invoices, forms, contracts)
- Sample image documents (driver's licenses, receipts, ID cards)
- Various document types for testing edge cases
- Documents with different quality levels for confidence testing

## User Journey Walkthrough

### Step 1: Upload Sample Document

**User Action**: Upload a sample document for AI analysis

```python
# Expected UI Flow
1. User navigates to "Create Schema" section
2. User selects "Generate from Sample Document" option
3. User uploads PDF or image file
4. System validates file type and size
5. Document queued for AI analysis
```

**Test Scenarios**:
```
✓ Upload valid PDF invoice → Analysis queued successfully
✓ Upload image of driver's license → Analysis queued successfully
✓ Upload unsupported file type → Clear error message displayed
✓ Upload oversized file → Size limit error with guidance
✓ Upload corrupted file → File validation error with retry option
```

**Expected Results**:
- Document uploaded and assigned unique ID
- Progress indicator shows "Analysis starting..."
- ETA displayed based on document complexity
- User can navigate away and return to check progress

### Step 2: AI Document Analysis

**System Action**: AI analyzes document structure and extracts fields

```python
# Expected Analysis Flow
1. Document converted to AI-compatible format
2. AI model (Llama Scout/Mistral) analyzes document
3. Document type classification performed
4. Field extraction with confidence scoring
5. Validation rule inference
6. Results stored with metadata
```

**Test Scenarios**:
```
✓ Simple invoice → High confidence document type detection
✓ Complex multi-page form → Successful field extraction across pages
✓ Poor quality scan → Lower confidence scores, requires review flags
✓ Ambiguous document → Multiple document type suggestions
✓ Handwritten document → Graceful handling with appropriate confidence
```

**Expected Results**:
- Document type identified with confidence score
- Fields extracted with individual confidence ratings
- Validation rules suggested based on content patterns
- Processing completes within performance targets (<5 seconds)

### Step 3: Analysis Results Review

**User Action**: Review AI analysis results before schema generation

```python
# Expected Review Interface
1. Document type suggestion with confidence indicator
2. List of extracted fields with confidence colors
3. Preview of validation rules with explanations
4. Option to retry with different parameters
5. Confidence-based recommendations
```

**Test Scenarios**:
```
✓ High confidence results → Mostly green indicators, auto-accept option
✓ Medium confidence results → Orange indicators, guided review
✓ Low confidence results → Red indicators, detailed review required
✓ Mixed confidence results → Clear prioritization of review items
✓ Alternative interpretations → Multiple options presented clearly
```

**Expected Results**:
- Clear visual indicators for confidence levels
- Actionable recommendations for each field
- Ability to modify or reject AI suggestions
- Context preservation from source document

### Step 4: Schema Generation and Transition

**System Action**: Generate schema and transition to edit mode

```python
# Expected Generation Flow
1. User confirms generation parameters
2. Schema created from analysis results
3. AI metadata preserved in schema
4. Schema management interface opens in edit mode
5. All AI-generated content available for review/modification
```

**Test Scenarios**:
```
✓ Accept all high-confidence fields → Schema generated with minimal review needs
✓ Modify confidence threshold → Different field inclusion based on threshold
✓ Custom schema name → Override AI suggestion with user preference
✓ Field formatting options → Apply snake_case, camelCase, or original naming
✓ Validation rule customization → User can modify AI-suggested rules
```

**Expected Results**:
- Complete schema generated matching user selections
- Seamless transition to existing schema management UI
- All AI metadata preserved for future reference
- Edit mode opens with confidence indicators

### Step 5: Manual Review and Refinement

**User Action**: Review and refine AI-generated schema in edit mode

```python
# Expected Edit Interface
1. Existing schema editor with AI annotations
2. Confidence indicators on each field
3. AI suggestions and alternatives available
4. Source document reference accessible
5. Full editing capabilities maintained
```

**Test Scenarios**:
```
✓ Modify field names → Changes reflected in real-time preview
✓ Adjust field types → Type validation and compatibility checking
✓ Edit validation rules → Rule builder with AI suggestions
✓ Add new fields → Manual field creation alongside AI fields
✓ Remove low-confidence fields → Clean removal with dependency checking
```

**Expected Results**:
- Full editing capabilities available
- AI suggestions preserved but not intrusive
- Real-time validation and preview
- Confidence context maintained during editing

### Step 6: Schema Validation and Saving

**System Action**: Validate refined schema and save to storage

```python
# Expected Validation Flow
1. Schema validation against existing standards
2. Compatibility checking with current schemas
3. Version control setup with AI provenance
4. Integration with existing storage system
5. Schema available for immediate use
```

**Test Scenarios**:
```
✓ Valid schema → Successful save with confirmation
✓ Schema conflicts → Clear resolution options
✓ Validation errors → Specific error messages with fix suggestions
✓ Version tracking → AI generation properly recorded in version history
✓ Integration test → Schema immediately usable in main extraction workflow
```

**Expected Results**:
- Schema successfully saved to existing storage system
- Version history includes AI generation metadata
- Schema available in document type selection
- Backup and migration support maintained

## Performance Validation

### Response Time Targets
```
✓ Simple document analysis: <2 seconds (Mistral fast path)
✓ Complex document analysis: <5 seconds (Llama accurate path)
✓ Schema generation: <1 second
✓ Edit mode transition: <500ms
✓ Schema save operation: <1 second
```

### Accuracy Expectations
```
✓ Document type classification: >85% accuracy on common types
✓ Field extraction: >90% accuracy for clearly labeled fields
✓ Validation rule inference: >75% applicable rules generated
✓ Overall user satisfaction: >80% successful schema creation without major revision
```

### System Integration
```
✓ Existing schema management features: Full compatibility maintained
✓ Storage system: No performance degradation
✓ UI responsiveness: No impact on existing workflows
✓ Memory usage: <200MB additional per analysis session
✓ Concurrent users: No degradation with multiple simultaneous analyses
```

## Error Handling Validation

### Expected Error Scenarios
```
✓ AI analysis timeout → Fallback to alternative model
✓ Low confidence results → Clear guidance for retry options
✓ Schema generation failure → Graceful fallback to manual creation
✓ Storage system error → Error recovery with temporary save
✓ UI session timeout → Progress preservation and recovery
```

### Error Recovery Testing
```
✓ Network interruption during analysis → Resume on reconnection
✓ Browser refresh during process → Session state recovery
✓ File upload failure → Clear retry mechanism
✓ Analysis server error → Transparent failover to backup processing
✓ Storage quota exceeded → Clear guidance and cleanup options
```

## Integration Validation

### Schema Management System
```
✓ Generated schemas appear in schema list
✓ AI metadata visible in schema details
✓ Version history properly recorded
✓ Import/export functionality maintained
✓ Search and filtering work with AI-generated schemas
```

### Main Extraction Workflow
```
✓ AI-generated schemas selectable in document type dropdown
✓ Extraction works correctly with AI-generated field definitions
✓ Validation rules function properly in extraction workflow
✓ Performance maintained with AI-generated schemas
✓ Results display properly with AI-defined field types
```

### User Experience
```
✓ Seamless workflow from upload to final schema
✓ Clear confidence indicators throughout process
✓ Intuitive review and editing interface
✓ Helpful guidance for low-confidence results
✓ Consistent UI patterns with existing functionality
```

## Success Criteria Validation

### Primary Success Metrics
```
✓ User completes end-to-end workflow successfully
✓ Generated schema accuracy meets user expectations
✓ Performance targets achieved consistently
✓ Integration with existing system seamless
✓ Error handling provides clear recovery paths
```

### User Acceptance Criteria
```
✓ Time to create schema reduced compared to manual process
✓ Generated schemas require minimal manual adjustment
✓ UI provides clear guidance throughout process
✓ Confidence indicators help prioritize review efforts
✓ Overall experience feels like natural extension of existing tools
```

## Testing Checklist

### Functional Testing
- [ ] Document upload and validation
- [ ] AI analysis with multiple models
- [ ] Confidence scoring accuracy
- [ ] Schema generation completeness
- [ ] Edit mode transition smoothness
- [ ] Schema save and integration

### Performance Testing
- [ ] Analysis time within targets
- [ ] Memory usage within limits
- [ ] Concurrent user handling
- [ ] Large document processing
- [ ] Cache performance optimization

### Integration Testing
- [ ] Schema management system compatibility
- [ ] Main extraction workflow integration
- [ ] Storage system operation
- [ ] UI component interaction
- [ ] Version control functionality

### Error Handling Testing
- [ ] AI analysis failures
- [ ] Network interruptions
- [ ] Invalid input handling
- [ ] Storage system errors
- [ ] User session management

### User Experience Testing
- [ ] Workflow intuitiveness
- [ ] Confidence indicator clarity
- [ ] Error message helpfulness
- [ ] Performance feedback adequacy
- [ ] Help and guidance availability

---

**Quickstart Status**: Ready for Implementation
**Next Steps**: Execute implementation tasks following TDD methodology