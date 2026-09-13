"""
Flight Agent — searches for flights and populates state['flight_results'].
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage

from .base_agent import BaseAgent
from ..config.prompts import FLIGHT_AGENT_SYSTEM_PROMPT
from ..tools.flight_tools import FLIGHT_TOOLS

logger = logging.getLogger(__name__)


class FlightAgent(BaseAgent):
    """
    Specialist agent for flight search.

    Uses AviationStack as the primary source and Tavily web search as fallback.
    Outputs structured flight options into TravelState.flight_results.
    """

    name = "flight_agent"
    system_prompt = FLIGHT_AGENT_SYSTEM_PROMPT
    tools = FLIGHT_TOOLS

    def build_input_message(self, state: dict) -> str:
        """
        Construct the human-turn prompt from the current travel state.
        """
        origin = state.get("origin", "")
        destination = state.get("destination", "")
        departure_date = state.get("departure_date", "")
        return_date = state.get("return_date")
        num_travelers = state.get("num_travelers", 1)
        budget = state.get("budget", "")
        user_query = state.get("user_query", "")

        lines = [
            f"User request: {user_query}",
            "",
            "Please search for flights with the following details:",
            f"- Origin: {origin}",
            f"- Destination: {destination}",
            f"- Departure date: {departure_date}",
        ]
        if return_date:
            lines.append(f"- Return date: {return_date}")
        lines.append(f"- Number of travellers: {num_travelers}")
        if budget:
            lines.append(f"- Budget preference: {budget}")
        lines += [
            "",
            "Use the search_flights tool first. If it returns no results or an error, "
            "use search_flights_web as a fallback.",
            "Return the top 3-5 best options with a brief recommendation.",
        ]
        return "\n".join(lines)


# Module-level singleton
_flight_agent: FlightAgent | None = None


def get_flight_agent() -> FlightAgent:
    global _flight_agent
    if _flight_agent is None:
        _flight_agent = FlightAgent()
    return _flight_agent
