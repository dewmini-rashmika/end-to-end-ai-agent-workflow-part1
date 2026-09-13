"""
Security headers middleware.

Adds production-standard HTTP security headers to every response:
  - X-Content-Type-Options
  - X-Frame-Options
  - X-XSS-Protection
  - Strict-Transport-Security (production only)
  - Content-Security-Policy
  - Referrer-Policy
  - Permissions-Policy
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject security headers on every HTTP response."""

    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self._is_production = environment == "production"

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Block clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Legacy XSS filter (belt + braces)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Don't leak referrer cross-origin
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Restrict browser feature access
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        if self._is_production:
            # Force HTTPS for 1 year, include subdomains
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Minimal CSP — tighten further for your specific frontend origin
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.smith.langchain.com;"
        )

        return response
