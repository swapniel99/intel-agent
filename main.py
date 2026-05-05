import json
import uuid
import logging
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
    RadarChart, ScatterChart, Sparkline, RadialChart,
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
    "sparkline": Sparkline, "radial": RadialChart,
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


_TOPIC_PALETTES: dict[str, str] = {
    "medical":  "🏥", "security": "🔐", "rust": "🦀", "python": "🐍", "ai": "🤖",
    "web": "🌐", "cloud": "☁️", "data": "🗄️", "game": "🎮", "crypto": "⛓️",
    "hardware": "🔧", "linux": "🐧", "science": "🔬", "devtools": "🛠️", "infra": "🏗️",
}
_DEFAULT_EMOJI = "📰"


@mcp.tool()
def render_prefab_dashboard(
    cards: list[dict],
    topic: str = "tech",
    theme_key: str = "default",
    display_title: str = "",
    chart: dict | None = None,
) -> dict:
    """The FINAL STEP for any research or data retrieval task.
    Compile curated articles (and optional chart) into a professional Prefab dashboard.

    ONLY call this tool ONCE at the very end of your research. DO NOT call it multiple times.

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
    - chart object: {type, title, data, series, x_axis}. 
      - data: list of dicts (rows).
      - series: list of {data_key, label}.
      - x_axis: key for labels (default "label").
      - legacy format {labels, values} also supported.

    Returns {status} — the Chrome Extension will automatically render the dashboard in the side panel.
    """
    global _LAST_DASHBOARD_HTML
    logger.info(f"Tool Call: render_prefab_dashboard(topic='{topic}', theme='{theme_key}', cards={len(cards)}, chart={chart and chart.get('type')})")

    emoji = _TOPIC_PALETTES.get(theme_key, _DEFAULT_EMOJI)
    heading = f"{emoji} {display_title or topic}"

    app = PrefabApp()
    with app:
        with Column():
            H2(heading)

            if chart and chart.get("type") in _CHART_REGISTRY:
                ctype = chart["type"]
                ChartCls = _CHART_REGISTRY[ctype]
                data = chart.get("data", [])
                series_input = chart.get("series", [])
                chart_title = chart.get("title", "")
                
                # Simple/Backward compatibility format
                if not data and chart.get("labels") and chart.get("values"):
                    labels = chart["labels"]
                    values = chart["values"]
                    data = [{"label": l, "value": v} for l, v in zip(labels, values)]
                    series_input = [{"data_key": "value", "label": chart_title or "Value"}]

                if chart_title:
                    H3(chart_title)

                if ctype == "sparkline":
                    ChartCls(data=chart.get("values", []))
                elif ctype in ("pie", "radial"):
                    # Circular charts use a single data_key
                    dk = series_input[0]["data_key"] if series_input else "value"
                    nk = chart.get("x_axis") or "label"
                    ChartCls(
                        data=data,
                        data_key=dk,
                        name_key=nk,
                        show_legend=True,
                    )
                elif ctype in ("bar", "line", "area", "scatter", "radar"):
                    series = [ChartSeries(**s) for s in series_input]
                    kwargs = {"data": data, "series": series}
                    
                    if ctype == "radar":
                        kwargs["axis_key"] = chart.get("x_axis") or "label"
                    else:
                        kwargs["x_axis"] = chart.get("x_axis") or "label"
                        if ctype == "scatter":
                            kwargs["y_axis"] = series[0].data_key if series else "value"
                    ChartCls(**kwargs)
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
