"""Command-line interface for brave-search-lab.

Examples
--------
    bravelab search "rust web frameworks" --count 5
    bravelab ask "who won the latest f1 race?"
    bravelab monitor "openai" "anthropic" "mistral ai"
    bravelab suggest "python async"
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from .client import BraveAPIError, BraveSearchClient
from .monitor import TrendMonitor
from .rag import answer_question


def _client() -> BraveSearchClient:
    try:
        return BraveSearchClient()
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)


def cmd_search(args: argparse.Namespace) -> int:
    client = _client()
    results = client.web(args.query, count=args.count, freshness=args.freshness)
    if not results:
        print("No results.")
        return 0
    for i, r in enumerate(results, start=1):
        age = f"  ({r.age})" if r.age else ""
        print(f"{i:>2}. {r.title}{age}\n    {r.url}\n    {r.description}\n")
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    client = _client()
    answer = answer_question(args.query, client, top_k=args.top_k)
    print(answer.render())
    return 0


def cmd_monitor(args: argparse.Namespace) -> int:
    client = _client()
    monitor = TrendMonitor(client)
    board = monitor.leaderboard(args.topics)
    width = max((len(p.topic) for p in board), default=10)
    print(f"{'TOPIC':<{width}}  BUZZ   ARTICLES  NEWEST     STATE")
    print("-" * (width + 38))
    for p in board:
        newest = "—" if p.newest_hours == float("inf") else f"{p.newest_hours:>5.1f}h"
        print(
            f"{p.topic:<{width}}  {p.buzz_score:>4.1f}   {p.article_count:>7}   "
            f"{newest:>7}   {p.temperature}"
        )
    return 0


def cmd_suggest(args: argparse.Namespace) -> int:
    client = _client()
    for s in client.suggest(args.query):
        print(s)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bravelab", description="Brave Search API toolkit")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("search", help="web search")
    s.add_argument("query")
    s.add_argument("--count", type=int, default=10)
    s.add_argument("--freshness", choices=["pd", "pw", "pm", "py"], default=None)
    s.set_defaults(func=cmd_search)

    a = sub.add_parser("ask", help="web-grounded answer with citations")
    a.add_argument("query")
    a.add_argument("--top-k", type=int, default=5)
    a.set_defaults(func=cmd_ask)

    m = sub.add_parser("monitor", help="rank topics by news buzz")
    m.add_argument("topics", nargs="+")
    m.set_defaults(func=cmd_monitor)

    g = sub.add_parser("suggest", help="query autocomplete")
    g.add_argument("query")
    g.set_defaults(func=cmd_suggest)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except BraveAPIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
