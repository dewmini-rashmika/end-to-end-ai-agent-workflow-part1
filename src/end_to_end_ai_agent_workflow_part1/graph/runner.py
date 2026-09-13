"""
Graph runner — async interface for invoking the compiled LangGraph workflow.

Handles:
- Building the initial TravelState from a user query
- Running the graph with a thread_id for checkpointing
- Persisting results to PostgreSQL via repositories
- Returning the final TravelState
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from langchain_core.messages import HumanMessage

from ..state.travel_state import TravelState
from ..db.checkpointer import get_checkpointer
from ..db.connection import get_connection
from ..db.repositories import ConversationRepository, AgentLogRepository
from .workflow import get_graph, build_graph

logger = logging.getLogger(__name__)


class GraphRunner:
    """
    Async wrapper around the compiled LangGraph that:
    1. Accepts a user query
    2. Builds the initial TravelState
    3. Invokes the graph with Postgres checkpointing
    4. Persists the conversation record and agent logs
    5. Returns the final state
    """

    async def run(
        self,
        user_query: str,
        session_id: str | None = None,
        overrides: dict | None = None,
    ) -> TravelState:
        """
        Execute the full TripMate pipeline for a travel query.

        Args:
            user_query:  Natural-language travel request.
            session_id:  Optional session identifier (thread_id for checkpointer).
            overrides:   Optional pre-set state fields (skip parsing step).

        Returns:
            Final TravelState with all agent outputs.
        """
        session_id = session_id or str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        logger.info(
            "GraphRunner.run | session=%s | query=%.80s", session_id, user_query
        )

        # ---- Build checkpointed graph ----
        checkpointer = await get_checkpointer()
        graph = build_graph(checkpointer=checkpointer)

        # ---- Build initial state ----
        initial_state: TravelState = {
            "user_query": user_query,
            "session_id": session_id,
            "conversation_id": conversation_id,
            "messages": [HumanMessage(content=user_query)],
            "flight_results": [],
            "hotel_results": [],
            "itinerary": [],
            "final_response": "",
            "errors": [],
            "completed_agents": [],
            "current_agent": "",
            "origin": "",
            "destination": "",
            "departure_date": "",
            "return_date": None,
            "num_travelers": 1,
            "trip_duration_days": 3,
            "budget": "mid-range",
            "interests": "",
        }

        if overrides:
            initial_state.update(overrides)  # type: ignore[arg-type]

        # ---- Persist conversation record ----
        try:
            async with get_connection() as conn:
                conv_repo = ConversationRepository(conn)
                conv_record = await conv_repo.create(session_id, user_query)
                conversation_id = conv_record.id
                initial_state["conversation_id"] = conversation_id
        except Exception as exc:
            logger.warning("Could not persist conversation record: %s", exc)

        # ---- Run the graph ----
        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": 25,
        }

        try:
            final_state: TravelState = await graph.ainvoke(initial_state, config)
        except Exception as exc:
            logger.error("Graph execution failed: %s", exc, exc_info=True)
            final_state = dict(initial_state)  # type: ignore[assignment]
            final_state["final_response"] = (
                f"An error occurred while planning your trip: {exc}. "
                "Please try again."
            )
            final_state["errors"] = [str(exc)]

        # ---- Persist results back to DB ----
        await self._persist_results(conversation_id, final_state)

        return final_state

    async def resume(
        self,
        session_id: str,
        follow_up: str,
    ) -> TravelState:
        """
        Resume an existing conversation with a follow-up message.
        The checkpointer restores the previous state automatically.

        Args:
            session_id:  Thread ID of the existing conversation.
            follow_up:   New user message to append.

        Returns:
            Updated TravelState.
        """
        logger.info("GraphRunner.resume | session=%s", session_id)

        checkpointer = await get_checkpointer()
        graph = build_graph(checkpointer=checkpointer)

        # Inject the follow-up as a new human message
        update = {"messages": [HumanMessage(content=follow_up)]}
        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": 25,
        }

        try:
            final_state: TravelState = await graph.ainvoke(update, config)
        except Exception as exc:
            logger.error("Graph resume failed: %s", exc, exc_info=True)
            raise

        return final_state

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_or_build_checkpointer(self):
        """Return the checkpointer; exposed for the SSE streaming route."""
        return await get_checkpointer()

    @staticmethod
    async def _persist_results(conversation_id: str, state: TravelState) -> None:
        """Write final agent outputs back to the conversations table."""
        try:
            async with get_connection() as conn:
                conv_repo = ConversationRepository(conn)
                await conv_repo.update_results(
                    conversation_id,
                    flight_results={"items": state.get("flight_results", [])},
                    hotel_results={"items": state.get("hotel_results", [])},
                    itinerary={"items": state.get("itinerary", [])},
                    final_response=state.get("final_response", ""),
                    status="completed" if not state.get("errors") else "error",
                )
        except Exception as exc:
            logger.warning("Could not persist results: %s", exc)


# Module-level singleton
_runner: GraphRunner | None = None


def get_graph_runner() -> GraphRunner:
    global _runner
    if _runner is None:
        _runner = GraphRunner()
    return _runner
