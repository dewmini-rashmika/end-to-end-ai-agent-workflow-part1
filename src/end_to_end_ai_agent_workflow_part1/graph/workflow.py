"""
TripMate AI — LangGraph workflow definition.

Builds and compiles the StateGraph with:
  - 5 nodes: parse_query → flight_agent → hotel_agent → itinerary_agent → final_response
  - Conditional edges with routing logic
  - AsyncPostgresSaver checkpointer for persistent conversation memory
  - Recursion limit from settings

Graph topology:
    START
      │
      ▼
  parse_query  ──(no destination)──► final_response
      │
      ▼ (destination found)
  flight_agent
      │
      ▼
  hotel_agent
      │
      ▼
  itinerary_agent
      │
      ▼
  final_response
      │
      ▼
     END
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from ..config.settings import settings
from ..state.travel_state import TravelState
from .nodes import (
    parse_query_node,
    flight_agent_node,
    hotel_agent_node,
    itinerary_agent_node,
    final_response_node,
)
from .edges import (
    NODE_PARSE_QUERY,
    NODE_FLIGHT,
    NODE_HOTEL,
    NODE_ITINERARY,
    NODE_FINAL,
    route_after_parse,
    route_after_flight,
    route_after_hotel,
    route_after_itinerary,
)

logger = logging.getLogger(__name__)


def build_graph(checkpointer: Any | None = None) -> Any:
    """
    Build and compile the TripMate LangGraph StateGraph.

    Args:
        checkpointer: An optional LangGraph checkpointer (e.g. AsyncPostgresSaver).
                      When provided, the graph can pause and resume across requests.

    Returns:
        Compiled LangGraph application (CompiledGraph).
    """
    logger.info("Building TripMate LangGraph workflow…")

    builder = StateGraph(TravelState)

    # ------------------------------------------------------------------ #
    # Register nodes                                                       #
    # ------------------------------------------------------------------ #
    builder.add_node(NODE_PARSE_QUERY, parse_query_node)
    builder.add_node(NODE_FLIGHT, flight_agent_node)
    builder.add_node(NODE_HOTEL, hotel_agent_node)
    builder.add_node(NODE_ITINERARY, itinerary_agent_node)
    builder.add_node(NODE_FINAL, final_response_node)

    # ------------------------------------------------------------------ #
    # Entry point                                                          #
    # ------------------------------------------------------------------ #
    builder.add_edge(START, NODE_PARSE_QUERY)

    # ------------------------------------------------------------------ #
    # Conditional edges (routing functions defined in edges.py)           #
    # ------------------------------------------------------------------ #
    builder.add_conditional_edges(
        NODE_PARSE_QUERY,
        route_after_parse,
        {
            NODE_FLIGHT: NODE_FLIGHT,
            NODE_FINAL: NODE_FINAL,
        },
    )
    builder.add_conditional_edges(
        NODE_FLIGHT,
        route_after_flight,
        {NODE_HOTEL: NODE_HOTEL},
    )
    builder.add_conditional_edges(
        NODE_HOTEL,
        route_after_hotel,
        {NODE_ITINERARY: NODE_ITINERARY},
    )
    builder.add_conditional_edges(
        NODE_ITINERARY,
        route_after_itinerary,
        {NODE_FINAL: NODE_FINAL},
    )

    # Final response always ends the graph
    builder.add_edge(NODE_FINAL, END)

    # ------------------------------------------------------------------ #
    # Compile                                                              #
    # ------------------------------------------------------------------ #
    compile_kwargs: dict[str, Any] = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer

    graph = builder.compile(**compile_kwargs)
    logger.info("LangGraph workflow compiled successfully.")
    return graph


# ---------------------------------------------------------------------------
# Module-level compiled graph singleton (no checkpointer — for testing)
# ---------------------------------------------------------------------------

_graph: Any | None = None


def get_graph(checkpointer: Any | None = None) -> Any:
    """
    Return a compiled graph.

    If called with a checkpointer the first time, stores that version as the
    module-level singleton. Subsequent calls without a checkpointer return
    the cached version.
    """
    global _graph
    if _graph is None:
        _graph = build_graph(checkpointer=checkpointer)
    return _graph


def reset_graph() -> None:
    """Force a rebuild on next get_graph() call. Useful in tests."""
    global _graph
    _graph = None
