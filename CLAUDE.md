# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AgentCurator** is a personal AI research assistant (Chrome Extension + local Python backend) that fetches trending tech articles, deduplicates them, and renders a curated dashboard. See `PRD.md` for full spec.

**Current state:** Backend (`main.py`) complete. Frontend (Chrome Extension) not yet implemented.

## Architecture

### Frontend (Chrome Extension — Manifest V3)
- Persistent **Side Panel** (`sidepanel.html` / `sidepanel.js`) acts as both Orchestrator and UI
- `sidepanel.js` fetches tool definitions from backend at init (`GET /tools`), calls Gemini API with those tools, proxies Gemini tool-call requests to backend (`POST`), injects final HTML into `#prefab-container`
- `background.js` opens the side panel on icon click via `chrome.sidePanel.setPanelBehavior`
- Package manager: `pnpm`

### Backend (Python 3.14 + FastMCP)
Runs on `http://localhost:8000`. FastMCP auto-exposes tools via SSE + HTTP POST.

**3 tools (all required):**
| Tool | Type | Details |
|---|---|---|
| `fetch_tech_news` | Internet | GET `hn.algolia.com/api/v1/search?query={q}&hitsPerPage={n}` → `[{title,url,points}]` |
| `manage_local_library` | File CRUD | `action="check_duplicates"` or `"save_new"` on `saved_articles.json` (deduplicates by URL) |
| `render_prefab_dashboard` | UI | Compiles articles → Prefab HTML/JSON string for injection |

**CORS:** Configured via `mcp.run(middleware=[...])` using Starlette `CORSMiddleware`. `allow_origins=["*"]`, `allow_credentials=False`. MCP protocol headers (`mcp-protocol-version`, `mcp-session-id`) explicitly listed in `allow_headers`.

**Fallback:** If `fetch_tech_news` fails, return cached `saved_articles.json` contents + status message. Never raise to the agent.

### Data
- `saved_articles.json`: `[{ id, title, url, points, ai_summary, saved_at }]`
- Prefab output: complete self-contained HTML page injected via `<iframe srcdoc>` (not `innerHTML` — scripts won't execute in innerHTML)

## Setup & Commands

```bash
# Backend — one-time setup
python -m venv .venv
source .venv/bin/activate
pip install -e .          # installs fastmcp, httpx, prefab-ui, uvicorn

# Backend — run server
python main.py            # http://localhost:8000 (streamable-http transport)

# Backend — verify server connectivity
python test_mcp.py        # async Streamable-HTTP client test → lists tools from running server

# Backend — run tests (when implemented)
pytest                    # unit tests for file CRUD, deduplication, API fallback

# Frontend
# pnpm install                    # when manifest.json + sidepanel.html created
# Load unpacked extension from chrome://extensions/
```

## Demo Sequence (must be demonstrable)

User prompt → Gemini chains: `fetch_tech_news` → `manage_local_library("check_duplicates")` → `manage_local_library("save_new")` → `render_prefab_dashboard` → Prefab UI injected in Side Panel.

## Key Constraints

- Gemini tool binding is **dynamic** — `sidepanel.js` POSTs `tools/list` to `http://localhost:8000/mcp` at init
- MCP protocol endpoint: `POST http://localhost:8000/mcp` (FastMCP streamable-http transport)
- Tool returns are uniform `dict` or `list[dict]` — no mixed `str|list` unions
- `fetch_tech_news` fallback prepends `{"status": "..."}` sentinel to result list — never raises
- Python version pinned to 3.14 (`.python-version`)

## Project Layout

```
agent_curator/
├── main.py                    # FastMCP server + 3 tools (fetch, manage, render)
├── test_mcp.py               # Async Streamable-HTTP client test
├── saved_articles.json        # Local article library (auto-created on first save)
├── pyproject.toml             # Python dependencies
├── .python-version            # Python 3.14 pin
├── CLAUDE.md                  # This file
├── README.md                  # Quick start guide
├── PRD.md                     # Complete spec + acceptance criteria
├── graphify-out/              # Knowledge graph (run `graphify update .` after code changes)
└── [FRONTEND TBD]
    ├── manifest.json          # Extension metadata
    ├── sidepanel.html         # Side panel UI template
    ├── sidepanel.js           # Gemini orchestrator + tool proxy
    ├── background.js          # Service worker (open panel on icon click)
    └── package.json / pnpm-lock.yaml
```

## Code Patterns

**Backend (main.py):**
- `@mcp.tool()` decorator registers functions as MCP tools auto-exposed via `/mcp` endpoint
- Tool docstrings become Gemini function descriptions
- `_load_library()` / `_save_library()` abstract JSON read/write
- Fallback pattern: catch exception → return cached data + status sentinel (never raise)

**Tool Return Schemas:**
- `fetch_tech_news`: `[{title, url, points}, ...]` or `[{status}, {title, url, points}, ...]` on fallback
- `manage_local_library`: `{status, articles?}` dict
- `render_prefab_dashboard`: HTML string (complete self-contained page)

**Frontend (TBD):**
- Init: `POST /mcp tools/list` → parse + register with Gemini
- Tool call: Gemini requests tool → `POST /mcp tools/call` → feed result back to Gemini
- Final render: `<iframe srcdoc={render_prefab_dashboard result}>`

## Testing & Verification

**Manual Server Test (Streamable-HTTP):**
```bash
# Terminal 1: Start backend
python main.py

# Terminal 2: Run connectivity test
python test_mcp.py
# Output: lists all 3 tools (fetch_tech_news, manage_local_library, render_prefab_dashboard)
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

**Unit Tests (pytest — when implemented):**
- Verify `manage_local_library` deduplicates by URL
- Mock Algolia API to test `fetch_tech_news` fallback
- Verify `render_prefab_dashboard` returns valid HTML

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
