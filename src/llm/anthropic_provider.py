"""
Anthropic LLM Provider (Claude models)
"""

import os
from typing import List, Dict, Any, Optional

from src.llm.base import BaseLLMClient


class AnthropicProvider(BaseLLMClient):
    """Anthropic API provider (Claude models)."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or os.getenv("LLM_MODEL", "claude-sonnet-4-6")
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            from src.config.credentials import CredentialsManager
            api_key = CredentialsManager().get_api_key("anthropic")
        self.client = __import__("anthropic").Anthropic(api_key=api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        # Anthropic: system is separate, messages are user/assistant only
        system = ""
        chat_msgs = []
        for m in messages:
            if m.get("role") == "system":
                system = m.get("content", "")
            else:
                chat_msgs.append({
                    "role": m.get("role", "user"),
                    "content": m.get("content", "")
                })

        # response_format (OpenAI-style) not supported; ignore if passed
        kwargs.pop("response_format", None)

        response = self.client.messages.create(
            model=self.model,
            system=system,
            messages=chat_msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        blocks = getattr(response, "content", None) or []
        for block in blocks:
            text = getattr(block, "text", None)
            if text:
                return text
        if not blocks:
            return (
                "[The model returned no text (empty response). "
                "Try a shorter question or check ANTHROPIC_API_KEY / model settings.]"
            )
        return f"[No text block in model response; got {len(blocks)} content block(s).]"
