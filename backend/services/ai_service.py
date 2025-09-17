"""
AI service - handles model configuration, prompts, and API calls
"""

import json
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List

from fastapi import HTTPException, status

from config import settings
from validators import InputSanitizer

# Import LiteLLM for AI model calls
try:
    import litellm
    from litellm import completion
    litellm.enable_json_schema_validation = True
except ImportError:
    raise ImportError("LiteLLM is required. Install with: pip install litellm")

logger = logging.getLogger(__name__)
input_sanitizer = InputSanitizer()

# Request tracking for concurrent limits
active_ai_requests = 0
ai_request_lock = asyncio.Lock()

# Provider and model configuration
PROVIDER_OPTIONS = {
    "Groq": "groq",
    "Mistral": "mistral"
}

MODEL_OPTIONS = {
    "groq": {
        "Llama Scout 17B": "meta-llama/llama-4-scout-17b-16e-instruct"
    },
    "mistral": {
        "Mistral Small 3.2": "mistral-small-2506"
    }
}


def get_model_param(provider: str, model: str) -> str:
    """Get the model parameter for LiteLLM"""
    if provider == "groq":
        return f"groq/{model}"
    elif provider == "mistral":
        return f"mistral/{model}"
    else:
        return model


def determine_ai_model(model: Optional[str]) -> tuple[str, str, str]:
    """
    Determine AI model parameters from request
    Returns: (provider_id, model_id, model_param)
    """
    if model and '_' in model:
        provider_id, model_id = model.split('_', 1)
    else:
        provider_id = settings.ai.default_provider
        model_id = settings.ai.default_model

    model_param = get_model_param(provider_id, model_id)
    return provider_id, model_id, model_param


async def make_ai_request_with_retry(
    prompt: str,
    image_base64: str,
    model_param: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """Make AI request with retry logic and error handling"""
    global active_ai_requests

    for attempt in range(max_retries):
        try:
            async with ai_request_lock:
                active_ai_requests += 1
                logger.info(f"Active AI requests: {active_ai_requests}")

            try:
                # Add timeout to AI request
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        completion,
                        model=model_param,
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                            ]
                        }],
                        temperature=settings.ai.temperature,
                        response_format={"type": "json_object"}
                    ),
                    timeout=settings.ai.request_timeout
                )

                return {
                    "content": response.choices[0].message.content,
                    "usage": getattr(response, 'usage', {}).dict() if hasattr(response, 'usage') and response.usage else {},
                    "model": getattr(response, 'model', model_param)
                }

            finally:
                async with ai_request_lock:
                    active_ai_requests = max(0, active_ai_requests - 1)
                    logger.info(f"Active AI requests: {active_ai_requests}")

        except asyncio.TimeoutError:
            logger.warning(f"AI request timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(settings.ai.retry_delay * (attempt + 1))
            else:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="AI request timed out"
                )

        except Exception as e:
            logger.error(f"AI request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(settings.ai.retry_delay * (attempt + 1))
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI service error: {str(e)}"
                )


def extract_json_from_text(text: str) -> tuple[bool, Optional[Dict], str]:
    """Extract JSON from AI response text with validation"""
    try:
        # Try direct JSON parse
        data = json.loads(text)
        # Sanitize the extracted data
        data = input_sanitizer.sanitize_json_field(data)
        return True, data, json.dumps(data, indent=2)
    except:
        pass

    # Try to find JSON blocks in markdown or text
    import re

    # Look for JSON blocks in markdown code fences
    json_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_blocks:
        for block in json_blocks:
            try:
                data = json.loads(block)
                data = input_sanitizer.sanitize_json_field(data)
                if isinstance(data, dict):
                    return True, data, json.dumps(data, indent=2)
            except:
                continue

    return False, None, text


def get_supported_models() -> List[Dict[str, str]]:
    """Get list of supported AI models"""
    models = []
    for provider_display_name, provider_id in PROVIDER_OPTIONS.items():
        if provider_id in MODEL_OPTIONS:
            for model_display_name, model_id in MODEL_OPTIONS[provider_id].items():
                models.append({
                    "id": f"{provider_id}_{model_id}",
                    "name": f"{provider_display_name} - {model_display_name}",
                    "provider": provider_display_name,
                    "model": model_display_name,
                    "provider_id": provider_id,
                    "model_id": model_id
                })
    return models


def get_active_ai_requests() -> int:
    """Get current number of active AI requests"""
    return active_ai_requests