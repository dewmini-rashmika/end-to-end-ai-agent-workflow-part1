"""
Database schema initialisation.

Creates all application tables if they do not already exist.
LangGraph's own checkpoint tables are created by the checkpointer itself;
this module handles the application-level tables only.
"""

import logging

from .connection import get_connection

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DDL Statements
# ---------------------------------------------------------------------------

CREATE_CONVERSATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS conversations (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      TEXT        NOT NULL,
    user_query      TEXT        NOT NULL,
    flight_results  JSONB,
    hotel_results   JSONB,
    itinerary       JSONB,
    final_response  TEXT,
    status          TEXT        NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

CREATE_CONVERSATIONS_SESSION_IDX = """
CREATE INDEX IF NOT EXISTS idx_conversations_session_id
    ON conversations (session_id);
"""

CREATE_CONVERSATIONS_CREATED_IDX = """
CREATE INDEX IF NOT EXISTS idx_conversations_created_at
    ON conversations (created_at DESC);
"""

CREATE_USER_PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS user_preferences (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      TEXT        NOT NULL UNIQUE,
    preferences     JSONB       NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

CREATE_AGENT_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS agent_logs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID        REFERENCES conversations(id) ON DELETE CASCADE,
    agent_name      TEXT        NOT NULL,
    input_data      JSONB,
    output_data     JSONB,
    duration_ms     INTEGER,
    status          TEXT        NOT NULL DEFAULT 'success',
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

CREATE_AGENT_LOGS_CONV_IDX = """
CREATE INDEX IF NOT EXISTS idx_agent_logs_conversation_id
    ON agent_logs (conversation_id);
"""

# Updated_at auto-update trigger
CREATE_UPDATED_AT_FUNCTION = """
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

CREATE_CONVERSATIONS_TRIGGER = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_conversations_updated_at'
    ) THEN
        CREATE TRIGGER set_conversations_updated_at
        BEFORE UPDATE ON conversations
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END;
$$;
"""

CREATE_USER_PREFS_TRIGGER = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_user_preferences_updated_at'
    ) THEN
        CREATE TRIGGER set_user_preferences_updated_at
        BEFORE UPDATE ON user_preferences
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END;
$$;
"""

# Ordered list of all DDL statements to run
ALL_DDL = [
    CREATE_CONVERSATIONS_TABLE,
    CREATE_CONVERSATIONS_SESSION_IDX,
    CREATE_CONVERSATIONS_CREATED_IDX,
    CREATE_USER_PREFERENCES_TABLE,
    CREATE_AGENT_LOGS_TABLE,
    CREATE_AGENT_LOGS_CONV_IDX,
    CREATE_UPDATED_AT_FUNCTION,
    CREATE_CONVERSATIONS_TRIGGER,
    CREATE_USER_PREFS_TRIGGER,
]


# ---------------------------------------------------------------------------
# Public initialisation function
# ---------------------------------------------------------------------------

async def init_schema() -> None:
    """
    Run all DDL statements to bring the schema up to date.
    Safe to call multiple times — all statements use IF NOT EXISTS.
    """
    logger.info("Initialising database schema…")
    async with get_connection() as conn:
        for ddl in ALL_DDL:
            await conn.execute(ddl)
    logger.info("Database schema initialisation complete.")
