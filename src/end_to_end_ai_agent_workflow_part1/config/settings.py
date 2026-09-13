"""
Application settings loaded from environment variables.
Uses pydantic-style validation via python-dotenv for a lightweight setup.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env from project root (two levels up from this file)
load_dotenv(override=True)


def _require(key: str) -> str:
    """Raise a clear error if a required env var is missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Check your .env file against .env.example."
        )
    return value


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default)


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LLMSettings:
    # Groq
    api_key: str = field(default_factory=lambda: _get("GROQ_API_KEY", ""))
    model_name: str = "openai/gpt-oss-120b"
    
    # Gemini
    gemini_api_key: str = field(default_factory=lambda: _get("GEMINI_API_KEY", ""))
    gemini_model_name: str = "gemini-3.5-flash-lite"
    
    # Common
    temperature: float = 0.2
    max_tokens: int = 1500
    streaming: bool = False


# ---------------------------------------------------------------------------
# Tavily
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TavilySettings:
    api_key: str = field(default_factory=lambda: _require("TAVILY_API_KEY"))
    max_results: int = 5
    search_depth: str = "advanced"  # "basic" | "advanced"


# ---------------------------------------------------------------------------
# AviationStack
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AviationStackSettings:
    api_key: str = field(default_factory=lambda: _require("AVIATIONSTACK_API_KEY"))
    base_url: str = field(default_factory=lambda: _get("AVIATIONSTACK_BASE_URL", "http://api.aviationstack.com/v1"))
    timeout: int = 30


# ---------------------------------------------------------------------------
# Google Maps
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GoogleMapsSettings:
    api_key: str = field(default_factory=lambda: _get("GOOGLE_MAPS_API_KEY", ""))
    enabled: bool = field(default_factory=lambda: bool(_get("GOOGLE_MAPS_API_KEY", "")))


# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PostgresSettings:
    host: str = field(default_factory=lambda: _get("POSTGRES_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(_get("POSTGRES_PORT", "5432")))
    db: str = field(default_factory=lambda: _get("POSTGRES_DB", "tripmate_db"))
    user: str = field(default_factory=lambda: _require("POSTGRES_USER"))
    password: str = field(default_factory=lambda: _require("POSTGRES_PASSWORD"))
    pool_min: int = field(default_factory=lambda: int(_get("POSTGRES_POOL_MIN", "2")))
    pool_max: int = field(default_factory=lambda: int(_get("POSTGRES_POOL_MAX", "10")))

    @property
    def connection_string(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )


# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AppSettings:
    host: str = field(default_factory=lambda: _get("APP_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(_get("APP_PORT", "8000")))
    env: str = field(default_factory=lambda: _get("APP_ENV", "development"))
    debug: bool = field(default_factory=lambda: _get("APP_DEBUG", "true").lower() == "true")
    title: str = field(default_factory=lambda: _get("APP_TITLE", "TripMate AI"))
    version: str = field(default_factory=lambda: _get("APP_VERSION", "1.0.0"))
    description: str = field(
        default_factory=lambda: _get("APP_DESCRIPTION", "LangGraph Multi-Agent Travel Planner")
    )


# ---------------------------------------------------------------------------
# LangGraph
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LangGraphSettings:
    checkpoint_table: str = field(
        default_factory=lambda: _get("LANGGRAPH_CHECKPOINT_TABLE", "tripmate_checkpoints")
    )
    recursion_limit: int = field(
        default_factory=lambda: int(_get("RECURSION_LIMIT", "25"))
    )


# ---------------------------------------------------------------------------
# LangSmith
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LangSmithSettings:
    enabled: bool = field(
        default_factory=lambda: _get("LANGSMITH_ENABLED", "false").lower() == "true"
    )
    api_key: str = field(default_factory=lambda: _get("LANGSMITH_API_KEY", ""))
    project: str = field(
        default_factory=lambda: _get("LANGSMITH_PROJECT", "tripmate-ai")
    )
    endpoint: str = field(
        default_factory=lambda: _get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    )
    tracing_v2: bool = field(
        default_factory=lambda: _get("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    )


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RateLimitSettings:
    enabled: bool = field(
        default_factory=lambda: _get("RATE_LIMIT_ENABLED", "true").lower() == "true"
    )
    # Default limits — format: "N/period" e.g. "10/minute"
    plan_trip: str = field(
        default_factory=lambda: _get("RATE_LIMIT_PLAN_TRIP", "10/minute")
    )
    global_limit: str = field(
        default_factory=lambda: _get("RATE_LIMIT_GLOBAL", "100/minute")
    )


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CORSSettings:
    origins: list = field(
        default_factory=lambda: [
            o.strip()
            for o in _get("CORS_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ]
    )
    allow_credentials: bool = True
    allow_methods: list = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    allow_headers: list = field(default_factory=lambda: ["*"])


# ---------------------------------------------------------------------------
# Root settings object  (singleton-style, imported everywhere)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Settings:
    llm: LLMSettings = field(default_factory=LLMSettings)
    tavily: TavilySettings = field(default_factory=TavilySettings)
    aviation_stack: AviationStackSettings = field(default_factory=AviationStackSettings)
    google_maps: GoogleMapsSettings = field(default_factory=GoogleMapsSettings)
    postgres: PostgresSettings = field(default_factory=PostgresSettings)
    app: AppSettings = field(default_factory=AppSettings)
    langgraph: LangGraphSettings = field(default_factory=LangGraphSettings)
    langsmith: LangSmithSettings = field(default_factory=LangSmithSettings)
    rate_limit: RateLimitSettings = field(default_factory=RateLimitSettings)
    cors: CORSSettings = field(default_factory=CORSSettings)


# Module-level singleton — import this everywhere
settings = Settings()
