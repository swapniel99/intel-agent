# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**IntelAgent** is a pharma-market intelligence assistant (Chrome Extension + local Python backend) that fetches brand sentiment and search presence, then renders a curated dashboard.

**Current branch (`google_trends`):** focused on marketing intel tools. `fetch_tech_news` and `manage_local_library` do NOT exist here; those are on `main`. `fetch_content_trends` is commented out (Google Trends client singleton `_get_trends_client()` still present in `main.py`).

## Architecture

### Frontend (Chrome Extension — Manifest V3)
- **Standalone Window UI** (`extension/index.html` / `index.js`) — orchestrator + primary UI
- **Provider abstraction** (`extension/providers/`): `GeminiProvider` wraps `@google/genai`; `OllamaProvider` converts Gemini-history format to OpenAI-compatible messages and calls a local Ollama instance. Provider selected at runtime from `chrome.storage.local`.
- `index.js` calls `mcpInitialize()` + `loadMcpTools()` at startup, runs agentic loop, proxies each `functionCall` to `POST http://localhost:8000/mcp`
- **Layout:** Resizable side-by-side panels — left: dashboard iframe, right: chat history + prompt input (default ~70/30)
- Dashboard rendering: `render_dashboard` → backend populates `_LAST_DASHBOARD_HTML` → iframe loads `http://localhost:8000/dashboard?theme=...`
- `background.js` opens extension window on icon click
- `genai.js` is bundled `@google/genai` SDK (no build step)
- Settings stored in `chrome.storage.local`: Gemini API key, MCP server URL, provider (`gemini`|`ollama`), Ollama URL/model, Ollama thinking toggle, theme, Gemini model

**Defaults:**
- Gemini model: `gemini-3.1-flash-lite` (change via inline settings panel)
- Ollama URL: `http://localhost:11434`, model: `gemma4:26b`
- MCP URL: `http://localhost:8000/mcp`

**Agentic loop:** MAX_TURNS=12, forceFinish at turn 8 (constrains tools to `render_dashboard` only)

### Backend (Python 3.14 + FastMCP)
Runs on `http://localhost:8000`. FastMCP exposes tools via streamable-HTTP at `/mcp`. Additional route `/dashboard` (GET) serves last rendered HTML.

**HuggingFace model loaded at startup** — `cardiffnlp/twitter-roberta-base-sentiment-latest` loaded via `transformers.pipeline` before any request. First cold start downloads the model (~500MB); subsequent starts load from cache.

**3 MCP tools:**
| Tool | Details |
|---|---|
| `fetch_brand_sentiment` | Reddit + Twitter/X + LinkedIn sentiment for pharma brands. Uses RoBERTa for scoring. Twitter: API v2 if `TWITTER_BEARER_TOKEN` set, else DDGS fallback. Returns `[{brand, platform, total_posts, positive_pct, negative_pct, neutral_pct, sentiment_score, top_posts}]`. |
| `fetch_search_presence` | DuckDuckGo rank check for brands across search keywords. DDGS backend chain: `yahoo → yandex → auto`. Returns `[{keyword, brand, rank, present, url, title, snippet, source_backend, top_results}]`. |
| `render_dashboard` | Compiles research into rich HTML. 6 chart types (Bar, Line, Area, Pie, Radar, Radial), metrics, tables, layouts. Returns `{"status": "dashboard_ready"}`. |

**Sentiment scoring:** `_score_sentiment(texts)` batches through RoBERTa (batch_size=16). `_bucket_top_posts()` groups by label (neg first). `_TWITTER_BRAND_QUERY` disambiguates short names (e.g. `"pharmeasy"` → `'"PharmEasy" OR "@pharmeasyapp"'`). `_BRAND_DOMAINS` maps brand names to domains for search presence.

**CORS:** `allow_origins=["*"]`, `allow_credentials=False`. MCP protocol headers explicitly listed in `allow_headers`.

## Setup & Commands

```bash
# Backend — one-time setup
uv sync

# Backend — run server (Twitter token optional — enables API v2; falls back to DDGS)
./.venv/bin/python main.py
TWITTER_BEARER_TOKEN=xxx ./.venv/bin/python main.py   # with Twitter API

# Tests — self-contained; spawn stdio subprocess or use TestClient (no external server needed)
uv run pytest test_mcp_server.py -v

# Run single test
uv run pytest test_mcp_server.py::test_render_basic_dashboard -v

# Twitter-gated tests skip unless token set
TWITTER_BEARER_TOKEN=xxx uv run pytest test_mcp_server.py -v
```

**Frontend:** Load unpacked from `chrome://extensions/` → "Load unpacked" → select `extension/`

**`.env` file:** create at repo root with `TWITTER_BEARER_TOKEN=...` (loaded via `python-dotenv` at startup)

## CI/CD

`.github/workflows/pytest.yml` — runs `uv run pytest` on push/PR to `main`. Python 3.14 + Ubuntu.

## Key Constraints

- Python environment: **use `./.venv/bin/python`** (Python 3.14 pinned in `.python-version`)
- `pytrends-modern[selenium]` is a dep — requires a browser/chromedriver available in PATH for Google Trends scraping; trends calls silently degrade without it
- **TODO:** `fetch_content_trends` commented out — Google Trends scraping unreliable; fix requires migrating to paid [SerpAPI](https://serpapi.com/google-trends-api) (`serpapi` or `google-search-results` pkg). Client singleton `_get_trends_client()` preserved in `main.py` as scaffold.
- **TODO:** LinkedIn arm of `fetch_brand_sentiment` ([main.py:275-289](main.py#L275-L289)) is unreliable — scrapes `site:linkedin.com/posts` via DDGS; LinkedIn posts barely search-indexed, frequently hits `insufficient_data` (<3 posts), only title+snippet (weak sentiment signal). No official LinkedIn API supports third-party brand-mention search (Marketing/Community APIs are scoped to owned org pages only). Fix requires a paid scraper with post-content search — Bright Data LinkedIn dataset/scraper preferred (Apify post-search actors as cheaper fallback). Otherwise drop LinkedIn and rely on Reddit + Twitter.
- HuggingFace model cold-starts may download ~500MB; set `TRANSFORMERS_CACHE` to control location
- Gemini tool binding is dynamic — `index.js` POSTs `tools/list` at init, converts to `functionDeclarations`
- MCP session auto-recovery: retry on session loss, 20s timeout, up to 2 attempts with exponential backoff
- Tool returns: uniform `dict` or `list[dict]`; errors return `[{"status": "..."}]`, never raise
- DDGS backend chain retries primary (yahoo) 5× before falling back; `_ddgs_text_with_fallback()` handles this
- Ollama provider: `geminiHistoryToOpenAI()` in `ollama-provider.js` converts Gemini-format history (role: `"model"`) to OpenAI format (role: `"assistant"`) including tool call ID mapping
- Theme passed to dashboard via `?theme=dark|light`; backend injects `class="dark"` on `<html>` tag

## Code Patterns

**Backend:**
- `@mcp.tool()` auto-exposes functions via `/mcp`; docstrings become Gemini function descriptions
- `_normalize_chart(chart)` fixes common agent mistakes (wrong keys, missing type, flat labels/values) before `_build_chart_node()` converts to Prefab JSON
- `layout="auto"` in `render_dashboard` picks effective layout from content shape: cards→`article_feed`, chart-only→`chart_focus`, table-only→`table_report`, else→`kpi_grid`

**Frontend:**
- Preset buttons inject canned prompts for common marketing intel queries
- `conversationCheckpoints` stack enables undo without reload
- `appendChatMessage()` for all UI updates

**Tool Return Schemas:**
- `fetch_brand_sentiment`: `[{brand, platform, total_posts, positive_pct, negative_pct, neutral_pct, sentiment_score, top_posts}]` or `[{brand, platform, status}]` on failure
- `fetch_search_presence`: `[{keyword, brand, rank, present, url, title, snippet, source_backend, top_results}]`
- `render_dashboard`: `{"status": "dashboard_ready"}` (backend caches HTML)

## Project Layout

```
intel-agent/
├── main.py                    # FastMCP server + 3 tools + /dashboard route
├── test_mcp_server.py         # Self-contained integration tests (stdio transport)
├── pyproject.toml             # deps: fastmcp, uvicorn, httpx, prefab-ui, ddgs, pytrends-modern, torch, transformers, python-dotenv
├── .env                       # TWITTER_BEARER_TOKEN (gitignored)
├── graphify-out/              # Knowledge graph
└── extension/
    ├── manifest.json          # MV3 — host: localhost:8000, localhost:11434, googleapis.com
    ├── index.html / index.js  # Main UI + agentic loop
    ├── background.js          # Opens window on icon click
    ├── options.html / options.js  # API key settings page
    ├── genai.js               # Bundled @google/genai ES module
    └── providers/
        ├── gemini-provider.js # Wraps @google/genai with googleSearch + forceFinish logic
        └── ollama-provider.js # OpenAI-compatible client + Gemini→OpenAI history converter
```

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
