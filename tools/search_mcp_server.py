import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from tools.search import search_serper

mcp = FastMCP("serper_search_server")


@mcp.tool()
async def search_web(query: str, limit: int = 8) -> dict:
    """Search the web via Serper and return top result links.

    Args:
        query: Search query/topic.
        limit: Max number of links to return.
    """
    links = search_serper(query)
    safe_links = [link for link in links if isinstance(link, str) and link.startswith("http")]
    return {"links": safe_links[: max(1, int(limit))]}


if __name__ == "__main__":
    mcp.run(transport="stdio")
