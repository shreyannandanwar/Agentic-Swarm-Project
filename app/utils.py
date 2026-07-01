# app/utils.py
"""JSON extraction and text cleaning utilities."""

import json
import re
from typing import Any


def extract_json(text: str) -> Any:
    """
    Robustly extract the first valid JSON object or array from LLM output.
    Prefers objects over arrays (claims should be inside an object, not bare).
    """
    if not text:
        raise ValueError("Empty LLM response")

    original = text.strip()
    text = original

    # Step 1: Strip common prose prefixes
    text = re.sub(
        r"^Here (?:are|is) (?:the )?(?:extracted )?verified facts:?[ \t]*\n*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^Here (?:are|is) (?:the )?JSON output:?[ \t]*\n*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^\*\*Summary:\*\*\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\*\*Claims:\*\*\s*", "", text, flags=re.IGNORECASE)

    # Step 2: Strip markdown fences — anywhere in text
    text = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```", "", text)

    # Step 3: Strip trailing notes/explanations
    text = re.sub(r"\n*Note:.*$", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\n*The confidence level.*$", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Step 4: Strip bold markdown artifacts
    text = re.sub(r"\*\*Claim \d+:\*\*\s*", "", text)
    text = re.sub(r"\*\*Statement:\*\*\s*", "", text)
    text = re.sub(r"\*\*Sources:\*\*\s*", "", text)
    text = re.sub(r"\*\*Confidence:\*\*\s*", "", text)

    text = text.strip()

    # Step 5: If the result looks like a JSON string (wrapped in quotes), unescape it
    if text.startswith('"') and text.endswith('"'):
        try:
            text = json.loads(text)
            if isinstance(text, str):
                text = text.strip()
        except Exception:
            pass

    # Step 6: Find and parse JSON objects/arrays
    # First pass: prefer objects (dicts) over arrays (lists)
    decoder = json.JSONDecoder()
    candidates = []
    
    for i, ch in enumerate(text):
        if ch not in "{[":
            continue
        try:
            obj, idx = decoder.raw_decode(text, i)
            candidates.append((i, obj))
        except json.JSONDecodeError:
            continue

    # Prefer objects (dicts) — the outer JSON structure we want.
    # Use the FIRST (earliest) object found: candidates are appended in
    # left-to-right order, so the outermost wrapper always comes first.
    objects = [obj for _, obj in candidates if isinstance(obj, dict)]
    if objects:
        return objects[0]

    # Fallback: return first array if no objects found
    arrays = [obj for _, obj in candidates if isinstance(obj, list)]
    if arrays:
        return arrays[0]

    # Step 7: Last resort — try to repair common JSON errors
    repaired = re.sub(r",\s*([}\]])", r"\1", text)
    repaired = re.sub(r"([{,]\s*)'([^']+)'(\s*:)", r'\1"\2"\3', repaired)
    repaired = re.sub(r"([{,]\s*)(\w+)(\s*:)", r'\1"\2"\3', repaired)

    for i, ch in enumerate(repaired):
        if ch not in "{[":
            continue
        try:
            obj, idx = decoder.raw_decode(repaired, i)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    print(f"DEBUG: Could not parse JSON from:\n{text[:500]}")

    raise ValueError(f"No valid JSON found after stripping and repair.\n\n{text[:400]}")


def safe_json_dumps(obj) -> str:
    """Pretty JSON for prompts."""
    return json.dumps(obj, indent=2, ensure_ascii=False)