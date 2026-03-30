"""
LLM Provider Factory
Creates the appropriate LLM client based on configuration
"""

import logging
import os
from typing import Optional

from src.llm.base import BaseLLMClient

logger = logging.getLogger(__name__)


def _log_client_load(provider: str, resolved_model: str, purpose: Optional[str]) -> None:
    """Print once per client creation so you can see which backend is active (testing / debugging)."""
    if os.getenv("LLM_SILENT_CLIENT_LOADS", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return
    extra = f" purpose={purpose}" if purpose else ""
    line = f"[LLM] Loaded client: provider={provider} model={resolved_model!r}{extra}"
    print(line, flush=True)
    logger.info(line)


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    *,
    purpose: Optional[str] = None,
) -> BaseLLMClient:
    """
    Create LLM client from config.

    Env vars (used as fallback when args not provided):
        LLM_PROVIDER: openai | anthropic | google
        LLM_MODEL: model name (e.g., gpt-4o, claude-sonnet-4-6, gemini-2.0-flash)
        OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY

    Args:
        provider: LLM provider (openai, anthropic, google)
        model: Model name for the provider
        api_key: API key (overrides env var for the selected provider)
        purpose: Optional label for logs, e.g. "intent_classification" or "response_generation"

    Returns:
        BaseLLMClient instance
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower().strip()
    model = model or os.getenv("LLM_MODEL")

    if provider == "openai":
        from src.llm.openai_provider import OpenAIProvider

        client = OpenAIProvider(model=model, api_key=api_key)
        _log_client_load(provider, getattr(client, "model", str(model)), purpose)
        return client
    elif provider == "anthropic":
        from src.llm.anthropic_provider import AnthropicProvider

        client = AnthropicProvider(model=model, api_key=api_key)
        _log_client_load(provider, getattr(client, "model", str(model)), purpose)
        return client
    elif provider == "google":
        from src.llm.google_provider import GoogleProvider

        client = GoogleProvider(model=model, api_key=api_key)
        resolved = getattr(client, "model_name", None) or str(model)
        _log_client_load(provider, resolved, purpose)
        return client
    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            f"Supported: openai, anthropic, google"
        )
