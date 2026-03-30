"""
Abstract base interface for LLM providers
All providers (OpenAI, Anthropic, Google) must implement this interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseLLMClient(ABC):
    """Abstract interface all LLM providers must implement."""

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Send messages and return the assistant's reply.

        Args:
            messages: [{"role": "system"|"user"|"assistant", "content": "..."}, ...]
            temperature: 0-1, controls randomness
            max_tokens: maximum output tokens
            **kwargs: provider-specific options (e.g., response_format for OpenAI)

        Returns:
            Assistant reply text
        """
        pass
