"""Shared fixtures: a fake Brave client that never hits the network."""
import pytest
import requests

from bravelab.client import BraveSearchClient
from bravelab.cache import TTLCache


class _FakeResponse:
    def __init__(self, payload, status=200, headers=None):
        self._payload = payload
        self.status_code = status
        self.text = str(payload)
        self.headers = headers or {}

    def json(self):
        return self._payload


WEB_PAYLOAD = {
    "web": {
        "results": [
            {
                "title": "Brave <strong>Search</strong> API",
                "url": "https://brave.com/search/api/",
                "description": "Independent <strong>search</strong> index for developers.",
                "age": "2 days ago",
                "language": "en",
            },
            {
                "title": "Pricing",
                "url": "https://brave.com/search/api/pricing",
                "description": "Free tier with 2,000 queries per month.",
                "page_age": "1 week ago",
            },
        ]
    }
}

NEWS_PAYLOAD = {
    "results": [
        {"title": "Big launch", "url": "https://ex.com/a", "description": "x",
         "age": "2 hours ago", "breaking": True, "meta_url": {"netloc": "ex.com"}},
        {"title": "Follow up", "url": "https://ex.com/b", "description": "y",
         "age": "3 days ago", "meta_url": {"netloc": "ex.com"}},
    ]
}

SUGGEST_PAYLOAD = {"results": [{"query": "python async await"}, {"query": "python asyncio"}]}


@pytest.fixture
def fake_client(tmp_path, monkeypatch):
    def fake_get(self, url, params=None, timeout=None):
        if "news" in url:
            return _FakeResponse(NEWS_PAYLOAD)
        if "suggest" in url:
            return _FakeResponse(SUGGEST_PAYLOAD)
        return _FakeResponse(WEB_PAYLOAD)

    monkeypatch.setattr(requests.Session, "get", fake_get)
    cache = TTLCache(directory=tmp_path / "cache", ttl_seconds=1)
    return BraveSearchClient(api_key="test-key", cache=cache)
