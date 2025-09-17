"""
AI models endpoint
"""

from fastapi import APIRouter

from services.ai_service import get_supported_models

router = APIRouter()


@router.get("/api/models")
async def get_models():
    """Get list of supported AI models"""
    models = get_supported_models()
    return {
        "models": models,
        "default_model": "groq_meta-llama/llama-4-scout-17b-16e-instruct"
    }