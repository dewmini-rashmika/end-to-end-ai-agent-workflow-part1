"""
Global error handler middleware.

Catches unhandled exceptions and returns consistent JSON error responses
instead of leaking stack traces to API consumers.
"""

from __future__ import annotations

import logging
import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("tripmate.errors")


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler registered on the FastAPI app.
    Returns a structured JSON error response for any unhandled exception.
    """
    tb = traceback.format_exc()
    logger.error(
        "Unhandled exception on %s %s:\n%s",
        request.method, request.url.path, tb,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if str(exc) else "An unexpected error occurred.",
            "status_code": 500,
        },
    )


async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not found",
            "detail": str(exc),
            "status_code": 404,
        },
    )
