"""Select the configured LLM provider without coupling it to API routes."""

from functools import lru_cache

from app.config import get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.mock import MockLLMProvider


class LLMConfigurationError(RuntimeError):
    """Raised when the selected LLM provider is unsupported or incomplete."""


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Return the configured provider adapter."""
    provider_name = get_settings().llm_provider.strip().lower()
    if provider_name == "mock":
        return MockLLMProvider()
    raise LLMConfigurationError(f"Unsupported LLM_PROVIDER: {provider_name}")
