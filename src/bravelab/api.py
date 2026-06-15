"""FastAPI service exposing the toolkit over HTTP.

Run it::

    uvicorn bravelab.api:app --reload

Then open http://127.0.0.1:8000/docs for interactive Swagger UI, or::

    curl "http://127.0.0.1:8000/search?q=brave+browser&count=3"
    curl "http://127.0.0.1:8000/ask?q=what+is+the+brave+search+api"
    curl "http://127.0.0.1:8000/monitor?topics=openai&topics=anthropic"
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from .client import BraveAPIError, BraveSearchClient
from .monitor import TrendMonitor
from .rag import answer_question

app = FastAPI(
    title="brave-search-lab",
    version="0.1.0",
    description="A tiny REST API over the Brave Search API: search, ask, monitor.",
)


@lru_cache
def get_client() -> BraveSearchClient:
    return BraveSearchClient()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search")
def search(
    q: str = Query(..., description="search query"),
    count: int = Query(10, ge=1, le=20),
    freshness: Optional[str] = Query(None, pattern="^(pd|pw|pm|py)$"),
):
    try:
        results = get_client().web(q, count=count, freshness=freshness)
    except BraveAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"query": q, "count": len(results), "results": [r.__dict__ for r in results]}


@app.get("/ask")
def ask(q: str = Query(..., description="question to answer"), top_k: int = Query(5, ge=1, le=10)):
    try:
        answer = answer_question(q, get_client(), top_k=top_k)
    except BraveAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {
        "question": answer.question,
        "answer": answer.text,
        "sources": [s.__dict__ for s in answer.sources],
    }


@app.get("/monitor")
def monitor(topics: list[str] = Query(..., description="one or more topics")):
    try:
        board = TrendMonitor(get_client()).leaderboard(topics)
    except BraveAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {
        "leaderboard": [
            {
                "topic": p.topic,
                "buzz_score": p.buzz_score,
                "article_count": p.article_count,
                "newest_hours": p.newest_hours,
                "state": p.temperature,
                "breaking": p.breaking,
            }
            for p in board
        ]
    }
