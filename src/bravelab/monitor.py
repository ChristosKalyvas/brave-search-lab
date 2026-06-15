"""Track topics over time and score how much 'buzz' each one has right now.

The monitor turns Brave news results into a single comparable number per topic
by combining *volume* (how many articles) with *freshness* (how recent they
are). It's a compact example of turning raw search output into a decision
signal you could alert on, chart, or rank.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from .client import BraveSearchClient
from .models import NewsResult

# Rough conversion of Brave's human "age" strings into hours.
_AGE_RE = re.compile(r"(\d+)\s*(minute|hour|day|week|month|year)", re.IGNORECASE)
_UNIT_HOURS = {
    "minute": 1 / 60,
    "hour": 1,
    "day": 24,
    "week": 24 * 7,
    "month": 24 * 30,
    "year": 24 * 365,
}


def age_to_hours(age: str | None) -> float:
    if not age:
        return _UNIT_HOURS["week"]  # unknown -> assume a week old
    m = _AGE_RE.search(age)
    if not m:
        return _UNIT_HOURS["week"]
    value, unit = int(m.group(1)), m.group(2).lower()
    return value * _UNIT_HOURS[unit]


def freshness_weight(hours: float, half_life_hours: float = 24.0) -> float:
    """Exponential decay: a 24h-old article counts half as much as a brand-new one."""
    return 0.5 ** (hours / half_life_hours)


@dataclass(slots=True)
class TopicPulse:
    topic: str
    article_count: int
    buzz_score: float
    newest_hours: float
    breaking: bool
    headlines: list[NewsResult] = field(default_factory=list)

    @property
    def temperature(self) -> str:
        if self.breaking or self.buzz_score >= 4:
            return "🔥 hot"
        if self.buzz_score >= 1.5:
            return "📈 warm"
        return "🧊 quiet"


class TrendMonitor:
    """Compute a freshness-weighted 'buzz' score for one or many topics."""

    def __init__(self, client: BraveSearchClient, *, per_topic: int = 12):
        self.client = client
        self.per_topic = per_topic

    def pulse(self, topic: str) -> TopicPulse:
        articles = self.client.news(topic, count=self.per_topic, freshness="pw")
        if not articles:
            return TopicPulse(topic, 0, 0.0, float("inf"), False, [])
        ages = [age_to_hours(a.age) for a in articles]
        buzz = sum(freshness_weight(h) for h in ages)
        breaking = any(a.breaking for a in articles)
        return TopicPulse(
            topic=topic,
            article_count=len(articles),
            buzz_score=round(buzz, 2),
            newest_hours=round(min(ages), 1),
            breaking=breaking,
            headlines=articles[:5],
        )

    def leaderboard(self, topics: Iterable[str]) -> list[TopicPulse]:
        """Rank several topics by buzz, hottest first."""
        pulses = [self.pulse(t) for t in topics]
        return sorted(pulses, key=lambda p: p.buzz_score, reverse=True)
