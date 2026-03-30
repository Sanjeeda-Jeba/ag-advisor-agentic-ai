"""
LLM feature flags (on/off) from environment variables.

Loads .env from project root so flags work even if nothing else imported dotenv yet.
"""

from pathlib import Path
import os
from typing import Optional

try:
    from dotenv import load_dotenv

    _PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass


def _parse_bool_env(raw: Optional[str], default: bool) -> bool:
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def is_llm_enabled() -> bool:
    """
    Master switch for LLM features (default: on).

    Env: LLM_ENABLED=true|false (default true)
    When false, intent + response LLM are off unless overridden below.
    """
    return _parse_bool_env(os.getenv("LLM_ENABLED"), True)


def is_llm_intent_enabled() -> bool:
    """
    Use LLM for tool / intent routing (ToolMatcher fallback path).

    Env: LLM_INTENT_ENABLED — if unset, follows LLM_ENABLED.
    """
    raw = os.getenv("LLM_INTENT_ENABLED")
    if raw is not None and str(raw).strip() != "":
        return _parse_bool_env(raw, True)
    return is_llm_enabled()


def is_llm_response_enabled() -> bool:
    """
    Use LLM to turn tool outputs into natural language (ToolExecutor).

    Env: LLM_RESPONSE_ENABLED — if unset, follows LLM_ENABLED.
    """
    raw = os.getenv("LLM_RESPONSE_ENABLED")
    if raw is not None and str(raw).strip() != "":
        return _parse_bool_env(raw, True)
    return is_llm_enabled()
