"""
Google Maps / Places API client (optional).

Falls back gracefully when GOOGLE_MAPS_API_KEY is not set.
Endpoints used:
  - Places Text Search  → find hotels/restaurants by name + location
  - Place Details       → rating, reviews, address, opening hours
  - Directions          → travel time between two places
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from .base import BaseHTTPClient, APIError
from ..config.settings import settings

logger = logging.getLogger(__name__)

GOOGLE_MAPS_BASE = "https://maps.googleapis.com/maps/api"


# ---------------------------------------------------------------------------
# Typed response dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PlaceResult:
    place_id: str
    name: str
    address: str
    rating: float | None
    total_ratings: int
    price_level: int | None   # 0-4, where 4 is most expensive
    types: list[str]
    lat: float | None
    lng: float | None
    open_now: bool | None
    phone: str | None = None
    website: str | None = None

    def to_dict(self) -> dict:
        return {
            "place_id": self.place_id,
            "name": self.name,
            "address": self.address,
            "rating": self.rating,
            "total_ratings": self.total_ratings,
            "price_level": self.price_level,
            "types": self.types,
            "coordinates": {"lat": self.lat, "lng": self.lng},
            "open_now": self.open_now,
            "phone": self.phone,
            "website": self.website,
        }


@dataclass
class DirectionResult:
    origin: str
    destination: str
    distance_km: float
    duration_minutes: int
    travel_mode: str
    summary: str

    def to_dict(self) -> dict:
        return {
            "origin": self.origin,
            "destination": self.destination,
            "distance_km": self.distance_km,
            "duration_minutes": self.duration_minutes,
            "travel_mode": self.travel_mode,
            "summary": self.summary,
        }


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class GoogleMapsClient(BaseHTTPClient):
    """
    Optional Google Maps API client.

    If GOOGLE_MAPS_API_KEY is not set, all methods return empty results
    rather than raising so the rest of the agent pipeline keeps working.
    """

    SERVICE_NAME = "GoogleMaps"

    def __init__(self):
        super().__init__(base_url=GOOGLE_MAPS_BASE, timeout=20)
        self._api_key = settings.google_maps.api_key
        self._enabled = settings.google_maps.enabled

        if not self._enabled:
            logger.warning(
                "GOOGLE_MAPS_API_KEY is not set — GoogleMapsClient running in disabled mode. "
                "Hotel Places and Directions features will be skipped."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_places(
        self,
        query: str,
        location: str = "",
        place_type: str = "lodging",
        radius_meters: int = 5000,
    ) -> list[PlaceResult]:
        """
        Text search for places (hotels, restaurants, attractions).

        Returns empty list if Google Maps is disabled or no results found.
        """
        if not self._enabled:
            return []

        full_query = f"{query} in {location}" if location else query
        logger.info("Google Places text search: %s", full_query)

        params = {
            "query": full_query,
            "type": place_type,
            "key": self._api_key,
        }
        if location:
            params["location"] = location
            params["radius"] = radius_meters

        try:
            data = self._get("/place/textsearch/json", params=params)
        except APIError as exc:
            logger.error("Google Places error: %s", exc)
            return []

        results = data.get("results", [])
        logger.info("Google Places returned %d result(s).", len(results))
        return [self._parse_place(r) for r in results]

    def get_place_details(self, place_id: str) -> PlaceResult | None:
        """
        Fetch detailed info for a specific place by its place_id.
        Returns None if Google Maps is disabled.
        """
        if not self._enabled:
            return None

        logger.info("Google Places detail: %s", place_id)
        params = {
            "place_id": place_id,
            "fields": (
                "name,formatted_address,rating,user_ratings_total,"
                "price_level,types,geometry,opening_hours,"
                "formatted_phone_number,website"
            ),
            "key": self._api_key,
        }

        try:
            data = self._get("/place/details/json", params=params)
        except APIError as exc:
            logger.error("Google Place Details error: %s", exc)
            return None

        result = data.get("result")
        return self._parse_place(result) if result else None

    def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",     # "driving" | "walking" | "transit"
    ) -> DirectionResult | None:
        """
        Get travel time and distance between two locations.
        Returns None if Google Maps is disabled or route not found.
        """
        if not self._enabled:
            return None

        logger.info("Google Directions: %s → %s (%s)", origin, destination, mode)
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "key": self._api_key,
        }

        try:
            data = self._get("/directions/json", params=params)
        except APIError as exc:
            logger.error("Google Directions error: %s", exc)
            return None

        routes = data.get("routes", [])
        if not routes:
            logger.warning("No route found: %s → %s", origin, destination)
            return None

        leg = routes[0].get("legs", [{}])[0]
        return DirectionResult(
            origin=origin,
            destination=destination,
            distance_km=round(leg.get("distance", {}).get("value", 0) / 1000, 2),
            duration_minutes=round(leg.get("duration", {}).get("value", 0) / 60),
            travel_mode=mode,
            summary=routes[0].get("summary", ""),
        )

    def search_hotels(
        self, city: str, max_results: int = 10
    ) -> list[PlaceResult]:
        """Convenience wrapper for hotel searches in a city."""
        results = self.search_places(
            query=f"hotels in {city}",
            location=city,
            place_type="lodging",
        )
        return results[:max_results]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_place(raw: dict) -> PlaceResult:
        geometry = raw.get("geometry", {}).get("location", {})
        hours = raw.get("opening_hours", {})

        return PlaceResult(
            place_id=raw.get("place_id", ""),
            name=raw.get("name", "Unknown"),
            address=raw.get("formatted_address") or raw.get("vicinity", ""),
            rating=raw.get("rating"),
            total_ratings=raw.get("user_ratings_total", 0),
            price_level=raw.get("price_level"),
            types=raw.get("types", []),
            lat=geometry.get("lat"),
            lng=geometry.get("lng"),
            open_now=hours.get("open_now"),
            phone=raw.get("formatted_phone_number"),
            website=raw.get("website"),
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_google_maps_client: GoogleMapsClient | None = None


def get_google_maps_client() -> GoogleMapsClient:
    global _google_maps_client
    if _google_maps_client is None:
        _google_maps_client = GoogleMapsClient()
    return _google_maps_client
