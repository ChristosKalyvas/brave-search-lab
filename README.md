# 🦁 brave-search-lab

A small, friendly toolkit for the **[Brave Search API](https://brave.com/search/api/)** — an independent web index built for developers.

It gives you four things in one tidy package:

| | Component | What it does |
|---|---|---|
| 🔌 | **Typed client** | Clean Python wrapper over Brave's web / news / suggest endpoints, with retries, backoff, and on-disk caching. |
| 🖥️ | **CLI** | `bravelab search`, `ask`, `monitor`, `suggest` — straight from your terminal. |
| 🌐 | **FastAPI service** | A tiny REST API (`/search`, `/ask`, `/monitor`) with auto-generated Swagger docs. |
| 🧠 | **Web-grounded Q&A** | Ask a question, get an answer built from live results **with inline citations** — no LLM key required. |
| 📈 | **Trend monitor** | Turn news results into a freshness-weighted *buzz score* and rank topics hottest-first. |

The whole thing runs **out of the box with nothing but a free Brave API key** — the question-answering uses a transparent extractive ranker by default, and *optionally* upgrades to an LLM if you set `ANTHROPIC_API_KEY`.

---

## Demo

All four commands, in one run:

```console
$ bravelab search "brave search api" --count 3
 1. Brave Search API  (3 days ago)
    https://brave.com/search/api/
    An independent index with billions of pages and a generous free tier.
 2. Brave Search API Pricing  (1 week ago)
    https://brave.com/search/api/pricing
    Free plan: 2,000 queries/month. Paid plans add news, AI snippets and higher limits.
 3. Getting started guide  (5 days ago)
    https://api-dashboard.search.brave.com/
    Create a subscription token and call the REST endpoint with an X-Subscription-Token header.

$ bravelab ask "What is the Brave Search API?"
Here's what the web says about "What is the Brave Search API?":

An independent index with billions of pages and a generous free tier. [1] Free
plan: 2,000 queries/month. Paid plans add news, AI snippets and higher limits. [2]
Create a subscription token and call the REST endpoint with a token header. [3]

Sources:
  [1] Brave Search API - https://brave.com/search/api/
  [2] Brave Search API Pricing - https://brave.com/search/api/pricing
  [3] Getting started guide - https://api-dashboard.search.brave.com/

$ bravelab monitor "openai" "anthropic" "mistral ai"
TOPIC       BUZZ   ARTICLES  NEWEST     STATE
------------------------------------------------
openai       3.1         4      1.0h   🔥 hot
anthropic    1.0         2     10.0h   🧊 quiet
mistral ai   0.1         1     72.0h   🧊 quiet

$ bravelab suggest "brave search api"
brave search api python
brave search api pricing
brave search api vs google
```

> The `ask` output above is the zero-dependency extractive answerer (no LLM key).
> Set `ANTHROPIC_API_KEY` and the same command returns a model-synthesized answer
> with the same `[n]` citation contract.

---

## Quickstart

```bash
git clone https://github.com/<you>/brave-search-lab.git
cd brave-search-lab
pip install -e .

cp .env.example .env        # then paste your key
export BRAVE_API_KEY="BSA..."   # free: 2,000 queries/month
```

> Get a free key in two minutes at **https://brave.com/search/api/**.

### CLI

```bash
bravelab search "rust web frameworks" --count 5 --freshness pw
bravelab ask "what is the brave search api?"
bravelab monitor "openai" "anthropic" "mistral ai"
bravelab suggest "python async"
```

`bravelab monitor` prints a live leaderboard:

```
TOPIC       BUZZ   ARTICLES  NEWEST     STATE
------------------------------------------------
openai       6.4         12     1.5h    🔥 hot
anthropic    2.1          9    18.0h    📈 warm
mistral ai   0.7          4    52.0h    🧊 quiet
```

### Python

```python
from bravelab import BraveSearchClient, answer_question, TrendMonitor

client = BraveSearchClient()                       # reads BRAVE_API_KEY

# 1) Plain search
for r in client.web("brave search api", count=3):
    print(r.title, "->", r.url)

# 2) Web-grounded answer with citations
print(answer_question("Who makes the Brave browser?", client).render())

# 3) Which topic is hottest right now?
board = TrendMonitor(client).leaderboard(["nvidia", "amd", "intel"])
print(board[0].topic, board[0].temperature)
```

### REST API

```bash
uvicorn bravelab.api:app --reload
# open http://127.0.0.1:8000/docs
curl "http://127.0.0.1:8000/ask?q=what+is+the+brave+search+api"
```

---

## How the pieces fit

```
            ┌──────────────┐
   CLI ────▶│              │
  REST ────▶│  bravelab    │──▶  Brave Search API  (web / news / suggest)
 Python ───▶│   client     │
            └──────┬───────┘
                   │ normalized WebResult / NewsResult
        ┌──────────┼───────────┐
        ▼          ▼           ▼
   ranking     TrendMonitor   TTL cache
   + citations  (buzz score)  (.bravecache/)
        │
        ▼
   Answer(text, sources[])