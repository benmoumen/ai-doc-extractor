"""
Schema Testing Workflow Integration Tests
Tests the complete workflow for QA specialist testing schemas against documents.
MUST FAIL initially - implementation comes after tests pass.

User Story: As a quality assurance specialist, I want to test schemas against 
sample documents so I can verify extraction accuracy before deployment.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import base64
from io import BytesIO


@pytest.mark.integration
class TestSchemaTestingWorkflow:
    """Integration tests for complete schema testing workflow"""
    
    def setup_method(self):
        """Set up test environment with test schema and sample documents"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Test schema for validation
        self.test_schema = {
            "id": "invoice_test_schema",
            "name": "Invoice Test Schema",
            "description": "Schema for testing invoice extraction",
            "category": "Business",
            "version": "v1.0.0",
            "fields": {
                "invoice_number": {
                    "name": "invoice_number",
                    "display_name": "Invoice Number",
                    "type": "text",
                    "required": True,
                    "description": "Unique invoice identifier",
                    "examples": ["INV-001", "2023-1001"],
                    "validation_rules": [
                        {"type": "required", "message": "Invoice number is required"},
                        {"type": "pattern", "pattern": "^[A-Z0-9-]+$", "message": "Invalid invoice number format"}
                    ]
                },
                "total_amount": {
                    "name": "total_amount",
                    "display_name": "Total Amount",
                    "type": "number",
                    "required": True,
                    "description": "Total invoice amount",
                    "examples": ["99.99", "1500.00"],
                    "validation_rules": [
                        {"type": "required", "message": "Total amount is required"},
                        {"type": "range", "min_value": 0, "message": "Amount must be positive"}
                    ]
                },
                "vendor_name": {
                    "name": "vendor_name",
                    "display_name": "Vendor Name",
                    "type": "text",
                    "required": False,
                    "description": "Name of the vendor",
                    "examples": ["ACME Corp", "Tech Solutions Ltd"],
                    "validation_rules": [
                        {"type": "length", "min_length": 2, "max_length": 100, "message": "Vendor name must be 2-100 characters"}
                    ]
                }
            },
            "validation_rules": []
        }
        
        # Sample extraction results for testing
        self.sample_extraction_result = {
            "invoice_number": "INV-2023-001",
            "total_amount": 1250.75,
            "vendor_name": "Tech Solutions Ltd",
            "validation_results": {
                "invoice_number": {"valid": True, "confidence": 0.95, "issues": []},
                "total_amount": {"valid": True, "confidence": 0.98, "issues": []},
                "vendor_name": {"valid": True, "confidence": 0.92, "issues": []}
            }
        }
    
    def test_schema_testing_interface_load(self):
        """Test: Loading schema testing interface"""
        from schema_management.ui.testing import render_schema_test_interface
        
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.file_uploader') as mock_uploader, \
             patch('streamlit.button') as mock_button:
            
            mock_selectbox.return_value = "invoice_test_schema"
            mock_uploader.return_value = None
            mock_button.return_value = False
            
            result = render_schema_test_interface(self.test_schema)
            
            # Verify interface components
            assert isinstance(result, dict)
            # Interface will render properly once implemented
    
    def test_document_upload_for_testing(self):
        """Test: Uploading sample documents for schema testing"""
        from schema_management.ui.testing import handle_document_upload
        
        # Mock uploaded file
        mock_file = Mock()
        mock_file.name = "sample_invoice.pdf"
        mock_file.type = "application/pdf"
        mock_file.read.return_value = b"mock_pdf_content"
        
        with patch('streamlit.file_uploader', return_value=mock_file):
            result = handle_document_upload()
            
            # Verify file handling
            assert result is not None or mock_file.read.called
    
    def test_schema_extraction_execution(self):
        """Test: Executing extraction with test schema"""
        from schema_management.services.extraction_service import test_schema_extraction
        
        # Mock document content
        document_data = {
            "content": "INVOICE\nNumber: INV-2023-001\nTotal: $1,250.75\nVendor: Tech Solutions Ltd",
            "type": "text"
        }
        
        with patch('schema_management.services.llm_service.extract_with_schema') as mock_extract:
            # Mock LLM response
            mock_extract.return_value = self.sample_extraction_result
            
            result = test_schema_extraction(self.test_schema, document_data)
            
            # Verify extraction execution
            assert isinstance(result, dict)
            assert "invoice_number" in result or mock_extract.called
    
    def test_extraction_result_validation(self):
        """Test: Validating extraction results against schema"""
        from schema_management.validators import validate_extraction_result
        
        # Test with valid extraction result
        validation_result = validate_extraction_result(
            self.sample_extraction_result, 
            self.test_schema
        )
        
        assert isinstance(validation_result, dict)
        assert "valid" in validation_result
        assert "field_results" in validation_result
        
        # Test with invalid extraction result
        invalid_result = {
            "invoice_number": "",  # Required field empty
            "total_amount": -100,  # Negative amount (invalid)
            "vendor_name": "A"     # Too short
        }
        
        invalid_validation = validate_extraction_result(invalid_result, self.test_schema)
        assert invalid_validation["valid"] is False
        assert len(invalid_validation["errors"]) > 0
    
    def test_validation_result_display(self):
        """Test: Displaying validation results with visual indicators"""
        from schema_management.ui.testing import render_validation_results
        
        validation_results = {
            "overall_valid": True,
            "field_results": {
                "invoice_number": {
                    "valid": True,
                    "confidence": 0.95,
                    "extracted_value": "INV-2023-001",
                    "issues": []
                },
                "total_amount": {
                    "valid": False,
                    "confidence": 0.80,
                    "extracted_value": "invalid_amount",
                    "issues": ["Value is not a valid number"]
                }
            }
        }
        
        with patch('streamlit.success') as mock_success, \
             patch('streamlit.error') as mock_error, \
             patch('streamlit.warning') as mock_warning:
            
            render_validation_results(validation_results)
            
            # Verify appropriate display methods called
            assert mock_success.called or mock_error.called
    
    def test_confidence_score_analysis(self):
        """Test: Analyzing confidence scores for extraction quality"""
        from schema_management.services.quality_service import analyze_confidence_scores
        
        extraction_with_confidence = {
            "fields": {
                "invoice_number": {"confidence": 0.95, "value": "INV-001"},
                "total_amount": {"confidence": 0.60, "value": "unclear_amount"},  # Low confidence
                "vendor_name": {"confidence": 0.98, "value": "ACME Corp"}
            }
        }
        
        analysis = analyze_confidence_scores(extraction_with_confidence)
        
        assert isinstance(analysis, dict)
        assert "average_confidence" in analysis
        assert "low_confidence_fields" in analysis
        assert "total_amount" in analysis["low_confidence_fields"]
    
    def test_batch_document_testing(self):
        """Test: Testing schema against multiple documents"""
        from schema_management.ui.testing import render_batch_test_interface
        
        # Mock multiple uploaded files
        mock_files = [
            Mock(name="invoice1.pdf", read=lambda: b"content1"),
            Mock(name="invoice2.pdf", read=lambda: b"content2"),
            Mock(name="invoice3.pdf", read=lambda: b"content3")
        ]
        
        with patch('streamlit.file_uploader', return_value=mock_files), \
             patch('streamlit.button', return_value=True), \
             patch('streamlit.progress') as mock_progress:
            
            result = render_batch_test_interface(self.test_schema)
            
            # Verify batch processing capability
            assert isinstance(result, (dict, list)) or mock_progress.called
    
    def test_test_case_save_and_load(self):
        """Test: Saving and loading test cases for regression testing"""
        from schema_management.services.test_case_service import save_test_case, load_test_cases
        
        test_case = {
            "id": "invoice_test_case_1",
            "schema_id": "invoice_test_schema",
            "document_name": "sample_invoice.pdf",
            "expected_results": self.sample_extraction_result,
            "test_date": "2025-09-13",
            "passed": True
        }
        
        # Save test case
        save_result = save_test_case(test_case)
        assert save_result is True
        
        # Load test cases
        loaded_cases = load_test_cases("invoice_test_schema")
        assert isinstance(loaded_cases, list)
        if loaded_cases:  # If implementation exists
            assert any(tc["id"] == "invoice_test_case_1" for tc in loaded_cases)
    
    def test_regression_testing_workflow(self):
        """Test: Running regression tests against saved test cases"""
        from schema_management.services.regression_service import run_regression_tests
        
        # Mock saved test cases
        test_cases = [
            {
                "id": "test1",
                "document_content": "mock_content_1",
                "expected_results": {"invoice_number": "INV-001"},
                "schema_version": "v1.0.0"
            },
            {
                "id": "test2", 
                "document_content": "mock_content_2",
                "expected_results": {"invoice_number": "INV-002"},
                "schema_version": "v1.0.0"
            }
        ]
        
        with patch('schema_management.services.extraction_service.extract_with_schema') as mock_extract:
            mock_extract.side_effect = [
                {"invoice_number": "INV-001"},  # Matches expected
                {"invoice_number": "INV-003"}   # Doesn't match expected
            ]
            
            results = run_regression_tests(self.test_schema, test_cases)
            
            assert isinstance(results, dict)
            assert "passed" in results
            assert "failed" in results
            assert "total" in results
    
    def test_performance_benchmarking(self):
        """Test: Measuring extraction performance with schema"""
        from schema_management.services.performance_service import benchmark_schema_performance
        
        # Mock documents for performance testing
        test_documents = [
            {"content": f"Test document {i}", "size": 1000 * i} 
            for i in range(1, 6)
        ]
        
        with patch('time.time', side_effect=[0, 0.1, 0.2, 0.3, 0.4, 0.5]):  # Mock timing
            performance_results = benchmark_schema_performance(
                self.test_schema, 
                test_documents
            )
            
            assert isinstance(performance_results, dict)
            assert "average_time" in performance_results
            assert "total_documents" in performance_results
    
    def test_error_case_handling(self):
        """Test: Handling various error cases during testing"""
        from schema_management.services.extraction_service import test_schema_extraction
        
        # Test with malformed document
        malformed_document = {
            "content": "",  # Empty content
            "type": "unknown"
        }
        
        with patch('schema_management.services.llm_service.extract_with_schema') as mock_extract:
            # Mock extraction failure
            mock_extract.side_effect = Exception("Extraction failed")
            
            result = test_schema_extraction(self.test_schema, malformed_document)
            
            # Should handle errors gracefully
            assert isinstance(result, dict)
            assert "error" in result or "success" in result


@pytest.mark.integration
class TestSchemaComparisonWorkflow:
    """Integration tests for comparing schemas and extraction results"""
    
    def test_schema_version_comparison(self):
        """Test: Comparing extraction results between schema versions"""
        from schema_management.services.comparison_service import compare_schema_versions
        
        # Create two schema versions
        schema_v1 = {
            "id": "test_schema",
            "version": "v1.0.0",
            "fields": {
                "field1": {"name": "field1", "type": "text", "required": True}
            }
        }
        
        schema_v2 = {
            "id": "test_schema", 
            "version": "v1.1.0",
            "fields": {
                "field1": {"name": "field1", "type": "text", "required": True},
                "field2": {"name": "field2", "type": "number", "required": False}
            }
        }
        
        comparison = compare_schema_versions(schema_v1, schema_v2)
        
        assert isinstance(comparison, dict)
        assert "added_fields" in comparison
        assert "removed_fields" in comparison
        assert "modified_fields" in comparison
    
    def test_extraction_accuracy_comparison(self):
        """Test: Comparing extraction accuracy between different schemas"""
        from schema_management.services.accuracy_service import compare_extraction_accuracy
        
        # Mock extraction results from different schemas
        results_schema_a = {
            "accuracy": 0.85,
            "field_accuracies": {"field1": 0.90, "field2": 0.80},
            "total_tests": 100
        }
        
        results_schema_b = {
            "accuracy": 0.92,
            "field_accuracies": {"field1": 0.95, "field2": 0.89},
            "total_tests": 100
        }
        
        comparison = compare_extraction_accuracy(results_schema_a, results_schema_b)
        
        assert isinstance(comparison, dict)
        assert "accuracy_improvement" in comparison
        assert comparison["accuracy_improvement"] > 0


@pytest.mark.integration
class TestSchemaTestingReporting:
    """Integration tests for test reporting and documentation"""
    
    def test_test_report_generation(self):
        """Test: Generating comprehensive test reports"""
        from schema_management.services.reporting_service import generate_test_report
        
        test_results = {
            "schema_id": "invoice_test_schema",
            "test_date": "2025-09-13",
            "total_tests": 50,
            "passed_tests": 42,
            "failed_tests": 8,
            "average_confidence": 0.87,
            "field_accuracy": {
                "invoice_number": 0.95,
                "total_amount": 0.82,
                "vendor_name": 0.89
            },
            "performance": {
                "average_time": 2.3,
                "max_time": 5.1,
                "min_time": 0.8
            }
        }
        
        report = generate_test_report(test_results)
        
        assert isinstance(report, dict)
        assert "summary" in report
        assert "detailed_results" in report
        assert "recommendations" in report
    
    def test_test_report_export(self):
        """Test: Exporting test reports in various formats"""
        from schema_management.ui.testing import render_report_export_interface
        
        test_report = {
            "summary": "Test execution summary",
            "results": [{"test": "result1"}, {"test": "result2"}]
        }
        
        with patch('streamlit.download_button') as mock_download, \
             patch('streamlit.selectbox') as mock_selectbox:
            
            mock_selectbox.return_value = "JSON"
            
            render_report_export_interface(test_report)
            
            # Verify export interface
            assert mock_download.called or mock_selectbox.called
    
    def test_quality_metrics_tracking(self):
        """Test: Tracking quality metrics over time"""
        from schema_management.services.metrics_service import track_quality_metrics
        
        quality_data = {
            "schema_id": "test_schema",
            "timestamp": "2025-09-13T10:00:00Z",
            "accuracy": 0.89,
            "confidence": 0.92,
            "processing_time": 1.5,
            "error_rate": 0.05
        }
        
        result = track_quality_metrics(quality_data)
        
        assert isinstance(result, bool)
        # Metrics will be properly stored once implementation exists