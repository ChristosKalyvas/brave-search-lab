from bravelab.client import BraveSearchClient
from bravelab.models import WebResult


def test_web_search_parses_and_cleans(fake_client):
    results = fake_client.web("brave search api", count=5)
    assert len(results) == 2
    first = results[0]
    assert isinstance(first, WebResult)
    assert first.title == "Brave Search API"          # <strong> stripped
    assert "search" in first.description.lower()
    assert "<strong>" not in first.description
    assert first.age == "2 days ago"


def test_page_age_fallback(fake_client):
    results = fake_client.web("x")
    assert results[1].age == "1 week ago"             # used page_age


def test_suggest(fake_client):
    suggestions = fake_client.suggest("python async")
    assert suggestions == ["python async await", "python asyncio"]


def test_combined_search(fake_client):
    resp = fake_client.search("ai", count=4)
    assert resp.query == "ai"
    assert len(resp.web) == 2
    assert len(resp.news) == 2
    assert len(resp) == 4


def test_missing_key(monkeypatch):
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    try:
        BraveSearchClient(cache=None)
    except ValueError as exc:
        assert "Brave API key" in str(exc)
    else:
        raise AssertionError("expected ValueError")
