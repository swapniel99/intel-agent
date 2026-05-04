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
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -e .          # installs fastmcp, httpx, prefab-ui, uvicorn

python main.py            # starts server at http://localhost:8000 (streamable-http transport)

# Tests
pytest                    # unit tests: file CRUD, deduplication, API fallback mock

# Frontend
# Load unpacked extension from chrome://extensions/
# pnpm for any frontend build steps (TBD)
```

## Demo Sequence (must be demonstrable)

User prompt → Gemini chains: `fetch_tech_news` → `manage_local_library("check_duplicates")` → `manage_local_library("save_new")` → `render_prefab_dashboard` → Prefab UI injected in Side Panel.

## Key Constraints

- Gemini tool binding is **dynamic** — `sidepanel.js` POSTs `tools/list` to `http://localhost:8000/mcp` at init
- MCP protocol endpoint: `POST http://localhost:8000/mcp` (FastMCP streamable-http transport)
- Tool returns are uniform `dict` or `list[dict]` — no mixed `str|list` unions
- `fetch_tech_news` fallback prepends `{"status": "..."}` sentinel to result list — never raises
- Python version pinned to 3.14 (`.python-version`)
