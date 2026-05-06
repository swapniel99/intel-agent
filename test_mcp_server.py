"""
MCP server integration tests. Requires server running at http://localhost:8000.

    ./.venv/bin/python main.py &
    uv run pytest test_mcp_server.py -v
"""
import json
import pytest
import httpx
from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession

SERVER_URL = "http://localhost:8000/mcp"
TOOL_NAMES = {"fetch_tech_news", "manage_local_library", "render_dashboard"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse(result) -> list | dict:
    raw = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
    return json.loads(raw)


async def _call(tool: str, args: dict):
    async with streamable_http_client(SERVER_URL) as streams:
        async with ClientSession(streams[0], streams[1]) as s:
            await s.initialize()
            return await s.call_tool(tool, args)


# ---------------------------------------------------------------------------
# Server / tool discovery
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_server_connects():
    async with streamable_http_client(SERVER_URL) as streams:
        async with ClientSession(streams[0], streams[1]) as s:
            await s.initialize()
            tools = await s.list_tools()
    names = {t.name for t in tools.tools}
    assert TOOL_NAMES.issubset(names), f"Missing tools: {TOOL_NAMES - names}"


# ---------------------------------------------------------------------------
# fetch_tech_news
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_hn():
    data = _parse(await _call("fetch_tech_news", {"query": "python", "limit": 3, "source": "hn"}))
    articles = [d for d in data if "title" in d]
    assert len(articles) > 0
    for a in articles:
        assert "url" in a
        assert a.get("source") == "hn"


@pytest.mark.asyncio
async def test_fetch_dev():
    data = _parse(await _call("fetch_tech_news", {"query": "python", "limit": 3, "source": "dev"}))
    articles = [d for d in data if "title" in d]
    assert len(articles) > 0
    for a in articles:
        assert "url" in a
        assert a.get("source") == "dev"


@pytest.mark.asyncio
async def test_fetch_reddit():
    data = _parse(await _call("fetch_tech_news", {"query": "python", "limit": 3, "source": "reddit"}))
    articles = [d for d in data if "title" in d]
    assert len(articles) > 0
    for a in articles:
        assert "url" in a
        assert a.get("source") == "reddit"


@pytest.mark.asyncio
async def test_fetch_all_sources():
    data = _parse(await _call("fetch_tech_news", {"query": "AI", "limit": 6, "source": "all"}))
    articles = [d for d in data if "title" in d]
    sources = {a.get("source") for a in articles}
    assert len(articles) > 0
    assert len(sources) >= 2, f"Expected multi-source, got: {sources}"


@pytest.mark.asyncio
async def test_fetch_unknown_source():
    data = _parse(await _call("fetch_tech_news", {"query": "AI", "limit": 3, "source": "bogus"}))
    assert isinstance(data, list)
    assert any("status" in d for d in data)


@pytest.mark.asyncio
async def test_fetch_returns_list():
    data = _parse(await _call("fetch_tech_news", {"query": "rust", "limit": 5, "source": "hn"}))
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# manage_local_library
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_library_list_all():
    data = _parse(await _call("manage_local_library", {"action": "list_all"}))
    assert "status" in data
    assert "articles" in data
    assert isinstance(data["articles"], list)


@pytest.mark.asyncio
async def test_library_check_duplicates_no_articles():
    data = _parse(await _call("manage_local_library", {"action": "check_duplicates"}))
    assert "status" in data


@pytest.mark.asyncio
async def test_library_save_and_dedup():
    article = {
        "title": "Test Article pytest",
        "url": "https://example.com/pytest-unique-12345",
        "points": 42,
        "source": "test",
        "ai_summary": "Pytest integration test article.",
    }
    data = _parse(await _call("manage_local_library", {"action": "save_new", "articles": [article]}))
    assert "new articles saved" in data["status"]

    data2 = _parse(await _call("manage_local_library", {"action": "save_new", "articles": [article]}))
    assert "1 duplicates skipped" in data2["status"]
    assert "0 new articles saved" in data2["status"]


@pytest.mark.asyncio
async def test_library_check_duplicates_novel():
    novel = {"title": "Novel", "url": "https://example.com/definitely-not-saved-xyz987"}
    data = _parse(await _call("manage_local_library", {"action": "check_duplicates", "articles": [novel]}))
    assert "articles" in data
    assert any(a["url"] == novel["url"] for a in data["articles"])


@pytest.mark.asyncio
async def test_library_search():
    data = _parse(await _call("manage_local_library", {"action": "search", "query": "pytest"}))
    assert "articles" in data


@pytest.mark.asyncio
async def test_library_search_missing_query():
    data = _parse(await _call("manage_local_library", {"action": "search"}))
    assert "query is required" in data["status"]


@pytest.mark.asyncio
async def test_library_update_and_delete():
    article = {
        "title": "Update/Delete Test",
        "url": "https://example.com/update-delete-test-99999",
        "points": 1,
        "source": "test",
        "ai_summary": "Will be updated then deleted.",
    }
    await _call("manage_local_library", {"action": "save_new", "articles": [article]})

    library = _parse(await _call("manage_local_library", {"action": "list_all"}))["articles"]
    target = next((a for a in library if a["url"] == article["url"]), None)
    assert target is not None
    aid = target["id"]

    upd = _parse(await _call("manage_local_library", {"action": "update", "article_id": aid, "updates": {"ai_summary": "Updated."}}))
    assert "updated successfully" in upd["status"]

    del_data = _parse(await _call("manage_local_library", {"action": "delete", "article_id": aid}))
    assert "deleted successfully" in del_data["status"]

    library2 = _parse(await _call("manage_local_library", {"action": "list_all"}))["articles"]
    assert all(a["id"] != aid for a in library2)


@pytest.mark.asyncio
async def test_library_delete_nonexistent():
    data = _parse(await _call("manage_local_library", {
        "action": "delete",
        "article_id": "00000000-0000-0000-0000-000000000000",
    }))
    assert "not found" in data["status"]


@pytest.mark.asyncio
async def test_library_update_missing_params():
    data = _parse(await _call("manage_local_library", {"action": "update"}))
    assert "required" in data["status"]


@pytest.mark.asyncio
async def test_library_unknown_action():
    data = _parse(await _call("manage_local_library", {"action": "explode"}))
    assert "Unknown action" in data["status"]


@pytest.mark.asyncio
async def test_library_save_no_articles():
    data = _parse(await _call("manage_local_library", {"action": "save_new"}))
    assert "0 articles provided" in data["status"]


# ---------------------------------------------------------------------------
# render_prefab_dashboard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_render_basic_dashboard():
    data = _parse(await _call("render_dashboard", {
        "title": "Test Dashboard",
        "summary": "This is a summary generated by pytest.",
        "cards": [{"title": "T", "url": "https://example.com", "points": 10, "source": "hn", "ai_summary": "S."}],
    }))
    assert data.get("status") == "dashboard_ready"


@pytest.mark.asyncio
async def test_render_with_bar_chart():
    data = _parse(await _call("render_dashboard", {
        "title": "Bar Chart Test",
        "summary": "Testing bar chart rendering.",
        "chart": {"type": "bar", "title": "Pts", "labels": ["HN", "Dev"], "values": [120, 80]},
    }))
    assert data.get("status") == "dashboard_ready"


@pytest.mark.asyncio
async def test_render_with_pie_chart():
    data = _parse(await _call("render_dashboard", {
        "title": "Pie Chart Test",
        "summary": "Testing pie chart rendering.",
        "chart": {"type": "pie", "title": "Dist", "labels": ["HN", "Dev"], "values": [60, 40]},
    }))
    assert data.get("status") == "dashboard_ready"


@pytest.mark.asyncio
async def test_render_with_radar_chart():
    data = _parse(await _call("render_dashboard", {
        "title": "Radar Chart Test",
        "summary": "Testing radar chart rendering.",
        "chart": {
            "type": "radar",
            "title": "Metrics",
            "data": [{"label": "Speed", "val": 80}, {"label": "Safety", "val": 90}],
            "series": [{"dataKey": "val", "label": "Score"}],
        },
    }))
    assert data.get("status") == "dashboard_ready"


@pytest.mark.asyncio
async def test_render_empty_cards():
    data = _parse(await _call("render_dashboard", {
        "title": "Empty Dashboard",
        "summary": "No articles found.",
        "cards": []
    }))
    assert data.get("status") == "dashboard_ready"


@pytest.mark.asyncio
async def test_render_with_metrics():
    data = _parse(await _call("render_dashboard", {
        "title": "Metrics Test",
        "summary": "Testing KPI metrics.",
        "metrics": [
            {"label": "Growth", "value": "15%", "trend": "up", "trendSentiment": "positive"},
            {"label": "Errors", "value": "2", "trend": "down", "trendSentiment": "positive"}
        ]
    }))
    assert data.get("status") == "dashboard_ready"


# ---------------------------------------------------------------------------
# /dashboard HTTP route
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dashboard_route_dark():
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://localhost:8000/dashboard?theme=dark")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "<html" in resp.text


@pytest.mark.asyncio
async def test_dashboard_route_light():
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://localhost:8000/dashboard?theme=light")
    assert resp.status_code == 200
    assert "<html" in resp.text
