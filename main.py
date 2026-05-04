import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastmcp import FastMCP
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

LIBRARY_FILE = Path(__file__).parent / "saved_articles.json"

mcp = FastMCP("AgentCurator")


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
    Falls back to saved_articles.json if the network request fails.
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
        if cached:
            return [
                {"title": a["title"], "url": a["url"], "points": a.get("points", 0)}
                for a in cached
            ]
        return []


@mcp.tool()
def manage_local_library(action: str, articles: list[dict] | None = None) -> str:
    """Read/write the local saved_articles.json library.

    action='check_duplicates': returns only articles whose URLs are not already saved.
    action='save_new': appends the provided articles (deduped by URL) and returns a status string.
    """
    if action == "check_duplicates":
        if not articles:
            return "[]"
        library = _load_library()
        saved_urls = {a["url"] for a in library}
        novel = [a for a in articles if a.get("url") not in saved_urls]
        return json.dumps(novel)

    if action == "save_new":
        if not articles:
            return "0 articles provided. Nothing saved."
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
        return f"{skipped} duplicates skipped. {len(new_articles)} new articles saved."

    return f"Unknown action '{action}'. Use 'check_duplicates' or 'save_new'."


@mcp.tool()
def render_prefab_dashboard(cards: list[dict]) -> str:
    """Compile curated articles into a self-contained Prefab HTML dashboard.

    Each card should have: title, url, points, ai_summary (optional).
    Returns a complete HTML page using prefab-ui components.
    """
    if not cards:
        with PrefabApp() as app:
            Heading("📰 AgentCurator Dashboard")
            Span("No articles to display.")
        return app.html()

    with PrefabApp() as app:
        Heading("📰 AgentCurator Dashboard")
        with Column(gap=3):
            for card in cards:
                with Card():
                    with CardHeader():
                        with Div(css_class="flex items-center justify-between"):
                            CardTitle(card.get("title", "Untitled"))
                            Badge(f"▲ {card.get('points', 0)}", variant="secondary")
                    with CardContent():
                        Link(
                            card.get("url", "#"),
                            href=card.get("url", "#"),
                            css_class="text-sm text-blue-600 underline break-all",
                        )
                        summary = card.get("ai_summary", "")
                        if summary:
                            Span(summary, css_class="text-sm text-muted-foreground mt-2 block")

    return app.html()


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
