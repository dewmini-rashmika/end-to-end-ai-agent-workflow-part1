"""
LangSmith tracing setup.

Configures the LangSmith / LangChain tracing environment variables so that
all LangChain and LangGraph calls are automatically traced without any code
changes in the agents.

Call `configure_langsmith()` once at startup (from app.py lifespan), right
after `configure_logging()`.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def configure_langsmith() -> None:
    """
    Set the LangSmith environment variables that LangChain reads automatically.

    LangChain looks for these env vars at import time / first call:
      - LANGCHAIN_TRACING_V2=true
      - LANGCHAIN_API_KEY=<your key>
      - LANGCHAIN_PROJECT=<project name>
      - LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

    Importing this module and calling configure_langsmith() is the canonical
    way to enable tracing without touching agent code.
    """
    # Import here to avoid circular import at module level
    from ..config.settings import settings

    if not settings.langsmith.enabled:
        logger.info("LangSmith tracing is DISABLED (set LANGSMITH_ENABLED=true to enable).")
        return

    if not settings.langsmith.api_key:
        logger.warning(
            "LangSmith is enabled but LANGSMITH_API_KEY is not set. "
            "Tracing will not work until you provide the key."
        )
        return

    # LangChain reads these os.environ values automatically
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith.api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith.project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith.endpoint

    logger.info(
        "LangSmith tracing ENABLED | project=%s | endpoint=%s",
        settings.langsmith.project,
        settings.langsmith.endpoint,
    )


def get_run_name(agent_name: str, session_id: str) -> str:
    """
    Build a structured run name for LangSmith traces.
    Appears as the run title in the LangSmith UI.
    """
    return f"TripMate/{agent_name}/{session_id[:8]}"


def get_langsmith_tags(agent_name: str) -> list[str]:
    """Return tags to attach to every LangSmith run for easy filtering."""
    return ["tripmate-ai", "part1", f"agent:{agent_name}"]


def get_langsmith_metadata(session_id: str, conversation_id: str) -> dict:
    """Return metadata dict attached to every LangSmith run."""
    return {
        "session_id": session_id,
        "conversation_id": conversation_id,
        "app": "tripmate-ai",
        "version": "1.0.0",
    }
