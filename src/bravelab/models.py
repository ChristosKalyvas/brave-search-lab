"""Normalized, dependency-free data models for Brave Search results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


def _clean(text: Optional[str]) -> str:
    """Brave wraps query-matched terms in <strong> tags; strip them out."""
    if not text:
        return ""
    return (
        text.replace("<strong>", "")
        .replace("</strong>", "")
        .replace("&#x27;", "'")
        .replace("&quot;", '"')
        .replace("&amp;", "&")
        .strip()
    )


@dataclass(slots=True)
class WebResult:
    title: str
    url: str
    description: str
    age: Optional[str] = None          # e.g. "2 days ago"
    language: Optional[str] = None
    family_friendly: bool = True

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> "WebResult":
        return cls(
            title=_clean(raw.get("title")),
            url=raw.get("url", ""),
            description=_clean(raw.get("description")),
            age=raw.get("age") or raw.get("page_age"),
            language=raw.get("language"),
            family_friendly=raw.get("family_friendly", True),
        )


@dataclass(slots=True)
class NewsResult:
    title: str
    url: str
    description: str
    source: Optional[str] = None
    age: Optional[str] = None
    breaking: bool = False

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> "NewsResult":
        meta = raw.get("meta_url") or {}
        return cls(
            title=_clean(raw.get("title")),
            url=raw.get("url", ""),
            description=_clean(raw.get("description")),
            source=meta.get("netloc") or raw.get("source"),
            age=raw.get("age") or raw.get("page_age"),
            breaking=raw.get("breaking", False),
        )


@dataclass(slots=True)
class SearchResponse:
    query: str
    web: list[WebResult] = field(default_factory=list)
    news: list[NewsResult] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.web) + len(self.news)
