import json
import uuid
import logging
# from ddgs import DDGS
import urllib.parse
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse

from prefab_ui import PrefabApp
from prefab_ui.components.charts import (
    AreaChart, BarChart, ChartSeries, LineChart, PieChart,
    RadarChart, ScatterChart, Sparkline,
)
from prefab_ui.components.card import Card
from prefab_ui.components.column import Column
from prefab_ui.components.row import Row
from prefab_ui.components.badge import Badge
from prefab_ui.components.markdown import Markdown
from prefab_ui.components.typography import H2, H3, Muted

_CHART_REGISTRY = {
    "bar": BarChart, "line": LineChart, "pie": PieChart,
    "area": AreaChart, "scatter": ScatterChart, "radar": RadarChart,
    "sparkline": Sparkline,
}

_LAST_DASHBOARD_HTML: str = ""

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentCurator")

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
    """Primary tool for DEVELOPER TRENDS and COMMUNITY DISCUSSION.
    Use this for: "What's trending in tech?", "What do developers think about X?",
    "Latest startup news", or "niche engineering topics".
    Source: Hacker News (Algolia).
    """
    logger.info(f"Tool Call: fetch_tech_news(query='{query}', limit={limit})")
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
    logger.info(f"Tool Call: manage_local_library(action='{action}', article_count={len(articles) if articles else 0})")
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
def render_prefab_dashboard(
    cards: list[dict],
    topic: str = "tech",
    theme_key: str = "default",
    display_title: str = "",
    chart: dict | None = None,
) -> dict:
    """The MANDATORY FINAL STEP for any research or data retrieval task.
    Compile curated articles (and optional chart) into a professional Prefab dashboard.

    ALWAYS call this tool once you have your final list of articles/data. DO NOT
    just return the raw text list from fetch_tech_news.

    Each card: {title, url, points, ai_summary: "mandatory 1-sentence summary"}.
    topic: full search subject (e.g. 'Local LLMs').
    theme_key: pick best match from: medical, security, rust, python, ai, web,
        cloud, data, game, crypto, hardware, linux, science, devtools, infra, default.
    display_title: short heading (capitalise AI, LLM, SQL, AWS, GCP, API, ML, UI, CSS, HTML, JS, TS, DB).

    CHART GUIDELINES:
    - ONLY include a chart if the data is quantitative (numbers, percentages, shares).
    - If data is purely qualitative (news titles, opinions), set chart=None.
    - pie: Use for Market Share, Proportions, or Percentage distributions.
    - line/area: Use for Trends over time or sequential data.
    - bar: Use for Comparisons between discrete categories (e.g., points, counts).
    - radar: Use for Multi-variable comparisons (e.g., feature sets).
    - chart object: {type, title, labels, values}. type ∈ bar/line/pie/area/scatter/radar/sparkline.

    Returns {status} — the Chrome Extension will automatically render the dashboard in the side panel.
    """
    global _LAST_DASHBOARD_HTML
    logger.info(f"Tool Call: render_prefab_dashboard(topic='{topic}', theme='{theme_key}', cards={len(cards)}, chart={chart and chart.get('type')})")

    meta = _TOPIC_PALETTES.get(theme_key, _DEFAULT_META)
    heading = f"{meta['emoji']} {display_title or topic}"

    app = PrefabApp()
    with app:
        with Column():
            H2(heading)

            if chart and chart.get("type") in _CHART_REGISTRY:
                ChartCls = _CHART_REGISTRY[chart["type"]]
                ctype = chart["type"]
                labels = chart.get("labels", [])
                values = chart.get("values", [])
                chart_title = chart.get("title", "")
                data = [{"label": l, "value": v} for l, v in zip(labels, values)]

                if chart_title:
                    H3(chart_title)

                if ctype == "sparkline":
                    ChartCls(data=values)
                elif ctype == "pie":
                    ChartCls(
                        data=data,
                        data_key="value",
                        name_key="label",
                        show_legend=True,
                    )
                elif ctype == "radar":
                    ChartCls(
                        data=data,
                        series=[ChartSeries(data_key="value", label=chart_title or "Value")],
                        axis_key="label",
                    )
                elif ctype == "scatter":
                    ChartCls(
                        data=data,
                        series=[ChartSeries(data_key="value", label=chart_title or "Value")],
                        x_axis="label",
                        y_axis="value",
                    )
                else:
                    ChartCls(
                        data=data,
                        series=[ChartSeries(data_key="value", label=chart_title or "Value")],
                    )

            for c in cards:
                with Card():
                    with Column():
                        with Row():
                            H3(c.get("title", "Untitled"))
                            Badge(label=f"▲ {c.get('points', 0) or 0}", variant="info")
                        Markdown(f"[Click Here]({c.get('url', '#')})")
                        if c.get("ai_summary"):
                            Muted(c["ai_summary"])

    _LAST_DASHBOARD_HTML = app.html()
    return {"status": "dashboard_ready", "topic": display_title or topic}


# @mcp.tool()
# async def search_internet(query: str, limit: int = 5) -> list[dict]:
#     """Primary tool for GENERAL NEWS, FACTUAL INFO, and PRODUCT UPDATES.
#     Use this for: "Is X released yet?", "Latest news about company Y",
#     "Product features/specs", or broad tech news not specific to developers.
#     Source: DuckDuckGo.
#     """
#     logger.info(f"Tool Call: search_internet(query='{query}', limit={limit})")
#     try:
#         results = []
#         with DDGS() as ddgs:
#             for r in ddgs.text(query, max_results=limit):
#                 results.append({
#                     "title": r.get("title", "No Title"),
#                     "url": r.get("href", "#"),
#                     "points": 0,
#                     "snippet": r.get("body", "")
#                 })
#         return results
#     except Exception as e:
#         return [{"status": f"Search failed: {str(e)}"}]


@mcp.custom_route("/dashboard", methods=["GET"])
async def dashboard(request: Request) -> HTMLResponse:
    """Serve last rendered Prefab dashboard HTML for iframe loading."""
    if not _LAST_DASHBOARD_HTML:
        app = PrefabApp()
        with app:
            with Column():
                Muted("No dashboard rendered yet. Run a prompt.")
        return HTMLResponse(app.html())
    return HTMLResponse(_LAST_DASHBOARD_HTML)


if __name__ == "__main__":
    import uvicorn
    app = mcp.http_app(transport="streamable-http", middleware=_cors_middleware)
    uvicorn.run(app, host="0.0.0.0", port=8000)
