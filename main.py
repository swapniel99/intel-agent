import json
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path

import urllib3

# pytrends uses urllib3 Retry with 'method_whitelist' (removed in urllib3>=2.0, replaced by 'allowed_methods')
_orig_retry = urllib3.Retry.__init__
def _patched_retry(self, *args, **kwargs):
    kwargs.pop("method_whitelist", None)
    _orig_retry(self, *args, **kwargs)
urllib3.Retry.__init__ = _patched_retry

import httpx
from ddgs import DDGS
from pytrends.request import TrendReq
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse

from prefab_ui import PrefabApp
from prefab_ui.components import Column, Muted

_CHART_TYPES = {"bar", "line", "area", "pie", "radar", "radial"}

_POSITIVE_WORDS = {
    "great", "love", "best", "fast", "easy", "excellent", "happy", "discount",
    "amazing", "reliable", "good", "quick", "convenient", "affordable", "genuine",
    "trusted", "recommend", "perfect", "smooth", "helpful", "awesome", "fantastic",
    "efficient", "safe", "legit", "original", "cheap", "savings", "prompt", "accurate",
}

_NEGATIVE_WORDS = {
    "bad", "worst", "terrible", "delay", "refund", "problem", "issue", "scam",
    "fake", "awful", "slow", "fraud", "pathetic", "horrible", "useless", "broken",
    "wrong", "missing", "expired", "damaged", "lost", "late", "cancelled", "blocked",
    "failed", "error", "poor", "disgrace", "cheat", "ripped", "overpriced", "disappointing",
    "complaint", "defective", "unreliable", "dangerous",
}

_TIER1_CITIES = {
    "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad",
    "pune", "kolkata", "ahmedabad",
}

_TIER2_CITIES = {
    "jaipur", "lucknow", "surat", "kanpur", "nagpur", "patna", "indore",
    "bhopal", "visakhapatnam", "vadodara", "coimbatore", "agra", "madurai",
    "nashik", "faridabad", "meerut", "rajkot", "kochi", "ludhiana",
    "aurangabad", "amritsar", "chandigarh", "noida", "gurgaon", "gurugram",
}

_BRAND_DOMAINS: dict[str, str] = {
    "pharmeasy": "pharmeasy.in",
    "1mg": "1mg.com",
    "apollo": "apollopharmacy.in",
    "hms": "hms.co.in",
}

_REDDIT_TIMEFRAME: dict[str, str] = {"d": "day", "w": "week", "m": "month"}

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


async def _fetch_reddit_sentiment(brand: str, timeframe: str, limit: int = 25) -> list[dict]:
    t = _REDDIT_TIMEFRAME.get(timeframe, "week")
    url = f"https://www.reddit.com/search.json?q={brand}&sort=new&t={t}&limit={limit}"
    headers = {"User-Agent": "IntelAgent/1.0"}
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    posts = resp.json().get("data", {}).get("children", [])
    return [
        {
            "title": p["data"].get("title", ""),
            "body": (p["data"].get("selftext", "") or "")[:400],
            "url": f"https://reddit.com{p['data'].get('permalink', '')}",
            "score": p["data"].get("score", 0),
            "num_comments": p["data"].get("num_comments", 0),
            "subreddit": p["data"].get("subreddit", ""),
        }
        for p in posts
    ]


def _score_sentiment(texts: list[str]) -> dict:
    pos_posts = neg_posts = neutral_posts = 0
    for text in texts:
        words = set(text.lower().split())
        p = len(words & _POSITIVE_WORDS)
        n = len(words & _NEGATIVE_WORDS)
        if p > n:
            pos_posts += 1
        elif n > p:
            neg_posts += 1
        else:
            neutral_posts += 1
    total = max(len(texts), 1)
    pos_pct = round(pos_posts / total * 100)
    neg_pct = round(neg_posts / total * 100)
    neutral_pct = max(100 - pos_pct - neg_pct, 0)
    score = round((pos_posts - neg_posts) / total, 3)
    return {
        "positive_pct": pos_pct,
        "negative_pct": neg_pct,
        "neutral_pct": neutral_pct,
        "sentiment_score": score,
    }


def _city_tier(city: str) -> str:
    c = city.lower().strip()
    if c in _TIER1_CITIES:
        return "tier1"
    if c in _TIER2_CITIES:
        return "tier2"
    return "tier3"


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


@mcp.tool()
async def fetch_brand_sentiment(
    brands: list[str],
    platforms: str = "all",
    timeframe: str = "w",
) -> list[dict]:
    """Fetch social media sentiment for pharma brands from Reddit, Twitter/X, and LinkedIn.

    brands: list of brand names e.g. ["PharmEasy", "1mg", "Apollo", "HMS"]
    platforms: "reddit" | "twitter" | "linkedin" | "all"
    timeframe: "d" (day) | "w" (week, default) | "m" (month)

    Returns: [{brand, platform, total_posts, positive_pct, negative_pct, neutral_pct, sentiment_score, top_posts}]
    Sentiment score in [-1.0, 1.0]: positive=closer to 1, negative=closer to -1.
    """
    logger.info(f"Tool Call: fetch_brand_sentiment(brands={brands}, platforms='{platforms}', timeframe='{timeframe}')")

    results = []
    for brand in brands:
        do_reddit = platforms in ("reddit", "all")
        do_twitter = platforms in ("twitter", "all")
        do_linkedin = platforms in ("linkedin", "all")

        if do_reddit:
            try:
                posts = await _fetch_reddit_sentiment(brand, timeframe, limit=25)
                texts = [p["title"] + " " + p["body"] for p in posts]
                sentiment = _score_sentiment(texts)
                top = [{"title": p["title"], "url": p["url"], "score": p["score"]} for p in posts[:5]]
                results.append({"brand": brand, "platform": "reddit", "total_posts": len(posts), **sentiment, "top_posts": top})
            except Exception as e:
                results.append({"brand": brand, "platform": "reddit", "status": f"unavailable: {e}"})

        if do_twitter:
            try:
                raw = list(DDGS().text(f'site:x.com "{brand}"', timelimit=timeframe, max_results=20))
                texts = [r.get("title", "") + " " + r.get("body", "") for r in raw]
                sentiment = _score_sentiment(texts)
                top = [{"title": r.get("title", ""), "url": r.get("href", ""), "score": 0} for r in raw[:5]]
                results.append({"brand": brand, "platform": "twitter", "total_posts": len(raw), **sentiment, "top_posts": top})
            except Exception as e:
                results.append({"brand": brand, "platform": "twitter", "status": f"unavailable: {e}"})

        if do_linkedin:
            try:
                raw = list(DDGS().text(f'site:linkedin.com "{brand}"', timelimit=timeframe, max_results=20))
                texts = [r.get("title", "") + " " + r.get("body", "") for r in raw]
                sentiment = _score_sentiment(texts)
                top = [{"title": r.get("title", ""), "url": r.get("href", ""), "score": 0} for r in raw[:5]]
                results.append({"brand": brand, "platform": "linkedin", "total_posts": len(raw), **sentiment, "top_posts": top})
            except Exception as e:
                results.append({"brand": brand, "platform": "linkedin", "status": f"unavailable: {e}"})

    return results if results else [{"status": "No results found for the given brands and platforms."}]


@mcp.tool()
def fetch_content_trends(
    topic: str,
    region_tier: str = "all",
    timeframe: str = "today 1-m",
) -> list[dict]:
    """Fetch Google Trends interest for health topics by Indian city tier.

    topic: search topic e.g. "online pharmacy", "medicine delivery", "health insurance"
    region_tier: "tier1" | "tier2" | "tier3" | "all"
    timeframe: pytrends format — "today 1-m", "today 3-m", or "YYYY-MM-DD YYYY-MM-DD"

    Returns: [{city, tier, interest_score, related_queries, related_topics}]
    interest_score is 0–100 (relative to peak in the period).
    """
    logger.info(f"Tool Call: fetch_content_trends(topic='{topic}', region_tier='{region_tier}', timeframe='{timeframe}')")

    try:
        pt = TrendReq(hl="en-IN", tz=330, retries=2, backoff_factor=0.5, timeout=(10, 25))
        pt.build_payload([topic], geo="IN", timeframe=timeframe)

        df = pt.interest_by_region(resolution="CITY", inc_low_vol=True)
        if df is None or df.empty:
            return [{"status": f"No Google Trends data for '{topic}' in India."}]

        related_q = pt.related_queries().get(topic, {})
        related_t = pt.related_topics().get(topic, {})

        top_q_df = related_q.get("top")
        top_queries = top_q_df.head(5)["query"].tolist() if top_q_df is not None and not top_q_df.empty else []

        top_t_df = related_t.get("top")
        top_topics = top_t_df.head(5)["topic_title"].tolist() if top_t_df is not None and not top_t_df.empty else []

        results = []
        for city, row in df.iterrows():
            score = int(row.iloc[0])
            if score == 0:
                continue
            tier = _city_tier(str(city))
            if region_tier != "all" and tier != region_tier:
                continue
            results.append({
                "city": str(city),
                "tier": tier,
                "interest_score": score,
                "related_queries": top_queries,
                "related_topics": top_topics,
            })

        results.sort(key=lambda x: x["interest_score"], reverse=True)
        return results if results else [{"status": f"No cities matched tier '{region_tier}'."}]

    except Exception as e:
        err = str(e)
        if "429" in err or "Too Many Requests" in err:
            return [{"status": "Google Trends rate-limited. Wait 60s and retry."}]
        return [{"status": f"fetch_content_trends error: {err}"}]


@mcp.tool()
def fetch_search_presence(
    brands: list[str],
    keywords: list[str],
) -> list[dict]:
    """Check where pharma brands appear in search results for given keywords.

    brands: e.g. ["PharmEasy", "1mg", "Apollo", "HMS"]
    keywords: e.g. ["buy medicine online", "online pharmacy india", "order medicines"]

    Returns: [{keyword, brand, rank, present, url}]
    rank is 1-indexed position in top 10 results; null if not found.
    """
    logger.info(f"Tool Call: fetch_search_presence(brands={brands}, keywords={keywords})")

    domain_map = {b.lower(): _BRAND_DOMAINS.get(b.lower(), b.lower().replace(" ", "") + ".in") for b in brands}
    results = []

    for keyword in keywords:
        try:
            hits = list(DDGS().text(keyword, max_results=10))
            for brand in brands:
                domain = domain_map.get(brand.lower(), "")
                rank = None
                url = None
                for i, h in enumerate(hits, start=1):
                    if domain in h.get("href", ""):
                        rank = i
                        url = h["href"]
                        break
                results.append({"keyword": keyword, "brand": brand, "rank": rank, "present": rank is not None, "url": url})
        except Exception as e:
            for brand in brands:
                results.append({"keyword": keyword, "brand": brand, "rank": None, "present": False, "url": None, "status": f"error: {e}"})

    return results if results else [{"status": "No results found."}]


_DEFAULT_EMOJI = "🔎"


def _normalize_chart(chart: dict) -> dict:
    """Lowercase type, convert labels/values simple format, normalize keys, enable legends/tooltips by default."""
    c = dict(chart)
    if "type" in c:
        c["type"] = c["type"].lower()

    # Handle common aliases
    for old, new in [
        ("show_legend", "showLegend"), ("show_tooltip", "showTooltip"),
        ("show_grid", "showGrid"), ("show_dots", "showDots"),
        ("animate", "animate")
    ]:
        if old in c and new not in c:
            c[new] = c.pop(old)

    # Enable legend/tooltip by default if not specified
    if "showLegend" not in c:
        c["showLegend"] = True
    if "showTooltip" not in c:
        c["showTooltip"] = True
    if "showGrid" not in c:
        c["showGrid"] = True

    if not c.get("data") and c.get("labels") and c.get("values"):
        labels = c.pop("labels")
        values = c.pop("values")
        c["data"] = [{"label": lbl, "value": val} for lbl, val in zip(labels, values)]
        if not c.get("series"):
            c["series"] = [{"dataKey": "value", "label": c.get("title") or "Value"}]

    if c.get("series"):
        c["series"] = [
            {("dataKey" if k == "data_key" else k): v for k, v in s.items()}
            for s in c["series"]
        ]

    # Chart-specific aliases
    if c.get("type") == "radar":
        for k in ["axis_key", "axis"]:
            if k in c and "axisKey" not in c:
                c["axisKey"] = c.pop(k)

    return c


def _build_chart_node(chart: dict) -> dict | None:
    """Convert normalized chart dict to Prefab JSON chart node."""
    ctype = chart.get("type", "")
    if ctype not in _CHART_TYPES:
        return None
    type_map = {
        "bar": "BarChart", "line": "LineChart", "area": "AreaChart",
        "pie": "PieChart", "radar": "RadarChart", "radial": "RadialChart",
    }
    data = chart.get("data", [])
    series = chart.get("series", [])

    # Smart axis key detection
    x_axis = chart.get("xAxis") or chart.get("axisKey") or chart.get("x_axis") or chart.get("axis_key")
    if not x_axis and data and isinstance(data[0], dict):
        # Find first key that isn't in series dataKeys
        series_keys = {s.get("dataKey") for s in series if s.get("dataKey")}
        for k in data[0].keys():
            if k not in series_keys:
                x_axis = k
                break
    if not x_axis:
        x_axis = "label"

    if data and not series and ctype not in ("pie", "radial"):
        series = [{"dataKey": k, "label": k.capitalize()} for k in data[0] if k != x_axis]

    node: dict = {"type": type_map[ctype], "data": data, "height": chart.get("height", 300)}

    # Apply common visual properties
    for prop in ("showLegend", "showTooltip", "showGrid", "animate", "title"):
        if prop in chart:
            node[prop] = chart[prop]

    if ctype in ("pie", "radial"):
        node["dataKey"] = chart.get("dataKey") or (series[0]["dataKey"] if series else "value")
        node["nameKey"] = chart.get("nameKey") or x_axis
    elif ctype == "radar":
        node["series"] = series
        node["axisKey"] = x_axis
    else:  # bar, line, area
        node["series"] = series
        node["xAxis"] = x_axis
        if chart.get("stacked"):
            node["stacked"] = True
    return node


@mcp.tool()
def render_dashboard(
    title: str,
    summary: str = "",
    cards: list[dict] | None = None,
    metrics: list[dict] | None = None,
    chart: dict | None = None,
    table: dict | None = None,
    badges: list[dict] | None = None,
    layout: str = "auto",
) -> dict:
    """
    Render a dashboard. Always call this when finished — it is the only output surface.
    PRO-ACTIVE VISUALIZATION: If you have numerical data, metrics, or comparisons, ALWAYS include a 'chart'.

    title: dashboard heading (required).
    summary: your full prose response to the user (2-3 sentences). ALWAYS populate this.

    cards: article/news cards. Use for feeds, search results, library views.
        Each: {title, url, points, source, ai_summary: "1-sentence executive summary"}

    metrics: KPI cards. Use for numbers, comparisons, benchmarks.
        Each: {label, value, delta?, trend?: "up|down|neutral", trendSentiment?: "positive|negative|neutral"}
        Example: {"label": "Stars", "value": "92K", "delta": "+12%", "trend": "up", "trendSentiment": "positive"}

    chart: one chart.
        SIMPLE (pie/bar/line/area):   {type, title?, labels: ["A","B"], values: [10,20]}
        MULTIVARIATE (bar/line/area): {type, title?, data: [{"x":"A","val":10}], series: [{dataKey:"val", label:"Metric"}], xAxis:"x"}
        PIE/RADIAL:                   {type, data: [{"cat":"X","pct":40}], dataKey:"pct", nameKey:"cat"}
        RADAR:                        {type, data: [{"axis":"Speed","a":80,"b":70}], series:[{dataKey:"a"},{dataKey:"b"}], axisKey:"axis"}

    table: data table.
        {columns: [{key, header, sortable?}], rows: [{...}], search?, paginated?, pageSize?}

    badges: header status badges.
        [{label, variant?: "default|outline|info|success|destructive|warning|secondary"}]

    layout: "auto" (default) | "kpi_grid" | "chart_focus" | "table_report" | "split"
        auto: cards→article feed, chart-only→chart_focus, table-only→table_report, else→kpi_grid
        split: chart left + metrics column right, side by side.

    Returns {status: "dashboard_ready"}.
    """
    global _LAST_DASHBOARD_HTML
    logger.info(
        f"Tool Call: render_dashboard(layout='{layout}', title='{title}', "
        f"cards={len(cards or [])}, metrics={len(metrics or [])}, "
        f"chart={bool(chart)}, table={bool(table)})"
    )

    def _article_card(c: dict) -> dict:
        p = c.get("points", 0) or 0
        if isinstance(p, (int, float)):
            if p >= 1_000_000_000:
                p_str = f"{p/1_000_000_000:.1f}B"
            elif p >= 1_000_000:
                p_str = f"{p/1_000_000:.1f}M"
            elif p >= 1_000:
                p_str = f"{p/1_000:.1f}K"
            else:
                p_str = str(int(p))
        else:
            p_str = str(p)
        src = c.get("source")
        badge_nodes: list[dict] = []
        if src:
            badge_nodes.append({"type": "Badge", "label": str(src).upper(), "variant": "outline"})
        badge_nodes.append({"type": "Badge", "label": f"▲ {p_str}", "variant": "info"})
        card_children: list[dict] = [
            {"type": "CardHeader", "children": [
                {"type": "Row", "align": "start", "justify": "between", "gap": 4, "children": [
                    {"type": "CardTitle", "children": [
                        {"type": "Markdown", "content": f"[{c.get('title', 'Untitled')}]({c.get('url', '#')})"}
                    ]},
                    {"type": "Row", "gap": 2, "children": badge_nodes},
                ]},
            ]},
        ]
        if c.get("ai_summary"):
            card_children.append({"type": "CardContent", "children": [
                {"type": "Muted", "content": c["ai_summary"]}
            ]})
        return {"type": "Card", "children": card_children}

    def _metric_card(m: dict) -> dict:
        mn: dict = {"type": "Metric", "label": m.get("label", ""), "value": str(m.get("value", ""))}
        for k in ("delta", "trend", "trendSentiment"):
            if m.get(k):
                mn[k] = m[k]
        return {"type": "Card", "children": [{"type": "CardContent", "children": [mn]}]}

    def _table_node() -> dict | None:
        if not table:
            return None
        n: dict = {"type": "DataTable", "columns": table.get("columns", []), "rows": table.get("rows", [])}
        if table.get("search"):
            n["search"] = True
        if table.get("paginated"):
            n["paginated"] = True
            n["pageSize"] = table.get("pageSize", 10)
        return n

    cn: dict | None = _build_chart_node(_normalize_chart(chart)) if chart else None

    eff = layout
    if layout == "auto":
        if cards:
            eff = "article_feed"
        elif cn and not metrics and not table:
            eff = "chart_focus"
        elif table and not cn and not metrics:
            eff = "table_report"
        else:
            eff = "kpi_grid"

    header: list[dict] = [{"type": "H2", "content": f"{_DEFAULT_EMOJI} {title}"}]
    if badges:
        header.append({"type": "Row", "gap": 2, "children": [
            {"type": "Badge", "label": b["label"],
             **({"variant": b["variant"]} if b.get("variant") else {})}
            for b in badges
        ]})
    if summary:
        header.append({"type": "Card", "children": [
            {"type": "CardContent", "children": [{"type": "Markdown", "content": summary}]}
        ]})

    body: list[dict] = []
    mg = {"type": "Grid", "columns": 3, "gap": 4, "children": [_metric_card(m) for m in metrics]} if metrics else None
    mr = {"type": "Row", "gap": 4, "children": [_metric_card(m) for m in metrics]} if metrics else None
    tn = _table_node()

    if eff == "article_feed":
        if cn:
            body.append(cn)
        for c in (cards or []):
            body.append(_article_card(c))
        if mg:
            body.append(mg)
        if tn:
            body.append(tn)
    elif eff == "kpi_grid":
        if mg:
            body.append(mg)
        if cn:
            body.append(cn)
        if tn:
            body.append(tn)
    elif eff == "chart_focus":
        if cn:
            body.append(cn)
        if mr:
            body.append(mr)
        if tn:
            body.append(tn)
    elif eff == "table_report":
        if tn:
            body.append(tn)
        if cn:
            body.append(cn)
        if mr:
            body.append(mr)
    elif eff == "split":
        left = cn or tn
        right_items = ([mg] if mg else []) + ([tn] if tn and left != tn else [])
        right = {"type": "Column", "gap": 4, "children": right_items} if right_items else None
        if left and right:
            body.append({"type": "Row", "gap": 4, "align": "start", "children": [left, right]})
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

    spec = {"type": "Column", "gap": 4, "children": header + body}
    try:
        app = PrefabApp.from_json({"view": spec})
        _LAST_DASHBOARD_HTML = app.html()
        return {"status": "dashboard_ready"}
    except Exception as e:
        logger.error(f"render_dashboard render error: {e}")
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
    import sys
    # Default to stdio for MCP, but allow 'http' for the dashboard server
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        mcp.run()
    else:
        import uvicorn
        app = mcp.http_app(transport="streamable-http", middleware=_cors_middleware)
        uvicorn.run(app, host="0.0.0.0", port=8000)
