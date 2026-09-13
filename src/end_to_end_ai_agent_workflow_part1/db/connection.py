"""
PostgreSQL connection pool management.

Uses psycopg3 async connection pool so the same pool is shared across
FastAPI requests and LangGraph checkpointer without re-connecting on every call.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import psycopg
from psycopg_pool import AsyncConnectionPool

from ..config.settings import settings

logger = logging.getLogger(__name__)

# Module-level pool — initialised once at app startup via lifespan
_pool: AsyncConnectionPool | None = None


async def init_pool() -> AsyncConnectionPool:
    """
    Create and open the async connection pool.
    Called once during FastAPI lifespan startup.
    """
    global _pool

    if _pool is not None:
        logger.warning("Connection pool already initialised — skipping.")
        return _pool

    conninfo = settings.postgres.connection_string
    logger.info(
        "Initialising PostgreSQL connection pool "
        "(min=%d, max=%d) → %s:%d/%s",
        settings.postgres.pool_min,
        settings.postgres.pool_max,
        settings.postgres.host,
        settings.postgres.port,
        settings.postgres.db,
    )

    _pool = AsyncConnectionPool(
        conninfo=conninfo,
        min_size=settings.postgres.pool_min,
        max_size=settings.postgres.pool_max,
        open=False,          # we open explicitly below
        kwargs={"autocommit": True},  # required by LangGraph checkpointer
    )
    await _pool.open()
    logger.info("PostgreSQL connection pool ready.")
    return _pool


async def close_pool() -> None:
    """
    Gracefully close the pool.
    Called during FastAPI lifespan shutdown.
    """
    global _pool
    if _pool is not None:
        logger.info("Closing PostgreSQL connection pool…")
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL connection pool closed.")


def get_pool() -> AsyncConnectionPool:
    """
    Return the active pool.
    Raises RuntimeError if called before init_pool().
    """
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialised. "
            "Ensure init_pool() is called during application startup."
        )
    return _pool


@asynccontextmanager
async def get_connection() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """
    Async context manager that yields a single connection from the pool.

    Usage:
        async with get_connection() as conn:
            await conn.execute("SELECT 1")
    """
    pool = get_pool()
    async with pool.connection() as conn:
        yield conn


# ---------------------------------------------------------------------------
# Sync connection string helper (used by LangGraph checkpointer setup)
# ---------------------------------------------------------------------------

def get_sync_connection_string() -> str:
    """Return the plain connection string for sync psycopg usage."""
    return settings.postgres.connection_string
