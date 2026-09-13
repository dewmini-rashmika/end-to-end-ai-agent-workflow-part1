"""
AviationStack API client.

Docs: https://aviationstack.com/documentation
Free tier: flight schedules (no real-time), limited calls/month.
"""

import logging
from dataclasses import dataclass
from typing import Any

import airportsdata

from .base import BaseHTTPClient, APIError
from ..config.settings import settings

logger = logging.getLogger(__name__)

# Pre-load IATA airport database once at import time (tiny, ~7k airports)
_AIRPORTS: dict[str, dict] = airportsdata.load("IATA")


# ---------------------------------------------------------------------------
# Typed response dataclasses
# ---------------------------------------------------------------------------

@dataclass
class FlightOption:
    flight_number: str
    airline: str
    origin_iata: str
    origin_city: str
    destination_iata: str
    destination_city: str
    departure_time: str       # ISO-8601 string from API
    arrival_time: str
    duration_minutes: int | None
    stops: int
    price_usd: float | None   # AviationStack free tier doesn't return price
    status: str               # "scheduled", "active", "landed", etc.
    aircraft: str | None

    def to_dict(self) -> dict:
        return {
            "flight_number": self.flight_number,
            "airline": self.airline,
            "origin": f"{self.origin_city} ({self.origin_iata})",
            "destination": f"{self.destination_city} ({self.destination_iata})",
            "departure": self.departure_time,
            "arrival": self.arrival_time,
            "duration_minutes": self.duration_minutes,
            "stops": self.stops,
            "price_usd": self.price_usd,
            "status": self.status,
            "aircraft": self.aircraft,
        }


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class AviationStackClient(BaseHTTPClient):
    """
    Wraps AviationStack /flights endpoint.

    Usage:
        client = AviationStackClient()
        options = client.search_flights("CMB", "LHR", "2026-10-15")
    """

    SERVICE_NAME = "AviationStack"

    def __init__(self):
        super().__init__(
            base_url=settings.aviation_stack.base_url,
            timeout=settings.aviation_stack.timeout,
        )
        self._api_key = settings.aviation_stack.api_key

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_flights(
        self,
        origin_iata: str,
        destination_iata: str,
        departure_date: str,        # YYYY-MM-DD
        limit: int = 10,
    ) -> list[FlightOption]:
        """
        Search for flights between two IATA airport codes on a given date.

        Returns a list of FlightOption dataclass instances sorted by
        estimated departure time.
        """
        origin_iata = origin_iata.upper().strip()
        destination_iata = destination_iata.upper().strip()

        logger.info(
            "Searching flights: %s → %s on %s",
            origin_iata, destination_iata, departure_date,
        )

        params = {
            "access_key": self._api_key,
            "dep_iata": origin_iata,
            "arr_iata": destination_iata,
            "flight_date": departure_date,
            "limit": limit,
        }

        try:
            data = self._get("/flights", params=params)
        except APIError as exc:
            logger.error("AviationStack error: %s", exc)
            raise

        raw_flights: list[dict] = data.get("data", [])
        if not raw_flights:
            logger.warning(
                "No flights found for %s → %s on %s",
                origin_iata, destination_iata, departure_date,
            )
            return []

        options = [self._parse_flight(f) for f in raw_flights]
        # Sort by departure time ascending
        options.sort(key=lambda x: x.departure_time or "")
        logger.info("Found %d flight(s).", len(options))
        return options

    def get_airport_info(self, iata_code: str) -> dict | None:
        """Return airport metadata from the local airportsdata database."""
        return _AIRPORTS.get(iata_code.upper())

    def iata_to_city(self, iata_code: str) -> str:
        """Return the city name for an IATA code, or the code itself if unknown."""
        info = _AIRPORTS.get(iata_code.upper())
        return info.get("city", iata_code) if info else iata_code

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_flight(self, raw: dict) -> FlightOption:
        departure = raw.get("departure", {})
        arrival = raw.get("arrival", {})
        flight_info = raw.get("flight", {})
        airline_info = raw.get("airline", {})
        aircraft_info = raw.get("aircraft", {})

        origin_iata = departure.get("iata", "")
        destination_iata = arrival.get("iata", "")

        # Calculate duration from scheduled times if available
        dep_scheduled = departure.get("scheduled", "")
        arr_scheduled = arrival.get("scheduled", "")
        duration_minutes = self._calc_duration(dep_scheduled, arr_scheduled)

        return FlightOption(
            flight_number=flight_info.get("iata") or flight_info.get("number") or "N/A",
            airline=airline_info.get("name", "Unknown"),
            origin_iata=origin_iata,
            origin_city=self.iata_to_city(origin_iata),
            destination_iata=destination_iata,
            destination_city=self.iata_to_city(destination_iata),
            departure_time=dep_scheduled,
            arrival_time=arr_scheduled,
            duration_minutes=duration_minutes,
            stops=0,   # AviationStack /flights returns direct legs only
            price_usd=None,   # Not provided on free tier
            status=raw.get("flight_status", "unknown"),
            aircraft=aircraft_info.get("iata") if aircraft_info else None,
        )

    @staticmethod
    def _calc_duration(dep: str, arr: str) -> int | None:
        """Return flight duration in minutes or None if times are unparseable."""
        if not dep or not arr:
            return None
        try:
            from datetime import datetime
            fmt = "%Y-%m-%dT%H:%M:%S%z"
            d = datetime.fromisoformat(dep)
            a = datetime.fromisoformat(arr)
            diff = (a - d).total_seconds() / 60
            return int(diff) if diff > 0 else None
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_aviation_client: AviationStackClient | None = None


def get_aviation_client() -> AviationStackClient:
    global _aviation_client
    if _aviation_client is None:
        _aviation_client = AviationStackClient()
    return _aviation_client
