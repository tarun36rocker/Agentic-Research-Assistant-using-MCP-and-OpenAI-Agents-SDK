import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from utils.content_utils import report_as_json_string, parse_json_maybe

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _coerce_score(value, default=6.5):
    try:
        return float(value)
    except (TypeError, ValueError):
        pass

    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return default

    return default

def evaluator_agent(content):
    normalized = report_as_json_string(content)

    prompt = f"""
Evaluate this research content strictly.

Criteria:
- clarity
- structure
- depth
- usefulness

Return ONLY JSON:
{{
    "clarity": float,
    "structure": float,
    "depth": float,
    "usefulness": float,
    "overall": float,
    "issues": ["short issue 1", "short issue 2"]
}}

Rules:
- Scores are 0 to 10
- Use one decimal place
- Do not keep all values identical unless truly deserved
- If depth is weak, penalize depth clearly
- Ensure overall reflects the four criteria

Be critical. Avoid giving same score repeatedly.

Content:
{normalized}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    parsed = parse_json_maybe(response.choices[0].message.content, fallback={"overall": 6.5})
    if not isinstance(parsed, dict):
        return {"overall": 6.5, "fallback_used": True}

    criteria = ["clarity", "structure", "depth", "usefulness"]
    result = {}

    for key in criteria:
        result[key] = max(0.0, min(10.0, _coerce_score(parsed.get(key), default=6.5)))

    raw_score = parsed.get("overall")
    if raw_score is None:
        raw_score = parsed.get("score", parsed.get("rating"))

    if raw_score is None:
        score = round(sum(result.values()) / len(criteria), 2)
        fallback_used = True
    else:
        score = max(0.0, min(10.0, _coerce_score(raw_score, default=6.5)))
        fallback_used = False

    issues = parsed.get("issues", [])
    if not isinstance(issues, list):
        issues = []

    result["overall"] = score
    result["issues"] = [str(i) for i in issues if str(i).strip()]
    result["fallback_used"] = fallback_used
    return result