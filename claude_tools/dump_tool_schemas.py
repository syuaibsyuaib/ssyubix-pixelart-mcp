"""Dump a compact JSON summary of all registered MCP tools (name + input schema).

Purpose: lets a future Claude session inspect the server's tool surface
in one cheap call instead of re-reading server.py + models.py in full.
Run: python claude_tools/dump_tool_schemas.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.shared.memory import create_connected_server_and_client_session as connect

from pixelart_mcp.server import mcp


async def main() -> None:
    async with connect(mcp._mcp_server) as client:
        tools = await client.list_tools()
        summary = [
            {"name": t.name, "description": (t.description or "").strip().split("\n")[0], "input_schema": t.inputSchema}
            for t in tools.tools
        ]
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
