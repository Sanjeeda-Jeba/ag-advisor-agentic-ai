"""
Google LLM Provider (Gemini models)
"""

import os
from typing import List, Dict, Any, Optional

from src.llm.base import BaseLLMClient


class GoogleProvider(BaseLLMClient):
    """Google AI provider (Gemini models)."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model or os.getenv("LLM_MODEL", "gemini-2.0-flash")
        api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            from src.config.credentials import CredentialsManager
            api_key = CredentialsManager().get_api_key("google")
        genai = __import__("google.generativeai", fromlist=["genai"])
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        # Gemini: combine system + user/assistant into a single prompt
        # (Gemini doesn't have separate system role in the same way)
        parts = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                parts.append(f"System: {content}")
            elif role == "user":
                parts.append(f"User: {content}")
            else:
                parts.append(f"Assistant: {content}")
        prompt = "\n\n".join(parts)

        # response_format (OpenAI-style) not supported; ignore if passed
        kwargs.pop("response_format", None)

        genai = __import__("google.generativeai", fromlist=["genai"])
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = self.model.generate_content(
            prompt,
            generation_config=generation_config,
            **kwargs
        )

        if not response.text:
            raise ValueError(
                f"Gemini returned empty response. "
                f"Blocked reason: {getattr(response, 'block_reason', 'unknown')}"
            )
        return response.text.strip()
