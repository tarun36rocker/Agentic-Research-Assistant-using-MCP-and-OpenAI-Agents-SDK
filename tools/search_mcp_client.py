import asyncio
import threading
from pathlib import Path
from typing import List

import mcp
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

from utils.content_utils import parse_json_maybe


ROOT = Path(__file__).resolve().parent.parent
SERVER_PATH = ROOT / "tools" / "search_mcp_server.py"

PARAMS = StdioServerParameters(
    command="python3",
    args=[str(SERVER_PATH)],
    env=None,
)


async def search_serper_mcp(query: str, limit: int = 8) -> List[str]:
    async with stdio_client(PARAMS) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool("search_web", {"query": query, "limit": limit})

    data = {}

    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        data = structured
    else:
        for item in getattr(result, "content", []) or []:
            text = getattr(item, "text", None)
            if isinstance(text, str) and text.strip():
                parsed = parse_json_maybe(text, fallback=None)
                if isinstance(parsed, dict):
                    data = parsed
                    break

            data_obj = getattr(item, "data", None)
            if isinstance(data_obj, dict):
                data = data_obj
                break

            json_obj = getattr(item, "json", None)
            if isinstance(json_obj, dict):
                data = json_obj
                break

    links = data.get("links", []) if isinstance(data, dict) else []

    return [link for link in links if isinstance(link, str) and link.startswith("http")]


def search_serper_mcp_sync(query: str, limit: int = 8) -> List[str]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(search_serper_mcp(query, limit=limit))

    result_box: dict = {}
    error_box: dict = {}

    def runner():
        try:
            result_box["value"] = asyncio.run(search_serper_mcp(query, limit=limit))
        except Exception as exc:
            error_box["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()

    if "error" in error_box:
        raise error_box["error"]

    return result_box.get("value", [])
