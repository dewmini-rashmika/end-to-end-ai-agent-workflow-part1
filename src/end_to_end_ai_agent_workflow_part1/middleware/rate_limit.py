"""
Rate limiting middleware using slowapi (Starlette-compatible limiter).

Configured from RateLimitSettings in config/settings.py.
Each endpoint can declare its own limit via the @limiter.limit() decorator.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


def _get_client_ip(request: Request) -> str:
    """
    Extract the real client IP, respecting X-Forwarded-For in proxy environments.
    Falls back to the direct connection address.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first (client) IP in the chain
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


# Module-level limiter — imported by routes that need per-endpoint limits
limiter = Limiter(key_func=_get_client_ip, default_limits=["200/minute"])


def configure_rate_limiter(app: FastAPI) -> Limiter:
    """
    Attach the slowapi limiter to the FastAPI app.
    Returns the limiter so routes can import it for per-endpoint decoration.

    Usage in routes:
        from ..middleware.rate_limit import limiter

        @router.post("/plan")
        @limiter.limit("10/minute")
        async def plan_trip(request: Request, ...):
            ...
    """
    from ..config.settings import settings

    if not settings.rate_limit.enabled:
        logger.info("Rate limiting is DISABLED.")
        return limiter

    logger.info(
        "Rate limiting ENABLED | plan_trip=%s | global=%s",
        settings.rate_limit.plan_trip,
        settings.rate_limit.global_limit,
    )
    return limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a clean 429 JSON response instead of the default HTML page."""
    logger.warning(
        "Rate limit exceeded | ip=%s | path=%s | limit=%s",
        _get_client_ip(request),
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Too many requests",
            "detail": f"Rate limit exceeded: {exc.detail}. Please slow down.",
            "status_code": 429,
        },
        headers={"Retry-After": "60"},
    )
