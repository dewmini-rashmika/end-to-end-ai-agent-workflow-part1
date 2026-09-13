"""
Trip planning routes.

POST /api/v1/trips/plan                    — run the full 4-agent pipeline
POST /api/v1/trips/plan/stream             — SSE streaming version (agent-by-agent)
POST /api/v1/trips/{session_id}/followup   — continue an existing conversation
GET  /api/v1/trips/{session_id}            — retrieve the latest plan for a session
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from ..graph.runner import get_graph_runner
from ..db.connection import get_connection
from ..db.repositories import ConversationRepository
from ..middleware.rate_limit import limiter
from ..config.settings import settings
from .schemas import (
    FollowUpRequest,
    PlanTripRequest,
    TripPlanResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["trips"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_to_response(state: dict, session_id: str) -> TripPlanResponse:
    """Map a TravelState dict to the TripPlanResponse schema."""
    return TripPlanResponse(
        session_id=session_id,
        conversation_id=state.get("conversation_id", ""),
        user_query=state.get("user_query", ""),
        origin=state.get("origin", ""),
        destination=state.get("destination", ""),
        departure_date=state.get("departure_date", ""),
        return_date=state.get("return_date"),
        num_travelers=state.get("num_travelers", 1),
        trip_duration_days=state.get("trip_duration_days", 0),
        budget=state.get("budget", ""),
        interests=state.get("interests", ""),
        flight_results=[
            r if isinstance(r, dict) else {"raw_text": str(r)}
            for r in (state.get("flight_results") or [])
        ],
        hotel_results=[
            r if isinstance(r, dict) else {"raw_text": str(r)}
            for r in (state.get("hotel_results") or [])
        ],
        itinerary=[
            r if isinstance(r, dict) else {"raw_text": str(r)}
            for r in (state.get("itinerary") or [])
        ],
        final_response=state.get("final_response", ""),
        completed_agents=state.get("completed_agents") or [],
        errors=state.get("errors") or [],
    )


def _build_overrides(request: PlanTripRequest) -> dict:
    """Extract explicit field overrides from the request body."""
    overrides: dict = {}
    if request.origin:
        overrides["origin"] = request.origin
    if request.destination:
        overrides["destination"] = request.destination
    if request.departure_date:
        overrides["departure_date"] = request.departure_date
    if request.return_date:
        overrides["return_date"] = request.return_date
    overrides["num_travelers"] = request.num_travelers
    overrides["trip_duration_days"] = request.trip_duration_days
    overrides["budget"] = request.budget
    overrides["interests"] = request.interests
    return overrides


def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Events message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------------
# POST /api/v1/trips/plan  (standard JSON response)
# ---------------------------------------------------------------------------

@router.post(
    "/plan",
    response_model=TripPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Plan a new trip",
    description=(
        "Runs the full TripMate AI pipeline (Flight → Hotel → Itinerary → "
        "Final Response) and returns a complete travel plan as JSON."
    ),
)
@limiter.limit(settings.rate_limit.plan_trip)
async def plan_trip(request: Request, body: PlanTripRequest) -> TripPlanResponse:
    session_id = body.session_id or str(uuid.uuid4())
    logger.info("POST /trips/plan | session=%s | query=%.60s…", session_id, body.user_query)

    runner = get_graph_runner()
    try:
        final_state = await runner.run(
            user_query=body.user_query,
            session_id=session_id,
            overrides=_build_overrides(body),
        )
    except Exception as exc:
        logger.error("Trip planning failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trip planning failed: {exc}",
        )

    return _state_to_response(final_state, session_id)


# ---------------------------------------------------------------------------
# POST /api/v1/trips/plan/stream  (SSE — agent progress in real-time)
# ---------------------------------------------------------------------------

@router.post(
    "/plan/stream",
    summary="Plan a trip with real-time agent progress via SSE",
    description=(
        "Streams agent execution progress as Server-Sent Events. "
        "The client receives one event per agent as it completes, "
        "followed by a final 'done' event with the complete plan."
    ),
    response_class=StreamingResponse,
)
@limiter.limit(settings.rate_limit.plan_trip)
async def plan_trip_stream(request: Request, body: PlanTripRequest) -> StreamingResponse:
    session_id = body.session_id or str(uuid.uuid4())
    logger.info(
        "POST /trips/plan/stream | session=%s | query=%.60s…",
        session_id, body.user_query,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        # Emit a "start" event immediately so the client knows we began
        yield _sse_event("start", {
            "session_id": session_id,
            "message": "TripMate AI pipeline started",
            "agents": ["parse_query", "flight_agent", "hotel_agent", "itinerary_agent", "final_response"],
        })

        runner = get_graph_runner()
        try:
            # Use the graph's async stream to get per-node updates
            checkpointer = await runner._get_or_build_checkpointer()
            from ..graph.workflow import build_graph
            from ..state.travel_state import TravelState
            from langchain_core.messages import HumanMessage
            import uuid as _uuid

            conversation_id = str(_uuid.uuid4())
            
            # Persist the initial conversation record so UPDATE works at the end
            from ..db.connection import get_connection
            from ..db.repositories import ConversationRepository
            try:
                async with get_connection() as conn:
                    conv_repo = ConversationRepository(conn)
                    conv_record = await conv_repo.create(session_id, body.user_query)
                    conversation_id = conv_record.id
            except Exception as exc:
                logger.warning("Could not persist conversation record in stream: %s", exc)

            graph = build_graph(checkpointer=checkpointer)
            overrides = _build_overrides(body)

            initial_state: TravelState = {
                "user_query": body.user_query,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "messages": [HumanMessage(content=body.user_query)],
                "flight_results": [],
                "hotel_results": [],
                "itinerary": [],
                "final_response": "",
                "errors": [],
                "completed_agents": [],
                "current_agent": "",
                "origin": overrides.get("origin", ""),
                "destination": overrides.get("destination", ""),
                "departure_date": overrides.get("departure_date", ""),
                "return_date": overrides.get("return_date"),
                "num_travelers": overrides.get("num_travelers", 1),
                "trip_duration_days": overrides.get("trip_duration_days", 3),
                "budget": overrides.get("budget", "mid-range"),
                "interests": overrides.get("interests", ""),
            }

            config = {
                "configurable": {"thread_id": session_id},
                "recursion_limit": 25,
            }

            final_state = initial_state
            async for chunk in graph.astream(initial_state, config, stream_mode="updates"):
                for node_name, node_output in chunk.items():
                    if node_name == "__end__":
                        continue

                    # Build a progress event for the completed node
                    event_data: dict = {
                        "agent": node_name,
                        "session_id": session_id,
                        "status": "completed",
                    }

                    # Include a brief summary of what the node produced
                    if "flight_results" in node_output and node_output["flight_results"]:
                        event_data["preview"] = "Flight options found"
                    elif "hotel_results" in node_output and node_output["hotel_results"]:
                        event_data["preview"] = "Hotel options found"
                    elif "itinerary" in node_output and node_output["itinerary"]:
                        event_data["preview"] = "Day-by-day itinerary created"
                    elif "final_response" in node_output:
                        resp = node_output.get("final_response", "")
                        event_data["preview"] = resp[:200] + "…" if len(resp) > 200 else resp
                    elif "origin" in node_output:
                        event_data["preview"] = (
                            f"Parsed: {node_output.get('origin', '')} → "
                            f"{node_output.get('destination', '')}"
                        )

                    # Accumulate errors
                    if node_output.get("errors"):
                        event_data["errors"] = node_output["errors"]

                    yield _sse_event("agent_update", event_data)

                    # Merge the chunk into final_state for the done event
                    final_state = {**final_state, **node_output}

            # Persist final results
            await runner._persist_results(conversation_id, final_state)

            # Emit the final complete plan
            response = _state_to_response(final_state, session_id)
            yield _sse_event("done", response.model_dump())

        except asyncio.CancelledError:
            logger.info("SSE stream cancelled for session %s", session_id)
            yield _sse_event("error", {"message": "Stream cancelled by client"})
        except Exception as exc:
            logger.error("SSE stream error for session %s: %s", session_id, exc, exc_info=True)
            yield _sse_event("error", {"message": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable Nginx buffering
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# POST /api/v1/trips/{session_id}/followup
# ---------------------------------------------------------------------------

@router.post(
    "/{session_id}/followup",
    response_model=TripPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Follow up on an existing trip plan",
)
@limiter.limit("20/minute")
async def follow_up(
    request: Request, session_id: str, body: FollowUpRequest
) -> TripPlanResponse:
    logger.info("POST /trips/%s/followup | msg=%.60s…", session_id, body.message)

    runner = get_graph_runner()
    try:
        final_state = await runner.resume(session_id=session_id, follow_up=body.message)
    except Exception as exc:
        logger.error("Follow-up failed for session %s: %s", session_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Follow-up failed: {exc}",
        )

    return _state_to_response(final_state, session_id)


# ---------------------------------------------------------------------------
# GET /api/v1/trips/{session_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{session_id}",
    response_model=list[TripPlanResponse],
    status_code=status.HTTP_200_OK,
    summary="Get trip history for a session",
)
async def get_session_trips(session_id: str, limit: int = 10) -> list[TripPlanResponse]:
    logger.info("GET /trips/%s | limit=%d", session_id, limit)

    try:
        async with get_connection() as conn:
            repo = ConversationRepository(conn)
            records = await repo.get_by_session(session_id, limit=limit)
    except Exception as exc:
        logger.error("DB read failed for session %s: %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history.",
        )

    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No trips found for session '{session_id}'.",
        )

    return [
        TripPlanResponse(
            session_id=rec.session_id,
            conversation_id=rec.id,
            user_query=rec.user_query,
            origin="",
            destination="",
            departure_date="",
            return_date=None,
            num_travelers=1,
            trip_duration_days=0,
            budget="",
            interests="",
            flight_results=(rec.flight_results or {}).get("items", []),
            hotel_results=(rec.hotel_results or {}).get("items", []),
            itinerary=(rec.itinerary or {}).get("items", []),
            final_response=rec.final_response or "",
            completed_agents=[],
            errors=[],
        )
        for rec in records
    ]
