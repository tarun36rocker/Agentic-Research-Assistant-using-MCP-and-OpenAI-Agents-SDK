import os
from openai import OpenAI
import json
from dotenv import load_dotenv
from utils.content_utils import normalize_report_content, parse_json_maybe

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def reviewer_agent(content, focus_areas=None, return_feedback=False):
    normalized_content = normalize_report_content(content)
    focus_text = ""
    if focus_areas:
        focus_text = "\nFocus especially on these weak areas: " + ", ".join(focus_areas)

    prompt = f"""
You are a strict reviewer.

Analyze the content and:

1. Identify issues
2. Suggest improvements
3. Rewrite the FULL improved version

The improved version must be materially better than the input, not just rephrased.
Add concrete details where possible and strengthen weak sections.

IMPORTANT:
- You MUST return valid JSON
- Do NOT include any extra text

Format:
{{
  "improvements": ["point 1", "point 2"],
    "improved_content": {{
        "title": "...",
        "sections": [
            {{"heading": "...", "content": "...", "bullets": ["...", "..."]}}
        ]
    }}
}}

Content:
{json.dumps(normalized_content, ensure_ascii=False)}
{focus_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content

    data = parse_json_maybe(raw, fallback={})
    if not isinstance(data, dict):
        if return_feedback:
            return normalized_content, "⚠️ Model did not return valid JSON, skipping improvement"
        return normalized_content

    improved = normalize_report_content(data.get("improved_content", normalized_content))

    if return_feedback:
        feedback = "\n".join(data.get("improvements", []))
        return improved, feedback or "No specific feedback provided."

    return improved