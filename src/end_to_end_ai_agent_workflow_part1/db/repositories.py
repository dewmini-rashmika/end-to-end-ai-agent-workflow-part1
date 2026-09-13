"""
Repository layer — all SQL queries live here, never in agents or routes.

Each repository receives a connection from the pool via dependency injection
so it stays testable and transaction-safe.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any

import psycopg

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Transfer Objects (plain dataclasses — no ORM overhead)
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field


@dataclass
class ConversationRecord:
    id: str
    session_id: str
    user_query: str
    flight_results: dict | None
    hotel_results: dict | None
    itinerary: dict | None
    final_response: str | None
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class AgentLogRecord:
    id: str
    conversation_id: str
    agent_name: str
    input_data: dict | None
    output_data: dict | None
    duration_ms: int | None
    status: str
    error_message: str | None
    created_at: datetime


@dataclass
class UserPreferencesRecord:
    id: str
    session_id: str
    preferences: dict
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Conversation Repository
# ---------------------------------------------------------------------------

class ConversationRepository:
    """CRUD operations for the conversations table."""

    def __init__(self, conn: psycopg.AsyncConnection):
        self._conn = conn

    async def create(self, session_id: str, user_query: str) -> ConversationRecord:
        """Insert a new conversation and return the created record."""
        row = await (
            await self._conn.execute(
                """
                INSERT INTO conversations (session_id, user_query)
                VALUES (%s, %s)
                RETURNING id, session_id, user_query, flight_results,
                          hotel_results, itinerary, final_response,
                          status, created_at, updated_at
                """,
                (session_id, user_query),
            )
        ).fetchone()
        return self._row_to_record(row)

    async def get_by_id(self, conversation_id: str) -> ConversationRecord | None:
        row = await (
            await self._conn.execute(
                """
                SELECT id, session_id, user_query, flight_results,
                       hotel_results, itinerary, final_response,
                       status, created_at, updated_at
                FROM   conversations
                WHERE  id = %s
                """,
                (conversation_id,),
            )
        ).fetchone()
        return self._row_to_record(row) if row else None

    async def get_by_session(
        self, session_id: str, limit: int = 20
    ) -> list[ConversationRecord]:
        rows = await (
            await self._conn.execute(
                """
                SELECT id, session_id, user_query, flight_results,
                       hotel_results, itinerary, final_response,
                       status, created_at, updated_at
                FROM   conversations
                WHERE  session_id = %s
                ORDER  BY created_at DESC
                LIMIT  %s
                """,
                (session_id, limit),
            )
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    async def update_results(
        self,
        conversation_id: str,
        *,
        flight_results: dict | None = None,
        hotel_results: dict | None = None,
        itinerary: dict | None = None,
        final_response: str | None = None,
        status: str | None = None,
    ) -> ConversationRecord | None:
        """Patch any subset of result fields."""
        fields: list[str] = []
        values: list[Any] = []

        if flight_results is not None:
            fields.append("flight_results = %s")
            values.append(json.dumps(flight_results))
        if hotel_results is not None:
            fields.append("hotel_results = %s")
            values.append(json.dumps(hotel_results))
        if itinerary is not None:
            fields.append("itinerary = %s")
            values.append(json.dumps(itinerary))
        if final_response is not None:
            fields.append("final_response = %s")
            values.append(final_response)
        if status is not None:
            fields.append("status = %s")
            values.append(status)

        if not fields:
            return await self.get_by_id(conversation_id)

        values.append(conversation_id)
        row = await (
            await self._conn.execute(
                f"""
                UPDATE conversations
                SET    {", ".join(fields)}
                WHERE  id = %s
                RETURNING id, session_id, user_query, flight_results,
                          hotel_results, itinerary, final_response,
                          status, created_at, updated_at
                """,
                values,
            )
        ).fetchone()
        return self._row_to_record(row) if row else None

    async def delete(self, conversation_id: str) -> bool:
        result = await self._conn.execute(
            "DELETE FROM conversations WHERE id = %s", (conversation_id,)
        )
        return result.rowcount > 0

    @staticmethod
    def _row_to_record(row: tuple) -> ConversationRecord:
        return ConversationRecord(
            id=str(row[0]),
            session_id=row[1],
            user_query=row[2],
            flight_results=row[3],
            hotel_results=row[4],
            itinerary=row[5],
            final_response=row[6],
            status=row[7],
            created_at=row[8],
            updated_at=row[9],
        )


# ---------------------------------------------------------------------------
# Agent Log Repository
# ---------------------------------------------------------------------------

class AgentLogRepository:
    """Append-only log of each agent invocation for observability."""

    def __init__(self, conn: psycopg.AsyncConnection):
        self._conn = conn

    async def log(
        self,
        conversation_id: str,
        agent_name: str,
        *,
        input_data: dict | None = None,
        output_data: dict | None = None,
        duration_ms: int | None = None,
        status: str = "success",
        error_message: str | None = None,
    ) -> AgentLogRecord:
        row = await (
            await self._conn.execute(
                """
                INSERT INTO agent_logs
                    (conversation_id, agent_name, input_data, output_data,
                     duration_ms, status, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, conversation_id, agent_name, input_data,
                          output_data, duration_ms, status,
                          error_message, created_at
                """,
                (
                    conversation_id,
                    agent_name,
                    json.dumps(input_data) if input_data else None,
                    json.dumps(output_data) if output_data else None,
                    duration_ms,
                    status,
                    error_message,
                ),
            )
        ).fetchone()
        return AgentLogRecord(
            id=str(row[0]),
            conversation_id=str(row[1]),
            agent_name=row[2],
            input_data=row[3],
            output_data=row[4],
            duration_ms=row[5],
            status=row[6],
            error_message=row[7],
            created_at=row[8],
        )

    async def get_by_conversation(
        self, conversation_id: str
    ) -> list[AgentLogRecord]:
        rows = await (
            await self._conn.execute(
                """
                SELECT id, conversation_id, agent_name, input_data,
                       output_data, duration_ms, status,
                       error_message, created_at
                FROM   agent_logs
                WHERE  conversation_id = %s
                ORDER  BY created_at ASC
                """,
                (conversation_id,),
            )
        ).fetchall()
        return [
            AgentLogRecord(
                id=str(r[0]),
                conversation_id=str(r[1]),
                agent_name=r[2],
                input_data=r[3],
                output_data=r[4],
                duration_ms=r[5],
                status=r[6],
                error_message=r[7],
                created_at=r[8],
            )
            for r in rows
        ]


# ---------------------------------------------------------------------------
# User Preferences Repository
# ---------------------------------------------------------------------------

class UserPreferencesRepository:
    """Store and retrieve per-session user preferences."""

    def __init__(self, conn: psycopg.AsyncConnection):
        self._conn = conn

    async def upsert(
        self, session_id: str, preferences: dict
    ) -> UserPreferencesRecord:
        row = await (
            await self._conn.execute(
                """
                INSERT INTO user_preferences (session_id, preferences)
                VALUES (%s, %s)
                ON CONFLICT (session_id)
                DO UPDATE SET preferences = EXCLUDED.preferences
                RETURNING id, session_id, preferences, created_at, updated_at
                """,
                (session_id, json.dumps(preferences)),
            )
        ).fetchone()
        return self._row_to_record(row)

    async def get(self, session_id: str) -> UserPreferencesRecord | None:
        row = await (
            await self._conn.execute(
                """
                SELECT id, session_id, preferences, created_at, updated_at
                FROM   user_preferences
                WHERE  session_id = %s
                """,
                (session_id,),
            )
        ).fetchone()
        return self._row_to_record(row) if row else None

    @staticmethod
    def _row_to_record(row: tuple) -> UserPreferencesRecord:
        return UserPreferencesRecord(
            id=str(row[0]),
            session_id=row[1],
            preferences=row[2] if isinstance(row[2], dict) else json.loads(row[2]),
            created_at=row[3],
            updated_at=row[4],
        )
