"""
Tavily Search API client.

Used by all agents as the primary web-search fallback / enrichment tool.
Wraps the official tavily-python SDK with a typed interface.
"""

import logging
from dataclasses import dataclass

from tavily import TavilyClient as _TavilySDK

from ..config.settings import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Typed response dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "score": self.score,
        }


@dataclass
class TavilySearchResponse:
    query: str
    answer: str | None          # AI-generated answer (advanced search only)
    results: list[SearchResult]

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "answer": self.answer,
            "results": [r.to_dict() for r in self.results],
        }

    def top_content(self, n: int = 3) -> str:
        """Return a concatenated string of the top-n result contents."""
        snippets = [r.content for r in self.results[:n] if r.content]
        return "\n\n".join(snippets)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class TavilySearchClient:
    """
    Typed wrapper around the official Tavily Python SDK.

    Usage:
        client = TavilySearchClient()
        response = client.search("best hotels in Paris under $150")
        print(response.answer)
    """

    def __init__(self):
        self._client = _TavilySDK(api_key=settings.tavily.api_key)
        self._max_results = settings.tavily.max_results
        self._search_depth = settings.tavily.search_depth

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        max_results: int | None = None,
        search_depth: str | None = None,
        include_answer: bool = True,
        topic: str = "general",          # "general" | "news"
    ) -> TavilySearchResponse:
        """
        Run a Tavily web search and return structured results.

        Args:
            query:          Natural-language search query.
            max_results:    Override default max results.
            search_depth:   "basic" or "advanced" (advanced costs 2 credits).
            include_answer: Whether to request the AI-synthesised answer.
            topic:          "general" or "news".

        Returns:
            TavilySearchResponse with optional answer and result list.
        """
        _max = max_results or self._max_results
        _depth = search_depth or self._search_depth

        logger.info("Tavily search [depth=%s]: %s", _depth, query)

        raw = self._client.search(
            query=query,
            search_depth=_depth,
            max_results=_max,
            include_answer=include_answer,
            topic=topic,
        )

        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=float(r.get("score", 0.0)),
            )
            for r in raw.get("results", [])
        ]

        logger.info("Tavily returned %d result(s).", len(results))

        return TavilySearchResponse(
            query=query,
            answer=raw.get("answer"),
            results=results,
        )

    def search_hotels(self, destination: str, budget: str = "") -> TavilySearchResponse:
        """Convenience method for hotel searches."""
        budget_hint = f" budget: {budget}" if budget else ""
        query = f"best hotels in {destination}{budget_hint} reviews ratings amenities price per night"
        return self.search(query, search_depth="advanced", include_answer=True)

    def search_attractions(self, destination: str, interests: str = "") -> TavilySearchResponse:
        """Convenience method for attractions and activities."""
        interest_hint = f" for {interests}" if interests else ""
        query = f"top tourist attractions and activities in {destination}{interest_hint}"
        return self.search(query, search_depth="advanced", include_answer=True)

    def search_flights_web(
        self, origin: str, destination: str, date: str
    ) -> TavilySearchResponse:
        """Fallback web search for flights when AviationStack returns no results."""
        query = (
            f"flights from {origin} to {destination} on {date} "
            "airlines price schedule direct"
        )
        return self.search(query, search_depth="advanced", include_answer=True)

    def search_travel_tips(self, destination: str) -> TavilySearchResponse:
        """Search for practical travel tips for a destination."""
        query = (
            f"travel tips for {destination} visa currency weather "
            "safety cultural etiquette"
        )
        return self.search(query, search_depth="basic", include_answer=True)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_tavily_client: TavilySearchClient | None = None


def get_tavily_client() -> TavilySearchClient:
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilySearchClient()
    return _tavily_client
