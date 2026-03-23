"""
Extract meaningful content insights for data visualization.
"""

from typing import Dict, List, Any, Tuple
import re
from collections import Counter


def extract_numbers(text: str) -> List[Tuple[float, str]]:
    """Extract numbers and their context from text."""
    pattern = r'(\d+\.?\d*)\s*(%|points|goals|wins|losses|runs|wickets|matches|years|million|billion|thousand|lakhs|crores)?'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    result = []
    for match in matches[:15]:
        try:
            num = float(match[0])
            unit = match[1].lower() if match[1] else ""
            result.append((num, unit))
        except ValueError:
            pass
    
    return result


def extract_comparisons(text: str) -> List[str]:
    """Extract comparative statements (better than, more than, less than, etc.)."""
    patterns = [
        r"([A-Za-z\s]+?)\s+(?:is|are)\s+(?:more|better|worse|faster|slower|higher|lower)\s+than\s+([A-Za-z\s]+)",
        r"([A-Za-z\s]+?)\s+(?:vs|versus|compared to|compared with)\s+([A-Za-z\s]+)",
        r"([A-Za-z\s]+?)\s+(?:outperformed|outscored|defeated|beat|surpassed)\s+([A-Za-z\s]+)",
    ]
    
    comparisons = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches[:5]:
            comparisons.append(f"{match[0].strip()} vs {match[1].strip()}")
    
    return comparisons[:10]


def extract_entities(text: str) -> List[Tuple[str, int]]:
    """Extract named entities (proper nouns) and their frequency."""
    # Find capitalized words/phrases (heuristic for entities)
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', text)
    
    # Filter out common non-entities
    non_entities = {"The", "A", "An", "In", "On", "At", "By", "From", "To", "And", "Or", "But"}
    entities = [w for w in words if w not in non_entities]
    
    # Count frequency
    freq = Counter(entities)
    return freq.most_common(8)


def extract_lists(text: str) -> Dict[str, List[str]]:
    """Extract key lists/categories from text."""
    # Look for patterns like "Types of X: A, B, C" or "X includes: ..."
    list_patterns = [
        r"(?:types|categories|kinds|varieties|forms|examples|including|include|such as)[\s:]+([^.!?\n]+)",
    ]
    
    lists_found = {}
    for pattern in list_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for i, match in enumerate(matches[:3]):
            items = [item.strip() for item in match.split(",") if item.strip()]
            if len(items) >= 2:
                lists_found[f"List_{i}"] = items[:6]
    
    return lists_found


def extract_metrics(content: str) -> Dict[str, Any]:
    """Extract all meaningful metrics from content."""
    metrics = {
        "numbers": extract_numbers(content),
        "comparisons": extract_comparisons(content),
        "entities": extract_entities(content),
        "lists": extract_lists(content),
    }
    
    return metrics


def analyze_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze report and extract content-based insights."""
    sections = report_data.get("sections", [])
    
    analysis = {
        "title": report_data.get("title", "Report"),
        "total_sections": len(sections),
        "charts_data": {},
    }
    
    if not sections:
        return analysis
    
    # Combine all content
    full_text = " ".join([
        s.get("heading", "") + " " + s.get("content", "") + " " + 
        " ".join(s.get("bullets", []))
        for s in sections
    ])
    
    # Extract entities with frequency for a meaningful chart
    entities = extract_entities(full_text)
    if entities:
        analysis["charts_data"]["top_entities"] = {
            "labels": [e[0][:20] for e in entities],
            "values": [e[1] for e in entities],
            "title": "Key Entities Mentioned"
        }
    
    # Extract numbers for a chart
    numbers = extract_numbers(full_text)
    if len(numbers) >= 3:
        # Group by unit or just take top numbers
        unique_numbers = list(dict.fromkeys([str(int(n[0]) if n[0] == int(n[0]) else n[0]) for n in numbers[:10]]))
        if len(unique_numbers) >= 3:
            analysis["charts_data"]["key_numbers"] = {
                "labels": [f"Value {i+1}" for i in range(len(unique_numbers))],
                "values": [float(n) for n in unique_numbers],
                "title": "Key Numbers in Content"
            }
    
    # Extract section-wise entity mentions
    section_entities = {}
    for section in sections:
        section_text = section.get("heading", "") + " " + section.get("content", "")
        entities = extract_entities(section_text)
        if entities:
            # Take top entity mention count per section
            section_entities[section.get("heading", "Section")[:15]] = entities[0][1] if entities else 0
    
    if section_entities:
        analysis["charts_data"]["section_focus"] = {
            "labels": list(section_entities.keys()),
            "values": list(section_entities.values()),
            "title": "Entity Density by Section"
        }
    
    # Comparisons found
    comparisons = extract_comparisons(full_text)
    if comparisons:
        analysis["charts_data"]["comparisons"] = {
            "items": comparisons[:5],
            "title": "Key Comparisons"
        }
    
    return analysis
