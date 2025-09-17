"""
Document schemas endpoints
"""

import json
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Form
from validators import InputSanitizer
from services.database import db_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize sanitizer
input_sanitizer = InputSanitizer()


@router.get("/api/schemas")
async def get_available_schemas():
    """Get list of available document schemas"""
    schemas = db_service.get_all_schemas()

    return {
        "success": True,
        "schemas": schemas
    }


@router.get("/api/schemas/{schema_id}")
async def get_schema_details(schema_id: str):
    """Get detailed schema information"""
    # Sanitize schema_id
    safe_schema_id = input_sanitizer.sanitize_string(schema_id, max_length=100)

    schema = db_service.get_schema(safe_schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    return {
        "success": True,
        "schema": schema
    }


@router.post("/api/schemas")
async def save_generated_schema(
    request: Request,
    schema_data: str = Form(...),
    schema_name: str = Form(...),
    schema_category: str = Form(None)
):
    """Save a generated schema for future use"""
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        # Sanitize inputs
        safe_schema_name = input_sanitizer.sanitize_string(schema_name, max_length=100)
        safe_schema_category = input_sanitizer.sanitize_string(schema_category or "Other", max_length=50)

        # Parse and validate schema data
        try:
            schema_dict = json.loads(schema_data)
            schema_dict = input_sanitizer.sanitize_json_field(schema_dict)
        except json.JSONDecodeError as e:
            logger.warning(f"[{request_id}] Invalid JSON in schema data: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid JSON in schema data")

        # Generate schema ID
        import uuid
        schema_id = str(uuid.uuid4())

        # Create schema metadata
        schema_with_metadata = {
            "id": schema_id,
            "name": safe_schema_name,
            "category": safe_schema_category,
            "description": f"Generated schema for {safe_schema_name}",
            "created_at": datetime.utcnow().isoformat(),
            "fields": schema_dict.get("fields", {}),
            "schema_data": schema_dict
        }

        # Store schema in database
        success = db_service.save_schema(schema_id, schema_with_metadata)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save schema to database")

        logger.info(f"[{request_id}] Schema saved with ID: {schema_id}")

        return {
            "success": True,
            "schema_id": schema_id,
            "message": "Schema saved successfully",
            "schema": {
                "id": schema_id,
                "name": safe_schema_name,
                "category": safe_schema_category,
                "field_count": len(schema_dict.get("fields", {}))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Schema save error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save schema")


@router.put("/api/schemas/{schema_id}")
async def update_schema(
    schema_id: str,
    request: Request,
    schema_data: str = Form(...),
    schema_name: str = Form(...),
    schema_category: str = Form(None)
):
    """Update an existing schema"""
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        # Sanitize schema ID
        safe_schema_id = input_sanitizer.sanitize_string(schema_id, max_length=100)

        # Check if schema exists
        existing_schema = db_service.get_schema(safe_schema_id)
        if not existing_schema:
            raise HTTPException(status_code=404, detail="Schema not found")

        # Sanitize inputs
        safe_schema_name = input_sanitizer.sanitize_string(schema_name, max_length=100)
        safe_schema_category = input_sanitizer.sanitize_string(schema_category or "Other", max_length=50)

        # Parse and validate schema data
        try:
            schema_dict = json.loads(schema_data)
            schema_dict = input_sanitizer.sanitize_json_field(schema_dict)
        except json.JSONDecodeError as e:
            logger.warning(f"[{request_id}] Invalid JSON in schema data: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid JSON in schema data")

        # Update schema metadata
        updated_schema = {
            "id": safe_schema_id,
            "name": safe_schema_name,
            "category": safe_schema_category,
            "description": f"Updated schema for {safe_schema_name}",
            "created_at": existing_schema.get("created_at", datetime.utcnow().isoformat()),
            "updated_at": datetime.utcnow().isoformat(),
            "fields": schema_dict.get("fields", {}),
            "schema_data": schema_dict
        }

        # Update schema in database
        success = db_service.save_schema(safe_schema_id, updated_schema)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update schema in database")

        logger.info(f"[{request_id}] Schema updated with ID: {safe_schema_id}")

        return {
            "success": True,
            "schema_id": safe_schema_id,
            "message": "Schema updated successfully",
            "schema": {
                "id": safe_schema_id,
                "name": safe_schema_name,
                "category": safe_schema_category,
                "field_count": len(schema_dict.get("fields", {}))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Schema update error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update schema")


@router.delete("/api/schemas/{schema_id}")
async def delete_schema(schema_id: str, request: Request):
    """Delete an existing schema"""
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        # Sanitize schema ID
        safe_schema_id = input_sanitizer.sanitize_string(schema_id, max_length=100)

        # Check if schema exists
        existing_schema = db_service.get_schema(safe_schema_id)
        if not existing_schema:
            raise HTTPException(status_code=404, detail="Schema not found")

        # Delete schema from database
        success = db_service.delete_schema(safe_schema_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete schema from database")

        logger.info(f"[{request_id}] Schema deleted with ID: {safe_schema_id}")

        return {
            "success": True,
            "schema_id": safe_schema_id,
            "message": "Schema deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Schema delete error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete schema")


def get_schemas_dict() -> Dict[str, Any]:
    """Get the schemas dictionary (for use by other modules)"""
    return db_service.get_all_schemas()


def get_schema_by_id(schema_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific schema by ID (for use by other modules)"""
    return db_service.get_schema(schema_id)


def load_default_schemas():
    """Load default document schemas"""
    from services.database import load_default_schemas
    load_default_schemas()