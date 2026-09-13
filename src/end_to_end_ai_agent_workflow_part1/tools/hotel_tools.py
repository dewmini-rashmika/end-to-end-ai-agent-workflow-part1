"""
LangChain tools for the Hotel Agent.
Combines Google Places (when available) with Tavily web search.
"""

import logging

from langchain_core.tools import tool

from ..clients.tavily_client import get_tavily_client
from ..clients.google_maps_client import get_google_maps_client

logger = logging.getLogger(__name__)


@tool
def search_hotels_google(
    city: str,
    max_results: int = 8,
) -> str:
    """
    Search for hotels in a city using Google Places API.
    Returns real ratings, price levels, and addresses.
    Falls back gracefully if the Google Maps API key is not configured.

    Args:
        city:        Destination city name, e.g. 'Paris', 'Tokyo', 'Colombo'.
        max_results: Maximum number of hotels to return (default 8).

    Returns:
        A formatted list of hotels with ratings and details.
    """
    client = get_google_maps_client()
    hotels = client.search_hotels(city, max_results=max_results)

    if not hotels:
        return (
            f"Google Places returned no hotels for '{city}'. "
            "Try search_hotels_web instead."
        )

    price_labels = {0: "Free", 1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}
    lines = [f"Hotels in {city} (via Google Places):\n"]
    for i, h in enumerate(hotels, 1):
        price = price_labels.get(h.price_level, "N/A") if h.price_level is not None else "N/A"
        rating = f"{h.rating}/5.0 ({h.total_ratings} reviews)" if h.rating else "No rating"
        open_now = "Open now" if h.open_now else ("Closed" if h.open_now is False else "Hours N/A")
        lines.append(
            f"{i}. {h.name}\n"
            f"   Address: {h.address}\n"
            f"   Rating: {rating}  Price: {price}\n"
            f"   Status: {open_now}\n"
            f"   Phone: {h.phone or 'N/A'}  Website: {h.website or 'N/A'}\n"
        )
    return "\n".join(lines)


@tool
def search_hotels_web(
    destination: str,
    budget: str = "",
    preferences: str = "",
) -> str:
    """
    Search for hotels using Tavily web search.
    Use this as the primary tool or as a fallback when Google Places is unavailable.

    Args:
        destination:  City or region to search in, e.g. 'Bangkok, Thailand'.
        budget:       Budget preference, e.g. 'under $100 per night', 'luxury', 'budget'.
        preferences:  Additional preferences, e.g. 'near beach', 'family-friendly', 'with pool'.

    Returns:
        A formatted string with hotel options gathered from the web.
    """
    client = get_tavily_client()

    query_parts = [f"best hotels in {destination}"]
    if budget:
        query_parts.append(f"budget {budget}")
    if preferences:
        query_parts.append(preferences)
    query_parts.append("price per night rating amenities reviews 2025")

    full_query = " ".join(query_parts)
    response = client.search(full_query, search_depth="advanced", include_answer=True)

    if not response.results and not response.answer:
        return f"No hotel information found for '{destination}'."

    output_parts = [f"Hotel search results for {destination}:\n"]
    if response.answer:
        output_parts.append(f"Summary: {response.answer}\n")

    for i, r in enumerate(response.results[:5], 1):
        output_parts.append(
            f"{i}. {r.title}\n"
            f"   {r.content[:400]}...\n"
            f"   Source: {r.url}\n"
        )
    return "\n".join(output_parts)


@tool
def get_hotel_details(place_id: str) -> str:
    """
    Get detailed information about a specific hotel using its Google Places ID.
    Requires GOOGLE_MAPS_API_KEY to be configured.

    Args:
        place_id: Google Places place_id obtained from search_hotels_google.

    Returns:
        Detailed hotel information as a formatted string.
    """
    client = get_google_maps_client()
    detail = client.get_place_details(place_id)

    if not detail:
        return f"Could not retrieve details for place_id '{place_id}'."

    price_labels = {0: "Free", 1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}
    price = price_labels.get(detail.price_level, "N/A") if detail.price_level is not None else "N/A"

    return (
        f"Hotel Details:\n"
        f"Name: {detail.name}\n"
        f"Address: {detail.address}\n"
        f"Rating: {detail.rating}/5.0 ({detail.total_ratings} reviews)\n"
        f"Price Level: {price}\n"
        f"Phone: {detail.phone or 'N/A'}\n"
        f"Website: {detail.website or 'N/A'}\n"
        f"Currently Open: {detail.open_now}\n"
        f"Types: {', '.join(detail.types[:5])}"
    )


@tool
def compare_hotel_tiers(destination: str) -> str:
    """
    Search for hotels across budget, mid-range, and luxury tiers simultaneously.

    Args:
        destination: City or region, e.g. 'Rome, Italy'.

    Returns:
        Structured comparison across three price tiers.
    """
    client = get_tavily_client()
    tiers = {
        "budget": f"cheap budget hostels guesthouses under $60 per night in {destination}",
        "mid-range": f"mid-range hotels $60-$150 per night in {destination} good reviews",
        "luxury": f"luxury 5-star hotels resorts in {destination} premium amenities",
    }

    output = [f"Hotel tiers comparison for {destination}:\n"]
    for tier, query in tiers.items():
        response = client.search(query, search_depth="basic", include_answer=True, max_results=3)
        output.append(f"--- {tier.upper()} ---")
        if response.answer:
            output.append(response.answer)
        elif response.results:
            output.append(response.results[0].content[:300])
        else:
            output.append("No results found for this tier.")
        output.append("")

    return "\n".join(output)


# Exported list for agent binding
HOTEL_TOOLS = [search_hotels_google, search_hotels_web, get_hotel_details, compare_hotel_tiers]
