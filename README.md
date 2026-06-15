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
```

### The "buzz score", briefly

Each topic's score combines **volume** (how many recent articles) with
**freshness** via exponential decay — an article loses half its weight every 24h:

```
buzz = Σ  0.5 ^ (age_hours / 24)
```

So ten articles from last week score lower than three from this morning. It's a
compact example of turning raw search output into a signal you could alert on.

---

## Configuration

| Variable | Required | Purpose |
|---|---|---|
| `BRAVE_API_KEY` | ✅ | Your Brave Search subscription token. |
| `ANTHROPIC_API_KEY` | optional | If set (with `pip install ".[llm]"`), `ask` synthesizes answers with a model instead of the built-in extractive ranker. |
| `BRAVELAB_MODEL` | optional | Override the model used for synthesis. |

---

## Development

```bash
pip install -e ".[dev,llm]"
make test     # pytest — fully mocked, no network, no API key needed
make lint     # ruff
make run-api  # uvicorn with reload
```

Tests stub the Brave HTTP layer (see `tests/conftest.py`), so CI is fast,
deterministic, and never spends your quota. GitHub Actions runs the suite on
Python 3.10–3.12.

## Project layout

```
src/bravelab/
  client.py    # BraveSearchClient: retries, backoff, caching
  models.py    # WebResult / NewsResult / SearchResponse
  cache.py     # TTLCache (on-disk, hashed keys)
  rag.py       # answer_question(): ranking + citations, pluggable LLM
  monitor.py   # TrendMonitor: freshness-weighted buzz score
  cli.py       # argparse CLI -> `bravelab`
  api.py       # FastAPI app
tests/         # network-free unit tests
examples/      # demo.py end-to-end script
```

## License

MIT — see [LICENSE](LICENSE). Not affiliated with Brave Software; "Brave" is a
trademark of its owner. This is an independent example project.
