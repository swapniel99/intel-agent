# Marketing Intelligence Control Tower — Implementation Plan

## Goal
Add social sentiment, content trend, and search presence tracking for pharma brands (PharmEasy, 1mg, Apollo, HMS) as a daily marketing control tower layered on top of the existing IntelAgent.

---

## What Changes

### REMOVE — nothing
All 3 existing MCP tools (`fetch_tech_news`, `manage_local_library`, `render_dashboard`) stay untouched.

### MODIFY — existing files

| File | What changes |
|---|---|
| `main.py` | Add 3 new `@mcp.tool()` functions + 3 private helpers + new imports (`duckduckgo_search`, `pytrends`) |
| `pyproject.toml` | Add `duckduckgo-search>=8.0.0` and `pytrends>=4.9.2` to dependencies |
| `extension/index.js` | (1) Add `MARKETING_INTEL` intent to `systemInstruction`. (2) Add 3 quick-action preset buttons above input |
| `CLAUDE.md` | Update Setup commands to reflect new deps |

### NEW — no new files
All additions go into existing `main.py` and `index.js`.

---

## New MCP Tools (main.py)

### Tool 1: `fetch_brand_sentiment`
```
fetch_brand_sentiment(
    brands: list[str],          # e.g. ["PharmEasy", "1mg", "Apollo"]
    platforms: str = "all",     # "reddit" | "twitter" | "linkedin" | "all"
    timeframe: str = "w"        # "d"=day | "w"=week | "m"=month
) -> list[dict]
```
**Returns:** `[{brand, platform, total_posts, positive_pct, negative_pct, neutral_pct, sentiment_score, top_posts: [{title, url, score, snippet}]}]`

**Implementation:**
- Reddit: `GET reddit.com/search.json?q={brand}&sort=new&t={timeframe}&limit=25` via httpx (no auth)
  - Private helper: `_fetch_reddit_sentiment(brand, timeframe, limit)` — separate from existing `_fetch_reddit`
  - Returns selftext/body + score + num_comments + subreddit
- Twitter/X: `ddgs.text(f'site:x.com "{brand}"', timelimit=timeframe, max_results=20)`
- LinkedIn: `ddgs.text(f'site:linkedin.com "{brand}"', timelimit=timeframe, max_results=20)`
- Sentiment scoring: keyword wordlists (no ML)
  - Positive: great, love, best, fast, easy, excellent, happy, discount, amazing, reliable, good
  - Negative: bad, worst, terrible, delay, refund, problem, issue, scam, fake, awful, slow, fraud, pathetic
  - Score per post: (positive_hits - negative_hits) / total_words → normalize to [-1, 1]
  - Aggregate across posts → pct buckets
- Fallback: return `[{status: "..."}]`, never raise

### Tool 2: `fetch_content_trends`
```
fetch_content_trends(
    topic: str,                  # e.g. "online pharmacy", "medicine delivery"
    region_tier: str = "all",    # "tier1" | "tier2" | "tier3" | "all"
    timeframe: str = "today 1-m" # pytrends format: "today 1-m" | "today 3-m" | "2025-01-01 2025-05-01"
) -> list[dict]
```
**Returns:** `[{city, tier, interest_score, related_queries: [...], related_topics: [...]}]`

**Implementation:**
- `pytrends.TrendReq(hl='en-IN', tz=330)` → `build_payload([topic], geo='IN', timeframe=timeframe)`
- `interest_by_region(resolution='CITY', geo='IN')` → pandas DataFrame → list of dicts
- Static tier map (hardcoded dict in module):
  - Tier 1: Mumbai, Delhi, Bengaluru, Chennai, Hyderabad, Pune, Kolkata, Ahmedabad
  - Tier 2: Jaipur, Lucknow, Surat, Kanpur, Nagpur, Patna, Indore, Bhopal, Visakhapatnam, Vadodara
  - Tier 3: everything else
- `related_queries()` + `related_topics()` — top 5 each, appended to result
- Filter by `region_tier` if not "all"
- Fallback: pytrends 429 → return `[{status: "Google Trends rate-limited. Retry in 60s."}]`

### Tool 3: `fetch_search_presence`
```
fetch_search_presence(
    brands: list[str],    # e.g. ["PharmEasy", "1mg", "Apollo", "HMS"]
    keywords: list[str]   # e.g. ["buy medicine online", "online pharmacy india"]
) -> list[dict]
```
**Returns:** `[{keyword, brand, rank, present, url}]` — one row per (keyword × brand)

**Implementation:**
- For each keyword: `ddgs.text(keyword, max_results=10)` → scan result `href` fields
- Brand → domain map: `{"PharmEasy": "pharmeasy.in", "1mg": "1mg.com", "Apollo": "apollopharmacy.in", "HMS": "hms.co.in"}`
- Find first result index where domain appears in URL → `rank` (1-indexed), `present=True`
- If not found in top 10: `rank=None`, `present=False`
- Fallback: ddgs failure → `[{status: "..."}]`

---

## Private Helpers to Add (main.py)

```python
# New — for sentiment (richer fields than existing _fetch_reddit)
async def _fetch_reddit_sentiment(brand, timeframe, limit) -> list[dict]

# New — keyword-based sentiment scorer
def _score_sentiment(texts: list[str]) -> dict  # {positive_pct, negative_pct, neutral_pct, score}

# New — tier lookup
def _city_tier(city_name: str) -> str  # "tier1" | "tier2" | "tier3"
```

Existing `_fetch_reddit` (used by `fetch_tech_news`) stays unchanged.

---

## Client Changes (extension/index.js)

### Change 1: System prompt — add intent class
Append to `systemInstruction` after existing TREND_ANALYSIS intent:
```
- MARKETING_INTEL: brand sentiment, competitor comparison, content trends, search rankings.
  → fetch_brand_sentiment → fetch_search_presence → fetch_content_trends
  → render_dashboard(metrics=[...], chart=..., table=..., layout="split")
  Use metrics for sentiment scores, chart (bar/radar) for brand comparisons, table for ranking data.
```

### Change 2: Quick-action preset buttons
Add 3 buttons in `index.html` (above the prompt input `<textarea>`), wired in `index.js`:
- **"Daily Sentiment"** → fills input: `"Show daily sentiment for PharmEasy vs 1mg vs Apollo on Reddit and Twitter"`
- **"Content Trends"** → fills input: `"What health content is trending in tier 1 and tier 2 cities this month?"`
- **"Search Rankings"** → fills input: `"Where does PharmEasy rank vs 1mg and Apollo for key pharmacy searches?"`

Buttons styled consistently with existing UI (dark/light theme aware).

---

## Deps to Add (pyproject.toml)

```toml
"duckduckgo-search>=8.0.0",
"pytrends>=4.9.2",
```

---

## Implementation Order

- [x] **Step 1** — `pyproject.toml`: add `ddgs` + `pytrends`; run `uv sync`
- [x] **Step 2** — `main.py`: add imports + constants (`_POSITIVE_WORDS`, `_NEGATIVE_WORDS`, `_TIER1/2_CITIES`, `_BRAND_DOMAINS`, `_REDDIT_TIMEFRAME`) + urllib3 monkey-patch for pytrends compat
- [x] **Step 3** — `main.py`: add `_fetch_reddit_sentiment` + `_score_sentiment` + `_city_tier` helpers
- [x] **Step 4** — `main.py`: implement `fetch_brand_sentiment` tool
- [x] **Step 5** — `main.py`: implement `fetch_content_trends` tool (fixed: `interest_by_region()` takes no `geo` param)
- [x] **Step 6** — `main.py`: implement `fetch_search_presence` tool
- [x] **Step 7 (smoke test)** — 6 tools confirmed; `fetch_brand_sentiment` ✅ `fetch_search_presence` ✅ `fetch_content_trends` ✅ (429 handled gracefully — Google rate-limit is external)
- [x] **Step 8** — `extension/index.js`: add `MARKETING_INTEL` intent to system prompt
- [x] **Step 9** — `extension/index.html` + `index.js`: add quick-action buttons
- [x] **Step 10** — `CLAUDE.md`: update Setup section

---

## Constraints
- Never raise from MCP tools — always catch + return `[{status: "..."}]`
- ddgs calls: `max_results` capped at 25 (avoid rate-limit)
- pytrends: wrap in try/except for 429; surface as status sentinel
- `_fetch_reddit_sentiment` uses `reddit.com/search.json` (public JSON API, no OAuth)
- No new files — all additions in `main.py` and `index.js`/`index.html`
