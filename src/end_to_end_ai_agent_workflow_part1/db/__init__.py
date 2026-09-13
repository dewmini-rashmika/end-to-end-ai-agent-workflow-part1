"""Database package — connection pool, schema, repositories, and checkpointer."""

from .connection import init_pool, close_pool, get_pool, get_connection
from .schema import init_schema
from .repositories import (
    ConversationRepository,
    AgentLogRepository,
    UserPreferencesRepository,
    ConversationRecord,
    AgentLogRecord,
    UserPreferencesRecord,
)
from .checkpointer import get_checkpointer, close_checkpointer

__all__ = [
    # Connection
    "init_pool",
    "close_pool",
    "get_pool",
    "get_connection",
    # Schema
    "init_schema",
    # Repositories
    "ConversationRepository",
    "AgentLogRepository",
    "UserPreferencesRepository",
    # DTOs
    "ConversationRecord",
    "AgentLogRecord",
    "UserPreferencesRecord",
    # Checkpointer
    "get_checkpointer",
    "close_checkpointer",
]
