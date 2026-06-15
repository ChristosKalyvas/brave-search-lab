"""Web-grounded question answering with inline citations.

The pipeline is deliberately simple and transparent:

    question --> Brave web search --> rank passages --> compose cited answer

By default it uses a **zero-dependency extractive answerer** that needs no LLM
and no extra API key, so the project runs out of the box. If you set
``ANTHROPIC_API_KEY`` (and install ``anthropic``), the answer is synthesized by
a model instead -- same citation contract either way.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from .client import BraveSearchClient
from .models import WebResult

_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


@dataclass(slots=True)
class Source:
    index: int
    title: str
    url: str
    snippet: str


@dataclass(slots=True)
class Answer:
    question: str
    text: str
    sources: list[Source] = field(default_factory=list)

    def render(self) -> str:
        lines = [self.text, "", "Sources:"]
        for s in self.sources:
            lines.append(f"  [{s.index}] {s.title} - {s.url}")
        return "\n".join(lines)


def _score(question_tokens: set[str], result: WebResult) -> float:
    """Lexical overlap between the question and a result's text."""
    text_tokens = _tokens(result.title + " " + result.description)
    if not text_tokens:
        return 0.0
    overlap = len(question_tokens & text_tokens)
    return overlap / (len(question_tokens) + 1)


def _extractive_answer(question: str, ranked: list[WebResult]) -> str:
    """Compose a readable answer from the top snippets, with [n] citations."""
    if not ranked:
        return "I couldn't find anything relevant on the web for that question."
    sentences: list[str] = []
    for i, r in enumerate(ranked, start=1):
        snippet = r.description.strip()
        if not snippet:
            continue
        if snippet[-1] not in ".!?":
            snippet += "."
        sentences.append(f"{snippet} [{i}]")
        if len(sentences) >= 3:
            break
    intro = f"Here's what the web says about “{question}”:\n\n"
    return intro + " ".join(sentences)


# Optional LLM synthesis -------------------------------------------------------
def _anthropic_answer(question: str, ranked: list[WebResult]) -> Optional[str]:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None
    context = "\n".join(
        f"[{i}] {r.title}\n{r.description}\n{r.url}"
        for i, r in enumerate(ranked, start=1)
    )
    prompt = (
        "Answer the question using ONLY the numbered sources below. "
        "Cite sources inline like [1], [2]. Be concise and factual.\n\n"
        f"Question: {question}\n\nSources:\n{context}\n\nAnswer:"
    )
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model=os.getenv("BRAVELAB_MODEL", "claude-3-5-haiku-latest"),
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in msg.content if block.type == "text")


def answer_question(
    question: str,
    client: BraveSearchClient,
    *,
    top_k: int = 5,
    answerer: Optional[Callable[[str, list[WebResult]], str]] = None,
) -> Answer:
    """Answer ``question`` using fresh Brave web results.

    ``answerer`` lets you swap the synthesis strategy. Resolution order when
    not provided: Anthropic (if configured) -> built-in extractive.
    """
    results = client.web(question, count=max(top_k, 8))
    q_tokens = _tokens(question)
    ranked = sorted(results, key=lambda r: _score(q_tokens, r), reverse=True)[:top_k]

    if answerer is not None:
        text = answerer(question, ranked)
    else:
        text = _anthropic_answer(question, ranked) or _extractive_answer(question, ranked)

    sources = [
        Source(index=i, title=r.title, url=r.url, snippet=r.description)
        for i, r in enumerate(ranked, start=1)
    ]
    return Answer(question=question, text=text, sources=sources)
