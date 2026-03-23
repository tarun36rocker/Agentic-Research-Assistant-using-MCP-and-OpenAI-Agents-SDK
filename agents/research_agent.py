import os
from openai import OpenAI
from tools.search import search_serper
from tools.scraper import scrape_url
from utils.content_utils import normalize_report_content

from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def research_agent(topic):
    # MCP-first search path; fallback to direct local tool.
    try:
        from tools.search_mcp_client import search_serper_mcp_sync
        links = search_serper_mcp_sync(topic, limit=8)
    except Exception:
        links = search_serper(topic)

    # Fallback if MCP call succeeds but returns no links.
    if not links:
        links = search_serper(topic)

    source_links = [link for link in links if isinstance(link, str) and link.startswith("http")][:8]

    if len(source_links) < 2:
        raise ValueError(
            "Insufficient searchable sources found. Refine the topic/query and try again."
        )

    contents = []
    for link in links[:5]:
        try:
            from tools.scraper_mcp_client import scrape_url_mcp_sync
            text = scrape_url_mcp_sync(link, max_chars=2000)
        except Exception:
            text = scrape_url(link)

        if text and len(text.strip()) >= 200:
            contents.append(f"Source: {link}\n{text}")

    combined = "\n\n".join(contents[:5])
    total_chars = sum(len(c) for c in contents)

    if len(contents) < 2 or total_chars < 1200:
        raise ValueError(
            "Insufficient scraped evidence. Could not collect enough source text to produce a grounded report."
        )

    prompt = f"""
Generate a structured research report on: {topic}

Use these source snippets:
{combined}

Strict grounding rules:
- Use ONLY information present in the provided source snippets.
- Do NOT use prior knowledge.
- Do NOT infer facts not explicitly supported by snippets.

Return ONLY JSON in this format:
{{
    "title": "...",
    "sections": [
        {{
            "heading": "...",
            "content": "...",
            "bullets": ["...", "..."]
        }}
    ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    return {
        "report": normalize_report_content(response.choices[0].message.content),
        "sources": source_links,
    }