# 🦁 brave-search-lab

A small, friendly toolkit for the **[Brave Search API](https://brave.com/search/api/)** — an independent web index built for developers.

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

All commands, against the live index:

```console
$ bravelab search "rust web frameworks" --count 3
 1. r/rust on Reddit: Which web framework do you use in Rust?  (December 22, 2023)
    https://www.reddit.com/r/rust/comments/18ogwtl/...
 2. GitHub - flosse/rust-web-framework-comparison
    https://github.com/flosse/rust-web-framework-comparison
 3. Rust Web Frameworks in 2026: Axum vs Actix vs Rocket vs Warp vs Salvo
    https://aarambhdevhub.medium.com/rust-web-frameworks-in-2026-...

$ bravelab ask "What is the Brave Search API?"
Here's what the web says about "What is the Brave Search API?":

The Brave Search API gives developers programmatic access to Brave's independent
web search index. [1] A search engine API is a standardized interface designed to
interact with a search engine using code rather than a website. [2] The Brave
Search API excels in RAG pipelines and AI applications. [3]

Sources:
  [1] Brave Search API - https://brave.com/search/api/
  [2] What is a search engine API? - https://brave.com/search/api/guides/...
  [3] Brave Search API | Brave - https://brave.com/search/api/

$ bravelab monitor "openai" "anthropic"
TOPIC      BUZZ   ARTICLES  NEWEST     STATE
-----------------------------------------------
openai      8.8        12      2.0h   🔥 hot
anthropic   8.7        12      1.0h   🔥 hot
```

> The `ask` output above is the zero-dependency extractive answerer (no LLM key).
> Set `ANTHROPIC_API_KEY` and the same command returns a model-synthesized answer
> with the same `[n]` citation contract.

---

## Search operators & plan tiers

Brave honors search operators **inside the query string** (just like Google),
and the CLI also exposes first-class `--site` and `--goggle` flags:

```bash
bravelab search "python asyncio" --site stackoverflow.com   # scope to one domain
bravelab search "climate" --goggle https://example.com/tech.goggle   # re-rank/filter
bravelab search "rust web frameworks -site:pinterest.com"   # operators still work too
```

`--site foo.com` and a bare `site:foo.com` in the query are equivalent. Other
operators: `intitle:`, `filetype:`, and `+`/`-` term boosting. A **Goggle** is a
small rule set (hosted URL or inline) that re-ranks or filters results by domain
lists — programmable search bias that plain Google doesn't offer.

Endpoint availability depends on your Brave plan:

| Command | Endpoint | Free tier |
|---|---|---|
| `search`, `ask` | Web | ✅ included |
| `monitor` | News | ✅ included |
| `suggest` | Suggest | ❌ separate subscription (`OPTION_NOT_IN_PLAN`) |

If an endpoint isn't in your plan, the client raises a clear, actionable error
rather than a raw API dump.

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
```

### Python

```python
from bravelab import BraveSearchClient, answer_question, TrendMonitor

client = BraveSearchClient()                       # reads BRAVE_API_KEY

for r in client.web("brave search api", count=3):
    print(r.title, "->", r.url)

print(answer_question("Who makes the Brave browser?", client).render())

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

So ten articles from last week score lower than three from this morning.

---

## Configuration

| Variable | Required | Purpose |
|---|---|---|
| `BRAVE_API_KEY` | ✅ | Your Brave Search subscription token. |
| `ANTHROPIC_API_KEY` | optional | If set (with `pip install ".[llm]"`), `ask` synthesizes answers with a model instead of the built-in extractive ranker. |
| `BRAVELAB_MODEL` | optional | Override the model used for synthesis. |

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
