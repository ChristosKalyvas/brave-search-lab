"""Tests for the --site / --goggle (domain filtering) features."""
import pytest
import requests

from bravelab.client import BraveSearchClient


@pytest.fixture
def capturing_client(monkeypatch):
    """A client whose outgoing request params are captured for assertions."""
    captured = {}

    def fake_get(self, url, params=None, timeout=None):
        captured.clear()
        captured.update(params or {})
        class R:
            status_code = 200
            headers = {}
            text = "{}"

            def json(self):
                return {"web": {"results": []}}

        return R()

    monkeypatch.setattr(requests.Session, "get", fake_get)
    client = BraveSearchClient(api_key="test-key", cache=None)
    return client, captured


def test_site_bare_domain_becomes_operator(capturing_client):
    client, captured = capturing_client
    client.web("python asyncio", site="stackoverflow.com")
    assert captured["q"] == "site:stackoverflow.com python asyncio"


def test_site_accepts_explicit_operator(capturing_client):
    client, captured = capturing_client
    client.web("python", site="site:github.com")        # not doubled
    assert captured["q"] == "site:github.com python"


def test_no_site_leaves_query_untouched(capturing_client):
    client, captured = capturing_client
    client.web("just a query")
    assert captured["q"] == "just a query"
    assert "goggles" not in captured


def test_goggle_is_passed_through(capturing_client):
    client, captured = capturing_client
    client.web("climate", goggles="https://example.com/tech.goggle")
    assert captured["goggles"] == "https://example.com/tech.goggle"


def test_apply_site_static_helper():
    assert BraveSearchClient._apply_site("q", None) == "q"
    assert BraveSearchClient._apply_site("q", "a.com") == "site:a.com q"
