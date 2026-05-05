import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from prefab_ui import PrefabApp
from prefab_ui.components import (
    Badge,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Column,
    Div,
    Heading,
    Link,
    Span,
)
from prefab_ui.themes import Theme

LIBRARY_FILE = Path(__file__).parent / "saved_articles.json"
_last_dashboard_html: str = ""

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


async def dashboard_handler(request: Request) -> HTMLResponse:
    return HTMLResponse(_last_dashboard_html or "<h1>No dashboard yet</h1>")


class _TopicPalette:
    def __init__(self, keywords, hue, emoji, bg, card, fg, muted_fg, border):
        self.keywords = keywords
        self.hue = hue
        self.emoji = emoji
        self.bg = bg
        self.card = card
        self.fg = fg
        self.muted_fg = muted_fg
        self.border = border

_TOPIC_THEMES: list[_TopicPalette] = [
    _TopicPalette(["medical","health","bio","medgemma","pharma","clinical"],
                  175.0,"🏥", bg="#071a18",card="#0d2820",fg="#c8f0eb",muted_fg="#6bbfb5",border="#1a4040"),
    _TopicPalette(["security","hack","exploit","vuln","cyber","malware","cve"],
                  5.0,  "🔐", bg="#1a0707",card="#280d0d",fg="#f0cdc8",muted_fg="#bf6b6b",border="#401a1a"),
    _TopicPalette(["rust","cargo","crate"],
                  22.0, "🦀", bg="#1a0e07",card="#28180d",fg="#f0d9c8",muted_fg="#bf956b",border="#40280d"),
    _TopicPalette(["python","django","flask","fastapi"],
                  210.0,"🐍", bg="#07101a",card="#0d1a28",fg="#c8daf0",muted_fg="#6b9abf",border="#1a2e40"),
    _TopicPalette(["ai","llm","ml","machine learning","gpt","gemini","claude","neural","model"],
                  270.0,"🤖", bg="#10071a",card="#180d28",fg="#dcc8f0",muted_fg="#9b6bbf",border="#2e1a40"),
    _TopicPalette(["web","react","vue","angular","frontend","css","html","javascript","typescript"],
                  195.0,"🌐", bg="#07141a",card="#0d2028",fg="#c8e8f0",muted_fg="#6baebf",border="#1a3040"),
    _TopicPalette(["cloud","aws","gcp","azure","kubernetes","docker","devops","infra"],
                  230.0,"☁️", bg="#07101a",card="#0d1828",fg="#c8d4f0",muted_fg="#6b80bf",border="#1a2440"),
    _TopicPalette(["data","database","sql","postgres","analytics","etl"],
                  150.0,"🗄️", bg="#071a0e",card="#0d2816",fg="#c8f0d4",muted_fg="#6bbf80",border="#1a402a"),
    _TopicPalette(["game","unity","unreal","wasm"],
                  45.0, "🎮", bg="#1a1007",card="#28180d",fg="#f0e0c8",muted_fg="#bfa06b",border="#40300d"),
    _TopicPalette(["crypto","blockchain","web3","defi"],
                  55.0, "⛓️", bg="#1a1407",card="#28200d",fg="#f0eac8",muted_fg="#bfae6b",border="#403810"),
]
_DEFAULT = _TopicPalette(
    keywords=[], hue=220.0, emoji="📰",
    bg="#0f1117", card="#1a2033", fg="#e2e8f0", muted_fg="#9ca3af", border="#1e2535"
)


def _topic_meta(topic: str) -> _TopicPalette:
    lower = topic.lower()
    for p in _TOPIC_THEMES:
        if any(kw in lower for kw in p.keywords):
            return p
    return _DEFAULT


def _badge_variant(points: int) -> str:
    if points >= 10:
        return "default"   # uses --primary → topic accent color
    if points >= 3:
        return "default"
    if points >= 1:
        return "outline"
    return "secondary"


@mcp.tool()
def render_prefab_dashboard(cards: list[dict], topic: str = "tech") -> str:
    """Compile curated articles into a self-contained Prefab HTML dashboard.

    Each card should have: title, url, points, ai_summary (optional).
    topic is the search subject (e.g. 'medgemma', 'rust', 'LLMs') — used to
    pick accent color and emoji for the dashboard heading.
    Returns a complete HTML page using prefab-ui components.
    """
    global _last_dashboard_html

    p = _topic_meta(topic)
    primary = f"oklch(0.72 0.20 {p.hue});"
    dark_vars = (
        f"--background: {p.bg};"
        f"--foreground: {p.fg};"
        f"--card: {p.card};"
        f"--card-foreground: {p.fg};"
        f"--border: {p.border};"
        f"--muted: {p.card};"
        f"--muted-foreground: {p.muted_fg};"
        f"--popover: {p.card};"
        f"--popover-foreground: {p.fg};"
        f"--primary: {primary}"
        f"--primary-foreground: {p.bg};"
        f"--ring: {primary}"
        f"--accent-hue: {p.hue};"
    )
    theme = Theme(accent=p.hue, mode="dark", light_css=dark_vars, dark_css=dark_vars)
    heading_text = f"{p.emoji} {topic.title()} Dashboard"
    dark_bootstrap = f"html,body{{background:{p.bg};color:{p.fg}}}"

    if not cards:
        with PrefabApp(title=heading_text, theme=theme, stylesheets=[dark_bootstrap]) as app:
            Heading(heading_text)
            Span("No articles to display.", css_class="text-muted-foreground")
        _last_dashboard_html = app.html()
        return _last_dashboard_html

    with PrefabApp(title=heading_text, theme=theme, stylesheets=[dark_bootstrap]) as app:
        Heading(heading_text)
        with Column(gap=3):
            for card in cards:
                points = card.get("points", 0) or 0
                with Card():
                    with CardHeader():
                        with Div(css_class="flex items-center justify-between gap-2"):
                            CardTitle(card.get("title", "Untitled"))
                            Badge(f"▲ {points}", variant=_badge_variant(points))
                    with CardContent():
                        Link(
                            card.get("url", "#"),
                            href=card.get("url", "#"),
                            css_class="text-sm underline break-all text-primary",
                        )
                        summary = card.get("ai_summary", "")
                        if summary:
                            Span(summary, css_class="text-sm text-muted-foreground mt-2 block")

    _last_dashboard_html = app.html()
    return _last_dashboard_html


if __name__ == "__main__":
    import uvicorn
    app = mcp.http_app(transport="streamable-http", middleware=_cors_middleware)
    app.add_route("/dashboard", dashboard_handler)
    uvicorn.run(app, host="0.0.0.0", port=8000)
