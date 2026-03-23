import json
import re
from typing import Any, Dict, List


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def parse_json_maybe(value: Any, fallback: Any = None) -> Any:
    if isinstance(value, (dict, list)):
        return value

    if not isinstance(value, str):
        return fallback

    cleaned = _strip_code_fences(value)

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Fallback: try to find first JSON object in text
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return fallback

    return fallback


def normalize_report_content(content: Any) -> Dict[str, Any]:
    default = {"title": "Research Report", "sections": []}
    parsed = parse_json_maybe(content, fallback=default)

    if not isinstance(parsed, dict):
        return default

    title = parsed.get("title")
    sections = parsed.get("sections")

    safe_title = title if isinstance(title, str) and title.strip() else "Research Report"
    safe_sections: List[Dict[str, Any]] = []

    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue

            heading = section.get("heading")
            body = section.get("content")
            bullets = section.get("bullets", [])

            if not isinstance(heading, str):
                heading = "Section"
            if not isinstance(body, str):
                body = ""
            if not isinstance(bullets, list):
                bullets = []

            safe_bullets = [str(item) for item in bullets if str(item).strip()]

            safe_sections.append(
                {
                    "heading": heading.strip() or "Section",
                    "content": body.strip(),
                    "bullets": safe_bullets,
                }
            )

    return {"title": safe_title.strip(), "sections": safe_sections}


def report_as_json_string(content: Any) -> str:
    return json.dumps(normalize_report_content(content), ensure_ascii=False, indent=2)