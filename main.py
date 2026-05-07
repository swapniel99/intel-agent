import json
import os
import logging
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
load_dotenv()

import httpx
from ddgs import DDGS
from pytrends_modern import TrendReq
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse

from prefab_ui import PrefabApp
from prefab_ui.components import Column, Muted

_CHART_TYPES = {"bar", "line", "area", "pie", "radar", "radial"}

from transformers import pipeline as _hf_pipeline
_sentiment_pipeline = _hf_pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    truncation=True,
    max_length=512,
)

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
    "netmeds": "netmeds.com",
    "hms": "hms.co.in",
}

_REDDIT_TIMEFRAME: dict[str, str] = {"d": "day", "w": "week", "m": "month"}

# Brand-specific Twitter search queries — disambiguates short/ambiguous names
_TWITTER_BRAND_QUERY: dict[str, str] = {
    "pharmeasy": '"PharmEasy" OR "@pharmeasyapp"',
    "1mg": '"Tata 1mg" OR "@1mgIndia"',
    "apollo": '"Apollo Pharmacy" OR "@ApolloPharmacy"',
    "hms": '"HMS Health" OR "@hmshealth"',
}

# Twitter API v2 — set TWITTER_BEARER_TOKEN env var to enable; falls back to DDGS if absent
_TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")
# Recent search endpoint max window is 7 days regardless of tier; full archive needs Pro
_TWITTER_LOOKBACK_DAYS: dict[str, int] = {"d": 1, "w": 7, "m": 7}

_LAST_DASHBOARD_HTML: str = ""

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IntelAgent")

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



async def _fetch_reddit_sentiment(brand: str, timeframe: str, limit: int = 25) -> list[dict]:
    t = _REDDIT_TIMEFRAME.get(timeframe, "week")
    from urllib.parse import quote
    url = f"https://www.reddit.com/search.json?q=%22{quote(brand)}%22&sort=top&t={t}&limit={limit}"
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


async def _fetch_twitter_api(brand: str, timeframe: str, limit: int = 50) -> list[dict]:
    """Fetch tweets via Twitter API v2 recent search. Requires TWITTER_BEARER_TOKEN in .env.
    Recent search capped at 7 days regardless of timeframe param. Returns [] if token absent."""
    if not _TWITTER_BEARER_TOKEN:
        return []
    days = _TWITTER_LOOKBACK_DAYS.get(timeframe, 7)
    start_time = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    brand_expr = _TWITTER_BRAND_QUERY.get(brand.lower(), f'"{brand}"')
    query = f"({brand_expr}) -is:retweet lang:en"
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": query,
        "max_results": min(limit, 100),
        "start_time": start_time,
        "tweet.fields": "text,public_metrics,created_at",
    }
    headers = {"Authorization": f"Bearer {_TWITTER_BEARER_TOKEN}"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
    data = resp.json()
    tweets = data.get("data") or []
    return [
        {
            "title": t.get("text", "")[:280],
            "body": "",
            "url": f"https://x.com/i/web/status/{t['id']}",
            "score": t.get("public_metrics", {}).get("like_count", 0),
        }
        for t in tweets
    ]


def _score_sentiment(texts: list[str]) -> dict:
    results = _sentiment_pipeline(texts, batch_size=16)
    pos_posts = sum(1 for r in results if r["label"] == "positive")
    neg_posts = sum(1 for r in results if r["label"] == "negative")
    neutral_posts = sum(1 for r in results if r["label"] == "neutral")
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
    On insufficient data: [{brand, platform, status}] sentinel instead.
    Sentiment score in [-1.0, 1.0]: positive=closer to 1, negative=closer to -1.
    Sentiment scored by RoBERTa model (twitter-roberta-base-sentiment-latest).
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
                api_posts = await _fetch_twitter_api(brand, timeframe, limit=50)
                if api_posts:
                    # API path — structured data, reliable
                    texts = [p["title"] for p in api_posts]
                    sentiment = _score_sentiment(texts)
                    top = [{"title": p["title"], "url": p["url"], "score": p["score"]} for p in api_posts[:5]]
                    results.append({
                        "brand": brand, "platform": "twitter",
                        "source": "twitter_api_v2",
                        "total_posts": len(api_posts),
                        **sentiment, "top_posts": top,
                    })
                else:
                    # DDGS fallback — use same brand expression to avoid ambiguous short names
                    ddgs_brand = _TWITTER_BRAND_QUERY.get(brand.lower(), f'"{brand}"').split(" OR ")[0].strip('"')
                    raw = list(DDGS().text(f'site:x.com "{ddgs_brand}"', timelimit=timeframe, region="in-en", max_results=20))
                    relevant = [r for r in raw if "/status/" in r.get("href", "") and ddgs_brand.lower() in (r.get("title", "") + r.get("body", "")).lower()]
                    if len(relevant) < 3:
                        results.append({"brand": brand, "platform": "twitter", "status": "insufficient_data: set TWITTER_BEARER_TOKEN for reliable data"})
                    else:
                        texts = [r.get("title", "") + " " + r.get("body", "") for r in relevant]
                        sentiment = _score_sentiment(texts)
                        top = [{"title": r.get("title", ""), "url": r.get("href", ""), "score": 0} for r in relevant[:5]]
                        results.append({
                            "brand": brand, "platform": "twitter",
                            "source": "ddgs_fallback",
                            "total_posts": len(relevant),
                            **sentiment, "top_posts": top,
                        })
            except Exception as e:
                results.append({"brand": brand, "platform": "twitter", "status": f"unavailable: {e}"})

        if do_linkedin:
            try:
                li_brand = _TWITTER_BRAND_QUERY.get(brand.lower(), f'"{brand}"').split(" OR ")[0].strip('"')
                # site:linkedin.com/posts returns actual posts; bare site:linkedin.com returns company pages/articles
                raw = list(DDGS().text(f'site:linkedin.com/posts "{li_brand}"', timelimit=timeframe, region="in-en", max_results=20))
                relevant = [r for r in raw if "/posts/" in r.get("href", "")]
                if len(relevant) < 3:
                    results.append({"brand": brand, "platform": "linkedin", "status": "insufficient_data: fewer than 3 indexed posts found"})
                else:
                    texts = [r.get("title", "") + " " + r.get("body", "") for r in relevant]
                    sentiment = _score_sentiment(texts)
                    top = [{"title": r.get("title", ""), "url": r.get("href", ""), "score": 0} for r in relevant[:5]]
                    results.append({"brand": brand, "platform": "linkedin", "total_posts": len(relevant), **sentiment, "top_posts": top})
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

    def _run_trends(pt: TrendReq) -> list[dict]:
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
            results.append({"city": str(city), "tier": tier, "interest_score": score,
                             "related_queries": top_queries, "related_topics": top_topics})
        results.sort(key=lambda x: x["interest_score"], reverse=True)
        return results if results else [{"status": f"No cities matched tier '{region_tier}'."}]

    try:
        pt = TrendReq(hl="en-IN", tz=330, retries=2, backoff_factor=0.5, timeout=(10, 25))
        return _run_trends(pt)
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

    Returns: [{keyword, brand, rank, present, url, presence_confidence}]
    rank: 1-indexed best position across 3 DDGS runs; null if not found.
    present: True only if found in ≥2/3 runs within top 10.
    presence_confidence: "X/3" — how many runs detected the brand.
    Use keywords specific to India e.g. "buy medicines online india" not generic US terms.
    """
    logger.info(f"Tool Call: fetch_search_presence(brands={brands}, keywords={keywords})")

    domain_map = {b.lower(): _BRAND_DOMAINS.get(b.lower(), b.lower().replace(" ", "") + ".in") for b in brands}
    results = []

    def _domain_match(domain: str, href: str) -> bool:
        return domain in href and (
            href.startswith(f"https://{domain}")
            or href.startswith(f"http://{domain}")
            or f".{domain}" in href
            or f"/{domain}" in href
        )

    for keyword in keywords:
        try:
            # DDGS backend rotation causes per-call rank drift.
            # Strategy: 3 independent queries, track best rank + how many runs found each brand.
            # Report best_rank (min across runs) + presence_confidence (X/3 runs found).
            # present = found in ≥2 of 3 runs within top 10.
            brand_best_rank: dict[str, int | None] = {b: None for b in brands}
            brand_found_runs: dict[str, int] = {b: 0 for b in brands}
            brand_url: dict[str, str | None] = {b: None for b in brands}

            for _ in range(3):
                hits = list(DDGS().text(keyword, region="in-en", max_results=10))
                for brand in brands:
                    domain = domain_map.get(brand.lower(), "")
                    for i, h in enumerate(hits, start=1):
                        href = h.get("href", "")
                        if _domain_match(domain, href):
                            brand_found_runs[brand] += 1
                            if brand_best_rank[brand] is None or i < brand_best_rank[brand]:
                                brand_best_rank[brand] = i
                                brand_url[brand] = href
                            break

            for brand in brands:
                best = brand_best_rank[brand]
                found = brand_found_runs[brand]
                results.append({
                    "keyword": keyword,
                    "brand": brand,
                    "rank": best,
                    "present": found >= 2 and best is not None and best <= 10,
                    "url": brand_url[brand],
                    "presence_confidence": f"{found}/3",
                })
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
