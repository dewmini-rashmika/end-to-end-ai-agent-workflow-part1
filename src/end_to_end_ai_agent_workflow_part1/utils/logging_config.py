"""
Logging configuration.

Sets up structured logging for the entire application.
Call configure_logging() once at startup before any loggers are used.
"""

from __future__ import annotations

import logging
import logging.config
import sys

from ..config.settings import settings


def configure_logging() -> None:
    """Configure application-wide logging based on APP_ENV."""

    level = logging.DEBUG if settings.app.debug else logging.INFO

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s | %(levelname)-8s | %(name)-40s | %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                # Simple JSON-ish format for production log aggregators
                "format": (
                    '{"time":"%(asctime)s","level":"%(levelname)s",'
                    '"logger":"%(name)s","msg":"%(message)s"}'
                ),
                "datefmt": "%Y-%m-%dT%H:%M:%SZ",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "standard" if settings.app.debug else "json",
                "level": level,
            },
        },
        "loggers": {
            # Application loggers
            "tripmate": {"handlers": ["console"], "level": level, "propagate": False},
            "end_to_end_ai_agent_workflow_part1": {
                "handlers": ["console"],
                "level": level,
                "propagate": False,
            },
            # Third-party noise reduction
            "httpx": {"level": logging.WARNING},
            "httpcore": {"level": logging.WARNING},
            "urllib3": {"level": logging.WARNING},
            "psycopg": {"level": logging.WARNING},
            "psycopg_pool": {"level": logging.INFO},
            "langchain": {"level": logging.WARNING},
            "langgraph": {"level": logging.INFO},
            "openai": {"level": logging.WARNING},
            "uvicorn": {"handlers": ["console"], "level": logging.INFO, "propagate": False},
            "uvicorn.error": {"handlers": ["console"], "level": logging.INFO, "propagate": False},
            "uvicorn.access": {"handlers": ["console"], "level": logging.INFO, "propagate": False},
        },
        "root": {
            "handlers": ["console"],
            "level": level,
        },
    }

    logging.config.dictConfig(config)
    logging.getLogger(__name__).info(
        "Logging configured | level=%s | env=%s",
        logging.getLevelName(level),
        settings.app.env,
    )
