"""
Request/response logging middleware.

Logs method, path, status code, and duration for every request.
Adds a unique X-Request-ID header for distributed tracing.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("tripmate.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with timing and assign a request ID."""

    async def dispatch(self, request: Request, call_next: any) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        # Attach request ID to state so route handlers can access it
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.error(
                "[%s] %s %s → UNHANDLED ERROR (%dms): %s",
                request_id,
                request.method,
                request.url.path,
                elapsed_ms,
                exc,
            )
            raise

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "[%s] %s %s → %d (%dms)",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
        return response
