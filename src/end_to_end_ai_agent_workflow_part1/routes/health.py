"""
Health check routes.

GET /health         — liveness probe (no DB dependency)
GET /health/ready   — readiness probe (checks DB connection)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from ..config.settings import settings
from ..db.connection import get_pool

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Liveness probe",
    description="Returns 200 OK if the application process is running.",
)
async def health_check() -> dict:
    return {
        "status": "ok",
        "version": settings.app.version,
        "environment": settings.app.env,
    }


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Returns 200 OK when the app is ready to serve traffic (DB connected).",
)
async def readiness_check() -> JSONResponse:
    """Check that the database connection pool is healthy."""
    try:
        pool = get_pool()
        # Quick connectivity test
        async with pool.connection() as conn:
            await conn.execute("SELECT 1")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "database": "connected",
                "version": settings.app.version,
            },
        )
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "error": str(exc),
            },
        )
