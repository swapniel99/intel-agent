# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AgentCurator** is a personal AI research assistant (Chrome Extension + local Python backend) that fetches trending tech articles, deduplicates them, and renders a curated dashboard. See `PRD.md` for full spec.

**Current state:** Backend (`main.py`) and frontend (`extension/`) both complete and functional.

## Architecture

### Frontend (Chrome Extension — Manifest V3)
- **Side Panel** (`extension/sidepanel.html` / `sidepanel.js`) acts as Orchestrator + primary UI (persistent across tabs)
- **Options Page** (`extension/options.html` / `options.js`) for one-time Gemini API key setup
- `sidepanel.js` calls `mcpInitialize()` + `loadMcpTools()` at startup, runs agentic loop calling Gemini with MCP tool declarations, proxies each `functionCall` to `POST http://localhost:8000/mcp tools/call`
- Dashboard rendering: final tool result (`render_prefab_dashboard`) → HTML string injected into `<iframe src="http://localhost:8000/dashboard">` (not `srcdoc` — avoids CSP issues with Prefab's CDN chunks)
- Analytics rendering: `render_analytics_chart` result injected into dedicated `<div id="chart-root">` 
- `background.js` opens side panel on icon click via `chrome.sidePanel.open`
- `genai.js` is bundled copy of `@google/genai` SDK (no build step — ES modules)
- Gemini API key stored in `chrome.storage.local`, configured via options page
- No package manager / build step — plain ES modules

### Backend (Python 3.14 + FastMCP)
Runs on `http://localhost:8000`. FastMCP exposes tools via streamable-HTTP at `/mcp`. Additional route `/dashboard` (GET) serves the last rendered prefab HTML for iframe loading.

**4 MCP tools** (web search delegated to Gemini built-in `googleSearch`, not MCP):
| Tool | Type | Details |
|---|---|---|
| `fetch_tech_news` | Internet | GET `hn.algolia.com/api/v1/search?query={q}&hitsPerPage={n}` → `[{title,url,points}]`. Falls back to `saved_articles.json` on failure. |
| `manage_local_library` | File CRUD | `action="check_duplicates"` or `"save_new"` on `saved_articles.json` (deduplicates by URL) |
| `render_prefab_dashboard` | UI | Compiles articles + topic/theme into dashboard spec → dict with status, topic, theme, cards |
| `render_analytics_chart` | UI | Renders bar/line/pie/percentage charts → dict with title, type, data |

`search_internet` (DuckDuckGo via `ddgs`) commented out at `main.py:170`. Replaced by Gemini native `googleSearch` tool wired in `sidepanel.js:179`. `ddgs`+`lxml` deps removed from `pyproject.toml`.

**CORS:** Configured via `mcp.run(middleware=[...])` using Starlette `CORSMiddleware`. `allow_origins=["*"]`, `allow_credentials=False`. MCP protocol headers (`mcp-protocol-version`, `mcp-session-id`) explicitly listed in `allow_headers`.

**Fallback:** If `fetch_tech_news` fails, return cached `saved_articles.json` contents + status message. Never raise to the agent.

### Data
- `saved_articles.json`: `[{ id, title, url, points, ai_summary, saved_at }]`
- Prefab output: complete self-contained HTML page injected via `<iframe srcdoc>` (not `innerHTML` — scripts won't execute in innerHTML)

## Setup & Commands

```bash
# Backend — one-time setup (uses uv, not pip directly)
uv sync                   # installs fastmcp, httpx, prefab-ui, uvicorn from uv.lock

# Backend — run server
python main.py            # http://localhost:8000 (streamable-http transport)

# Backend — verify server connectivity
python test_mcp.py        # async Streamable-HTTP client test → lists tools from running server

# Backend — run tests (when implemented)
pytest

# Frontend — no build step
# Load unpacked extension from chrome://extensions/ → "Load unpacked" → select extension/
```

## Demo Sequences

**Basic flow:** User prompt → Gemini chains: `fetch_tech_news` → `manage_local_library("check_duplicates")` → `manage_local_library("save_new")` → `render_prefab_dashboard` → dashboard injected into Side Panel.

**Extended flow:** User asks for trend analysis → Gemini calls native `googleSearch` → `render_analytics_chart` → chart rendered via `frappe-charts` into `<div id="chart-root">` alongside dashboard.

## Key Constraints

- Gemini tool binding is **dynamic** — `sidepanel.js` POSTs `tools/list` to `http://localhost:8000/mcp` at init, converts to `functionDeclarations`
- MCP protocol endpoint: `POST http://localhost:8000/mcp` (FastMCP streamable-http transport, JSON-RPC 2.0)
- Tool returns are uniform `dict` or `list[dict]` — no mixed `str|list` unions; exceptions return `[{status: "error message"}]`
- Fallback pattern: `fetch_tech_news` returns `{status}` sentinel, never raises (keeps agent running)
- MCP session auto-recovery: `sidepanel.js` retries on session loss, re-initializes `mcp-session-id` transparently
- Theme: global dark/light mode toggle in side panel UI (commit 8869476), state in `chrome.storage.local`
- Theme matching: Gemini must select best-match theme from exact list (medical, security, rust, python, ai, web, cloud, data, game, crypto, hardware, linux, science, devtools, infra, default)
- Python version pinned to 3.14 (`.python-version`)
- Prefab dashboard rendering happens client-side (JS), not server-side HTML generation

## Project Layout

```
agent_curator/
├── main.py                    # FastMCP server + 4 tools + /dashboard route
├── test_mcp.py                # Async Streamable-HTTP client test
├── saved_articles.json        # Local article library (auto-created on first save)
├── pyproject.toml             # Python deps (fastmcp, uvicorn, httpx, prefab-ui)
├── uv.lock                    # Locked deps (managed by uv)
├── .python-version            # Python 3.14 pin
├── graphify-out/              # Knowledge graph
└── extension/
    ├── manifest.json          # MV3 — permissions: sidePanel, storage; host: localhost:8000, googleapis.com, cdn.jsdelivr.net
    ├── sidepanel.html         # Side panel UI (orchestrator + dashboard/chart rendering + theme toggle)
    ├── sidepanel.js           # Gemini agentic loop + MCP proxy + Google Search + chart/dashboard injection
    ├── background.js          # Service worker — opens side panel on icon click
    ├── options.html           # API key settings page
    ├── options.js             # Save/load Gemini API key to chrome.storage.local
    ├── genai.js               # Bundled @google/genai ES module
    └── lib/
        └── frappe-charts.min.iife.js  # Chart rendering library for render_analytics_chart output
```

## Code Patterns

**Backend (main.py):**
- `@mcp.tool()` decorator registers async/sync functions as MCP tools auto-exposed via `/mcp` endpoint
- Tool docstrings become Gemini function descriptions (critical for agents to understand usage)
- `_load_library()` / `_save_library()` abstract JSON read/write
- Theme system: `_TOPIC_PALETTES` dict maps topic keywords (rust, python, ai, etc.) to color schemes; fallback to `_DEFAULT_META`
- Fallback pattern: catch exception → return cached data + `{status: "..."}` sentinel (never raise to agent)
- Tool execution logging emitted to stdout for debugging multi-tool agent routing

**Tool Return Schemas:**
- `fetch_tech_news`: `[{title, url, points}, ...]` or `[{status}, ...]` on fallback
- `manage_local_library`: `{status, articles?}` dict
- `render_prefab_dashboard`: `{status, topic, theme, cards}` dict (client renders HTML)
- `render_analytics_chart`: `{status, title, type, data: {labels, datasets}}` dict

**Frontend (extension/sidepanel.js):**
- Init: `mcpInitialize()` → `loadMcpTools()` → convert to Gemini `functionDeclarations` schema
- Agentic loop: `generateContent` → detect `functionCalls` → `callMcpTool()` → `functionResponse` → repeat up to 12 turns (configurable `MAX_TURNS`)
- Dashboard rendering: `render_prefab_dashboard` result → extract HTML from `/dashboard` endpoint → set `$dashboardRoot.innerHTML` (or inject into iframe)
- Chart rendering: `render_analytics_chart` result → `frappe-charts` (lib/frappe-charts.min.iife.js) draws into `<div id="chart-root">`
- MCP session continuity: `mcp-session-id` header persisted; auto-recovery on session loss (re-init transparently)
- Gemini config: MCP `functionDeclarations` + native `googleSearch` tool registered together at `sidepanel.js:179`
- Theme: dark/light toggle wired via `chrome.storage.local`, applied to dashboard iframe + chart container
- Error state: if server unavailable, display "Server Disconnected" message (not silent failure)

## Testing & Verification

**Manual Server Test (Streamable-HTTP):**
```bash
# Terminal 1: Start backend
python main.py

# Terminal 2: Run connectivity test
python test_mcp.py
# Output: lists all 4 tools (fetch_tech_news, manage_local_library, render_prefab_dashboard, render_analytics_chart)
```

**Integration Test (curl):**
```bash
# MCP tools/list
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# MCP tools/call (fetch_tech_news)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
    "params": {
      "name": "fetch_tech_news",
      "arguments": {"query": "rust", "limit": 5}
    }
  }'
```

**Unit Tests (pytest — not yet implemented):**
- Verify `manage_local_library` deduplicates by URL
- Mock Algolia API to test `fetch_tech_news` fallback to `saved_articles.json`
- Verify theme selection logic handles edge cases (misspelled topics fall back to default)
- Verify chart spec generation with all chart types (bar, line, pie, percentage)

## Troubleshooting

**"Connection refused" on test_mcp.py:**
- Ensure `python main.py` is running in another terminal on port 8000
- Check firewall: `lsof -i :8000` should show uvicorn listening

**CORS errors in Chrome Extension:**
- CORS middleware is configured with `allow_origins=["*"]` in main.py
- Verify `mcp-protocol-version` and `mcp-session-id` headers in requests

**saved_articles.json doesn't exist:**
- It's auto-created on first `manage_local_library("save_new")` call
- Safe to delete; system will regenerate it

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
