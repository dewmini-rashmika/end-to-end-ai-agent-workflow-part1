"""
Pydantic request/response schemas for all API routes.
Keeps validation logic out of route handlers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class PlanTripRequest(BaseModel):
    """Body for POST /api/v1/trips/plan"""

    user_query: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural-language travel request from the user.",
        examples=["Plan a 5-day trip from Colombo to Tokyo in October 2026 for 2 people"],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID to continue an existing conversation.",
    )
    # Optional pre-parsed overrides — skip LLM parsing if provided
    origin: str | None = Field(default=None, description="Origin IATA code or city.")
    destination: str | None = Field(default=None, description="Destination IATA code or city.")
    departure_date: str | None = Field(
        default=None,
        description="Departure date in YYYY-MM-DD format.",
        examples=["2026-10-15"],
    )
    return_date: str | None = Field(
        default=None,
        description="Return date in YYYY-MM-DD format. Null for one-way.",
    )
    num_travelers: int = Field(default=1, ge=1, le=20, description="Number of travellers.")
    trip_duration_days: int = Field(
        default=3, ge=1, le=30, description="Trip duration in days."
    )
    budget: str = Field(
        default="mid-range",
        description="Budget tier: budget, mid-range, or luxury.",
    )
    interests: str = Field(
        default="",
        max_length=500,
        description="Free-text interests, e.g. 'beaches, food, history'.",
    )

    @field_validator("budget")
    @classmethod
    def validate_budget(cls, v: str) -> str:
        allowed = {"budget", "mid-range", "luxury", ""}
        if v.lower() not in allowed:
            raise ValueError(f"budget must be one of: {allowed}")
        return v.lower()


class FollowUpRequest(BaseModel):
    """Body for POST /api/v1/trips/{session_id}/followup"""

    message: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description="Follow-up question or clarification from the user.",
    )


class SavePreferencesRequest(BaseModel):
    """Body for PUT /api/v1/sessions/{session_id}/preferences"""

    preferences: dict[str, Any] = Field(
        ...,
        description="Arbitrary key-value user preferences to store.",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class FlightResultResponse(BaseModel):
    raw_text: str | None = None


class HotelResultResponse(BaseModel):
    raw_text: str | None = None


class ItineraryDayResponse(BaseModel):
    raw_text: str | None = None


class TripPlanResponse(BaseModel):
    """Returned by POST /api/v1/trips/plan and GET /api/v1/trips/{session_id}"""

    session_id: str
    conversation_id: str
    user_query: str
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    num_travelers: int
    trip_duration_days: int
    budget: str
    interests: str
    flight_results: list[dict]
    hotel_results: list[dict]
    itinerary: list[dict]
    final_response: str
    completed_agents: list[str]
    errors: list[str]


class ConversationSummaryResponse(BaseModel):
    """Item in GET /api/v1/sessions/{session_id}/history"""

    id: str
    session_id: str
    user_query: str
    status: str
    created_at: datetime
    updated_at: datetime
    has_final_response: bool


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    status_code: int
