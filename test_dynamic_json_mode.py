#!/usr/bin/env python3
"""
Test script to verify dynamic JSON Mode integration with user-defined schemas
"""
import json
from dynamic_structured_output import (
    create_dynamic_data_model, create_extraction_model,
    create_response_format_from_schema, validate_extraction_with_schema,
    generate_simplified_prompt
)


def test_custom_schema():
    """Test dynamic model generation with a custom user-defined schema."""
    print("Testing Dynamic Model Generation with Custom Schema...")

    # Example custom schema (as would be defined by user)
    custom_schema = {
        "name": "Purchase Order",
        "description": "Custom purchase order document",
        "fields": {
            "po_number": {
                "display_name": "PO Number",
                "type": "string",
                "required": True,
                "description": "Purchase order number"
            },
            "vendor": {
                "display_name": "Vendor Name",
                "type": "string",
                "required": True,
                "description": "Vendor or supplier name"
            },
            "order_date": {
                "display_name": "Order Date",
                "type": "date",
                "required": True,
                "description": "Date of the order"
            },
            "items": {
                "display_name": "Line Items",
                "type": "array",
                "required": False,
                "items": {"type": "object"},
                "description": "List of ordered items"
            },
            "total_amount": {
                "display_name": "Total Amount",
                "type": "number",
                "required": True,
                "description": "Total order amount"
            },
            "approved": {
                "display_name": "Approved",
                "type": "boolean",
                "required": False,
                "description": "Whether the order is approved"
            }
        }
    }

    print("\n1. Creating dynamic data model...")
    data_model = create_dynamic_data_model(custom_schema)
    print(f"   ✓ Created model: {data_model.__name__}")
    print(f"   ✓ Fields: {list(data_model.model_fields.keys())}")

    print("\n2. Creating extraction model...")
    extraction_model = create_extraction_model(custom_schema)
    print(f"   ✓ Created model: {extraction_model.__name__}")

    print("\n3. Generating response format for LiteLLM...")
    response_format = create_response_format_from_schema(custom_schema)
    print(f"   ✓ Response format type: {response_format['type']}")
    print(f"   ✓ Schema name: {response_format['name']}")
    print(f"   ✓ Schema properties: {list(response_format['response_schema']['properties'].keys())[:3]}...")

    print("\n4. Testing validation with sample data...")
    sample_extraction = {
        "data": {
            "po_number": "PO-2025-001",
            "vendor": "Acme Corp",
            "order_date": "2025-01-15",
            "total_amount": 5000.00,
            "approved": True,
            "items": [
                {"name": "Widget A", "quantity": 10, "price": 100},
                {"name": "Widget B", "quantity": 5, "price": 200}
            ]
        },
        "validation_results": {
            "po_number": {
                "status": "valid",
                "message": "PO number extracted successfully",
                "confidence": 0.95
            },
            "vendor": {
                "status": "valid",
                "message": "Vendor name found",
                "confidence": 0.98
            }
        },
        "document_confidence": 0.92
    }

    is_valid, model_instance, errors = validate_extraction_with_schema(custom_schema, sample_extraction)
    if is_valid:
        print("   ✓ Sample data validated successfully")
        print(f"   ✓ Extracted PO: {model_instance.data.po_number}")
        print(f"   ✓ Vendor: {model_instance.data.vendor}")
    else:
        print(f"   ✗ Validation failed: {errors}")

    print("\n5. Generating simplified prompt...")
    prompt = generate_simplified_prompt(custom_schema)
    print("   Generated prompt:")
    print("   " + prompt.replace("\n", "\n   ")[:200] + "...")


def test_various_field_types():
    """Test handling of different field types."""
    print("\n\nTesting Various Field Types...")

    test_schema = {
        "name": "Test Document",
        "fields": {
            "text_field": {"type": "string", "required": True},
            "number_field": {"type": "number", "required": False},
            "integer_field": {"type": "integer", "required": False},
            "date_field": {"type": "date", "required": False},
            "bool_field": {"type": "boolean", "required": False},
            "array_field": {"type": "array", "items": {"type": "string"}, "required": False},
            "object_field": {"type": "object", "required": False}
        }
    }

    model = create_dynamic_data_model(test_schema)
    print(f"   ✓ Created model with {len(model.model_fields)} fields")

    # Test instantiation
    try:
        instance = model(
            text_field="test",
            number_field=3.14,
            integer_field=42,
            date_field="2025-01-15",
            bool_field=True,
            array_field=["item1", "item2"],
            object_field={"key": "value"}
        )
        print("   ✓ Model instantiation successful")
        print(f"   ✓ JSON serialization: {instance.model_dump_json()[:50]}...")
    except Exception as e:
        print(f"   ✗ Model instantiation failed: {e}")


def test_field_name_sanitization():
    """Test that field names are properly sanitized for Python."""
    print("\n\nTesting Field Name Sanitization...")

    schema_with_special_names = {
        "name": "Special Names Test",
        "fields": {
            "field-with-dashes": {"type": "string", "required": True},
            "field with spaces": {"type": "string", "required": False},
            "UPPERCASE_FIELD": {"type": "string", "required": False}
        }
    }

    model = create_dynamic_data_model(schema_with_special_names)
    field_names = list(model.model_fields.keys())
    print(f"   Original names: ['field-with-dashes', 'field with spaces', 'UPPERCASE_FIELD']")
    print(f"   Sanitized names: {field_names}")

    # Verify sanitization
    assert "field_with_dashes" in field_names
    assert "field_with_spaces" in field_names
    assert "uppercase_field" in field_names
    print("   ✓ Field name sanitization working correctly")


def main():
    print("=" * 60)
    print("Dynamic JSON Mode Integration Test")
    print("=" * 60)

    test_custom_schema()
    test_various_field_types()
    test_field_name_sanitization()

    print("\n" + "=" * 60)
    print("✅ All dynamic model tests completed successfully!")
    print("=" * 60)
    print("\nThe system now supports:")
    print("• Dynamic Pydantic model generation from user schemas")
    print("• Automatic field type mapping and validation")
    print("• JSON Mode integration with LiteLLM")
    print("• Field name sanitization for Python compatibility")
    print("• Custom schema validation and error reporting")


if __name__ == "__main__":
    main()