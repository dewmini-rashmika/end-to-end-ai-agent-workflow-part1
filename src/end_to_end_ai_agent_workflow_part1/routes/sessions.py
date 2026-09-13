"""
Session management routes.

GET  /api/v1/sessions/{session_id}/history      — list conversation history
PUT  /api/v1/sessions/{session_id}/preferences  — upsert user preferences
GET  /api/v1/sessions/{session_id}/preferences  — get user preferences
DELETE /api/v1/sessions/{session_id}            — delete all session data
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from ..db.connection import get_connection
from ..db.repositories import (
    ConversationRepository,
    UserPreferencesRepository,
)
from .schemas import (
    ConversationSummaryResponse,
    SavePreferencesRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


# ---------------------------------------------------------------------------
# GET /api/v1/sessions/{session_id}/history
# ---------------------------------------------------------------------------

@router.get(
    "/{session_id}/history",
    response_model=list[ConversationSummaryResponse],
    summary="List conversation history for a session",
)
async def get_session_history(
    session_id: str, limit: int = 20
) -> list[ConversationSummaryResponse]:
    """Return a summary list of all conversations for a session."""
    logger.info("GET /sessions/%s/history | limit=%d", session_id, limit)

    try:
        async with get_connection() as conn:
            repo = ConversationRepository(conn)
            records = await repo.get_by_session(session_id, limit=limit)
    except Exception as exc:
        logger.error("DB error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch session history.",
        )

    return [
        ConversationSummaryResponse(
            id=rec.id,
            session_id=rec.session_id,
            user_query=rec.user_query,
            status=rec.status,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
            has_final_response=bool(rec.final_response),
        )
        for rec in records
    ]


# ---------------------------------------------------------------------------
# GET /api/v1/sessions/{session_id}/preferences
# ---------------------------------------------------------------------------

@router.get(
    "/{session_id}/preferences",
    response_model=dict,
    summary="Get stored user preferences for a session",
)
async def get_preferences(session_id: str) -> dict:
    """Return the preferences stored for this session."""
    logger.info("GET /sessions/%s/preferences", session_id)

    try:
        async with get_connection() as conn:
            repo = UserPreferencesRepository(conn)
            record = await repo.get(session_id)
    except Exception as exc:
        logger.error("DB error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch preferences.",
        )

    if not record:
        return {}
    return record.preferences


# ---------------------------------------------------------------------------
# PUT /api/v1/sessions/{session_id}/preferences
# ---------------------------------------------------------------------------

@router.put(
    "/{session_id}/preferences",
    response_model=dict,
    summary="Save or update user preferences for a session",
)
async def save_preferences(
    session_id: str,
    request: SavePreferencesRequest,
) -> dict:
    """Upsert preferences for a session. Merges with existing if present."""
    logger.info("PUT /sessions/%s/preferences | keys=%s", session_id, list(request.preferences.keys()))

    try:
        async with get_connection() as conn:
            repo = UserPreferencesRepository(conn)
            # Merge with existing preferences
            existing = await repo.get(session_id)
            merged = {**(existing.preferences if existing else {}), **request.preferences}
            record = await repo.upsert(session_id, merged)
    except Exception as exc:
        logger.error("DB error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save preferences.",
        )

    return record.preferences


# ---------------------------------------------------------------------------
# DELETE /api/v1/sessions/{session_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete all data for a session",
)
async def delete_session(session_id: str) -> None:
    """
    Delete all conversation records for this session.
    Preferences are also removed.
    This operation is irreversible.
    """
    logger.info("DELETE /sessions/%s", session_id)

    try:
        async with get_connection() as conn:
            conv_repo = ConversationRepository(conn)
            records = await conv_repo.get_by_session(session_id, limit=100)
            for rec in records:
                await conv_repo.delete(rec.id)
    except Exception as exc:
        logger.error("DB error during session delete: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session data.",
        )
