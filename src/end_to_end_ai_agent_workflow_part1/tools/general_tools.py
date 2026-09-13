"""
General-purpose LangChain tools shared across agents.
Used primarily by the Final Response Agent for enrichment.
"""

import logging

from langchain_core.tools import tool

from ..clients.tavily_client import get_tavily_client

logger = logging.getLogger(__name__)


@tool
def search_travel_tips(destination: str) -> str:
    """
    Search for practical travel tips for a destination.
    Covers visa requirements, currency, weather, safety, and cultural etiquette.

    Args:
        destination: Country or city, e.g. 'Japan', 'Morocco', 'New York'.

    Returns:
        A formatted summary of practical travel information.
    """
    client = get_tavily_client()
    response = client.search_travel_tips(destination)

    if not response.results and not response.answer:
        return f"No travel tips found for '{destination}'."

    output_parts = [f"Travel tips for {destination}:\n"]
    if response.answer:
        output_parts.append(response.answer + "\n")
    for i, r in enumerate(response.results[:4], 1):
        output_parts.append(f"{i}. {r.title}\n   {r.content[:350]}\n")
    return "\n".join(output_parts)


@tool
def get_visa_requirements(
    nationality: str,
    destination_country: str,
) -> str:
    """
    Search for visa requirements for a specific nationality travelling to a country.

    Args:
        nationality:         Traveller's nationality, e.g. 'Sri Lankan', 'American', 'British'.
        destination_country: Country being visited, e.g. 'Thailand', 'United Kingdom'.

    Returns:
        Visa requirement summary from web search.
    """
    client = get_tavily_client()
    query = (
        f"visa requirements for {nationality} passport holders visiting {destination_country} "
        "2025 2026 visa on arrival e-visa documents needed"
    )
    response = client.search(query, search_depth="advanced", include_answer=True, max_results=3)

    if not response.results and not response.answer:
        return (
            f"Could not find visa info for {nationality} → {destination_country}. "
            "Please check your country's official embassy website."
        )

    output_parts = [
        f"Visa requirements ({nationality} → {destination_country}):\n"
    ]
    if response.answer:
        output_parts.append(response.answer + "\n")
    for i, r in enumerate(response.results[:3], 1):
        output_parts.append(f"{i}. {r.title}\n   {r.content[:300]}\n   Source: {r.url}\n")
    return "\n".join(output_parts)


@tool
def get_currency_info(destination_country: str) -> str:
    """
    Get currency and money exchange information for a destination.

    Args:
        destination_country: Country name, e.g. 'Japan', 'France', 'Brazil'.

    Returns:
        Currency info, exchange rates, and tipping customs.
    """
    client = get_tavily_client()
    query = (
        f"currency of {destination_country} exchange rate USD EUR "
        "tipping customs ATM cash or card travel money 2026"
    )
    response = client.search(query, search_depth="basic", include_answer=True, max_results=3)

    if not response.results and not response.answer:
        return f"No currency info found for '{destination_country}'."

    output_parts = [f"Currency & money tips for {destination_country}:\n"]
    if response.answer:
        output_parts.append(response.answer + "\n")
    for r in response.results[:2]:
        output_parts.append(f"- {r.title}: {r.content[:250]}\n")
    return "\n".join(output_parts)


@tool
def get_weather_forecast(destination: str, travel_month: str) -> str:
    """
    Get typical weather conditions and packing advice for a destination during a specific month.

    Args:
        destination:  City or country, e.g. 'Bali', 'Iceland'.
        travel_month: Month of travel, e.g. 'October', 'December'.

    Returns:
        Weather summary and packing recommendations.
    """
    client = get_tavily_client()
    query = (
        f"weather in {destination} in {travel_month} temperature rainfall "
        "what to pack travel advice"
    )
    response = client.search(query, search_depth="basic", include_answer=True, max_results=3)

    if not response.results and not response.answer:
        return f"No weather info found for '{destination}' in '{travel_month}'."

    output_parts = [f"Weather in {destination} ({travel_month}):\n"]
    if response.answer:
        output_parts.append(response.answer + "\n")
    for r in response.results[:2]:
        output_parts.append(f"- {r.content[:250]}\n")
    return "\n".join(output_parts)


@tool
def estimate_trip_budget(
    destination: str,
    duration_days: int,
    budget_tier: str = "mid-range",
    num_travelers: int = 1,
) -> str:
    """
    Estimate the total trip budget based on destination, duration, and tier.

    Args:
        destination:    City or country.
        duration_days:  Number of days.
        budget_tier:    'budget', 'mid-range', or 'luxury'.
        num_travelers:  Number of people travelling.

    Returns:
        A budget breakdown estimate.
    """
    client = get_tavily_client()
    query = (
        f"travel budget {destination} {duration_days} days {budget_tier} "
        f"daily cost accommodation food transport activities per person 2025 2026"
    )
    response = client.search(query, search_depth="advanced", include_answer=True, max_results=3)

    if not response.results and not response.answer:
        return f"Could not estimate budget for {destination}."

    output_parts = [
        f"Budget estimate: {destination} | {duration_days} days | "
        f"{budget_tier} | {num_travelers} traveller(s)\n"
    ]
    if response.answer:
        output_parts.append(response.answer + "\n")
    for r in response.results[:2]:
        output_parts.append(f"- {r.content[:300]}\n")
    return "\n".join(output_parts)


# Exported list for agent binding
GENERAL_TOOLS = [
    search_travel_tips,
    get_visa_requirements,
    get_currency_info,
    get_weather_forecast,
    estimate_trip_budget,
]
