"""Smoke test: connect an in-memory MCP client to the server and list tools."""
import asyncio

from mcp.shared.memory import create_connected_server_and_client_session as connect

from pixelart_mcp.server import mcp


async def main() -> None:
    async with connect(mcp._mcp_server) as client:
        tools = await client.list_tools()
        names = sorted(t.name for t in tools.tools)
        print(f"Registered tools ({len(names)}):")
        for n in names:
            print(f"  - {n}")

        result = await client.call_tool(
            "pixelart_create_canvas",
            {"params": {"canvas_id": "smoke", "width": 8, "height": 8, "background": [0, 0, 0, 0]}},
        )
        print("\ncreate_canvas result:", result.content[0].text)


asyncio.run(main())
