"""
Schema Organization Workflow Integration Tests
Tests the complete workflow for admin organizing and managing schemas.
MUST FAIL initially - implementation comes after tests pass.

User Story: As a system administrator, I want to organize document types into 
categories and manage schema versions so I can maintain an organized schema library.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
from datetime import datetime, timedelta


@pytest.mark.integration
class TestSchemaOrganizationWorkflow:
    """Integration tests for complete schema organization workflow"""
    
    def setup_method(self):
        """Set up test environment with multiple schemas"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test schemas for organization
        self.test_schemas = [
            {
                "id": "national_id",
                "name": "National ID Card",
                "category": "Government",
                "version": "v1.0.0",
                "created_date": "2025-01-01",
                "usage_count": 150
            },
            {
                "id": "passport", 
                "name": "Passport Document",
                "category": "Government",
                "version": "v1.2.0",
                "created_date": "2025-02-15",
                "usage_count": 89
            },
            {
                "id": "invoice",
                "name": "Business Invoice",
                "category": "Business",
                "version": "v2.0.0", 
                "created_date": "2025-03-01",
                "usage_count": 245
            },
            {
                "id": "receipt",
                "name": "Receipt Document",
                "category": "Business",
                "version": "v1.1.0",
                "created_date": "2025-03-10",
                "usage_count": 67
            },
            {
                "id": "birth_certificate",
                "name": "Birth Certificate",
                "category": "Personal",
                "version": "v1.0.0",
                "created_date": "2025-02-20",
                "usage_count": 34
            }
        ]
    
    def test_schema_library_overview(self):
        """Test: Loading complete schema library overview"""
        from schema_management.ui.admin import render_schema_library_overview
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Save test schemas
        for schema in self.test_schemas:
            storage.save_schema(schema["id"], schema)
        
        with patch('streamlit.metric') as mock_metric, \
             patch('streamlit.bar_chart') as mock_chart:
            
            overview_data = render_schema_library_overview(storage)
            
            # Verify overview displays key metrics
            assert isinstance(overview_data, dict)
            assert "total_schemas" in overview_data
            assert "categories" in overview_data
            assert overview_data["total_schemas"] == len(self.test_schemas)
    
    def test_category_based_organization(self):
        """Test: Organizing schemas by categories"""
        from schema_management.ui.admin import render_category_organization
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Save test schemas
        for schema in self.test_schemas:
            storage.save_schema(schema["id"], schema)
        
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.expander') as mock_expander:
            
            mock_selectbox.return_value = "Government"
            mock_expander.return_value.__enter__ = Mock()
            mock_expander.return_value.__exit__ = Mock()
            
            category_data = render_category_organization(storage)
            
            # Verify category organization
            assert isinstance(category_data, dict)
            government_schemas = [s for s in self.test_schemas if s["category"] == "Government"]
            assert len(government_schemas) == 2
    
    def test_schema_search_and_filtering(self):
        """Test: Searching and filtering schemas"""
        from schema_management.services.search_service import search_schemas
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Save test schemas
        for schema in self.test_schemas:
            storage.save_schema(schema["id"], schema)
        
        # Test search by name
        search_results = search_schemas(storage, query="invoice", field="name")
        assert isinstance(search_results, list)
        assert any("invoice" in s.get("name", "").lower() for s in search_results)
        
        # Test filter by category
        business_schemas = search_schemas(storage, category="Business")
        business_count = len([s for s in self.test_schemas if s["category"] == "Business"])
        assert len(business_schemas) == business_count
    
    def test_bulk_schema_operations(self):
        """Test: Performing bulk operations on multiple schemas"""
        from schema_management.ui.admin import render_bulk_operations_interface
        
        selected_schema_ids = ["national_id", "passport", "birth_certificate"]
        
        with patch('streamlit.multiselect', return_value=selected_schema_ids), \
             patch('streamlit.selectbox', return_value="change_category"), \
             patch('streamlit.text_input', return_value="Updated_Category"), \
             patch('streamlit.button', return_value=True):
            
            result = render_bulk_operations_interface(self.test_schemas)
            
            # Verify bulk operations interface
            assert isinstance(result, dict)
            assert "operation" in result
            assert "selected_schemas" in result
    
    def test_schema_version_management(self):
        """Test: Managing schema versions and deprecation"""
        from schema_management.services.version_service import manage_schema_versions
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Create multiple versions of same schema
        versions = [
            {"id": "invoice", "version": "v1.0.0", "is_active": False, "deprecated": True},
            {"id": "invoice", "version": "v1.5.0", "is_active": False, "deprecated": True},
            {"id": "invoice", "version": "v2.0.0", "is_active": True, "deprecated": False}
        ]
        
        for version_data in versions:
            storage.save_schema("invoice", version_data)
        
        # Get version management data
        version_info = manage_schema_versions("invoice", storage)
        
        assert isinstance(version_info, dict)
        assert "versions" in version_info
        assert "active_version" in version_info
        assert version_info["active_version"] == "v2.0.0"
    
    def test_usage_analytics_and_reporting(self):
        """Test: Analyzing schema usage patterns"""
        from schema_management.services.analytics_service import generate_usage_analytics
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Save schemas with usage data
        for schema in self.test_schemas:
            storage.save_schema(schema["id"], schema)
            # Record usage
            for _ in range(schema["usage_count"]):
                storage.record_schema_usage(schema["id"])
        
        analytics = generate_usage_analytics(storage)
        
        assert isinstance(analytics, dict)
        assert "most_used_schemas" in analytics
        assert "least_used_schemas" in analytics
        assert "usage_by_category" in analytics
        
        # Most used should be invoice (245 uses)
        most_used = analytics["most_used_schemas"][0]
        assert most_used["id"] == "invoice"
    
    def test_schema_archival_workflow(self):
        """Test: Archiving old or unused schemas"""
        from schema_management.services.archival_service import archive_old_schemas
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Create schemas with different ages
        old_schema = {
            "id": "old_schema",
            "name": "Old Unused Schema",
            "created_date": (datetime.now() - timedelta(days=365)).isoformat(),
            "usage_count": 0,  # Never used
            "is_active": True
        }
        
        recent_schema = {
            "id": "recent_schema", 
            "name": "Recent Active Schema",
            "created_date": datetime.now().isoformat(),
            "usage_count": 100,
            "is_active": True
        }
        
        storage.save_schema("old_schema", old_schema)
        storage.save_schema("recent_schema", recent_schema)
        
        # Archive old unused schemas
        archival_result = archive_old_schemas(
            storage, 
            max_age_days=180,
            min_usage_threshold=5
        )
        
        assert isinstance(archival_result, dict)
        assert "archived_count" in archival_result
        assert "archived_schemas" in archival_result
        assert "old_schema" in archival_result["archived_schemas"]
    
    def test_schema_backup_and_restore(self):
        """Test: Backing up and restoring schema library"""
        from schema_management.services.backup_service import create_full_backup, restore_from_backup
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage(data_dir=self.temp_dir)
        
        # Save test schemas
        for schema in self.test_schemas:
            storage.save_schema(schema["id"], schema)
        
        # Create backup
        backup_data = create_full_backup(storage)
        
        assert isinstance(backup_data, dict)
        assert "schemas" in backup_data
        assert "metadata" in backup_data
        assert "backup_date" in backup_data
        assert len(backup_data["schemas"]) == len(self.test_schemas)
        
        # Test restore capability
        storage.clear_all_schemas()  # Clear existing data
        restore_result = restore_from_backup(storage, backup_data)
        
        assert restore_result is True
        
        # Verify restored schemas
        restored_schemas = storage.list_schemas()
        assert len(restored_schemas) == len(self.test_schemas)
    
    def test_schema_dependency_tracking(self):
        """Test: Tracking dependencies between schemas"""
        from schema_management.services.dependency_service import analyze_schema_dependencies
        
        # Create schemas with cross-references
        schemas_with_deps = [
            {
                "id": "parent_schema",
                "fields": {
                    "ref_field": {
                        "type": "reference",
                        "references_schema": "child_schema"
                    }
                }
            },
            {
                "id": "child_schema",
                "fields": {
                    "data_field": {"type": "text"}
                }
            },
            {
                "id": "standalone_schema",
                "fields": {
                    "simple_field": {"type": "text"}
                }
            }
        ]
        
        dependencies = analyze_schema_dependencies(schemas_with_deps)
        
        assert isinstance(dependencies, dict)
        assert "parent_schema" in dependencies
        assert "child_schema" in dependencies["parent_schema"]
    
    def test_schema_quality_monitoring(self):
        """Test: Monitoring schema quality and health"""
        from schema_management.services.quality_service import assess_schema_quality
        
        # Schema with quality issues
        problematic_schema = {
            "id": "problematic_schema",
            "name": "Problematic Schema",
            "description": "",  # Missing description
            "fields": {
                "field1": {
                    "name": "field1",
                    "type": "text",
                    "description": "",  # Missing description
                    "validation_rules": []  # No validation
                },
                "field2": {
                    "name": "field2",
                    "type": "number",
                    "required": True,
                    "validation_rules": [
                        {"type": "required", "message": "Field 2 required"}
                    ]
                }
            }
        }
        
        quality_assessment = assess_schema_quality(problematic_schema)
        
        assert isinstance(quality_assessment, dict)
        assert "overall_score" in quality_assessment
        assert "issues" in quality_assessment
        assert "recommendations" in quality_assessment
        
        # Should identify quality issues
        assert len(quality_assessment["issues"]) > 0
    
    def test_schema_compliance_checking(self):
        """Test: Checking schemas against organizational standards"""
        from schema_management.services.compliance_service import check_schema_compliance
        
        # Define organizational standards
        compliance_rules = {
            "required_metadata": ["name", "description", "category"],
            "field_naming_pattern": "^[a-z_]+$",
            "required_validation_types": ["required"],
            "max_fields_per_schema": 20
        }
        
        # Test compliant schema
        compliant_schema = {
            "name": "Compliant Schema",
            "description": "Well-documented schema",
            "category": "Business",
            "fields": {
                "compliant_field": {
                    "name": "compliant_field",
                    "type": "text",
                    "validation_rules": [
                        {"type": "required", "message": "Required field"}
                    ]
                }
            }
        }
        
        compliance_result = check_schema_compliance(compliant_schema, compliance_rules)
        
        assert isinstance(compliance_result, dict)
        assert "compliant" in compliance_result
        assert "violations" in compliance_result
        
        # Should be compliant
        assert compliance_result["compliant"] is True
        assert len(compliance_result["violations"]) == 0


@pytest.mark.integration
class TestSchemaMetricsAndReporting:
    """Integration tests for schema metrics and administrative reporting"""
    
    def test_schema_metrics_dashboard(self):
        """Test: Comprehensive metrics dashboard"""
        from schema_management.ui.admin import render_metrics_dashboard
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage()
        
        with patch('streamlit.metric') as mock_metric, \
             patch('streamlit.line_chart') as mock_line_chart, \
             patch('streamlit.bar_chart') as mock_bar_chart:
            
            dashboard_data = render_metrics_dashboard(storage)
            
            # Verify dashboard components
            assert isinstance(dashboard_data, dict)
            assert mock_metric.called
    
    def test_administrative_reports_generation(self):
        """Test: Generating administrative reports"""
        from schema_management.services.reporting_service import generate_admin_report
        
        report_config = {
            "report_type": "monthly_summary",
            "date_range": {
                "start": "2025-09-01", 
                "end": "2025-09-30"
            },
            "include_sections": [
                "usage_statistics",
                "quality_metrics", 
                "performance_data"
            ]
        }
        
        report = generate_admin_report(report_config)
        
        assert isinstance(report, dict)
        assert "report_date" in report
        assert "summary" in report
        assert "sections" in report
    
    def test_schema_audit_trail(self):
        """Test: Maintaining audit trail of schema changes"""
        from schema_management.services.audit_service import get_schema_audit_trail
        
        schema_id = "audit_test_schema"
        
        # Mock audit events
        audit_events = [
            {
                "timestamp": "2025-09-10T10:00:00Z",
                "action": "schema_created",
                "user": "admin",
                "details": {"version": "v1.0.0"}
            },
            {
                "timestamp": "2025-09-11T14:30:00Z",
                "action": "field_added",
                "user": "editor",
                "details": {"field_name": "new_field"}
            },
            {
                "timestamp": "2025-09-12T09:15:00Z",
                "action": "validation_modified",
                "user": "editor", 
                "details": {"field": "existing_field", "rule": "length"}
            }
        ]
        
        with patch('schema_management.storage.audit_storage.get_audit_events', return_value=audit_events):
            audit_trail = get_schema_audit_trail(schema_id)
            
            assert isinstance(audit_trail, list)
            assert len(audit_trail) == 3
            assert all("timestamp" in event for event in audit_trail)


@pytest.mark.integration
class TestSchemaMaintenanceWorkflow:
    """Integration tests for schema maintenance operations"""
    
    def test_schema_health_check(self):
        """Test: Running comprehensive health checks on schema library"""
        from schema_management.services.maintenance_service import run_health_check
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage()
        
        health_result = run_health_check(storage)
        
        assert isinstance(health_result, dict)
        assert "overall_health" in health_result
        assert "issues_found" in health_result
        assert "recommendations" in health_result
    
    def test_orphaned_schema_cleanup(self):
        """Test: Cleaning up orphaned schemas and data"""
        from schema_management.services.cleanup_service import cleanup_orphaned_data
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage()
        
        cleanup_result = cleanup_orphaned_data(storage)
        
        assert isinstance(cleanup_result, dict)
        assert "cleaned_files" in cleanup_result
        assert "space_freed" in cleanup_result
    
    def test_schema_optimization(self):
        """Test: Optimizing schema storage and performance"""
        from schema_management.services.optimization_service import optimize_schema_storage
        from schema_management.storage.schema_storage import SchemaStorage
        
        storage = SchemaStorage()
        
        optimization_result = optimize_schema_storage(storage)
        
        assert isinstance(optimization_result, dict)
        assert "optimization_performed" in optimization_result
        assert "performance_improvement" in optimization_result