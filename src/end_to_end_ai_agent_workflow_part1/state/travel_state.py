"""
Shared LangGraph state — TravelState.

All four agents read from and write to this single TypedDict.
LangGraph merges updates via the annotated reducer functions.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from typing_extensions import TypedDict


class FlightResult(TypedDict, total=False):
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure: str
    arrival: str
    duration_minutes: int | None
    stops: int
    price_usd: float | None
    status: str
    aircraft: str | None


class HotelResult(TypedDict, total=False):
    name: str
    address: str
    rating: float | None
    total_ratings: int
    price_level: int | None
    price_per_night_usd: float | None
    amenities: list[str]
    coordinates: dict[str, float]
    url: str | None
    tier: str   # "budget" | "mid-range" | "luxury"


class ItineraryDay(TypedDict, total=False):
    day: int
    date: str
    morning: str
    afternoon: str
    evening: str
    notes: str


class TravelState(TypedDict, total=False):
    # ------------------------------------------------------------------ #
    # Core query info — set once at the start, never overwritten           #
    # ------------------------------------------------------------------ #
    user_query: str
    session_id: str
    conversation_id: str

    # Parsed travel parameters (extracted from user query by the graph)
    origin: str
    destination: str
    departure_date: str           # YYYY-MM-DD
    return_date: str | None       # YYYY-MM-DD, None for one-way
    num_travelers: int
    trip_duration_days: int
    budget: str                   # "budget" | "mid-range" | "luxury" | ""
    interests: str                # free-text, e.g. "beaches, food, hiking"

    # ------------------------------------------------------------------ #
    # Agent outputs — accumulated across agent nodes                       #
    # ------------------------------------------------------------------ #
    flight_results: Annotated[list[FlightResult], operator.add]
    hotel_results: Annotated[list[HotelResult], operator.add]
    itinerary: Annotated[list[ItineraryDay], operator.add]

    # Final synthesised response
    final_response: str

    # ------------------------------------------------------------------ #
    # Conversation history — add_messages reducer deduplicates by id      #
    # ------------------------------------------------------------------ #
    messages: Annotated[list[BaseMessage], add_messages]

    # ------------------------------------------------------------------ #
    # Error tracking                                                        #
    # ------------------------------------------------------------------ #
    errors: Annotated[list[str], operator.add]

    # ------------------------------------------------------------------ #
    # Agent execution metadata                                             #
    # ------------------------------------------------------------------ #
    current_agent: str            # name of the currently executing agent
    completed_agents: Annotated[list[str], operator.add]
