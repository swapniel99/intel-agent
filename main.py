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
    RadarChart, RadialChart,
)
from prefab_ui.components.card import Card, CardHeader, CardTitle, CardContent
from prefab_ui.components.column import Column
from prefab_ui.components.row import Row
from prefab_ui.components.badge import Badge
from prefab_ui.components.markdown import Markdown
from prefab_ui.components.typography import H2, H3, Muted

_CHART_REGISTRY = {
    "bar": BarChart, "line": LineChart, "pie": PieChart,
    "area": AreaChart, "radar": RadarChart,
    "radial": RadialChart,
}

_LAST_DASHBOARD_HTML: str = ""

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IntelAgent")

LIBRARY_FILE = Path(__file__).parent / "saved_articles.json"

mcp = FastMCP("IntelAgent")

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


async def _fetch_hn(query: str, limit: int) -> list[dict]:
    """Fetch from Hacker News (Algolia)."""
    url = f"https://hn.algolia.com/api/v1/search?query={query}&hitsPerPage={limit}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    hits = resp.json().get("hits", [])
    return [
        {"title": h.get("title", ""), "url": h.get("url", ""), "points": h.get("points", 0), "source": "hn"}
        for h in hits if h.get("url")
    ]


async def _fetch_dev(query: str, limit: int) -> list[dict]:
    """Fetch from Dev.to."""
    url = f"https://dev.to/api/articles?tag={query}&per_page={limit}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    articles = resp.json()
    return [
        {"title": a.get("title", ""), "url": a.get("url", ""), "points": a.get("positive_reactions_count", 0), "source": "dev"}
        for a in articles
    ]


async def _fetch_reddit(query: str, limit: int) -> list[dict]:
    """Fetch from Reddit."""
    url = f"https://www.reddit.com/r/all/search.json?q={query}&limit={limit}"
    headers = {"User-Agent": "IntelAgent/1.0"}
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    posts = resp.json().get("data", {}).get("children", [])
    return [
        {"title": p["data"].get("title", ""), "url": p["data"].get("url", ""), "points": p["data"].get("score", 0), "source": "reddit"}
        for p in posts if p["data"].get("url")
    ]


@mcp.tool()
async def fetch_tech_news(query: str, limit: int = 10, source: str = "all") -> list[dict]:
    """Fetch articles from multiple sources.

    source: 'hn' (Hacker News), 'dev' (Dev.to), 'reddit', or 'all' (combines all sources).
    Returns: [{title, url, points, source}]
    """
    logger.info(f"Tool Call: fetch_tech_news(query='{query}', limit={limit}, source='{source}')")

    try:
        if source == "hn":
            return await _fetch_hn(query, limit)
        elif source == "dev":
            return await _fetch_dev(query, limit)
        elif source == "reddit":
            return await _fetch_reddit(query, limit)
        elif source == "all":
            per_source = max(1, limit // 3)
            hn = await _fetch_hn(query, per_source)
            dev = await _fetch_dev(query, per_source)
            reddit = await _fetch_reddit(query, per_source)
            return (hn + dev + reddit)[:limit]
        else:
            return [{"status": f"Unknown source '{source}'. Use 'hn', 'dev', 'reddit', or 'all'."}]
    except Exception:
        cached = _load_library()
        status = {"status": "The internet sources are currently unavailable. Displaying previously saved articles from your local storage."}
        if cached:
            articles = [
                {"title": a["title"], "url": a["url"], "points": a.get("points", 0), "source": "cache"}
                for a in cached
            ]
            return [status] + articles
        return [status]


@mcp.tool()
def manage_local_library(
    action: str,
    articles: list[dict] | None = None,
    article_id: str | None = None,
    updates: dict | None = None,
    query: str | None = None
) -> dict:
    """Read/write the local saved_articles.json library.

    action='check_duplicates': Returns {status, articles} with novel articles not yet in library.
        RECOMMENDED: Call this before 'save_new' to filter results.
    action='save_new': Appends articles (deduped by URL) to the JSON ledger.
        REQUIREMENT: Articles must include 'ai_summary' (1-sentence max).
    action='list_all': Returns the entire archive for browsing.
    action='search': Filters the library by query (scans titles and summaries).
    action='update': Modifies a record by article_id (e.g., refreshing a summary).
    action='delete': Permanently removes a record by article_id.
    """
    logger.info(f"Tool Call: manage_local_library(action='{action}', query='{query}', id={article_id}, updates={updates}, articles_count={len(articles) if articles else 0})")

    if action == "list_all":
        library = _load_library()
        return {"status": f"Found {len(library)} articles.", "articles": library}

    if action == "search":
        if not query:
            return {"status": "query is required for 'search' action.", "articles": []}
        library = _load_library()
        q = query.lower()
        matches = [
            a for a in library
            if q in a.get("title", "").lower() or q in a.get("ai_summary", "").lower()
        ]
        return {"status": f"Found {len(matches)} matches for '{query}'.", "articles": matches}

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

    if action == "update":
        if not article_id or not updates:
            return {"status": "article_id and updates are required for 'update' action."}
        library = _load_library()
        found = False
        for a in library:
            if a["id"] == article_id:
                a.update(updates)
                found = True
                break
        if found:
            _save_library(library)
            return {"status": f"Article {article_id} updated successfully."}
        return {"status": f"Article {article_id} not found."}

    if action == "delete":
        if not article_id:
            return {"status": "article_id is required for 'delete' action."}
        library = _load_library()
        initial_len = len(library)
        library = [a for a in library if a["id"] != article_id]
        if len(library) < initial_len:
            _save_library(library)
            return {"status": f"Article {article_id} deleted successfully."}
        return {"status": f"Article {article_id} not found."}

    return {"status": f"Unknown action '{action}'. Use 'check_duplicates', 'save_new', 'list_all', 'update', or 'delete'."}


_DEFAULT_EMOJI = "🔎"


@mcp.tool()
def render_prefab_dashboard(
    cards: list[dict],
    topic: str = "tech",
    display_title: str = "",
    chart: dict | None = None,
    ai_answer: str = "",
) -> dict:
    """
    Compile curated articles and data into a professional dashboard.

    Each card: {title, url, points, source, ai_summary: "MUST be a 1-sentence executive summary"}.
    topic: pass the user's search subject verbatim (e.g. 'Local LLMs').
    ai_answer: your full text response to the user (2-3 sentences). ALWAYS populate this — it is displayed in the dashboard instead of the chat panel.

    CARDS:
    - If no chart, ALWAYS include 3-5 article cards.
    - If no data found, pass empty cards list with topic explaining why.

    CHART SELECTION LOGIC:
    - ONLY include a chart for quantitative data (numbers/percentages).
    - type: ['pie', 'bar', 'line', 'area', 'radar', 'radial'].
    - pie/bar/line/area: Use SIMPLE format (labels + values). 'area' is best for volume trends.
    - radar: Use MULTIVARIATE format (data + series).
    - radial: Use MULTIVARIATE format to show scores for a single subject.

    DATA FORMATS (CRITICAL):
    - SIMPLE: chart={type, title, labels: ["A", "B"], values: [10, 20]} (Auto-converts to 'label' and 'value' keys)
    - MULTIVARIATE: chart={type, title, data: [{label: "Speed", val: 10}, {label: "Power", val: 20}], series: [{data_key: "val", label: "Metric"}]}
    - RADAR/RADIAL: Use 'label' in the data objects for the spoke/axis names.

    Returns {status} — the UI will automatically render in the side panel.
    """
    global _LAST_DASHBOARD_HTML

    # Normalize chart type to lowercase for registry lookup
    if chart and "type" in chart:
        chart["type"] = chart["type"].lower()

    logger.info(f"Tool Call: render_prefab_dashboard(topic='{topic}', cards_count={len(cards)}, chart={chart}, ai_answer='{ai_answer[:100]}...')")

    heading = f"{_DEFAULT_EMOJI} {display_title or topic}"

    app = PrefabApp()
    with app:
        with Column():
            H2(heading)

            if ai_answer:
                with Card():
                    with CardContent():
                        Markdown(ai_answer)

            if chart and chart.get("type") in _CHART_REGISTRY:
                ctype = chart["type"]
                ChartCls = _CHART_REGISTRY[ctype]
                data = chart.get("data", [])
                series_input = chart.get("series", [])
                chart_title = chart.get("title", "")

                # Simple/Backward compatibility: labels+values arrays
                if not data and chart.get("labels") and chart.get("values"):
                    labels = chart["labels"]
                    values = chart["values"]
                    data = [{"label": l, "value": v} for l, v in zip(labels, values)]
                    series_input = [{"data_key": "value", "label": chart_title or "Value"}]

                # Auto-infer series from data keys when series omitted
                if data and not series_input and ctype not in ("pie", "radial"):
                    x_key = chart.get("x_axis") or "label"
                    inferred_keys = [k for k in data[0].keys() if k != x_key]
                    series_input = [{"data_key": k, "label": k.capitalize()} for k in inferred_keys]

                if chart_title:
                    H3(chart_title)

                if ctype in ("pie", "radial"):
                    dk = series_input[0]["data_key"] if series_input else "value"
                    nk = chart.get("x_axis") or "label"
                    ChartCls(data=data, data_key=dk, name_key=nk, show_legend=True)
                elif ctype == "radar":
                    series = [ChartSeries(**s) for s in series_input]
                    ChartCls(data=data, series=series, axis_key=chart.get("x_axis") or "label")
                elif ctype in ("bar", "line", "area"):
                    series = [ChartSeries(**s) for s in series_input]
                    ChartCls(data=data, series=series, x_axis=chart.get("x_axis") or "label")
                else:
                    series = [ChartSeries(**s) for s in series_input] if series_input else [ChartSeries(data_key="value", label="Value")]
                    ChartCls(data=data, series=series)

            for c in cards:
                with Card():
                    with CardHeader():
                        with Row(align="start", justify="between", gap=4, css_class="flex-wrap"):
                            with CardTitle(css_class="flex-1"):
                                Markdown(f"[{c.get('title', 'Untitled')}]({c.get('url', '#')})")
                            with Row(align="center", gap=2, css_class="shrink-0 pt-1"):
                                src = c.get("source")
                                if src:
                                    Badge(label=str(src).upper(), variant="outline")
                                # Format points for readability
                                p = c.get("points", 0) or 0
                                if isinstance(p, (int, float)):
                                    if p >= 1_000_000_000:
                                        p_str = f"{p/1_000_000_000:.1f}B"
                                    elif p >= 1_000_000:
                                        p_str = f"{p/1_000_000:.1f}M"
                                    elif p >= 1_000:
                                        p_str = f"{p/1_000:.1f}K"
                                    else:
                                        p_str = str(p)
                                else:
                                    p_str = str(p)
                                Badge(label=f"▲ {p_str}", variant="info")
                    with CardContent():
                        if c.get("ai_summary"):
                            Muted(c["ai_summary"])

    _LAST_DASHBOARD_HTML = app.html()
    return {"status": "dashboard_ready", "topic": display_title or topic}


def _build_chart_component(chart: dict) -> dict | None:
    """Convert a chart param dict to a Prefab JSON chart node."""
    ctype = chart.get("type", "").lower()
    if ctype not in _CHART_REGISTRY:
        return None
    type_map = {"bar": "BarChart", "line": "LineChart", "area": "AreaChart",
                "pie": "PieChart", "radar": "RadarChart", "radial": "RadialChart"}
    data = chart.get("data", [])
    series = chart.get("series", [])
    x_axis = chart.get("xAxis") or chart.get("x_axis") or "label"

    # Auto-infer series if missing
    if data and not series and ctype not in ("pie", "radial"):
        series = [{"dataKey": k, "label": k.capitalize()} for k in data[0] if k != x_axis]

    node: dict = {"type": type_map[ctype], "data": data, "height": chart.get("height", 300)}
    if ctype in ("pie", "radial"):
        node["dataKey"] = chart.get("dataKey") or (series[0]["dataKey"] if series else "value")
        node["nameKey"] = chart.get("nameKey") or x_axis
    elif ctype == "radar":
        node["series"] = series
        node["axisKey"] = x_axis
    else:
        node["series"] = series
        node["xAxis"] = x_axis
        if chart.get("stacked"):
            node["stacked"] = True
        if chart.get("showLegend"):
            node["showLegend"] = True
    return node


@mcp.tool()
def render_rich_dashboard(
    title: str,
    summary: str = "",
    layout: str = "kpi_grid",
    metrics: list[dict] | None = None,
    chart: dict | None = None,
    table: dict | None = None,
    badges: list[dict] | None = None,
) -> dict:
    """
    Render a rich dashboard from typed data slots. No JSON tree authoring required.
    Use for: KPI dashboards, metric grids, comparison charts, data tables, analysis reports.
    Prefer render_prefab_dashboard for simple article card feeds.

    layout options:
    - "kpi_grid"      — metrics grid (top) + optional chart + optional table
    - "chart_focus"   — chart (full width, top) + optional metrics row + optional table
    - "table_report"  — table (top) + optional chart + optional metrics row
    - "split"         — chart (left) + metrics column (right), side by side

    title: dashboard heading (required)
    summary: 1-3 sentence prose summary displayed below the title (optional)

    metrics: list of KPI cards, each:
        {label: str, value: str, delta?: str, trend?: "up|down|neutral", trendSentiment?: "positive|negative|neutral"}
        Example: {"label": "MRR", "value": "$42K", "delta": "+12%", "trend": "up", "trendSentiment": "positive"}

    chart: one chart, format:
        {type: "bar|line|area|pie|radar|radial", title?: str, data: [...], series?: [{dataKey, label}], xAxis?: str}
        For pie/radial: {type, data, dataKey, nameKey}
        data rows are plain dicts — no "type" key. Example: {"month": "Jan", "revenue": 4200}

    table: a data table:
        {columns: [{key: str, header: str, sortable?: bool}], rows: [{...}], search?: bool, paginated?: bool, pageSize?: int}

    badges: list of status badges shown in the header row:
        [{label: str, variant?: "default|outline|info|success|destructive|warning|secondary"}]

    Returns {status: "dashboard_ready"}.
    """
    global _LAST_DASHBOARD_HTML
    logger.info(f"Tool Call: render_rich_dashboard(layout='{layout}', title='{title}', "
                f"metrics={len(metrics or [])}, chart={bool(chart)}, table={bool(table)})")

    def metric_card(m: dict) -> dict:
        metric_node: dict = {"type": "Metric", "label": m.get("label", ""), "value": str(m.get("value", ""))}
        if m.get("delta"):
            metric_node["delta"] = m["delta"]
        if m.get("trend"):
            metric_node["trend"] = m["trend"]
        if m.get("trendSentiment"):
            metric_node["trendSentiment"] = m["trendSentiment"]
        return {"type": "Card", "children": [{"type": "CardContent", "children": [metric_node]}]}

    def metrics_grid(cols: int = 3) -> dict | None:
        if not metrics:
            return None
        return {"type": "Grid", "columns": cols, "gap": 4,
                "children": [metric_card(m) for m in metrics]}

    def metrics_row() -> dict | None:
        if not metrics:
            return None
        return {"type": "Row", "gap": 4,
                "children": [metric_card(m) for m in metrics]}

    def chart_node() -> dict | None:
        return _build_chart_component(chart) if chart else None

    def table_node() -> dict | None:
        if not table:
            return None
        node: dict = {"type": "DataTable",
                      "columns": table.get("columns", []),
                      "rows": table.get("rows", [])}
        if table.get("search"):
            node["search"] = True
        if table.get("paginated"):
            node["paginated"] = True
            node["pageSize"] = table.get("pageSize", 10)
        return node

    # ── Assemble header ───────────────────────────────────────────────────────
    header_children: list[dict] = [{"type": "H2", "content": title}]
    if badges:
        header_children.append({
            "type": "Row", "gap": 2,
            "children": [{"type": "Badge", "label": b["label"],
                           **({"variant": b["variant"]} if b.get("variant") else {})}
                         for b in badges]
        })
    if summary:
        header_children.append({"type": "Card", "children": [
            {"type": "CardContent", "children": [{"type": "Markdown", "content": summary}]}
        ]})

    # ── Assemble body by layout ───────────────────────────────────────────────
    body: list[dict] = []
    cn = chart_node()
    mg = metrics_grid()
    mr = metrics_row()
    tn = table_node()

    if layout == "kpi_grid":
        if mg:
            body.append(mg)
        if cn:
            body.append(cn)
        if tn:
            body.append(tn)

    elif layout == "chart_focus":
        if cn:
            body.append(cn)
        if mr:
            body.append(mr)
        if tn:
            body.append(tn)

    elif layout == "table_report":
        if tn:
            body.append(tn)
        if cn:
            body.append(cn)
        if mr:
            body.append(mr)

    elif layout == "split":
        left = cn or tn
        right_items = ([mg] if mg else []) + ([tn] if tn and not left == tn else [])
        right = {"type": "Column", "gap": 4, "children": right_items} if right_items else None
        if left and right:
            body.append({"type": "Row", "gap": 4, "align": "start",
                          "children": [left, right]})
        elif left:
            body.append(left)
        elif right:
            body.append(right)

    else:
        if mg:
            body.append(mg)
        if cn:
            body.append(cn)
        if tn:
            body.append(tn)

    spec = {"type": "Column", "gap": 4, "children": header_children + body}

    try:
        app = PrefabApp.from_json({"view": spec})
        _LAST_DASHBOARD_HTML = app.html()
        return {"status": "dashboard_ready"}
    except Exception as e:
        logger.error(f"render_rich_dashboard render error: {e}")
        return {"status": "error", "errors": [str(e)]}


@mcp.custom_route("/dashboard", methods=["GET"])
async def dashboard(request: Request) -> HTMLResponse:
    """Serve last rendered Prefab dashboard HTML with theme support."""
    theme = request.query_params.get("theme", "dark")

    if not _LAST_DASHBOARD_HTML:
        app = PrefabApp()
        if theme == "dark":
            app.css_class = "dark"
        with app:
            with Column():
                Muted("No dashboard rendered yet. Run a prompt.")
        html = app.html()
    else:
        html = _LAST_DASHBOARD_HTML

    # Inject dark class if requested
    if theme == "dark":
        # Prefab renderer uses .dark on <html> or <body> for dark mode
        html = html.replace('<html lang="en">', '<html lang="en" class="dark">')
        # Also ensure the body has a dark background if the renderer doesn't set it
        dark_style = '<style>html.dark, html.dark body { background: #161b26 !important; color: #c8cfdb !important; }</style>'
        html = html.replace('</head>', f'{dark_style}</head>')

    return HTMLResponse(html)


if __name__ == "__main__":
    import uvicorn
    app = mcp.http_app(transport="streamable-http", middleware=_cors_middleware)
    uvicorn.run(app, host="0.0.0.0", port=8000)
