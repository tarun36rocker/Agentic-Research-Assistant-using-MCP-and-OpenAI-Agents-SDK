import os
import json
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from utils.content_utils import normalize_report_content, parse_json_maybe

load_dotenv()


def chart_agent(content: Any) -> Dict[str, Any]:
    """
    Build a chart plan from report content using an LLM.

    Returns:
    {
      "charts": [
        {
          "title": str,
          "chart_type": "column" | "bar",
          "series_name": str,
          "categories": [str],
          "values": [float],
          "insight": str
        }
      ]
    }
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"charts": []}

    data = normalize_report_content(content)
    client = OpenAI(api_key=api_key)

    prompt = f"""
You are a data visualization planner.

From the research report JSON below, extract ONLY meaningful chart data supported by the content.
Do not invent facts.

Return JSON only in this format:
{{
  "charts": [
    {{
      "title": "...",
      "chart_type": "column",
      "series_name": "...",
      "categories": ["...", "..."],
      "values": [1.0, 2.0],
      "insight": "One-line explanation of what this chart shows"
    }}
  ]
}}

Rules:
- 1 to 3 charts max
- chart_type must be "column" or "bar"
- categories and values must have same length
- each chart must have at least 3 points
- use concise titles and labels
- if not enough quantitative evidence, return empty charts list

Report JSON:
{json.dumps(data, ensure_ascii=False)}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
    except Exception:
        return {"charts": []}

    parsed = parse_json_maybe(response.choices[0].message.content, fallback={"charts": []})
    if not isinstance(parsed, dict):
        return {"charts": []}

    charts = parsed.get("charts", [])
    if not isinstance(charts, list):
        return {"charts": []}

    cleaned: List[Dict[str, Any]] = []
    for chart in charts[:3]:
        if not isinstance(chart, dict):
            continue

        title = str(chart.get("title", "Chart")).strip() or "Chart"
        chart_type = str(chart.get("chart_type", "column")).strip().lower()
        if chart_type not in {"column", "bar"}:
            chart_type = "column"

        series_name = str(chart.get("series_name", "Value")).strip() or "Value"
        categories = chart.get("categories", [])
        values = chart.get("values", [])
        insight = str(chart.get("insight", "")).strip()

        if not isinstance(categories, list) or not isinstance(values, list):
            continue
        if len(categories) != len(values) or len(categories) < 3:
            continue

        safe_categories = [str(c)[:30] for c in categories[:8]]
        safe_values: List[float] = []
        for v in values[:8]:
            try:
                safe_values.append(float(v))
            except (TypeError, ValueError):
                safe_values.append(0.0)

        if len(safe_categories) != len(safe_values):
            continue

        cleaned.append(
            {
                "title": title,
                "chart_type": chart_type,
                "series_name": series_name,
                "categories": safe_categories,
                "values": safe_values,
                "insight": insight,
            }
        )

    return {"charts": cleaned}