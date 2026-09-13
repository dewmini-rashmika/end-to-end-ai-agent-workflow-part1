"""
Final Response Agent — synthesises all agent outputs into the polished user-facing plan.
"""

from __future__ import annotations

import json
import logging

from .base_agent import BaseAgent
from ..config.prompts import FINAL_RESPONSE_AGENT_SYSTEM_PROMPT
from ..tools.general_tools import GENERAL_TOOLS

logger = logging.getLogger(__name__)


class FinalResponseAgent(BaseAgent):
    """
    Orchestrating agent that combines flight results, hotel options,
    and the itinerary into a single, coherent, polished travel plan.

    Also enriches the plan with visa info, weather, currency, and budget estimates.
    """

    name = "final_response_agent"
    system_prompt = FINAL_RESPONSE_AGENT_SYSTEM_PROMPT
    tools = GENERAL_TOOLS

    def build_input_message(self, state: dict) -> str:
        destination = state.get("destination", "")
        origin = state.get("origin", "")
        departure_date = state.get("departure_date", "")
        return_date = state.get("return_date")
        trip_duration = state.get("trip_duration_days", 0)
        num_travelers = state.get("num_travelers", 1)
        budget = state.get("budget", "mid-range")
        interests = state.get("interests", "")
        user_query = state.get("user_query", "")

        # Serialise agent outputs compactly for injection into the prompt
        flight_results = state.get("flight_results", [])
        hotel_results = state.get("hotel_results", [])
        itinerary = state.get("itinerary", [])

        # Convert to readable summaries if they are dicts / TypedDicts
        flights_text = self._format_section("FLIGHT RESULTS", flight_results)
        hotels_text = self._format_section("HOTEL RESULTS", hotel_results)
        itinerary_text = self._format_section("ITINERARY", itinerary)

        lines = [
            f"User request: {user_query}",
            "",
            "Trip details:",
            f"- Origin: {origin}",
            f"- Destination: {destination}",
            f"- Dates: {departure_date}" + (f" → {return_date}" if return_date else ""),
            f"- Duration: {trip_duration} day(s)",
            f"- Travellers: {num_travelers}",
            f"- Budget: {budget}",
            f"- Interests: {interests or 'general sightseeing'}",
            "",
            flights_text,
            "",
            hotels_text,
            "",
            itinerary_text,
            "",
            "Instructions:",
            "1. Synthesise the above into a single, polished travel plan.",
            "2. Use search_travel_tips to add practical advice for the destination.",
            "3. Use get_weather_forecast for the travel month.",
            "4. Use get_currency_info for money/tipping guidance.",
            "5. Use estimate_trip_budget to provide a rough cost breakdown.",
            "6. If the user has a non-local nationality, use get_visa_requirements.",
            "",
            "Structure your response as:",
            "1. Trip Summary  2. Flights  3. Accommodation  "
            "4. Day-by-Day Itinerary  5. Practical Tips  6. Budget Breakdown",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_section(title: str, data: list) -> str:
        if not data:
            return f"--- {title} ---\nNo data available from the specialist agent."
        try:
            text = json.dumps(data, indent=2, default=str)
            # Truncate very long outputs to avoid exceeding context window
            if len(text) > 1500:
                text = text[:1500] + "\n... (truncated)"
        except (TypeError, ValueError):
            text = str(data)[:1500]
        return f"--- {title} ---\n{text}"


# Module-level singleton
_final_response_agent: FinalResponseAgent | None = None


def get_final_response_agent() -> FinalResponseAgent:
    global _final_response_agent
    if _final_response_agent is None:
        _final_response_agent = FinalResponseAgent()
    return _final_response_agent
