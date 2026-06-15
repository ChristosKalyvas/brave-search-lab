"""A small, well-behaved client for the Brave Search API.

Docs: https://api-dashboard.search.brave.com/app/documentation
Get a free key at https://brave.com/search/api/ and export it:

    export BRAVE_API_KEY="BSA..."
"""
from __future__ import annotations

import os
import time
from typing import Any, Optional

import requests

from .cache import TTLCache
from .models import NewsResult, SearchResponse, WebResult

WEB_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
NEWS_ENDPOINT = "https://api.search.brave.com/res/v1/news/search"
SUGGEST_ENDPOINT = "https://api.search.brave.com/res/v1/suggest/search"


class BraveAPIError(RuntimeError):
    """Raised when the Brave API returns a non-success response."""

    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Brave API error {status}: {message}")


class BraveSearchClient:
    """Typed wrapper over the Brave Search API with retries and caching.

    Parameters
    ----------
    api_key:
        Your subscription token. Falls back to ``$BRAVE_API_KEY``.
    cache:
        Optional :class:`TTLCache`. Pass ``None`` to disable caching.
    max_retries:
        How many times to retry on 429 / 5xx with exponential backoff.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        cache: Optional[TTLCache] = None,
        max_retries: int = 3,
        timeout: float = 15.0,
        session: Optional[requests.Session] = None,
    ):
        self.api_key = api_key or os.getenv("BRAVE_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "No Brave API key. Pass api_key=... or set BRAVE_API_KEY. "
                "Grab a free one at https://brave.com/search/api/"
            )
        self.cache = cache if cache is not None else TTLCache()
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.api_key,
                "User-Agent": "brave-search-lab/0.1 (+https://github.com)",
            }
        )

    # ----------------------------------------------------------------- core
    def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        cache_key = endpoint + "?" + repr(sorted(params.items()))
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        backoff = 1.0
        last_msg = "unknown error"
        for attempt in range(self.max_retries + 1):
            resp = self.session.get(endpoint, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                if self.cache:
                    self.cache.set(cache_key, data)
                return data
            last_msg = resp.text[:300]
            # Retry only on rate-limit / transient server errors.
            if resp.status_code in (429, 500, 502, 503) and attempt < self.max_retries:
                retry_after = float(resp.headers.get("Retry-After", backoff))
                time.sleep(retry_after)
                backoff *= 2
                continue
            raise BraveAPIError(resp.status_code, last_msg)
        raise BraveAPIError(429, last_msg)

    # -------------------------------------------------------------- queries
    def web(
        self,
        query: str,
        *,
        count: int = 10,
        country: str = "us",
        search_lang: str = "en",
        freshness: Optional[str] = None,  # pd (24h), pw (week), pm (month), py (year)
        safesearch: str = "moderate",
    ) -> list[WebResult]:
        """Run a web search and return normalized :class:`WebResult` objects."""
        params: dict[str, Any] = {
            "q": query,
            "count": max(1, min(count, 20)),
            "country": country,
            "search_lang": search_lang,
            "safesearch": safesearch,
        }
        if freshness:
            params["freshness"] = freshness
        data = self._request(WEB_ENDPOINT, params)
        results = (data.get("web") or {}).get("results", [])
        return [WebResult.from_api(r) for r in results]

    def news(
        self,
        query: str,
        *,
        count: int = 10,
        country: str = "us",
        freshness: str = "pw",
    ) -> list[NewsResult]:
        """Run a news search, biased toward recent coverage."""
        params = {
            "q": query,
            "count": max(1, min(count, 20)),
            "country": country,
            "freshness": freshness,
        }
        data = self._request(NEWS_ENDPOINT, params)
        results = (data.get("results") or [])
        return [NewsResult.from_api(r) for r in results]

    def suggest(self, query: str, *, count: int = 5, country: str = "us") -> list[str]:
        """Autocomplete-style query suggestions."""
        params = {"q": query, "count": count, "country": country}
        data = self._request(SUGGEST_ENDPOINT, params)
        results = (data.get("results") or [])
        return [r.get("query", "") for r in results if r.get("query")]

    def search(self, query: str, *, count: int = 10, **kw: Any) -> SearchResponse:
        """Convenience: combine web + news into one :class:`SearchResponse`."""
        web = self.web(query, count=count, **{k: v for k, v in kw.items() if k != "freshness"})
        try:
            news = self.news(query, count=min(count, 5))
        except BraveAPIError:
            news = []
        return SearchResponse(query=query, web=web, news=news)
