"""
TripMate AI — FastAPI application factory.

Startup / shutdown lifecycle:
  1. Configure logging
  2. Configure LangSmith tracing
  3. Initialise PostgreSQL connection pool
  4. Run database schema migrations (idempotent DDL)
  5. Set up LangGraph checkpointer
  6. Compile LangGraph workflow (with checkpointer)

Shutdown:
  - Close LangGraph checkpointer
  - Close PostgreSQL connection pool
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config.settings import settings
from .utils.logging_config import configure_logging
from .utils.langsmith_setup import configure_langsmith
from .db.connection import init_pool, close_pool
from .db.schema import init_schema
from .db.checkpointer import get_checkpointer, close_checkpointer
from .graph.workflow import get_graph
from .middleware.logging_middleware import RequestLoggingMiddleware
from .middleware.security import SecurityHeadersMiddleware
from .middleware.error_handler import global_exception_handler
from .middleware.rate_limit import configure_rate_limiter, rate_limit_exceeded_handler
from .routes import trips_router, sessions_router, health_router

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown resources."""

    # ---- STARTUP ----
    configure_logging()
    configure_langsmith()

    logger.info("=" * 60)
    logger.info(
        "Starting %s v%s [%s]",
        settings.app.title, settings.app.version, settings.app.env,
    )
    logger.info("=" * 60)

    await init_pool()
    await init_schema()
    checkpointer = await get_checkpointer()
    get_graph(checkpointer=checkpointer)

    logger.info("All systems ready. TripMate AI is accepting requests.")

    yield  # ← application runs here

    # ---- SHUTDOWN ----
    logger.info("Shutting down TripMate AI…")
    await close_checkpointer()
    await close_pool()
    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app.title,
        version=settings.app.version,
        description=settings.app.description,
        # Show docs only in non-production environments
        docs_url="/docs" if settings.app.env != "production" else None,
        redoc_url="/redoc" if settings.app.env != "production" else None,
        openapi_url="/openapi.json" if settings.app.env != "production" else None,
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------ #
    # Rate limiter (slowapi)                                               #
    # ------------------------------------------------------------------ #
    limiter = configure_rate_limiter(app)
    app.state.limiter = limiter
    app.add_exception_handler(429, rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # ------------------------------------------------------------------ #
    # CORS                                                                 #
    # ------------------------------------------------------------------ #
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )

    # ------------------------------------------------------------------ #
    # Custom middleware                                                    #
    # ------------------------------------------------------------------ #
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, environment=settings.app.env)

    # ------------------------------------------------------------------ #
    # Exception handlers                                                  #
    # ------------------------------------------------------------------ #
    app.add_exception_handler(Exception, global_exception_handler)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "detail": exc.errors(),
                "status_code": 422,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
            },
        )

    # ------------------------------------------------------------------ #
    # Routers                                                             #
    # ------------------------------------------------------------------ #
    API_PREFIX = "/api/v1"
    app.include_router(health_router)
    app.include_router(trips_router, prefix=API_PREFIX)
    app.include_router(sessions_router, prefix=API_PREFIX)

    return app


# Module-level app instance (imported by uvicorn in main.py)
app = create_app()
