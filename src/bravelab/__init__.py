"""brave-search-lab: a friendly toolkit for the Brave Search API.

Public surface:
    BraveSearchClient  - thin, typed wrapper over the Brave Search REST API
    WebResult, NewsResult - normalized result objects
    answer_question    - web-grounded Q&A with inline citations
    TrendMonitor       - track topics over time with a freshness/buzz score
"""
from .client import BraveSearchClient, BraveAPIError
from .models import WebResult, NewsResult, SearchResponse
from .rag import answer_question, Answer
from .monitor import TrendMonitor, TopicPulse

__version__ = "0.1.0"

__all__ = [
    "BraveSearchClient",
    "BraveAPIError",
    "WebResult",
    "NewsResult",
    "SearchResponse",
    "answer_question",
    "Answer",
    "TrendMonitor",
    "TopicPulse",
    "__version__",
]
