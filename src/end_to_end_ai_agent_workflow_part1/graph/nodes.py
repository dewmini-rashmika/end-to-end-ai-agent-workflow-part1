"""
LangGraph node functions.

Each node receives the full TravelState, runs one agent, and returns
a partial state dict with only the fields it updates. LangGraph merges
partial updates via the Annotated reducers defined in TravelState.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..agents import (
    get_flight_agent,
    get_hotel_agent,
    get_itinerary_agent,
    get_final_response_agent,
)
from ..services.agent_executor import execute_agent
from ..state.travel_state import TravelState, FlightResult, HotelResult, ItineraryDay

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: parse LLM JSON blocks safely
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> Any | None:
    """Try to extract a JSON object or array from a markdown code block or raw text."""
    # Try ```json ... ``` block first
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Try raw JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Node 1: parse_query
# ---------------------------------------------------------------------------

def parse_query_node(state: TravelState) -> dict:
    """
    Parse the user's natural-language query into structured travel parameters.

    Uses the LLM (without tools) to extract: origin, destination,
    departure_date, return_date, num_travelers, trip_duration_days,
    budget, and interests.
    """
    from ..config.settings import settings
    logger.info("[node:parse_query] Parsing user query…")
    
    if settings.llm.gemini_api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model=settings.llm.gemini_model_name,
            api_key=settings.llm.gemini_api_key,
            temperature=0.0,
        )
    else:
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            api_key=settings.llm.api_key,
            model=settings.llm.model_name,
            temperature=0.0,
        )

    system = SystemMessage(content=(
        "You are a travel query parser. Extract structured travel parameters from "
        "the user's message and return them as a single JSON object with these exact keys:\n"
        "  origin (city or IATA code),\n"
        "  destination (city or IATA code),\n"
        "  departure_date (YYYY-MM-DD or empty string),\n"
        "  return_date (YYYY-MM-DD or null),\n"
        "  num_travelers (integer, default 1),\n"
        "  trip_duration_days (integer, default 3),\n"
        "  budget (one of: budget, mid-range, luxury — default mid-range),\n"
        "  interests (free text, e.g. 'beaches food history' or empty string).\n\n"
        "Return ONLY the JSON object, no markdown fences, no extra text."
    ))
    human = HumanMessage(content=state.get("user_query", ""))

    from tenacity import retry, wait_exponential, stop_after_attempt
    
    @retry(wait=wait_exponential(multiplier=2, min=5, max=30), stop=stop_after_attempt(5))
    def _invoke_llm():
        return llm.invoke([system, human])

    try:
        response = _invoke_llm()
        content = response.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        elif not isinstance(content, str):
            content = str(content)

        parsed = _extract_json(content) or {}
        if not isinstance(parsed, dict):
            parsed = {}
    except Exception as exc:
        logger.error("[node:parse_query] LLM parsing failed: %s", exc)
        parsed = {}

    # Safe defaults
    result = {
        "origin": parsed.get("origin", ""),
        "destination": parsed.get("destination", ""),
        "departure_date": parsed.get("departure_date", ""),
        "return_date": parsed.get("return_date"),
        "num_travelers": int(parsed.get("num_travelers") or 1),
        "trip_duration_days": int(parsed.get("trip_duration_days") or 3),
        "budget": parsed.get("budget", "mid-range") or "mid-range",
        "interests": parsed.get("interests", ""),
        "current_agent": "parse_query",
    }
    logger.info("[node:parse_query] → %s", result)
    return result


# ---------------------------------------------------------------------------
# Node 2: flight_agent_node
# ---------------------------------------------------------------------------

def flight_agent_node(state: TravelState) -> dict:
    """Run the Flight Agent and return parsed flight results."""
    logger.info("[node:flight_agent] Starting…")
    agent = get_flight_agent()

    try:
        text, new_messages = execute_agent(agent, state)
        # Store raw text — structured parsing happens in the response agent
        flight_data: list[FlightResult] = [{"raw_text": text}]  # type: ignore
    except Exception as exc:
        logger.error("[node:flight_agent] Failed: %s", exc, exc_info=True)
        flight_data = []
        new_messages = []
        return {
            "flight_results": flight_data,
            "errors": [f"flight_agent: {exc}"],
            "completed_agents": ["flight_agent"],
            "current_agent": "flight_agent",
        }

    return {
        "flight_results": flight_data,
        "messages": new_messages,
        "completed_agents": ["flight_agent"],
        "current_agent": "flight_agent",
    }


# ---------------------------------------------------------------------------
# Node 3: hotel_agent_node
# ---------------------------------------------------------------------------

def hotel_agent_node(state: TravelState) -> dict:
    """Run the Hotel Agent and return parsed hotel results."""
    logger.info("[node:hotel_agent] Starting…")
    agent = get_hotel_agent()

    try:
        text, new_messages = execute_agent(agent, state)
        hotel_data: list[HotelResult] = [{"raw_text": text}]  # type: ignore
    except Exception as exc:
        logger.error("[node:hotel_agent] Failed: %s", exc, exc_info=True)
        return {
            "hotel_results": [],
            "errors": [f"hotel_agent: {exc}"],
            "completed_agents": ["hotel_agent"],
            "current_agent": "hotel_agent",
        }

    return {
        "hotel_results": hotel_data,
        "messages": new_messages,
        "completed_agents": ["hotel_agent"],
        "current_agent": "hotel_agent",
    }


# ---------------------------------------------------------------------------
# Node 4: itinerary_agent_node
# ---------------------------------------------------------------------------

def itinerary_agent_node(state: TravelState) -> dict:
    """Run the Itinerary Agent and return the day-wise plan."""
    logger.info("[node:itinerary_agent] Starting…")
    agent = get_itinerary_agent()

    try:
        text, new_messages = execute_agent(agent, state)
        itinerary_data: list[ItineraryDay] = [{"raw_text": text}]  # type: ignore
    except Exception as exc:
        logger.error("[node:itinerary_agent] Failed: %s", exc, exc_info=True)
        return {
            "itinerary": [],
            "errors": [f"itinerary_agent: {exc}"],
            "completed_agents": ["itinerary_agent"],
            "current_agent": "itinerary_agent",
        }

    return {
        "itinerary": itinerary_data,
        "messages": new_messages,
        "completed_agents": ["itinerary_agent"],
        "current_agent": "itinerary_agent",
    }


# ---------------------------------------------------------------------------
# Node 5: final_response_node
# ---------------------------------------------------------------------------

def final_response_node(state: TravelState) -> dict:
    """
    Run the Final Response Agent to synthesise all agent outputs
    into a single polished travel plan.
    """
    logger.info("[node:final_response] Starting…")
    agent = get_final_response_agent()

    try:
        text, new_messages = execute_agent(agent, state)
    except Exception as exc:
        logger.error("[node:final_response] Failed: %s", exc, exc_info=True)
        return {
            "final_response": f"Error generating travel plan: {exc}",
            "errors": [f"final_response_agent: {exc}"],
            "completed_agents": ["final_response_agent"],
            "current_agent": "final_response_agent",
        }

    return {
        "final_response": text,
        "messages": new_messages,
        "completed_agents": ["final_response_agent"],
        "current_agent": "final_response_agent",
    }
