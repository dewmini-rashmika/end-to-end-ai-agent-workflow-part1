"""Config package — settings singleton and agent prompts."""

from .settings import settings, Settings
from .prompts import get_agent_prompt

__all__ = ["settings", "Settings", "get_agent_prompt"]
