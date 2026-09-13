"""
TripMate AI — LangGraph Multi-Agent Travel Planner
====================================================
Part 1: Simple workflow without MCP.

Package structure:
    config/     — settings singleton, system prompts
    clients/    — AviationStack, Tavily, Google Maps HTTP clients
    db/         — PostgreSQL connection pool, schema, repositories, checkpointer
    state/      — shared LangGraph TravelState TypedDict
    tools/      — LangChain tools (flight, hotel, itinerary, general)
    agents/     — four specialist LangChain agents + base class
    services/   — ReAct executor loop, high-level TravelService
    graph/      — LangGraph nodes, edges, workflow, async runner
    routes/     — FastAPI routers (trips, sessions, health)
    middleware/ — request logging, global error handler
    utils/      — logging configuration
    app.py      — FastAPI application factory
    main.py     — uvicorn entry point
"""

__version__ = "1.0.0"
__author__ = "dewmini-rashmika"


def main() -> None:
    """
    CLI entry point registered in pyproject.toml.
    Starts the uvicorn server using settings from .env.
    """
    import uvicorn
    from .config.settings import settings

    uvicorn.run(
        "end_to_end_ai_agent_workflow_part1.app:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level="debug" if settings.app.debug else "info",
    )
