"""
TravelService — high-level service that orchestrates the full agent pipeline
outside of LangGraph (useful for testing and direct invocation).

For the main production flow, the LangGraph graph in graph/workflow.py is used.
This service is a convenience wrapper for programmatic / script-level usage.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from datetime import datetime, date
from typing import Any

from ..agents import (
    get_flight_agent,
    get_hotel_agent,
    get_itinerary_agent,
    get_final_response_agent,
)
from ..services.agent_executor import execute_agent
from ..state.travel_state import TravelState

logger = logging.getLogger(__name__)


class TravelService:
    """
    Orchestrates all four agents sequentially and returns a complete TravelState.

    Usage:
        service = TravelService()
        result = await service.plan_trip(user_query="...", session_id="abc")
    """

    def __init__(self):
        self._flight_agent = get_flight_agent()
        self._hotel_agent = get_hotel_agent()
        self._itinerary_agent = get_itinerary_agent()
        self._final_agent = get_final_response_agent()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plan_trip(
        self,
        user_query: str,
        session_id: str | None = None,
        overrides: dict | None = None,
    ) -> TravelState:
        """
        Run the full 4-agent pipeline for a travel query.

        Args:
            user_query:  Natural-language travel request from the user.
            session_id:  Optional session identifier (generated if not provided).
            overrides:   Optional dict to pre-set parsed travel parameters
                         (origin, destination, departure_date, etc.).

        Returns:
            Completed TravelState with all agent outputs.
        """
        session_id = session_id or str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        logger.info(
            "TravelService.plan_trip | session=%s | query=%s",
            session_id, user_query[:80],
        )

        # Build initial state
        state: TravelState = {
            "user_query": user_query,
            "session_id": session_id,
            "conversation_id": conversation_id,
            "messages": [],
            "flight_results": [],
            "hotel_results": [],
            "itinerary": [],
            "final_response": "",
            "errors": [],
            "completed_agents": [],
            "current_agent": "",
            # Defaults — overridden by parse or by caller
            "origin": "",
            "destination": "",
            "departure_date": "",
            "return_date": None,
            "num_travelers": 1,
            "trip_duration_days": 3,
            "budget": "mid-range",
            "interests": "",
        }

        # Apply any caller-supplied overrides (e.g. pre-parsed params)
        if overrides:
            state.update(overrides)

        # Auto-parse if origin/destination are still empty
        if not state["origin"] or not state["destination"]:
            parsed = self._parse_query(user_query)
            state.update({k: v for k, v in parsed.items() if v})

        # ---- Agent 1: Flights ----
        state = self._run_agent(self._flight_agent, state, "flight_results")

        # ---- Agent 2: Hotels ----
        state = self._run_agent(self._hotel_agent, state, "hotel_results")

        # ---- Agent 3: Itinerary ----
        state = self._run_agent(self._itinerary_agent, state, "itinerary")

        # ---- Agent 4: Final Response ----
        state = self._run_final_agent(state)

        logger.info(
            "TravelService.plan_trip complete | session=%s | agents=%s",
            session_id, state.get("completed_agents"),
        )
        return state

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_agent(
        self,
        agent: Any,
        state: TravelState,
        result_key: str,
    ) -> TravelState:
        """Run a single agent, capture its text output, and store in state."""
        agent_name = agent.name
        state["current_agent"] = agent_name
        logger.info("Running agent: %s", agent_name)

        start = time.perf_counter()
        try:
            text, new_messages = execute_agent(agent, state)
            elapsed_ms = int((time.perf_counter() - start) * 1000)

            # Store the raw text output — the graph nodes do structured parsing;
            # here we store as a single-item list with the text for simplicity
            existing = list(state.get(result_key) or [])
            existing.append({"raw_text": text, "agent": agent_name})
            state[result_key] = existing  # type: ignore[literal-required]

            # Extend the message history
            existing_msgs = list(state.get("messages") or [])
            state["messages"] = existing_msgs + new_messages

            completed = list(state.get("completed_agents") or [])
            completed.append(agent_name)
            state["completed_agents"] = completed

            logger.info("Agent %s done in %dms.", agent_name, elapsed_ms)

        except Exception as exc:
            logger.error("Agent %s failed: %s", agent_name, exc, exc_info=True)
            errors = list(state.get("errors") or [])
            errors.append(f"{agent_name}: {exc}")
            state["errors"] = errors

        return state

    def _run_final_agent(self, state: TravelState) -> TravelState:
        """Run the final response agent and store its output."""
        agent = self._final_agent
        state["current_agent"] = agent.name
        logger.info("Running final response agent.")

        try:
            text, new_messages = execute_agent(agent, state)
            state["final_response"] = text
            existing_msgs = list(state.get("messages") or [])
            state["messages"] = existing_msgs + new_messages
            completed = list(state.get("completed_agents") or [])
            completed.append(agent.name)
            state["completed_agents"] = completed
        except Exception as exc:
            logger.error("Final response agent failed: %s", exc, exc_info=True)
            errors = list(state.get("errors") or [])
            errors.append(f"{agent.name}: {exc}")
            state["errors"] = errors
            state["final_response"] = (
                "I encountered an error while generating your travel plan. "
                "Please try again. Details: " + str(exc)
            )

        return state

    @staticmethod
    def _parse_query(query: str) -> dict:
        """
        Very lightweight heuristic parser to extract travel parameters from
        free-text queries. The LLM-based graph approach in workflow.py is
        the preferred production path — this is a fallback for direct service calls.
        """
        parsed: dict = {}

        # Attempt to extract a date like "15 October 2026" or "2026-10-15"
        date_patterns = [
            r"\b(\d{4}-\d{2}-\d{2})\b",
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        ]
        for pattern in date_patterns:
            m = re.search(pattern, query)
            if m and not parsed.get("departure_date"):
                parsed["departure_date"] = m.group(1)

        # Extract number of days: "5 days", "a week"
        days_match = re.search(r"\b(\d+)\s*days?\b", query, re.IGNORECASE)
        if days_match:
            parsed["trip_duration_days"] = int(days_match.group(1))
        elif re.search(r"\b(a\s+)?week\b", query, re.IGNORECASE):
            parsed["trip_duration_days"] = 7

        # Extract traveller count: "2 people", "family of 4"
        pax_match = re.search(
            r"\b(\d+)\s*(people|person|travell?er|adult|pax)\b", query, re.IGNORECASE
        )
        if pax_match:
            parsed["num_travelers"] = int(pax_match.group(1))

        # Budget tier
        if re.search(r"\bluxury\b", query, re.IGNORECASE):
            parsed["budget"] = "luxury"
        elif re.search(r"\bbudget\b|\bcheap\b", query, re.IGNORECASE):
            parsed["budget"] = "budget"
        else:
            parsed["budget"] = "mid-range"

        return parsed


# Module-level singleton
_travel_service: TravelService | None = None


def get_travel_service() -> TravelService:
    global _travel_service
    if _travel_service is None:
        _travel_service = TravelService()
    return _travel_service
