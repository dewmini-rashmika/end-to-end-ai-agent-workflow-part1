"""
LangGraph edge / routing logic.

Conditional edges decide what node to visit next based on the current state.
Keeps all routing rules in one place rather than scattered across node functions.
"""

from __future__ import annotations

import logging

from ..state.travel_state import TravelState

logger = logging.getLogger(__name__)

# Node name constants — avoids magic strings
NODE_PARSE_QUERY = "parse_query"
NODE_FLIGHT = "flight_agent"
NODE_HOTEL = "hotel_agent"
NODE_ITINERARY = "itinerary_agent"
NODE_FINAL = "final_response"
NODE_END = "__end__"


def route_after_parse(state: TravelState) -> str:
    """
    After query parsing, decide if we have enough info to continue.
    If the destination is still empty, end early with an error signal.
    """
    if not state.get("destination"):
        logger.warning(
            "[edge:route_after_parse] No destination found — ending early."
        )
        # We still continue to final_response so it can ask the user to clarify
        return NODE_FINAL

    logger.debug("[edge:route_after_parse] → %s", NODE_FLIGHT)
    return NODE_FLIGHT


def route_after_flight(state: TravelState) -> str:
    """
    After the flight agent, always proceed to hotel search.
    Even if flight results are empty, the hotel agent should still run.
    """
    errors = state.get("errors") or []
    if errors:
        logger.warning("[edge:route_after_flight] Errors present: %s", errors)
    return NODE_HOTEL


def route_after_hotel(state: TravelState) -> str:
    """
    After the hotel agent, always proceed to itinerary planning.
    """
    return NODE_ITINERARY


def route_after_itinerary(state: TravelState) -> str:
    """
    After the itinerary agent, always proceed to final response synthesis.
    """
    return NODE_FINAL
