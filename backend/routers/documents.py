"""
Document upload endpoints
"""

import logging
import uuid

from fastapi import APIRouter, UploadFile, File, Request, HTTPException, status

from services.document_processor import process_uploaded_document, create_document_metadata

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/documents")
async def upload_document(
    request: Request,
    file: UploadFile = File(...)
):
    """Upload document with comprehensive validation"""
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        # Use shared document processing function
        file_data, metadata = await process_uploaded_document(file, request_id)

        # Generate document metadata using shared function
        document_metadata = create_document_metadata(metadata, request_id)

        # Generate analysis ID
        analysis_id = str(uuid.uuid4())

        return {
            "success": True,
            "document": document_metadata,
            "analysis": {
                "id": analysis_id,
                "status": "pending"
            },
            "metadata": {
                "processing_time": 0.1,
                "validation_passed": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Document upload error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document upload"
        )