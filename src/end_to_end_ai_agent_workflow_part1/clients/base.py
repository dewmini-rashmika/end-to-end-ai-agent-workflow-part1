"""
Base HTTP client with retry logic, timeout handling, and structured error reporting.
All external API clients inherit from this.
"""

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Raised when an external API returns an error response."""

    def __init__(self, service: str, status_code: int, message: str, raw: Any = None):
        self.service = service
        self.status_code = status_code
        self.message = message
        self.raw = raw
        super().__init__(f"[{service}] HTTP {status_code}: {message}")


class BaseHTTPClient:
    """
    Thin wrapper around requests.Session with:
    - Configurable retry strategy (exponential back-off)
    - Structured error raising via APIError
    - Per-request timing logs
    """

    SERVICE_NAME: str = "external_api"

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        total_retries: int = 3,
        backoff_factor: float = 0.5,
        status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504),
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = self._build_session(total_retries, backoff_factor, status_forcelist)

    # ------------------------------------------------------------------
    # Session factory
    # ------------------------------------------------------------------

    @staticmethod
    def _build_session(
        total_retries: int,
        backoff_factor: float,
        status_forcelist: tuple[int, ...],
    ) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=total_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=["GET", "POST"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        start = time.perf_counter()
        try:
            response = self._session.get(url, params=params, timeout=self.timeout)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.debug(
                "%s GET %s → %d (%dms)",
                self.SERVICE_NAME, url, response.status_code, elapsed_ms,
            )
            return self._handle_response(response)
        except requests.exceptions.Timeout:
            raise APIError(self.SERVICE_NAME, 408, f"Request timed out after {self.timeout}s")
        except requests.exceptions.ConnectionError as exc:
            raise APIError(self.SERVICE_NAME, 503, f"Connection error: {exc}")

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        start = time.perf_counter()
        try:
            response = self._session.post(url, json=payload, timeout=self.timeout)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.debug(
                "%s POST %s → %d (%dms)",
                self.SERVICE_NAME, url, response.status_code, elapsed_ms,
            )
            return self._handle_response(response)
        except requests.exceptions.Timeout:
            raise APIError(self.SERVICE_NAME, 408, f"Request timed out after {self.timeout}s")
        except requests.exceptions.ConnectionError as exc:
            raise APIError(self.SERVICE_NAME, 503, f"Connection error: {exc}")

    def _handle_response(self, response: requests.Response) -> dict:
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                raise APIError(
                    self.SERVICE_NAME,
                    response.status_code,
                    "Response is not valid JSON",
                    response.text,
                )
        # Try to extract a useful error message from the body
        try:
            body = response.json()
            message = (
                body.get("error", {}).get("message")
                or body.get("message")
                or body.get("error")
                or response.text
            )
        except ValueError:
            message = response.text or "Unknown error"

        raise APIError(self.SERVICE_NAME, response.status_code, str(message), body if 'body' in dir() else None)

    def close(self) -> None:
        self._session.close()
