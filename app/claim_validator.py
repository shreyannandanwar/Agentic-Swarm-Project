#app/claim_validator.py
"""
Claim validation and construction.

Responsibilities:
- Validate URLs
- Build Evidence objects
- Remove duplicate evidence
- Construct Claim objects

No confidence scoring.
No source ranking.
"""

import uuid
from typing import List

from app.schemas import (
    Claim,
    Evidence,
)
from app.search import get_source_tier


def _normalize_url(url: str) -> str:
    """Normalize URLs for matching."""

    return url.strip().rstrip("/")


def _build_evidence(
    urls: List[str],
    source_map: dict,
) -> List[Evidence]:

    evidence = []
    seen = set()

    for url in urls:

        if not isinstance(url, str):
            continue

        url = _normalize_url(url)

        if not url.startswith(("http://", "https://")):
            continue

        if url in seen:
            continue

        seen.add(url)

        meta = (
            source_map.get(url)
            or source_map.get(url.rstrip("/"))
            or source_map.get(url + "/")
            or {}
        )

        evidence.append(
            Evidence(
                url=url,
                title=meta.get("title", ""),
                snippet=meta.get("content", "")[:300],
                tier=get_source_tier(url),

                # temporary placeholder
                # Analyst will compute this later.
                trust_score=0.5,
            )
        )

    return evidence


def build_claim(
    raw_claim: dict,
    source_map: dict,
) -> Claim | None:

    if not isinstance(raw_claim, dict):
        return None

    statement = raw_claim.get("statement", "").strip()

    if not statement:
        return None

    urls = raw_claim.get("sources", [])

    if not isinstance(urls, list):
        urls = []

    evidence = _build_evidence(
        urls,
        source_map,
    )

    if not evidence:
        return None

    return Claim(
        id=str(uuid.uuid4())[:8],
        statement=statement,

        evidence=evidence,

        # temporary baseline
        confidence=0.5,

        is_quantified=raw_claim.get(
            "is_quantified",
            False,
        ),
    )