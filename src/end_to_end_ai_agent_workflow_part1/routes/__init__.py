"""Routes package — FastAPI routers for trips, sessions, and health."""

from .trips import router as trips_router
from .sessions import router as sessions_router
from .health import router as health_router

__all__ = ["trips_router", "sessions_router", "health_router"]
