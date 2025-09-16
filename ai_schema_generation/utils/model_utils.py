"""
Centralized utilities for AI model handling and format conversion.

This module provides a robust, extensible solution for:
- Model name format conversion between different systems
- Model validation and normalization
- Provider-specific handling
- Configuration-driven model management
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ModelFormat(Enum):
    """Supported model name formats."""
    FRONTEND = "frontend"      # provider_model_id
    LITELLM = "litellm"       # provider/model_id
    OPENAI = "openai"         # model_id only
    ANTHROPIC = "anthropic"   # model_id only


class ModelProvider(Enum):
    """Supported AI model providers."""
    GROQ = "groq"
    MISTRAL = "mistral"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    TOGETHER = "together"
    COHERE = "cohere"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    id: str
    name: str
    provider: ModelProvider
    model_id: str
    max_tokens: Optional[int] = None
    cost_per_token: Optional[float] = None
    supports_json_mode: bool = True
    temperature_range: Tuple[float, float] = (0.0, 2.0)
    aliases: List[str] = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


class ModelValidationError(Exception):
    """Raised when model validation fails."""
    pass


class ModelFormatConverter:
    """Handles conversion between different model name formats."""

    # Provider patterns for validation
    PROVIDER_PATTERNS = {
        ModelProvider.GROQ: re.compile(r'^groq[/_](.+)$'),
        ModelProvider.MISTRAL: re.compile(r'^mistral[/_](.+)$'),
        ModelProvider.OPENAI: re.compile(r'^(openai[/_])?(.+)$'),
        ModelProvider.ANTHROPIC: re.compile(r'^(anthropic[/_])?(.+)$'),
        ModelProvider.TOGETHER: re.compile(r'^together[/_](.+)$'),
        ModelProvider.COHERE: re.compile(r'^cohere[/_](.+)$'),
    }

    @staticmethod
    def normalize_model_name(model_name: str) -> str:
        """Normalize model name by removing extra whitespace and converting to lowercase provider."""
        if not model_name:
            return model_name

        model_name = model_name.strip()

        # Handle provider prefix normalization
        for provider in ModelProvider:
            prefix_underscore = f"{provider.value}_"
            prefix_slash = f"{provider.value}/"

            if model_name.lower().startswith(prefix_underscore.lower()):
                # Replace case-insensitive match with correct case
                rest = model_name[len(prefix_underscore):]
                return f"{provider.value}_{rest}"
            elif model_name.lower().startswith(prefix_slash.lower()):
                # Replace case-insensitive match with correct case
                rest = model_name[len(prefix_slash):]
                return f"{provider.value}/{rest}"

        return model_name

    @staticmethod
    def detect_format(model_name: str) -> ModelFormat:
        """Detect the format of a model name."""
        if not model_name:
            raise ModelValidationError("Empty model name")

        model_name = ModelFormatConverter.normalize_model_name(model_name)

        # Check for provider/model format (LiteLLM)
        if '/' in model_name and '_' not in model_name.split('/')[0]:
            return ModelFormat.LITELLM

        # Check for provider_model format (Frontend)
        if '_' in model_name:
            parts = model_name.split('_', 1)
            if len(parts) == 2 and parts[0] in [p.value for p in ModelProvider]:
                return ModelFormat.FRONTEND

        # If no provider prefix, assume it's a direct model ID
        return ModelFormat.OPENAI  # Default for bare model names

    @staticmethod
    def parse_model_name(model_name: str) -> Tuple[Optional[ModelProvider], str]:
        """Parse model name into provider and model ID components."""
        if not model_name:
            raise ModelValidationError("Empty model name")

        model_name = ModelFormatConverter.normalize_model_name(model_name)

        # Try to match against provider patterns
        for provider, pattern in ModelFormatConverter.PROVIDER_PATTERNS.items():
            match = pattern.match(model_name)
            if match:
                if provider in [ModelProvider.OPENAI, ModelProvider.ANTHROPIC]:
                    # These can have optional provider prefix
                    model_id = match.group(2) if match.group(1) else match.group(1)
                else:
                    model_id = match.group(1)
                return provider, model_id

        # No provider detected, return as bare model ID
        return None, model_name

    @staticmethod
    def convert_to_format(model_name: str, target_format: ModelFormat) -> str:
        """Convert model name to specified format."""
        if not model_name:
            return model_name

        # Parse the model name
        provider, model_id = ModelFormatConverter.parse_model_name(model_name)

        if target_format == ModelFormat.LITELLM:
            if provider:
                return f"{provider.value}/{model_id}"
            else:
                # Assume OpenAI if no provider specified
                return model_id

        elif target_format == ModelFormat.FRONTEND:
            if provider:
                return f"{provider.value}_{model_id}"
            else:
                # Assume OpenAI if no provider specified
                return f"openai_{model_id}"

        elif target_format in [ModelFormat.OPENAI, ModelFormat.ANTHROPIC]:
            return model_id

        else:
            raise ModelValidationError(f"Unsupported target format: {target_format}")

    @staticmethod
    def to_litellm_format(model_name: str) -> str:
        """Convert model name to LiteLLM format (provider/model_id)."""
        return ModelFormatConverter.convert_to_format(model_name, ModelFormat.LITELLM)

    @staticmethod
    def to_frontend_format(model_name: str) -> str:
        """Convert model name to frontend format (provider_model_id)."""
        return ModelFormatConverter.convert_to_format(model_name, ModelFormat.FRONTEND)


class ModelRegistry:
    """Registry for managing available models and their configurations."""

    def __init__(self):
        self._models: Dict[str, ModelConfig] = {}
        self._aliases: Dict[str, str] = {}  # alias -> canonical_id
        self._default_model: Optional[str] = None

        # Load default models
        self._load_default_models()

    def _load_default_models(self):
        """Load default model configurations."""
        default_models = [
            ModelConfig(
                id="groq/meta-llama/llama-4-scout-17b-16e-instruct",
                name="Llama Scout 17B",
                provider=ModelProvider.GROQ,
                model_id="meta-llama/llama-4-scout-17b-16e-instruct",
                max_tokens=8192,
                supports_json_mode=True,
                aliases=["groq_meta-llama/llama-4-scout-17b-16e-instruct", "llama-scout"]
            ),
            ModelConfig(
                id="mistral/mistral-small-2506",
                name="Mistral Small",
                provider=ModelProvider.MISTRAL,
                model_id="mistral-small-2506",
                max_tokens=4096,
                supports_json_mode=True,
                aliases=["mistral_mistral-small-2506", "mistral-small"]
            ),
            ModelConfig(
                id="openai/gpt-4o",
                name="GPT-4O",
                provider=ModelProvider.OPENAI,
                model_id="gpt-4o",
                max_tokens=4096,
                supports_json_mode=True,
                aliases=["openai_gpt-4o", "gpt-4o"]
            ),
            ModelConfig(
                id="anthropic/claude-3-5-sonnet-20241022",
                name="Claude 3.5 Sonnet",
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                supports_json_mode=False,  # Anthropic doesn't support JSON mode
                aliases=["anthropic_claude-3-5-sonnet-20241022", "claude-sonnet"]
            )
        ]

        for model in default_models:
            self.register_model(model)

        # Set default model
        self._default_model = "groq/meta-llama/llama-4-scout-17b-16e-instruct"

    def register_model(self, model: ModelConfig):
        """Register a model configuration."""
        self._models[model.id] = model

        # Register aliases
        for alias in model.aliases:
            self._aliases[alias] = model.id

        logger.debug(f"Registered model: {model.id} with {len(model.aliases)} aliases")

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        """Get model configuration by ID or alias."""
        # Try direct lookup
        if model_id in self._models:
            return self._models[model_id]

        # Try alias lookup
        if model_id in self._aliases:
            canonical_id = self._aliases[model_id]
            return self._models[canonical_id]

        return None

    def resolve_model_id(self, model_input: str) -> str:
        """Resolve any model input to a canonical LiteLLM format ID."""
        if not model_input:
            if self._default_model:
                return self._default_model
            raise ModelValidationError("No model specified and no default available")

        # Try to find registered model
        model = self.get_model(model_input)
        if model:
            return model.id

        # If not found in registry, try format conversion
        try:
            return ModelFormatConverter.to_litellm_format(model_input)
        except Exception as e:
            logger.warning(f"Failed to resolve model '{model_input}': {e}")
            raise ModelValidationError(f"Unknown model: {model_input}")

    def validate_model(self, model_id: str) -> bool:
        """Validate that a model is supported."""
        try:
            self.resolve_model_id(model_id)
            return True
        except ModelValidationError:
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models in API format."""
        models = []
        for model in self._models.values():
            models.append({
                "id": model.id,
                "name": model.name,
                "provider": model.provider.value,
                "model": model.model_id,
                "provider_id": model.provider.value,
                "model_id": model.model_id,
                "max_tokens": model.max_tokens,
                "cost_per_token": model.cost_per_token,
                "supports_json_mode": model.supports_json_mode
            })
        return models

    def get_default_model(self) -> Optional[str]:
        """Get the default model ID."""
        return self._default_model

    def set_default_model(self, model_id: str):
        """Set the default model."""
        if not self.validate_model(model_id):
            raise ModelValidationError(f"Cannot set unknown model as default: {model_id}")

        canonical_id = self.resolve_model_id(model_id)
        self._default_model = canonical_id


# Global model registry instance
model_registry = ModelRegistry()


# Convenience functions for backward compatibility
def convert_model_name_to_litellm_format(model: str) -> str:
    """Convert model name to LiteLLM format - backward compatibility function."""
    if not model:
        return None

    try:
        return model_registry.resolve_model_id(model)
    except ModelValidationError:
        # Fallback to format converter for unknown models
        return ModelFormatConverter.to_litellm_format(model)


def validate_model_name(model: str) -> bool:
    """Validate that a model name is supported."""
    return model_registry.validate_model(model)


def get_supported_models() -> List[Dict[str, Any]]:
    """Get list of supported models in API format."""
    return model_registry.list_models()


def get_default_model() -> Optional[str]:
    """Get the default model."""
    return model_registry.get_default_model()


# Utility for debugging model resolution
def debug_model_resolution(model_input: str) -> Dict[str, Any]:
    """Debug helper to trace model resolution process."""
    debug_info = {
        "input": model_input,
        "normalized": ModelFormatConverter.normalize_model_name(model_input),
        "detected_format": None,
        "parsed_provider": None,
        "parsed_model_id": None,
        "resolved_id": None,
        "is_registered": False,
        "error": None
    }

    try:
        normalized = debug_info["normalized"]
        debug_info["detected_format"] = ModelFormatConverter.detect_format(normalized).value

        provider, model_id = ModelFormatConverter.parse_model_name(normalized)
        debug_info["parsed_provider"] = provider.value if provider else None
        debug_info["parsed_model_id"] = model_id

        resolved = model_registry.resolve_model_id(model_input)
        debug_info["resolved_id"] = resolved
        debug_info["is_registered"] = model_registry.get_model(model_input) is not None

    except Exception as e:
        debug_info["error"] = str(e)

    return debug_info