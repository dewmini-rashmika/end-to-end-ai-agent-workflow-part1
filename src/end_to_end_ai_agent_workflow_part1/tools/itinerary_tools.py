"""
LangChain tools for the Itinerary Agent.
Uses Tavily for attractions and Google Maps for directions/distances.
"""

import logging

from langchain_core.tools import tool

from ..clients.tavily_client import get_tavily_client
from ..clients.google_maps_client import get_google_maps_client

logger = logging.getLogger(__name__)


@tool
def search_attractions(
    destination: str,
    interests: str = "",
    days: int = 3,
) -> str:
    """
    Search for top tourist attractions and activities at a destination.

    Args:
        destination: City or region to search in, e.g. 'Kyoto, Japan'.
        interests:   Traveller interests, e.g. 'history temples food street art'.
        days:        Number of trip days to calibrate the volume of suggestions.

    Returns:
        A curated list of attractions and activities.
    """
    client = get_tavily_client()
    interest_hint = f" focusing on {interests}" if interests else ""
    query = (
        f"top tourist attractions things to do in {destination}{interest_hint} "
        f"must-see places local experiences itinerary {days} days"
    )
    response = client.search_attractions(destination, interests)

    if not response.results and not response.answer:
        return f"No attraction data found for '{destination}'."

    output_parts = [f"Top attractions in {destination}:\n"]
    if response.answer:
        output_parts.append(f"Overview: {response.answer}\n")

    for i, r in enumerate(response.results[:6], 1):
        output_parts.append(
            f"{i}. {r.title}\n"
            f"   {r.content[:400]}\n"
            f"   Source: {r.url}\n"
        )
    return "\n".join(output_parts)


@tool
def search_restaurants(
    destination: str,
    cuisine: str = "",
    budget: str = "",
) -> str:
    """
    Search for the best restaurants and local food experiences at a destination.

    Args:
        destination: City or area.
        cuisine:     Cuisine type, e.g. 'Italian', 'street food', 'vegan'.
        budget:      Budget range, e.g. 'budget', 'fine dining', 'under $20'.

    Returns:
        A list of recommended dining options.
    """
    client = get_tavily_client()
    parts = [f"best restaurants local food {destination}"]
    if cuisine:
        parts.append(cuisine)
    if budget:
        parts.append(budget)
    parts.append("must try dishes 2025 recommendations")

    response = client.search(" ".join(parts), search_depth="advanced", include_answer=True)

    if not response.results and not response.answer:
        return f"No restaurant info found for '{destination}'."

    output_parts = [f"Dining options in {destination}:\n"]
    if response.answer:
        output_parts.append(f"Summary: {response.answer}\n")

    for i, r in enumerate(response.results[:5], 1):
        output_parts.append(f"{i}. {r.title}\n   {r.content[:350]}\n   Source: {r.url}\n")
    return "\n".join(output_parts)


@tool
def get_travel_directions(
    origin: str,
    destination: str,
    mode: str = "driving",
) -> str:
    """
    Get travel time and distance between two locations using Google Maps Directions.
    Falls back to a web search estimate if Google Maps is not configured.

    Args:
        origin:      Starting location, e.g. 'Eiffel Tower, Paris'.
        destination: Ending location, e.g. 'Louvre Museum, Paris'.
        mode:        Travel mode — 'driving', 'walking', or 'transit'.

    Returns:
        Travel time and distance as a formatted string.
    """
    maps_client = get_google_maps_client()
    direction = maps_client.get_directions(origin, destination, mode)

    if direction:
        return (
            f"Route: {origin} → {destination}\n"
            f"Mode: {mode}\n"
            f"Distance: {direction.distance_km} km\n"
            f"Duration: ~{direction.duration_minutes} minutes\n"
            f"Via: {direction.summary or 'N/A'}"
        )

    # Fallback: web search estimate
    tavily = get_tavily_client()
    query = f"travel time from {origin} to {destination} by {mode}"
    response = tavily.search(query, search_depth="basic", include_answer=True, max_results=2)
    if response.answer:
        return f"Estimated travel ({origin} → {destination} by {mode}):\n{response.answer}"
    return f"Could not determine travel time from {origin} to {destination}."


@tool
def search_day_trips(destination: str) -> str:
    """
    Search for popular day trips and excursions from a destination.

    Args:
        destination: Base city, e.g. 'Barcelona'.

    Returns:
        A list of recommended day trip options with estimated travel times.
    """
    client = get_tavily_client()
    query = f"best day trips from {destination} nearby destinations excursions 2025"
    response = client.search(query, search_depth="advanced", include_answer=True)

    if not response.results and not response.answer:
        return f"No day trip suggestions found for '{destination}'."

    output_parts = [f"Day trips from {destination}:\n"]
    if response.answer:
        output_parts.append(f"Overview: {response.answer}\n")

    for i, r in enumerate(response.results[:4], 1):
        output_parts.append(f"{i}. {r.title}\n   {r.content[:300]}\n   Source: {r.url}\n")
    return "\n".join(output_parts)


@tool
def search_local_events(destination: str, travel_dates: str = "") -> str:
    """
    Search for local events, festivals, and seasonal activities at a destination.

    Args:
        destination:  City or region.
        travel_dates: Travel period, e.g. 'October 2026', 'Christmas week'.

    Returns:
        A summary of events and festivals happening during the visit.
    """
    client = get_tavily_client()
    date_hint = f" in {travel_dates}" if travel_dates else ""
    query = f"local events festivals things happening in {destination}{date_hint}"
    response = client.search(query, search_depth="basic", include_answer=True)

    if not response.results and not response.answer:
        return f"No events found for '{destination}' during '{travel_dates}'."

    output_parts = [f"Events & festivals in {destination}{date_hint}:\n"]
    if response.answer:
        output_parts.append(response.answer + "\n")
    for i, r in enumerate(response.results[:4], 1):
        output_parts.append(f"{i}. {r.title}\n   {r.content[:250]}\n")
    return "\n".join(output_parts)


# Exported list for agent binding
ITINERARY_TOOLS = [
    search_attractions,
    search_restaurants,
    get_travel_directions,
    search_day_trips,
    search_local_events,
]
