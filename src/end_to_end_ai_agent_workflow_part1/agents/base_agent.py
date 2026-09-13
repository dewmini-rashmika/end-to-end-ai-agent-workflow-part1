"""
Base agent class.

All four specialist agents inherit from this. It handles:
- LLM initialisation with Groq
- Tool binding
- Structured invoke / stream interface
- Error handling and logging
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception

from ..config.settings import settings
from ..utils.langsmith_setup import get_run_name, get_langsmith_tags, get_langsmith_metadata

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base for all TripMate specialist agents.

    Subclasses must define:
        - name: str — unique agent identifier
        - system_prompt: str — injected as the first SystemMessage
        - tools: list[BaseTool] — bound to the LLM
    """

    name: str = "base_agent"
    system_prompt: str = ""
    tools: list[BaseTool] = []

    def __init__(self):
        self._llm = self._build_llm()
        self._llm_with_tools = self._llm.bind_tools(self.tools) if self.tools else self._llm
        logger.debug("Agent '%s' initialised with %d tool(s).", self.name, len(self.tools))

    # ------------------------------------------------------------------
    # LLM factory
    # ------------------------------------------------------------------

    @staticmethod
    def _build_llm():
        if settings.llm.gemini_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            logger.info("Using Google Gemini API (%s)", settings.llm.gemini_model_name)
            return ChatGoogleGenerativeAI(
                model=settings.llm.gemini_model_name,
                api_key=settings.llm.gemini_api_key,
                temperature=settings.llm.temperature,
                max_tokens=settings.llm.max_tokens,
            )
        else:
            logger.info("Using Groq API (%s)", settings.llm.model_name)
            return ChatGroq(
                api_key=settings.llm.api_key,
                model=settings.llm.model_name,
                temperature=settings.llm.temperature,
                max_tokens=settings.llm.max_tokens,
                streaming=settings.llm.streaming,
            )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @staticmethod
    def _is_rate_limit(exc: Exception) -> bool:
        msg = str(exc).lower()
        return "429" in msg or "413" in msg or "rate limit" in msg or "too large" in msg

    @retry(
        wait=wait_exponential(multiplier=2, min=5, max=30),
        stop=stop_after_attempt(5),
        retry=retry_if_exception(_is_rate_limit),
        reraise=True
    )
    def invoke(
        self,
        messages: list[BaseMessage],
        session_id: str = "",
        conversation_id: str = "",
        **kwargs: Any,
    ) -> AIMessage:
        """
        Run the agent with the given message history.

        Prepends the system prompt if it is not already the first message.
        Attaches LangSmith run metadata when tracing is enabled.
        Returns the AIMessage response.
        """
        full_messages = self._build_messages(messages)
        start = time.perf_counter()

        # Build LangSmith run config
        run_config: dict[str, Any] = {}
        if settings.langsmith.enabled and session_id:
            run_config = {
                "run_name": get_run_name(self.name, session_id),
                "tags": get_langsmith_tags(self.name),
                "metadata": get_langsmith_metadata(session_id, conversation_id),
            }

        try:
            response: AIMessage = self._llm_with_tools.invoke(
                full_messages, config=run_config if run_config else None, **kwargs
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "Agent '%s' responded in %dms | tokens: %s",
                self.name,
                elapsed_ms,
                getattr(response, "usage_metadata", "N/A"),
            )
            return response
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            if self._is_rate_limit(exc):
                logger.warning("Agent '%s' hit rate limit after %dms. Retrying...", self.name, elapsed_ms)
                raise  # Tenacity catches this
            logger.error(
                "Agent '%s' failed after %dms: %s", self.name, elapsed_ms, exc
            )
            raise

    def get_system_message(self) -> SystemMessage:
        return SystemMessage(content=self.system_prompt)

    # ------------------------------------------------------------------
    # Abstract hook (optional override for subclasses)
    # ------------------------------------------------------------------

    @abstractmethod
    def build_input_message(self, state: dict) -> str:
        """
        Build the human-turn message text from the current TravelState.
        Each agent formats the prompt differently based on what it needs.
        """
        ...

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_messages(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """Ensure the system message is always first."""
        if messages and isinstance(messages[0], SystemMessage):
            return messages
        return [self.get_system_message()] + list(messages)
