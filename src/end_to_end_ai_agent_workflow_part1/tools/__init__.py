"""
Tools package — LangChain tools grouped by agent.

Each agent imports its own tool list. The lists are also exported here
for convenience (e.g. the graph builder needs them all).
"""

from .flight_tools import FLIGHT_TOOLS, search_flights, search_flights_web, get_airport_info
from .hotel_tools import HOTEL_TOOLS, search_hotels_google, search_hotels_web, get_hotel_details, compare_hotel_tiers
from .itinerary_tools import (
    ITINERARY_TOOLS,
    search_attractions,
    search_restaurants,
    get_travel_directions,
    search_day_trips,
    search_local_events,
)
from .general_tools import (
    GENERAL_TOOLS,
    search_travel_tips,
    get_visa_requirements,
    get_currency_info,
    get_weather_forecast,
    estimate_trip_budget,
)

# All tools combined — useful for documentation / testing
ALL_TOOLS = FLIGHT_TOOLS + HOTEL_TOOLS + ITINERARY_TOOLS + GENERAL_TOOLS

__all__ = [
    "FLIGHT_TOOLS",
    "HOTEL_TOOLS",
    "ITINERARY_TOOLS",
    "GENERAL_TOOLS",
    "ALL_TOOLS",
    # Individual tools
    "search_flights",
    "search_flights_web",
    "get_airport_info",
    "search_hotels_google",
    "search_hotels_web",
    "get_hotel_details",
    "compare_hotel_tiers",
    "search_attractions",
    "search_restaurants",
    "get_travel_directions",
    "search_day_trips",
    "search_local_events",
    "search_travel_tips",
    "get_visa_requirements",
    "get_currency_info",
    "get_weather_forecast",
    "estimate_trip_budget",
]
