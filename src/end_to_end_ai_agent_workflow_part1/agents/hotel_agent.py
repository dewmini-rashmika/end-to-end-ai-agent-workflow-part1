"""
Hotel Agent — searches for accommodation and populates state['hotel_results'].
"""

from __future__ import annotations

import logging

from .base_agent import BaseAgent
from ..config.prompts import HOTEL_AGENT_SYSTEM_PROMPT
from ..tools.hotel_tools import HOTEL_TOOLS

logger = logging.getLogger(__name__)


class HotelAgent(BaseAgent):
    """
    Specialist agent for hotel and accommodation search.

    Uses Google Places (when configured) and Tavily web search.
    Surfaces options across budget, mid-range, and luxury tiers.
    """

    name = "hotel_agent"
    system_prompt = HOTEL_AGENT_SYSTEM_PROMPT
    tools = HOTEL_TOOLS

    def build_input_message(self, state: dict) -> str:
        destination = state.get("destination", "")
        departure_date = state.get("departure_date", "")
        return_date = state.get("return_date")
        trip_duration = state.get("trip_duration_days", 0)
        num_travelers = state.get("num_travelers", 1)
        budget = state.get("budget", "")
        interests = state.get("interests", "")
        user_query = state.get("user_query", "")

        lines = [
            f"User request: {user_query}",
            "",
            "Please search for accommodation with the following criteria:",
            f"- Destination: {destination}",
            f"- Check-in: {departure_date}",
        ]
        if return_date:
            lines.append(f"- Check-out: {return_date}")
        if trip_duration:
            lines.append(f"- Duration: {trip_duration} night(s)")
        lines.append(f"- Guests: {num_travelers}")
        if budget:
            lines.append(f"- Budget tier: {budget}")
        if interests:
            lines.append(f"- Traveller interests (location preference): {interests}")
        lines += [
            "",
            "Use compare_hotel_tiers to show budget / mid-range / luxury options.",
            "Also use search_hotels_web for detailed descriptions and reviews.",
            "If GOOGLE_MAPS_API_KEY is available, use search_hotels_google for ratings.",
            "Return the top 5 options with a clear recommendation per tier.",
        ]
        return "\n".join(lines)


# Module-level singleton
_hotel_agent: HotelAgent | None = None


def get_hotel_agent() -> HotelAgent:
    global _hotel_agent
    if _hotel_agent is None:
        _hotel_agent = HotelAgent()
    return _hotel_agent
