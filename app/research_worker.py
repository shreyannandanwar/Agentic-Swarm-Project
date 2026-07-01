# app/research_worker.py
"""Research worker: searches web, extracts structured claims with Evidence."""
"""
Research worker.

Responsibilities:
1. Search the web.
2. Build LLM context.
3. Extract structured JSON.
4. Convert raw claims into Claim models.

The worker DOES NOT:
- score trust
- calculate confidence
- merge claims
- detect conflicts
"""

import asyncio
from typing import List

from app.claim_validator import build_claim
from app.llm import generate
from app.schemas import WorkerOutput
from app.search import search_web
from app.utils import extract_json


WORKER_PROMPT = """
Extract verified facts from the supplied sources.

Question:
{question}

Sources:
{context}

Return ONLY valid JSON.

Schema:

{{
  "summary":"2 sentence factual summary",
  "claims":[
    {{
      "statement":"fact",
      "sources":[
        "https://example.com"
      ],
      "is_quantified":false
    }}
  ]
}}

Rules:

- Use ONLY the supplied sources.
- Never invent URLs.
- Copy URLs exactly.
- Never output "SOURCE 1", "[1]" or similar placeholders.
- If evidence is insufficient, omit the claim.
- Return JSON only.
"""


def build_context(results: List[dict]) -> str:
    """
    Convert Tavily results into prompt context.
    """

    if not results:
        return "No sources."

    sections = []

    for i, result in enumerate(results, start=1):

        sections.append(
            f"""
SOURCE {i}

URL:
{result.get("url","")}

TITLE:
{result.get("title","")}

CONTENT:
{result.get("content","")[:500]}
"""
        )

    return "\n".join(sections)


async def research_subquestion(
    question: str,
) -> WorkerOutput:

    print(f"🔍 {question}")

    try:

        results = await asyncio.to_thread(
            search_web,
            question,
            3,
        )

    except Exception as e:

        print(f"❌ Search failed: {e}")

        return WorkerOutput(
            question=question,
            summary="Search failed.",
            claims=[],
        )

    if not results:

        return WorkerOutput(
            question=question,
            summary="No search results.",
            claims=[],
        )

    source_map = {
        r["url"]: r
        for r in results
        if r.get("url")
    }

    prompt = WORKER_PROMPT.format(
        question=question,
        context=build_context(results),
    )

    try:

        response = await asyncio.to_thread(
            generate,
            prompt,
            model="smart",
            max_tokens=1024,
        )

    except Exception as e:

        print(f"❌ LLM failed: {e}")

        return WorkerOutput(
            question=question,
            summary="LLM failed.",
            claims=[],
        )

    if not response.strip():

        return WorkerOutput(
            question=question,
            summary="Empty model response.",
            claims=[],
        )

    try:

        data = extract_json(response)

    except Exception as e:

        print(f"⚠️ JSON parse failed: {e}")

        return WorkerOutput(
            question=question,
            summary="JSON parse failed.",
            claims=[],
        )

    if not isinstance(data, dict):

        return WorkerOutput(
            question=question,
            summary="Invalid JSON structure.",
            claims=[],
        )

    claims = []

    for raw_claim in data.get("claims", []):

        if not isinstance(raw_claim, dict):
            continue

        claim = build_claim(
            raw_claim,
            source_map,
        )

        if claim:
            claims.append(claim)

    return WorkerOutput(
        question=question,
        summary=data.get("summary", ""),
        claims=claims,
    )