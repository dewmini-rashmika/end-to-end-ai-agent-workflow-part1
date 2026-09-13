"""
Clients package — external API clients for AviationStack, Tavily, and Google Maps.
All clients expose module-level singleton getters for easy import.
"""

from .base import BaseHTTPClient, APIError
from .aviation_client import AviationStackClient, FlightOption, get_aviation_client
from .tavily_client import TavilySearchClient, TavilySearchResponse, SearchResult, get_tavily_client
from .google_maps_client import (
    GoogleMapsClient,
    PlaceResult,
    DirectionResult,
    get_google_maps_client,
)

__all__ = [
    # Base
    "BaseHTTPClient",
    "APIError",
    # AviationStack
    "AviationStackClient",
    "FlightOption",
    "get_aviation_client",
    # Tavily
    "TavilySearchClient",
    "TavilySearchResponse",
    "SearchResult",
    "get_tavily_client",
    # Google Maps
    "GoogleMapsClient",
    "PlaceResult",
    "DirectionResult",
    "get_google_maps_client",
]
