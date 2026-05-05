import asyncio
import sys
from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession

async def run_test():
    url = "http://localhost:8000/mcp"

    print(f"🔄 Attempting to connect to Streamable-HTTP server at {url}...")
    try:
        async with streamable_http_client(url) as streams:
            # streamable_http_client returns (read_stream, write_stream, get_session_id)
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("✅ Successfully connected to the MCP Server via Streamable-HTTP!")

                print("\n📡 Fetching tools...")
                response = await session.list_tools()

                print("\n🛠️  Available Tools:")
                for tool in response.tools:
                    print(f"  - {tool.name}")

                print("\n✅ SSE test completed successfully!")
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nMake sure you have your server running in another terminal window with:")
        print("  python main.py")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_test())
