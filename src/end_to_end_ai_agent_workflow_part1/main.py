"""
TripMate AI — uvicorn entry point.

Run directly:
    python -m end_to_end_ai_agent_workflow_part1.main

Or via the CLI script defined in pyproject.toml:
    uv run end-to-end-ai-agent-workflow-part1

Or with uvicorn directly:
    uvicorn end_to_end_ai_agent_workflow_part1.app:app --reload
"""

import uvicorn
from .config.settings import settings


def main() -> None:
    uvicorn.run(
        "end_to_end_ai_agent_workflow_part1.app:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level="debug" if settings.app.debug else "info",
        # Allow uvicorn to handle graceful shutdown
        timeout_graceful_shutdown=10,
    )


if __name__ == "__main__":
    main()
