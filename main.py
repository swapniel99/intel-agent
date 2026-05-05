import json
import uuid
from ddgs import DDGS
import urllib.parse
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

LIBRARY_FILE = Path(__file__).parent / "saved_articles.json"

mcp = FastMCP("AgentCurator")

_cors_middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["mcp-protocol-version", "mcp-session-id", "Authorization", "Content-Type"],
        expose_headers=["mcp-session-id"],
    )
]


def _load_library() -> list[dict]:
    if not LIBRARY_FILE.exists():
        return []
    return json.loads(LIBRARY_FILE.read_text())


def _save_library(articles: list[dict]) -> None:
    LIBRARY_FILE.write_text(json.dumps(articles, indent=2))


@mcp.tool()
async def fetch_tech_news(query: str, limit: int = 10) -> list[dict]:
    """Fetch trending tech articles from Hacker News via Algolia.

    Returns a list of {title, url, points} objects.
    Falls back to saved_articles.json if the network request fails, with a
    sentinel {status} dict prepended so the agent can surface the message.
    """
    url = f"https://hn.algolia.com/api/v1/search?query={query}&hitsPerPage={limit}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        hits = resp.json().get("hits", [])
        return [
            {"title": h.get("title", ""), "url": h.get("url", ""), "points": h.get("points", 0)}
            for h in hits
            if h.get("url")
        ]
    except Exception:
        cached = _load_library()
        status = {"status": "The internet source is currently unavailable. Displaying previously saved articles from your local storage."}
        if cached:
            articles = [
                {"title": a["title"], "url": a["url"], "points": a.get("points", 0)}
                for a in cached
            ]
            return [status] + articles
        return [status]


@mcp.tool()
def manage_local_library(action: str, articles: list[dict] | None = None) -> dict:
    """Read/write the local saved_articles.json library.

    action='check_duplicates': returns {status, articles} with novel articles not yet in library.
    action='save_new': appends articles (deduped by URL), returns {status} string.
    """
    if action == "check_duplicates":
        if not articles:
            return {"status": "No articles provided.", "articles": []}
        library = _load_library()
        saved_urls = {a["url"] for a in library}
        novel = [a for a in articles if a.get("url") not in saved_urls]
        return {"status": f"{len(novel)} novel articles found.", "articles": novel}

    if action == "save_new":
        if not articles:
            return {"status": "0 articles provided. Nothing saved."}
        library = _load_library()
        saved_urls = {a["url"] for a in library}
        new_articles = []
        for a in articles:
            if a.get("url") and a["url"] not in saved_urls:
                new_articles.append({
                    "id": str(uuid.uuid4()),
                    "title": a.get("title", ""),
                    "url": a["url"],
                    "points": a.get("points", 0),
                    "ai_summary": a.get("ai_summary", ""),
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                })
                saved_urls.add(a["url"])
        skipped = len(articles) - len(new_articles)
        _save_library(library + new_articles)
        return {"status": f"{skipped} duplicates skipped. {len(new_articles)} new articles saved."}

    return {"status": f"Unknown action '{action}'. Use 'check_duplicates' or 'save_new'."}


_TOPIC_PALETTES: dict[str, dict] = {
    "medical":  {"emoji": "🏥", "hue": 175, "bg": "#071a18", "card": "#0d2820", "fg": "#c8f0eb", "muted": "#6bbfb5", "border": "#1a4040"},
    "security": {"emoji": "🔐", "hue": 5,   "bg": "#1a0707", "card": "#280d0d", "fg": "#f0cdc8", "muted": "#bf6b6b", "border": "#401a1a"},
    "rust":     {"emoji": "🦀", "hue": 22,  "bg": "#1a0e07", "card": "#28180d", "fg": "#f0d9c8", "muted": "#bf956b", "border": "#40280d"},
    "python":   {"emoji": "🐍", "hue": 210, "bg": "#07101a", "card": "#0d1a28", "fg": "#c8daf0", "muted": "#6b9abf", "border": "#1a2e40"},
    "ai":       {"emoji": "🤖", "hue": 270, "bg": "#10071a", "card": "#180d28", "fg": "#dcc8f0", "muted": "#9b6bbf", "border": "#2e1a40"},
    "web":      {"emoji": "🌐", "hue": 195, "bg": "#07141a", "card": "#0d2028", "fg": "#c8e8f0", "muted": "#6baebf", "border": "#1a3040"},
    "cloud":    {"emoji": "☁️", "hue": 230, "bg": "#07101a", "card": "#0d1828", "fg": "#c8d4f0", "muted": "#6b80bf", "border": "#1a2440"},
    "data":     {"emoji": "🗄️", "hue": 150, "bg": "#071a0e", "card": "#0d2816", "fg": "#c8f0d4", "muted": "#6bbf80", "border": "#1a402a"},
    "game":     {"emoji": "🎮", "hue": 45,  "bg": "#1a1007", "card": "#28180d", "fg": "#f0e0c8", "muted": "#bfa06b", "border": "#40300d"},
    "crypto":   {"emoji": "⛓️", "hue": 55,  "bg": "#1a1407", "card": "#28200d", "fg": "#f0eac8", "muted": "#bfae6b", "border": "#403810"},
    "hardware": {"emoji": "🔧", "hue": 30,  "bg": "#1a0f07", "card": "#281808", "fg": "#f0dcc8", "muted": "#bf8c6b", "border": "#40250d"},
    "linux":    {"emoji": "🐧", "hue": 240, "bg": "#07081a", "card": "#0d1028", "fg": "#c8caf0", "muted": "#6b6ebf", "border": "#1a1c40"},
    "science":  {"emoji": "🔬", "hue": 165, "bg": "#071a12", "card": "#0d281c", "fg": "#c8f0de", "muted": "#6bbf96", "border": "#1a4030"},
    "devtools": {"emoji": "🛠️", "hue": 185, "bg": "#07171a", "card": "#0d2428", "fg": "#c8eef0", "muted": "#6bb8bf", "border": "#1a3840"},
    "infra":    {"emoji": "🏗️", "hue": 215, "bg": "#07101a", "card": "#0d1a2a", "fg": "#c8d8f0", "muted": "#6b90bf", "border": "#1a2a40"},
}
_DEFAULT_META = {"emoji": "📰", "hue": 220, "bg": "#0f1117", "card": "#1a2033", "fg": "#e2e8f0", "muted": "#9ca3af", "border": "#1e2535"}


@mcp.tool()
def render_prefab_dashboard(cards: list[dict], topic: str = "tech", theme_key: str = "default", display_title: str = "") -> dict:
    """Compile curated articles into a dashboard spec for client rendering.

    Each card should have: title, url, points, ai_summary (optional).
    topic: the full search subject string (e.g. 'Local LLMs', 'Rust async').
    theme_key: pick the single best match for the topic from this exact list:
        medical, security, rust, python, ai, web, cloud, data, game, crypto,
        hardware, linux, science, devtools, infra, default
    Examples: pytorch→ai, kubernetes→infra, solidity→crypto, medgemma→medical, nextjs→web,
        risc-v→hardware, kernel→linux, crispr→science, neovim→devtools, postgres→infra, golang→devtools.
    display_title: a short, well-capitalised heading for the dashboard (e.g. 'AI Investments', 'Local LLMs', 'Rust Async Runtime').
        Capitalise acronyms correctly: AI, LLM, SQL, AWS, GCP, API, ML, UI, CSS, HTML, JS, TS, DB.
    Returns {status, topic, theme, cards} for the client to render.
    """
    return {
        "status": "dashboard_ready",
        "topic": display_title or topic,
        "theme": _TOPIC_PALETTES.get(theme_key, _DEFAULT_META),
        "cards": [
            {
                "title": c.get("title", "Untitled"),
                "url": c.get("url", "#"),
                "points": c.get("points", 0) or 0,
                "ai_summary": c.get("ai_summary", ""),
            }
            for c in cards
        ],
    }


@mcp.tool()
async def search_internet(query: str, limit: int = 5) -> list[dict]:
    """Search the broader internet for tech news and blogs via the ddgs library.
    
    Use this when hacker news doesn't have enough specific info.
    Returns list of {title, url, points, snippet}.
    """
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=limit):
                results.append({
                    "title": r.get("title", "No Title"),
                    "url": r.get("href", "#"),
                    "points": 0, 
                    "snippet": r.get("body", "")
                })
        return results
    except Exception as e:
        return [{"status": f"Search failed: {str(e)}"}]


@mcp.tool()
def render_analytics_chart(title: str, labels: list[str], values: list[int], chart_type: str = "bar") -> dict:
    """Render a trend chart or graph for data visualization.
    
    chart_type: 'bar', 'line', 'pie', or 'percentage'
    labels: list of strings (e.g. ['Rust', 'Python', 'Go'])
    values: list of integers (e.g. [85, 92, 78])
    """
    return {
        "status": "chart_ready",
        "title": title,
        "type": chart_type,
        "data": {
            "labels": labels,
            "datasets": [{"name": title, "values": values}]
        }
    }


if __name__ == "__main__":
    import uvicorn
    app = mcp.http_app(transport="streamable-http", middleware=_cors_middleware)
    uvicorn.run(app, host="0.0.0.0", port=8000)
