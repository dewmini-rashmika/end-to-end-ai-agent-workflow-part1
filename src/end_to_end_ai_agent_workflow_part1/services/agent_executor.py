"""
Agent executor service.

Runs the ReAct tool-use loop for a single agent:
  1. Send messages to the LLM (with tools bound)
  2. If the LLM calls a tool, execute it and append the result
  3. Repeat until the LLM returns a final text response (no tool calls)

This is intentionally decoupled from LangGraph so each agent node in the
graph can call it cleanly. LangSmith tracing metadata is forwarded to
every agent.invoke() call so all LLM calls appear under the same trace.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool

from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 10  # Safety cap on tool-call loops


def execute_agent(
    agent: BaseAgent,
    state: dict,
    extra_messages: list[BaseMessage] | None = None,
) -> tuple[str, list[BaseMessage]]:
    """
    Run the full ReAct loop for an agent against the current TravelState.

    Args:
        agent:          The specialist agent to run.
        state:          Current TravelState dict.
        extra_messages: Optional additional context messages.

    Returns:
        (final_text, all_messages) — the agent's final text response and
        the full updated message list including tool calls and results.
    """
    # Extract tracing context from state
    session_id: str = state.get("session_id", "")
    conversation_id: str = state.get("conversation_id", "")

    # Build the initial human-turn message from state
    human_text = agent.build_input_message(state)
    messages: list[BaseMessage] = list(extra_messages or [])
    messages.append(HumanMessage(content=human_text))

    # Build a name → tool lookup for fast dispatch
    tool_map: dict[str, BaseTool] = {t.name: t for t in agent.tools}

    start_total = time.perf_counter()
    iterations = 0

    while iterations < MAX_TOOL_ITERATIONS:
        iterations += 1
        response: AIMessage = agent.invoke(
            messages,
            session_id=session_id,
            conversation_id=conversation_id,
        )
        messages.append(response)

        # No tool calls — we have the final answer
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            if isinstance(response.content, list):
                final_text = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in response.content
                )
            else:
                final_text = str(response.content)

            elapsed = int((time.perf_counter() - start_total) * 1000)
            logger.info(
                "Agent '%s' completed in %dms after %d iteration(s).",
                agent.name, elapsed, iterations,
            )
            return final_text, messages

        # Execute all tool calls returned in this response
        for tc in tool_calls:
            tool_name: str = tc["name"]
            tool_args: dict = tc.get("args", {})
            tool_call_id: str = tc["id"]

            tool = tool_map.get(tool_name)
            if tool is None:
                tool_result = f"Error: unknown tool '{tool_name}'."
                logger.warning("Agent '%s' called unknown tool: %s", agent.name, tool_name)
            else:
                logger.debug(
                    "Agent '%s' → tool '%s' args=%s", agent.name, tool_name, tool_args
                )
                try:
                    tool_result = tool.invoke(tool_args)
                except Exception as exc:
                    tool_result = f"Tool '{tool_name}' raised an error: {exc}"
                    logger.error(
                        "Tool '%s' error for agent '%s': %s",
                        tool_name, agent.name, exc,
                    )

            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            )

    # Exceeded max iterations — ask for a final answer without tools
    logger.warning(
        "Agent '%s' hit max tool iterations (%d). Forcing final response.",
        agent.name, MAX_TOOL_ITERATIONS,
    )
    messages.append(
        HumanMessage(
            content=(
                "You have reached the maximum number of tool calls. "
                "Please provide your final answer based on the information gathered so far."
            )
        )
    )
    response = agent.invoke(
        messages,
        session_id=session_id,
        conversation_id=conversation_id,
    )
    messages.append(response)
    if isinstance(response.content, list):
        final_text = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in response.content
        )
    else:
        final_text = str(response.content)
    return final_text, messages
