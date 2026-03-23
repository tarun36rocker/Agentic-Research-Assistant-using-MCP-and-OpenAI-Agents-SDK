import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from tools.scraper import scrape_url

mcp = FastMCP("scraper_server")


@mcp.tool()
async def scrape_page(url: str, max_chars: int = 2000) -> dict:
    """Scrape a web page and return extracted text.

    Args:
        url: Page URL.
        max_chars: Max chars to return.
    """
    text = scrape_url(url)
    safe_text = (text or "")[: max(100, int(max_chars))]
    return {"url": url, "text": safe_text}


if __name__ == "__main__":
    mcp.run(transport="stdio")
