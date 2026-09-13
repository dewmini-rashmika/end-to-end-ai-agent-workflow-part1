"""
LangGraph PostgreSQL checkpointer setup.

Wraps langgraph-checkpoint-postgres so the graph can persist and resume
conversations using the same Postgres instance.
"""

import logging

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from ..config.settings import settings

logger = logging.getLogger(__name__)

_checkpointer: AsyncPostgresSaver | None = None


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Lazily create and return the async Postgres checkpointer.
    The checkpointer creates its own internal tables on first use.
    """
    global _checkpointer

    if _checkpointer is not None:
        return _checkpointer

    logger.info("Setting up LangGraph AsyncPostgresSaver…")

    from .connection import get_pool
    pool = get_pool()
    _checkpointer = AsyncPostgresSaver(pool)
    
    # Create the internal checkpoint tables if they don't exist
    await _checkpointer.setup()

    logger.info("LangGraph checkpointer ready.")
    return _checkpointer


async def close_checkpointer() -> None:
    """Close the checkpointer connection. Called during app shutdown."""
    global _checkpointer
    if _checkpointer is not None:
        logger.info("Closing LangGraph checkpointer…")
        # AsyncPostgresSaver manages its own connection pool internally
        _checkpointer = None
        logger.info("LangGraph checkpointer closed.")
