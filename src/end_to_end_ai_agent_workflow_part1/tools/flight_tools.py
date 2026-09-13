"""
LangChain tools for the Flight Agent.

Each tool is decorated with @tool so LangGraph can bind them to the LLM.
"""

import logging
from typing import Optional

from langchain_core.tools import tool

from ..clients.aviation_client import get_aviation_client
from ..clients.tavily_client import get_tavily_client
from ..clients.base import APIError

logger = logging.getLogger(__name__)


@tool
def search_flights(
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    limit: int = 10,
) -> str:
    """
    Search for available flights using the AviationStack API.

    Args:
        origin_iata:      IATA airport code for the origin, e.g. 'CMB', 'LHR', 'JFK'.
        destination_iata: IATA airport code for the destination.
        departure_date:   Travel date in YYYY-MM-DD format.
        limit:            Maximum number of results to return (default 10).

    Returns:
        A formatted string listing available flights, or a fallback message.
    """
    client = get_aviation_client()
    try:
        options = client.search_flights(
            origin_iata=origin_iata,
            destination_iata=destination_iata,
            departure_date=departure_date,
            limit=limit,
        )
    except APIError as exc:
        logger.warning("AviationStack error, will fall back to web search: %s", exc)
        return (
            f"AviationStack API error ({exc.status_code}): {exc.message}. "
            "Use search_flights_web as a fallback."
        )

    if not options:
        return (
            f"No flights found via AviationStack for {origin_iata} → {destination_iata} "
            f"on {departure_date}. Use search_flights_web as a fallback."
        )

    lines = [
        f"Found {len(options)} flight(s) from {origin_iata} to {destination_iata} "
        f"on {departure_date}:\n"
    ]
    for i, opt in enumerate(options, 1):
        d = opt.to_dict()
        duration = f"{d['duration_minutes']} min" if d["duration_minutes"] else "N/A"
        price = f"${d['price_usd']:.0f}" if d["price_usd"] else "Price N/A (check airline)"
        lines.append(
            f"{i}. {d['flight_number']} | {d['airline']}\n"
            f"   {d['origin']} → {d['destination']}\n"
            f"   Departs: {d['departure']}  Arrives: {d['arrival']}\n"
            f"   Duration: {duration}  Stops: {d['stops']}  Price: {price}\n"
            f"   Status: {d['status']}  Aircraft: {d['aircraft'] or 'N/A'}\n"
        )
    return "\n".join(lines)


@tool
def search_flights_web(
    origin: str,
    destination: str,
    departure_date: str,
) -> str:
    """
    Fallback web search for flight information when the AviationStack API
    returns no results or encounters an error.

    Args:
        origin:         City name or airport name (e.g. 'Colombo', 'London Heathrow').
        destination:    City or airport name.
        departure_date: Travel date in YYYY-MM-DD format.

    Returns:
        A formatted string with flight info gathered from the web.
    """
    client = get_tavily_client()
    response = client.search_flights_web(origin, destination, departure_date)

    if not response.results and not response.answer:
        return f"No web results found for flights from {origin} to {destination} on {departure_date}."

    output_parts = [
        f"Web search results for flights {origin} → {destination} on {departure_date}:\n"
    ]
    if response.answer:
        output_parts.append(f"Summary: {response.answer}\n")

    for i, r in enumerate(response.results[:5], 1):
        output_parts.append(f"{i}. {r.title}\n   {r.content[:300]}...\n   Source: {r.url}\n")

    return "\n".join(output_parts)


@tool
def get_airport_info(iata_code: str) -> str:
    """
    Look up airport details (city, country, timezone) for a given IATA code.

    Args:
        iata_code: 3-letter IATA airport code, e.g. 'CMB', 'LHR'.

    Returns:
        Airport details as a formatted string.
    """
    client = get_aviation_client()
    info = client.get_airport_info(iata_code.upper())
    if not info:
        return f"No airport found for IATA code '{iata_code}'."
    return (
        f"Airport: {info.get('name', 'N/A')}\n"
        f"City: {info.get('city', 'N/A')}\n"
        f"Country: {info.get('country', 'N/A')}\n"
        f"IATA: {iata_code.upper()}\n"
        f"Timezone: {info.get('tz', 'N/A')}"
    )


# Exported list for agent binding
FLIGHT_TOOLS = [search_flights, search_flights_web, get_airport_info]
