"""
OpenAI LLM Provider (GPT-4o, GPT-4o-mini, GPT-4.1, etc.)
"""

import os
from typing import List, Dict, Any, Optional

from src.llm.base import BaseLLMClient


class OpenAIProvider(BaseLLMClient):
    """OpenAI API provider (GPT models)."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            from src.config.credentials import CredentialsManager
            api_key = CredentialsManager().get_api_key("openai")
        self.client = __import__("openai").OpenAI(api_key=api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        # Newer models (GPT-5, GPT-4.1+) require max_completion_tokens
        # Some models (e.g. reasoning models) only support temperature=1
        api_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
            **kwargs
        }
        try:
            response = self.client.chat.completions.create(**api_params)
        except Exception as e:
            err_msg = str(e).lower()
            if "temperature" in err_msg and "only the default" in err_msg:
                # Retry with temperature=1 for models that don't support custom temperature
                api_params["temperature"] = 1
                response = self.client.chat.completions.create(**api_params)
            else:
                raise
        choices = getattr(response, "choices", None) or []
        if not choices:
            return (
                "[The model returned no completion choices. "
                "Try again or check OPENAI_API_KEY / model name.]"
            )
        content = choices[0].message.content
        return (content or "").strip()
