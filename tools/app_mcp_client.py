import asyncio
import threading
from pathlib import Path
from typing import Any, Dict, List, Tuple

import mcp
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

from utils.content_utils import parse_json_maybe


ROOT = Path(__file__).resolve().parent.parent
SERVER_PATH = ROOT / "tools" / "app_mcp_server.py"

PARAMS = StdioServerParameters(
    command="python3",
    args=[str(SERVER_PATH)],
    env=None,
)


def _parse_result_text(result) -> Dict[str, Any]:
    def unwrap(data: Any) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return {}
        if isinstance(data.get("result"), dict):
            return data["result"]
        if isinstance(data.get("data"), dict):
            return data["data"]
        return data

    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return unwrap(structured)

    for item in getattr(result, "content", []) or []:
        # Text content
        text = getattr(item, "text", None)
        if isinstance(text, str) and text.strip():
            parsed = parse_json_maybe(text, fallback=None)
            if isinstance(parsed, dict):
                return parsed

        # JSON content variants
        data_obj = getattr(item, "data", None)
        if isinstance(data_obj, dict):
            return unwrap(data_obj)
        if isinstance(data_obj, str):
            parsed = parse_json_maybe(data_obj, fallback=None)
            if isinstance(parsed, dict):
                return unwrap(parsed)

        json_obj = getattr(item, "json", None)
        if isinstance(json_obj, dict):
            return unwrap(json_obj)

    return {}


async def _call_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    async with stdio_client(PARAMS) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
    return _parse_result_text(result)


def _run_sync(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result_box: dict = {}
    error_box: dict = {}

    def runner():
        try:
            result_box["value"] = asyncio.run(coro)
        except Exception as exc:
            error_box["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()

    if "error" in error_box:
        raise error_box["error"]

    return result_box.get("value")


def research_agent_mcp_sync(topic: str) -> Dict[str, Any]:
    return _run_sync(_call_tool("run_research", {"topic": topic})) or {}


def evaluator_agent_mcp_sync(content: Any) -> Dict[str, Any]:
    return _run_sync(_call_tool("run_evaluator", {"content": content})) or {}


def reviewer_agent_mcp_sync(content: Any, focus_areas: List[str] | None = None) -> Tuple[Dict[str, Any], str]:
    payload = {"content": content, "focus_areas": focus_areas or []}
    data = _run_sync(_call_tool("run_reviewer", payload)) or {}

    improved = data.get("improved_content", content)
    feedback = data.get("feedback", "No specific feedback provided.")
    if not isinstance(feedback, str):
        feedback = str(feedback)

    return improved, feedback


def generate_pdf_mcp_sync(content: Any, topic: str) -> str:
    data = _run_sync(_call_tool("run_pdf", {"content": content, "topic": topic})) or {}
    return str(data.get("path", ""))


def generate_ppt_mcp_sync(content: Any, topic: str) -> str:
    data = _run_sync(_call_tool("run_ppt", {"content": content, "topic": topic})) or {}
    return str(data.get("path", ""))
