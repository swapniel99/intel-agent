# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**IntelAgent** is a personal AI research assistant (Chrome Extension + local Python backend) that fetches trending tech articles from multiple sources and renders a curated dashboard.

**Current state:** Backend (`main.py`) and frontend (`extension/`) both complete and functional.

## Architecture

### Frontend (Chrome Extension — Manifest V3)
- **Standalone Window UI** (`extension/index.html` / `index.js`) — orchestrator + primary UI in dedicated window (not side panel)
- **Options Page** (`extension/options.html` / `options.js`) for one-time Gemini API key setup
- `index.js` calls `mcpInitialize()` + `loadMcpTools()` at startup, runs agentic loop with active provider, proxies each `functionCall` to `POST http://localhost:8000/mcp tools/call`
- **Provider abstraction** — `GeminiProvider` (`providers/gemini-provider.js`) and `OllamaProvider` (`providers/ollama-provider.js`) implement identical `generateContent()` interface. `index.js` instantiates one based on settings; loop code is provider-agnostic.
- **Layout:** Resizable side-by-side panels — left (dynamic %): dashboard iframe, right (dynamic %): chat history + prompt input. Default is roughly 70/30 split.
- Dashboard rendering: final tool result (`render_dashboard`) → backend populates `_LAST_DASHBOARD_HTML` → left panel sets `iframe.src` to `http://localhost:8000/dashboard?theme=...`
- `background.js` opens extension window on icon click
- `genai.js` is bundled copy of `@google/genai` SDK (no build step — ES modules)
- Gemini API key + MCP server URL stored in `chrome.storage.local`. Configurable via inline settings panel (gear icon in main UI) or `options.html` (manifest `options_page`)
- **Thinking/reasoning:** Gemini supports `thinkingLevel` (`MINIMAL`|`LOW`|`MEDIUM`|`HIGH`|off); Ollama supports `reasoning_effort` (`low`|`medium`|`high`|off). Both configurable via settings UI.
- Model: `gemini-3-flash-preview` default (configured in `index.js`); Ollama default `gemma4:e2b`
- No package manager / build step — plain ES modules
- Theme: dark/light mode toggle in UI, applied to dashboard iframe via query parameter

### Backend (Python 3.14 + FastMCP)
Runs on `http://localhost:8000`. FastMCP exposes tools via streamable-HTTP at `/mcp`. Additional route `/dashboard` (GET) serves the last rendered prefab HTML for iframe loading.

**3 MCP tools** (web search delegated to Gemini built-in `googleSearch`, not MCP):
| Tool | Type | Details |
|---|---|---|
| `fetch_tech_news` | Internet | Fetches from HN (Algolia), Dev.to, or Reddit; `source` param: `"hn"` | `"dev"` | `"reddit"` | `"all"` (default). Returns `[{title,url,points,source}]`. Falls back to `saved_articles.json` on failure. |
| `manage_local_library` | File CRUD | 6 actions on `saved_articles.json`: `check_duplicates`, `save_new`, `list_all`, `search`, `update`, `delete`. Deduplicates by URL. |
| `render_dashboard` | UI | Compiles research into a rich HTML dashboard. Supports 4 chart types (Bar, Line, Pie, Radar), metrics, tables, and layouts (`auto`, `split`). Requires at least one content field (cards/metrics/chart/table) — server-side guard returns error if all absent. |

`search_internet` (DuckDuckGo via `ddgs`) removed. Replaced by Gemini native `googleSearch` tool wired in `index.js`.

**CORS:** Configured via `mcp.run(middleware=[...])` using Starlette `CORSMiddleware`. `allow_origins=["*"]`, `allow_credentials=False`. MCP protocol headers (`mcp-protocol-version`, `mcp-session-id`) explicitly listed in `allow_headers`.

**Fallback:** If `fetch_tech_news` fails, return cached `saved_articles.json` contents + status message. Never raise to the agent.

### Data
- `saved_articles.json`: `[{ id, title, url, points, ai_summary, saved_at }]`
- Prefab output: complete self-contained HTML page served via `/dashboard` route with theme injection.

## Setup & Commands

```bash
# Backend — one-time setup (uses uv, not pip directly)
uv sync --all-groups       # installs fastmcp, httpx, prefab-ui, uvicorn + dev deps (pytest)

# Backend — run server
./.venv/bin/python main.py            # http://localhost:8000 (streamable-http transport)

# Backend — run all tests (uses TestClient internally; no live server required)
uv run pytest

# Backend — run single test
uv run pytest test_mcp_server.py::test_function_name -v

# Frontend — no build step
# Load unpacked extension from chrome://extensions/ → "Load unpacked" → select extension/
```

`asyncio_mode = "auto"` set in `pyproject.toml` — all async tests run without `@pytest.mark.asyncio`.

## CI/CD

GitHub Actions workflow in `.github/workflows/pytest.yml` runs unit tests on every push and pull request to the `main` branch.
- **Environment**: Python 3.14 (Ubuntu)
- **Tooling**: `uv` for dependency management and test execution


## Demo Sequences

**Basic flow:** User prompt → Gemini chains: `fetch_tech_news` → `manage_local_library("check_duplicates")` → `manage_local_library("save_new")` → `render_dashboard` → dashboard injected into main iframe.

## Key Constraints

- Gemini tool binding is **dynamic** — `index.js` POSTs `tools/list` to `http://localhost:8000/mcp` at init, converts to `functionDeclarations`
- Gemini model pinned: `gemini-3.1-flash-lite-preview` (index.js:4) — preview SKU, swap when GA
- MCP protocol endpoint: `POST http://localhost:8000/mcp` (FastMCP streamable-http transport, JSON-RPC 2.0)
- Tool returns are uniform `dict` or `list[dict]` — no mixed `str|list` unions; exceptions return `[{status: "error message"}]`
- Fallback pattern: `fetch_tech_news` returns `{status}` sentinel, never raises (keeps agent running)
- MCP session auto-recovery: `index.js` retries on session loss, re-initializes `mcp-session-id` transparently with timeout
- MCP request timeout: retry logic implemented; requests timeout after 20s, retry up to 2 attempts with exponential backoff
- Conversation history: in-memory tracking (not truncated); checkpoint stack enables undo/clear without reloading
- Theme: global dark/light mode toggle in extension UI, state in `chrome.storage.local`. Passed to dashboard via `?theme=dark|light`.
- Dashboard content: handled entirely by `render_dashboard` tool which returns `{"status": "dashboard_ready"}`.
- **Data Visualization**: Pro-actively use charts in `render_dashboard` whenever numerical data, metrics, or comparisons are involved.
- Python environment: **Mandatory** use of `./.venv/bin/python`. Always check for `.venv/` before running any command.
- Python version pinned to 3.14 (`.python-version`)
- Prefab dashboard rendering happens server-side, results cached in `_LAST_DASHBOARD_HTML`, served via `/dashboard`.
- Extension window: launched via `chrome.windows.create()` on icon click (not side panel); window dims configurable.

## Project Layout

```
intel-agent/
├── main.py                    # FastMCP server + 3 tools + /dashboard route
├── test_mcp_server.py         # Async Streamable-HTTP client test
├── saved_articles.json        # Local article library (auto-created on first save)
├── pyproject.toml             # Python deps (fastmcp, uvicorn, httpx, prefab-ui)
├── uv.lock                    # Locked deps (managed by uv)
├── .python-version            # Python 3.14 pin
├── graphify-out/              # Knowledge graph
└── extension/
    ├── manifest.json          # MV3 — permissions: storage; host: localhost:8000, googleapis.com, cdn.jsdelivr.net
    ├── index.html             # Main UI (resizable chat + dashboard panels)
    ├── index.js               # Agentic loop + MCP proxy + provider wiring + dashboard injection
    ├── background.js          # Service worker — opens window on icon click
    ├── options.html           # API key settings page
    ├── options.js             # Save/load Gemini API key to chrome.storage.local
    ├── genai.js               # Bundled @google/genai ES module
    ├── providers/
    │   ├── gemini-provider.js # Gemini generateContent wrapper (thinking support)
    │   └── ollama-provider.js # Ollama OpenAI-compat wrapper (reasoning_effort support)
    └── icons/                 # Extension branding assets
```

## Code Patterns

**Backend (main.py):**
- `@mcp.tool()` decorator registers async/sync functions as MCP tools auto-exposed via `/mcp` endpoint
- Tool docstrings become Gemini function descriptions (critical for agents to understand usage)
- `_load_library()` / `_save_library()` abstract JSON read/write
- Theme system: Dashboard theme (dark/light) handled via route injection.
- Fallback pattern: catch exception → return cached data + `{status: "..."}` sentinel (never raise to agent)
- Tool execution logging emitted to stdout for debugging multi-tool agent routing

**Tool Return Schemas:**
- `fetch_tech_news`: `[{title, url, points}, ...]` or `[{status}, ...]` on fallback
- `manage_local_library`: `{status, articles?}` dict
- `render_dashboard`: `{"status": "dashboard_ready"}` dict (backend caches HTML)

**Frontend (extension/index.js):**
- Init: `mcpInitialize()` → `loadMcpTools()` → convert to `functionDeclarations` → `initProvider()`
- Provider selection: `initProvider()` reads settings, constructs `GeminiProvider` or `OllamaProvider`; loop calls `provider.generateContent()` uniformly
- Agentic loop: MAX_TURNS=12, forceFinish at turn 8 (constrains tools to `render_dashboard` only)
  - generateContent → detect toolCalls → callMcpTool() → functionResponse → repeat
  - Fallback: if no toolCalls + text response, render text-only dashboard
  - System prompt: plain-English flows (no tool names/call format — model discovers tools from MCP docstrings)
  - System prompt rules: ALWAYS gather data before rendering; dashboard MUST include at least one content field; `summary` = 2-3 sentence prose only (never data)
- Conversation history: tracked in-memory (full history), checkpoint stack for undo/clear without reload
- Dashboard rendering: `render_dashboard` result triggers iframe reload with `?theme=...&t=...` (cache buster)
- MCP session continuity: `mcp-session-id` header persisted; auto-recovery on session loss with retry logic + timeout
- Gemini config: MCP `functionDeclarations` + native `googleSearch` tool registered together (Gemini only)
- OllamaProvider: converts Gemini-format history → OpenAI messages; calls `/v1/chat/completions`; returns Gemini-format parts so history stays uniform
- Theme: dark/light toggle wired via `chrome.storage.local`, applied to extension UI and passed to dashboard iframe
- UI Layout: dashboard panel (left) displays iframe; chat panel (right) shows conversation history + prompt input
- Error state: if server unavailable, display "Server Disconnected" message (not silent failure)

## UI/UX Patterns & Layout

**Auto-Resizing Prompt Input:**
- Textarea grows vertically as user types; height range: 40px min → 200px max
- CSS: `resize: vertical; overflow-y: auto;` + JS `onInput` adjusts `style.height`
- Prevents layout shift + keeps chat history visible while typing

**Conversation Checkpoints:**
- Undo button: revert to previous checkpoint (pops `conversationCheckpoints` stack)
- Clear button: reset all history + checkpoints + dashboard
- Checkpoints stored in-memory; lost on window close

**Conversation History Display:**
- Chat panel (right) logs all agent turns + user prompts.
- History is maintained for the duration of the window session; checkpoint stack enables undo.
- Use `appendChatMessage()` for UI updates.

**Resizable Panels:**
- `<div class="resizer">` between dashboard + chat divs enables horizontal resizing
- Mouse drag updates `flex` basis of panels; stored in session state.
- Stored in session state (not persisted across closes)

**Dashboard Iframe Rendering:**
- Right panel loads `http://localhost:8000/dashboard?theme={dark|light}&t={timestamp}`
- Cache buster (`&t=...`) forces reload on new dashboard generation
- Prefab HTML rendered server-side; iframe receives pre-built content
- Theme parameter injected into HTML template server-side

## Testing & Verification

**Unit Tests (no live server needed):**
```bash
uv run pytest test_mcp_server.py -v
# Tests use TestClient(mcp.http_app(transport="streamable-http")) — no server process required
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

## Troubleshooting

**"Connection refused" on test_mcp_server.py:**
- Ensure `python main.py` is running in another terminal on port 8000
- Check firewall: `lsof -i :8000` should show uvicorn listening

**CORS errors in Chrome Extension:**
- CORS middleware is configured with `allow_origins=["*"]` in main.py
- Verify `mcp-protocol-version` and `mcp-session-id` headers in requests

**Ollama 403 Forbidden from Chrome Extension:**
- Ollama blocks cross-origin requests by default
- Fix: set `OLLAMA_ORIGINS="*"` before starting Ollama
  ```bash
  launchctl setenv OLLAMA_ORIGINS "*"   # macOS — then restart Ollama app
  # or: OLLAMA_ORIGINS="*" ollama serve
  ```

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
