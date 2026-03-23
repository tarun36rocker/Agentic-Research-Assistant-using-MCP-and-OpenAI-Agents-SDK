import asyncio
import threading
from pathlib import Path

import mcp
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

from utils.content_utils import parse_json_maybe


ROOT = Path(__file__).resolve().parent.parent
SERVER_PATH = ROOT / "tools" / "scraper_mcp_server.py"

PARAMS = StdioServerParameters(
    command="python3",
    args=[str(SERVER_PATH)],
    env=None,
)


async def scrape_url_mcp(url: str, max_chars: int = 2000) -> str:
    async with stdio_client(PARAMS) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool("scrape_page", {"url": url, "max_chars": max_chars})

    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return str(structured.get("text", ""))

    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if isinstance(text, str) and text.strip():
            parsed = parse_json_maybe(text, fallback=None)
            if isinstance(parsed, dict):
                return str(parsed.get("text", ""))

        data_obj = getattr(item, "data", None)
        if isinstance(data_obj, dict):
            return str(data_obj.get("text", ""))

        json_obj = getattr(item, "json", None)
        if isinstance(json_obj, dict):
            return str(json_obj.get("text", ""))

    return ""


def scrape_url_mcp_sync(url: str, max_chars: int = 2000) -> str:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(scrape_url_mcp(url, max_chars=max_chars))

    result_box: dict = {}
    error_box: dict = {}

    def runner():
        try:
            result_box["value"] = asyncio.run(scrape_url_mcp(url, max_chars=max_chars))
        except Exception as exc:
            error_box["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()

    if "error" in error_box:
        raise error_box["error"]

    return result_box.get("value", "")
