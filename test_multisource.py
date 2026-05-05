import asyncio
from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession

async def test_fetch(session, query, limit, source):
    print(f"\n📡 Testing fetch_tech_news(query='{query}', limit={limit}, source='{source}')...")
    try:
        result = await session.call_tool("fetch_tech_news", {
            "query": query,
            "limit": limit,
            "source": source
        })

        if result.content:
            articles = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
            try:
                import json
                articles = json.loads(articles)
                print(f"✅ Got {len(articles)} articles")
                for a in articles[:2]:
                    src = a.get('source', 'unknown')
                    title = a.get('title', 'N/A')[:60]
                    print(f"   [{src}] {title}...")
            except:
                print(f"   {articles[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

async def run():
    url = "http://localhost:8000/mcp"
    print(f"Connecting to {url}...")

    try:
        async with streamable_http_client(url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("✅ Connected")

                # Test individual sources
                await test_fetch(session, "AI", 2, "hn")
                await test_fetch(session, "AI", 2, "dev")
                await test_fetch(session, "AI", 2, "reddit")

                # Test combined
                await test_fetch(session, "AI", 6, "all")

                print("\n✅ All tests passed!")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run())
