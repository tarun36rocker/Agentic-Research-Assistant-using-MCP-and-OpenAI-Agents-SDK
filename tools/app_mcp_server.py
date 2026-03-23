import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from agents.research_agent import research_agent
from agents.reviewer_agent import reviewer_agent
from agents.evaluator_agent import evaluator_agent
from tools.pdf_generator import generate_pdf
from tools.ppt_generator import generate_ppt
from utils.content_utils import parse_json_maybe

mcp = FastMCP("agentic_app_server")


def _parse_content(content: Any):
    if isinstance(content, (dict, list)):
        return content
    if isinstance(content, str):
        parsed = parse_json_maybe(content, fallback=content)
        return parsed
    return content


@mcp.tool()
async def run_research(topic: str) -> dict:
    """Generate initial research report and sources for a topic."""
    return research_agent(topic)


@mcp.tool()
async def run_evaluator(content: Any) -> dict:
    """Evaluate report quality and return scoring breakdown."""
    return evaluator_agent(_parse_content(content))


@mcp.tool()
async def run_reviewer(content: Any, focus_areas: list[str] | None = None) -> dict:
    """Review and improve report content with optional focus areas."""
    improved, feedback = reviewer_agent(
        _parse_content(content),
        focus_areas=focus_areas or [],
        return_feedback=True,
    )
    if not isinstance(feedback, str):
        feedback = str(feedback)
    return {"improved_content": improved, "feedback": feedback}


@mcp.tool()
async def run_pdf(content: Any, topic: str) -> dict:
    """Generate PDF output from report content."""
    path = generate_pdf(_parse_content(content), topic)
    return {"path": path}


@mcp.tool()
async def run_ppt(content: Any, topic: str) -> dict:
    """Generate PPTX output from report content."""
    path = generate_ppt(_parse_content(content), topic)
    return {"path": path}


if __name__ == "__main__":
    mcp.run(transport="stdio")
