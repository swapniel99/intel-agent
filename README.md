# AgentCurator

Personal AI research assistant — Chrome Extension + local Python MCP backend.

Fetches trending HN articles, deduplicates against a local JSON library, and renders a curated Prefab dashboard in the browser side panel via Gemini tool chaining.

## Stack

- **Backend:** Python 3.14, FastMCP (streamable-http), uvicorn
- **Frontend:** Chrome Extension (Manifest V3), Gemini API
- **UI:** prefab-ui components rendered in `<iframe srcdoc>`

## Backend Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python main.py            # http://localhost:8000
```

## Tools

| Tool | Action |
|---|---|
| `fetch_tech_news` | GET HN Algolia → `[{title, url, points}]`. Falls back to local library on failure. |
| `manage_local_library` | `check_duplicates` → novel articles; `save_new` → write to `saved_articles.json` |
| `render_prefab_dashboard` | Compile articles → self-contained HTML page |

## MCP Endpoint

`POST http://localhost:8000/mcp` — use `tools/list` and `tools/call` JSON-RPC methods.

## Demo Sequence

> "Fetch top 4 articles on Local LLMs. Filter duplicates, save new ones, generate a Prefab dashboard."

Gemini chains: `fetch_tech_news` → `manage_local_library(check_duplicates)` → `manage_local_library(save_new)` → `render_prefab_dashboard` → iframe renders in Side Panel.

## Tests

```bash
pytest
```
