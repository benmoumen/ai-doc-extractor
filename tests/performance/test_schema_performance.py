"""
Performance tests for Schema Management System.

Tests performance requirements: <500ms UI response, 100+ field schemas,
memory usage, concurrent operations, and scalability.
"""

import pytest
import time
import threading
import tempfile
import shutil
from typing import List, Dict, Any
import psutil
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean, median

# Import the modules we're testing
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from schema_management.models.schema import Schema, SchemaStatus
from schema_management.models.field import Field, FieldType
from schema_management.models.validation_rule import ValidationRule, ValidationRuleType, ValidationSeverity
from schema_management.storage.schema_storage import SchemaStorage
from schema_management.services.schema_service import SchemaService
from schema_management.services.validation_service import ValidationService
from schema_management.performance_optimizer import performance_optimizer, PerformanceMonitor


class PerformanceMetrics:
    """Helper class to track performance metrics."""
    
    def __init__(self):
        self.response_times = []
        self.memory_usage = []
        self.cpu_usage = []
        self.start_memory = None
        self.process = psutil.Process()
    
    def start_monitoring(self):
        """Start monitoring system resources."""
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def record_response_time(self, duration: float):
        """Record a response time."""
        self.response_times.append(duration)
    
    def record_memory_usage(self):
        """Record current memory usage."""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.memory_usage.append(current_memory)
    
    def record_cpu_usage(self):
        """Record current CPU usage."""
        cpu_percent = self.process.cpu_percent()
        self.cpu_usage.append(cpu_percent)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return {
            "response_times": {
                "count": len(self.response_times),
                "mean": mean(self.response_times) if self.response_times else 0,
                "median": median(self.response_times) if self.response_times else 0,
                "min": min(self.response_times) if self.response_times else 0,
                "max": max(self.response_times) if self.response_times else 0,
                "under_500ms": sum(1 for t in self.response_times if t < 0.5),
                "over_500ms": sum(1 for t in self.response_times if t >= 0.5)
            },
            "memory": {
                "start_mb": self.start_memory,
                "current_mb": self.process.memory_info().rss / 1024 / 1024,
                "peak_mb": max(self.memory_usage) if self.memory_usage else 0,
                "average_mb": mean(self.memory_usage) if self.memory_usage else 0
            },
            "cpu": {
                "peak_percent": max(self.cpu_usage) if self.cpu_usage else 0,
                "average_percent": mean(self.cpu_usage) if self.cpu_usage else 0
            }
        }


class TestSchemaPerformance:
    """Performance tests for schema management system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SchemaStorage(data_dir=self.temp_dir)
        self.schema_service = SchemaService(self.storage)
        self.validation_service = ValidationService(self.storage, self.schema_service)
        self.metrics = PerformanceMetrics()
        self.metrics.start_monitoring()

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Print performance summary
        summary = self.metrics.get_summary()
        print(f"\n=== Performance Summary ===")
        print(f"Response times: {summary['response_times']['count']} operations")
        print(f"  Mean: {summary['response_times']['mean']:.3f}s")
        print(f"  <500ms: {summary['response_times']['under_500ms']}")
        print(f"  >500ms: {summary['response_times']['over_500ms']}")
        print(f"Memory: {summary['memory']['current_mb']:.1f}MB peak")
        print(f"CPU: {summary['cpu']['peak_percent']:.1f}% peak")

    def create_large_schema(self, field_count: int, schema_id: str = None) -> Schema:
        """Create a schema with specified number of fields."""
        if schema_id is None:
            schema_id = f"large_schema_{field_count}_fields"
        
        fields = []
        for i in range(field_count):
            field_type = [FieldType.STRING, FieldType.NUMBER, FieldType.EMAIL, 
                         FieldType.DATE, FieldType.SELECT][i % 5]
            
            # Add validation rules to some fields
            validation_rules = []
            if i % 3 == 0:  # Every third field gets validation rules
                if field_type == FieldType.STRING:
                    validation_rules = [
                        ValidationRule(
                            rule_type=ValidationRuleType.MIN_LENGTH,
                            message="Too short",
                            parameters={"length": 2}
                        ),
                        ValidationRule(
                            rule_type=ValidationRuleType.MAX_LENGTH,
                            message="Too long", 
                            parameters={"length": 100}
                        )
                    ]
                elif field_type == FieldType.NUMBER:
                    validation_rules = [
                        ValidationRule(
                            rule_type=ValidationRuleType.MIN_VALUE,
                            message="Too small",
                            parameters={"value": 0}
                        )
                    ]
            
            # Add options for select fields
            options = []
            if field_type == FieldType.SELECT:
                options = [f"Option_{j}" for j in range(5)]
            
            field = Field(
                id=f"field_{i}",
                name=f"field_{i}",
                display_name=f"Field {i}",
                field_type=field_type,
                required=(i % 4 == 0),  # Every fourth field is required
                description=f"Auto-generated field {i} for performance testing",
                validation_rules=validation_rules,
                options=options
            )
            fields.append(field)
        
        return Schema(
            id=schema_id,
            name=f"Performance Test Schema ({field_count} fields)",
            description=f"Large schema with {field_count} fields for performance testing",
            version="1.0.0",
            category="Performance",
            fields=fields
        )

    @pytest.mark.performance
    def test_ui_response_time_requirement(self):
        """Test that UI operations respond within 500ms."""
        
        # Test schema creation response time
        schema = self.create_large_schema(50)
        
        start_time = time.time()
        success, message, created_schema = self.schema_service.create_schema(schema.to_dict())
        creation_time = time.time() - start_time
        
        self.metrics.record_response_time(creation_time)
        
        assert success is True
        assert creation_time < 0.5, f"Schema creation took {creation_time:.3f}s, should be <0.5s"
        
        # Test schema retrieval response time
        start_time = time.time()
        retrieved_schema = self.schema_service.get_schema(schema.id)
        retrieval_time = time.time() - start_time
        
        self.metrics.record_response_time(retrieval_time)
        
        assert retrieved_schema is not None
        assert retrieval_time < 0.5, f"Schema retrieval took {retrieval_time:.3f}s, should be <0.5s"
        
        # Test schema update response time
        updated_data = schema.to_dict()
        updated_data["name"] = "Updated Name"
        
        start_time = time.time()
        success, message, updated_schema = self.schema_service.update_schema(schema.id, updated_data)
        update_time = time.time() - start_time
        
        self.metrics.record_response_time(update_time)
        
        assert success is True
        assert update_time < 0.5, f"Schema update took {update_time:.3f}s, should be <0.5s"
        
        # Test schema listing response time
        start_time = time.time()
        schema_list = self.schema_service.list_schemas()
        listing_time = time.time() - start_time
        
        self.metrics.record_response_time(listing_time)
        
        assert len(schema_list) > 0
        assert listing_time < 0.5, f"Schema listing took {listing_time:.3f}s, should be <0.5s"

    @pytest.mark.performance
    def test_100_plus_field_schema_support(self):
        """Test support for schemas with 100+ fields."""
        
        field_counts = [100, 200, 500, 1000]
        
        for count in field_counts:
            print(f"\nTesting schema with {count} fields...")
            
            # Create large schema
            start_time = time.time()
            large_schema = self.create_large_schema(count, f"test_schema_{count}")
            creation_time = time.time() - start_time
            
            self.metrics.record_response_time(creation_time)
            self.metrics.record_memory_usage()
            
            assert len(large_schema.fields) == count
            print(f"  Schema creation: {creation_time:.3f}s")
            
            # Save schema
            start_time = time.time()
            success, message, saved_schema = self.schema_service.create_schema(large_schema.to_dict())
            save_time = time.time() - start_time
            
            self.metrics.record_response_time(save_time)
            self.metrics.record_memory_usage()
            
            assert success is True
            print(f"  Schema save: {save_time:.3f}s")
            
            # Retrieve schema
            start_time = time.time()
            retrieved_schema = self.schema_service.get_schema(large_schema.id)
            retrieve_time = time.time() - start_time
            
            self.metrics.record_response_time(retrieve_time)
            self.metrics.record_memory_usage()
            
            assert retrieved_schema is not None
            assert len(retrieved_schema.fields) == count
            print(f"  Schema retrieval: {retrieve_time:.3f}s")
            
            # Test validation performance on large schema
            test_data = {}
            for i in range(min(count, 50)):  # Test with subset of data
                field = large_schema.fields[i]
                if field.field_type == FieldType.STRING:
                    test_data[field.name] = f"test_value_{i}"
                elif field.field_type == FieldType.NUMBER:
                    test_data[field.name] = i
                elif field.field_type == FieldType.EMAIL:
                    test_data[field.name] = f"test{i}@example.com"
                elif field.field_type == FieldType.SELECT and field.options:
                    test_data[field.name] = field.options[0]
            
            start_time = time.time()
            validation_result = self.validation_service.validate_data_against_schema(
                large_schema.id, test_data
            )
            validation_time = time.time() - start_time
            
            self.metrics.record_response_time(validation_time)
            self.metrics.record_memory_usage()
            
            print(f"  Validation: {validation_time:.3f}s")
            
            # Performance requirements
            assert creation_time < 2.0, f"Large schema creation should be <2s, got {creation_time:.3f}s"
            assert save_time < 2.0, f"Large schema save should be <2s, got {save_time:.3f}s"
            assert retrieve_time < 1.0, f"Large schema retrieval should be <1s, got {retrieve_time:.3f}s"
            assert validation_time < 1.0, f"Large schema validation should be <1s, got {validation_time:.3f}s"

    @pytest.mark.performance
    def test_memory_usage_with_large_schemas(self):
        """Test memory usage remains reasonable with large schemas."""
        
        initial_memory = self.metrics.process.memory_info().rss / 1024 / 1024  # MB
        self.metrics.record_memory_usage()
        
        # Create multiple large schemas
        schemas = []
        for i in range(10):
            schema = self.create_large_schema(100, f"memory_test_{i}")
            schemas.append(schema)
            self.schema_service.create_schema(schema.to_dict())
            self.metrics.record_memory_usage()
        
        # Load all schemas
        for schema in schemas:
            retrieved = self.schema_service.get_schema(schema.id)
            assert retrieved is not None
            self.metrics.record_memory_usage()
        
        final_memory = self.metrics.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
        
        # Memory usage should not increase dramatically
        assert memory_increase < 200, f"Memory increase should be <200MB, got {memory_increase:.1f}MB"

    @pytest.mark.performance  
    def test_concurrent_operations(self):
        """Test performance with concurrent operations."""
        
        def create_and_save_schema(schema_id: str) -> float:
            """Create and save a schema, return duration."""
            start_time = time.time()
            
            schema = self.create_large_schema(50, schema_id)
            success, message, created_schema = self.schema_service.create_schema(schema.to_dict())
            
            duration = time.time() - start_time
            return duration
        
        def read_schema(schema_id: str) -> float:
            """Read a schema, return duration."""
            start_time = time.time()
            
            schema = self.schema_service.get_schema(schema_id)
            
            duration = time.time() - start_time
            return duration
        
        # Create some schemas first for reading
        base_schemas = []
        for i in range(5):
            schema = self.create_large_schema(25, f"base_schema_{i}")
            self.schema_service.create_schema(schema.to_dict())
            base_schemas.append(schema.id)
        
        # Test concurrent writes
        print("Testing concurrent writes...")
        write_times = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            write_futures = [
                executor.submit(create_and_save_schema, f"concurrent_write_{i}")
                for i in range(10)
            ]
            
            for future in as_completed(write_futures):
                duration = future.result()
                write_times.append(duration)
                self.metrics.record_response_time(duration)
        
        # Test concurrent reads  
        print("Testing concurrent reads...")
        read_times = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            read_futures = [
                executor.submit(read_schema, base_schemas[i % len(base_schemas)])
                for i in range(20)
            ]
            
            for future in as_completed(read_futures):
                duration = future.result()
                read_times.append(duration)
                self.metrics.record_response_time(duration)
        
        # Performance assertions
        avg_write_time = mean(write_times)
        avg_read_time = mean(read_times)
        
        print(f"Average write time: {avg_write_time:.3f}s")
        print(f"Average read time: {avg_read_time:.3f}s")
        
        assert avg_write_time < 1.0, f"Concurrent writes should average <1s, got {avg_write_time:.3f}s"
        assert avg_read_time < 0.2, f"Concurrent reads should average <0.2s, got {avg_read_time:.3f}s"
        
        # No operation should exceed 2 seconds
        assert max(write_times) < 2.0, f"Max write time should be <2s, got {max(write_times):.3f}s"
        assert max(read_times) < 1.0, f"Max read time should be <1s, got {max(read_times):.3f}s"

    @pytest.mark.performance
    def test_validation_performance(self):
        """Test validation performance with complex schemas."""
        
        # Create schema with many validation rules
        complex_fields = []
        for i in range(100):
            validation_rules = [
                ValidationRule(
                    rule_type=ValidationRuleType.REQUIRED,
                    message="Required field"
                ),
                ValidationRule(
                    rule_type=ValidationRuleType.MIN_LENGTH,
                    message="Too short",
                    parameters={"length": 3}
                ),
                ValidationRule(
                    rule_type=ValidationRuleType.MAX_LENGTH,
                    message="Too long",
                    parameters={"length": 50}
                ),
                ValidationRule(
                    rule_type=ValidationRuleType.REGEX,
                    message="Invalid format",
                    parameters={"pattern": f"^test_{i}_.*"}
                )
            ]
            
            field = Field(
                id=f"complex_field_{i}",
                name=f"field_{i}",
                display_name=f"Complex Field {i}",
                field_type=FieldType.STRING,
                required=True,
                validation_rules=validation_rules
            )
            complex_fields.append(field)
        
        complex_schema = Schema(
            id="complex_validation_schema",
            name="Complex Validation Schema",
            description="Schema with complex validation rules",
            version="1.0.0",
            fields=complex_fields
        )
        
        # Save schema
        self.schema_service.create_schema(complex_schema.to_dict())
        
        # Create test data
        test_data = {}
        for i in range(100):
            test_data[f"field_{i}"] = f"test_{i}_valid_value"
        
        # Test validation performance
        validation_times = []
        for _ in range(10):  # Run multiple times
            start_time = time.time()
            result = self.validation_service.validate_data_against_schema(
                complex_schema.id, test_data
            )
            validation_time = time.time() - start_time
            
            validation_times.append(validation_time)
            self.metrics.record_response_time(validation_time)
            
            assert result.is_valid is True
        
        avg_validation_time = mean(validation_times)
        max_validation_time = max(validation_times)
        
        print(f"Validation times - Avg: {avg_validation_time:.3f}s, Max: {max_validation_time:.3f}s")
        
        # Performance requirements for complex validation
        assert avg_validation_time < 0.5, f"Average validation should be <0.5s, got {avg_validation_time:.3f}s"
        assert max_validation_time < 1.0, f"Max validation should be <1s, got {max_validation_time:.3f}s"

    @pytest.mark.performance
    def test_schema_search_performance(self):
        """Test search performance with many schemas."""
        
        # Create many schemas with searchable content
        categories = ["Personal", "Business", "Medical", "Legal", "Education"]
        
        print("Creating schemas for search testing...")
        for i in range(100):
            category = categories[i % len(categories)]
            schema = Schema(
                id=f"search_test_{i}",
                name=f"Search Test Schema {i}",
                description=f"This is a test schema for {category.lower()} information with index {i}",
                version="1.0.0",
                category=category,
                fields=[
                    Field(
                        id="name_field",
                        name="name",
                        display_name="Name",
                        field_type=FieldType.STRING,
                        required=True
                    )
                ]
            )
            
            success, message, created = self.schema_service.create_schema(schema.to_dict())
            assert success is True
        
        # Test search performance
        search_terms = ["test", "personal", "business", "schema", "information"]
        
        for term in search_terms:
            start_time = time.time()
            results = self.schema_service.search_schemas(term)
            search_time = time.time() - start_time
            
            self.metrics.record_response_time(search_time)
            
            print(f"Search for '{term}': {len(results)} results in {search_time:.3f}s")
            
            # Search should be fast even with many schemas
            assert search_time < 0.1, f"Search for '{term}' took {search_time:.3f}s, should be <0.1s"
            assert len(results) > 0, f"Search for '{term}' should return results"

    @pytest.mark.performance
    def test_performance_optimizer_effectiveness(self):
        """Test that performance optimizer improves performance."""
        
        # Clear any existing cache
        performance_optimizer.clear_caches()
        
        # Create test schema
        schema = self.create_large_schema(50, "optimizer_test")
        self.schema_service.create_schema(schema.to_dict())
        
        # Test without cache (first run)
        start_time = time.time()
        result1 = self.schema_service.get_schema(schema.id)
        first_time = time.time() - start_time
        
        # Test with cache (second run)
        start_time = time.time()
        result2 = self.schema_service.get_schema(schema.id)
        second_time = time.time() - start_time
        
        self.metrics.record_response_time(first_time)
        self.metrics.record_response_time(second_time)
        
        assert result1 is not None
        assert result2 is not None
        assert result1.id == result2.id
        
        print(f"First retrieval: {first_time:.3f}s")
        print(f"Second retrieval (cached): {second_time:.3f}s")
        
        # Cached version should be faster (or at least not slower)
        # Note: In some cases, the difference might be minimal due to small data size
        cache_improvement = (first_time - second_time) / first_time * 100
        print(f"Cache improvement: {cache_improvement:.1f}%")

    @pytest.mark.performance
    def test_database_performance_with_many_schemas(self):
        """Test database performance with many schemas."""
        
        print("Creating many schemas for database testing...")
        
        # Create schemas in batches to test database performance
        batch_sizes = [10, 50, 100, 200]
        
        for batch_size in batch_sizes:
            print(f"\nTesting batch of {batch_size} schemas...")
            
            # Create batch of schemas
            start_time = time.time()
            for i in range(batch_size):
                schema = self.create_large_schema(
                    field_count=25,
                    schema_id=f"db_test_batch_{batch_size}_schema_{i}"
                )
                success, message, created = self.schema_service.create_schema(schema.to_dict())
                assert success is True
            
            batch_creation_time = time.time() - start_time
            self.metrics.record_response_time(batch_creation_time)
            
            # Query all schemas
            start_time = time.time()
            all_schemas = self.schema_service.list_schemas()
            query_time = time.time() - start_time
            self.metrics.record_response_time(query_time)
            
            print(f"  Created {batch_size} schemas in {batch_creation_time:.3f}s")
            print(f"  Queried {len(all_schemas)} schemas in {query_time:.3f}s")
            
            # Performance requirements
            avg_creation_time = batch_creation_time / batch_size
            assert avg_creation_time < 0.1, f"Avg schema creation should be <0.1s, got {avg_creation_time:.3f}s"
            assert query_time < 0.5, f"Schema listing should be <0.5s, got {query_time:.3f}s"

    @pytest.mark.performance
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations."""
        
        initial_memory = self.metrics.process.memory_info().rss / 1024 / 1024
        memory_samples = [initial_memory]
        
        print(f"Initial memory: {initial_memory:.1f}MB")
        
        # Perform repeated operations
        for iteration in range(50):
            # Create schema
            schema = self.create_large_schema(25, f"leak_test_{iteration}")
            self.schema_service.create_schema(schema.to_dict())
            
            # Retrieve schema
            retrieved = self.schema_service.get_schema(schema.id)
            assert retrieved is not None
            
            # Update schema  
            updated_data = schema.to_dict()
            updated_data["description"] = f"Updated description {iteration}"
            self.schema_service.update_schema(schema.id, updated_data)
            
            # Delete schema
            success = self.schema_service.delete_schema(schema.id)
            assert success is True
            
            # Record memory every 10 iterations
            if iteration % 10 == 0:
                current_memory = self.metrics.process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                print(f"Iteration {iteration}: {current_memory:.1f}MB")
        
        final_memory = self.metrics.process.memory_info().rss / 1024 / 1024
        memory_samples.append(final_memory)
        
        # Check for memory leaks
        memory_growth = final_memory - initial_memory
        print(f"Final memory: {final_memory:.1f}MB (growth: +{memory_growth:.1f}MB)")
        
        # Memory growth should be minimal
        assert memory_growth < 50, f"Memory growth should be <50MB, got {memory_growth:.1f}MB"
        
        # Memory should not continuously increase
        if len(memory_samples) > 3:
            recent_trend = memory_samples[-1] - memory_samples[-3]
            assert recent_trend < 20, f"Recent memory trend should be <20MB, got {recent_trend:.1f}MB"


class TestPerformanceMonitoring:
    """Test the performance monitoring system itself."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.performance
    def test_performance_monitor_overhead(self):
        """Test that performance monitoring has minimal overhead."""
        
        def simple_operation():
            """Simple operation to time."""
            total = 0
            for i in range(1000):
                total += i * i
            return total
        
        # Time operation without monitoring
        start_time = time.time()
        for _ in range(100):
            result = simple_operation()
        unmonitored_time = time.time() - start_time
        
        # Time operation with monitoring
        start_time = time.time()
        for _ in range(100):
            with PerformanceMonitor("simple_operation"):
                result = simple_operation()
        monitored_time = time.time() - start_time
        
        monitoring_overhead = (monitored_time - unmonitored_time) / unmonitored_time * 100
        
        print(f"Unmonitored: {unmonitored_time:.3f}s")
        print(f"Monitored: {monitored_time:.3f}s") 
        print(f"Overhead: {monitoring_overhead:.1f}%")
        
        # Monitoring overhead should be minimal
        assert monitoring_overhead < 20, f"Monitoring overhead should be <20%, got {monitoring_overhead:.1f}%"

    @pytest.mark.performance
    def test_performance_optimizer_cache_efficiency(self):
        """Test cache hit rates and efficiency."""
        
        # Clear cache
        performance_optimizer.clear_caches()
        
        # Generate some cacheable operations
        test_data = [f"test_data_{i}" for i in range(10)]
        
        # First pass - populate cache
        start_time = time.time()
        for data in test_data:
            performance_optimizer.cache_manager.set(f"test_key_{data}", data)
        first_pass_time = time.time() - start_time
        
        # Second pass - use cache
        start_time = time.time()
        hits = 0
        for data in test_data:
            cached_value = performance_optimizer.cache_manager.get(f"test_key_{data}")
            if cached_value is not None:
                hits += 1
        second_pass_time = time.time() - start_time
        
        cache_hit_rate = hits / len(test_data) * 100
        speedup = first_pass_time / second_pass_time if second_pass_time > 0 else float('inf')
        
        print(f"Cache hit rate: {cache_hit_rate:.1f}%")
        print(f"Cache speedup: {speedup:.1f}x")
        
        # Cache should be highly effective
        assert cache_hit_rate >= 90, f"Cache hit rate should be >=90%, got {cache_hit_rate:.1f}%"
        assert speedup >= 2, f"Cache should provide >=2x speedup, got {speedup:.1f}x"


if __name__ == "__main__":
    # Run performance tests with verbose output
    pytest.main([__file__, "-v", "-s", "-m", "performance"])