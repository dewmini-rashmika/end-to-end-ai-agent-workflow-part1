"""
Itinerary Agent — builds the day-by-day travel plan and populates state['itinerary'].
"""

from __future__ import annotations

import logging

from .base_agent import BaseAgent
from ..config.prompts import ITINERARY_AGENT_SYSTEM_PROMPT
from ..tools.itinerary_tools import ITINERARY_TOOLS

logger = logging.getLogger(__name__)


class ItineraryAgent(BaseAgent):
    """
    Specialist agent for day-wise itinerary planning.

    Uses Tavily for attractions/restaurants and Google Maps for directions.
    Produces a structured day-by-day plan in TravelState.itinerary.
    """

    name = "itinerary_agent"
    system_prompt = ITINERARY_AGENT_SYSTEM_PROMPT
    tools = ITINERARY_TOOLS

    def build_input_message(self, state: dict) -> str:
        destination = state.get("destination", "")
        departure_date = state.get("departure_date", "")
        return_date = state.get("return_date")
        trip_duration = state.get("trip_duration_days", 3)
        num_travelers = state.get("num_travelers", 1)
        budget = state.get("budget", "")
        interests = state.get("interests", "")
        user_query = state.get("user_query", "")

        lines = [
            f"User request: {user_query}",
            "",
            "Please create a detailed day-by-day itinerary with the following details:",
            f"- Destination: {destination}",
            f"- Arrival date: {departure_date}",
        ]
        if return_date:
            lines.append(f"- Departure date: {return_date}")
        lines.append(f"- Trip duration: {trip_duration} day(s)")
        lines.append(f"- Travellers: {num_travelers}")
        if budget:
            lines.append(f"- Budget: {budget}")
        if interests:
            lines.append(f"- Interests: {interests}")
        lines += [
            "",
            "Instructions:",
            "1. Use search_attractions to find the top sights and activities.",
            "2. Use search_restaurants for dining recommendations.",
            "3. Use get_travel_directions to estimate travel time between key locations.",
            "4. Use search_local_events to check for any events during the trip dates.",
            "5. Use search_day_trips to suggest any worthwhile excursions.",
            "",
            "Format the itinerary as Day 1, Day 2, … with Morning / Afternoon / Evening slots.",
            "Group nearby activities to minimise backtracking.",
        ]
        return "\n".join(lines)


# Module-level singleton
_itinerary_agent: ItineraryAgent | None = None


def get_itinerary_agent() -> ItineraryAgent:
    global _itinerary_agent
    if _itinerary_agent is None:
        _itinerary_agent = ItineraryAgent()
    return _itinerary_agent
