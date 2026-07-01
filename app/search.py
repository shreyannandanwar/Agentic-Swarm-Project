# app/search.py
"""Web search with source quality ranking and filtering."""

import os
from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient

from app.schemas import SourceTier

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@dataclass
class RankedSource:
    """A search result with quality metadata."""
    title: str
    url: str
    content: str
    tier: SourceTier
    score: float


# Domain authority database — extend as needed
DOMAIN_TIERS: dict[str, SourceTier] = {
    # OFFICIAL
    "github.com": SourceTier.OFFICIAL,
    "docs.python.org": SourceTier.OFFICIAL,
    "python.org": SourceTier.OFFICIAL,
    "arxiv.org": SourceTier.OFFICIAL,
    "langchain-ai.github.io": SourceTier.OFFICIAL,
    "docs.crewai.com": SourceTier.OFFICIAL,
    "docs.anthropic.com": SourceTier.OFFICIAL,
    "platform.openai.com": SourceTier.OFFICIAL,
    "cloud.google.com": SourceTier.OFFICIAL,
    "aws.amazon.com": SourceTier.OFFICIAL,
    "microsoft.com": SourceTier.OFFICIAL,
    "ibm.com": SourceTier.OFFICIAL,
    
    # ESTABLISHED
    "medium.com": SourceTier.ESTABLISHED,
    "dev.to": SourceTier.ESTABLISHED,
    "stackoverflow.com": SourceTier.ESTABLISHED,
    "zenml.io": SourceTier.ESTABLISHED,
    "towardsai.net": SourceTier.ESTABLISHED,
    "pub.towardsai.net": SourceTier.ESTABLISHED,
    "myengineeringpath.dev": SourceTier.ESTABLISHED,
    "automely.ai": SourceTier.ESTABLISHED,
    "aimec.io": SourceTier.ESTABLISHED,
    "thinking.inc": SourceTier.ESTABLISHED,
    "maritime.sh": SourceTier.ESTABLISHED,
    "kalviumlabs.ai": SourceTier.ESTABLISHED,
    "datacamp.com": SourceTier.ESTABLISHED,
    "freecodecamp.org": SourceTier.ESTABLISHED,
    
    # LOW
    "linkedin.com": SourceTier.LOW,
    "youtube.com": SourceTier.LOW,
    "reddit.com": SourceTier.LOW,
    "quora.com": SourceTier.LOW,
    "geeksforgeeks.org": SourceTier.LOW,
    "pinterest.com": SourceTier.LOW,
    "substack.com": SourceTier.LOW,
    "slideshare.net": SourceTier.LOW,
    "twitter.com": SourceTier.LOW,
    "x.com": SourceTier.LOW,
}


def get_source_tier(url: str) -> SourceTier:
    """Determine authority tier for a URL."""
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        # Check parent domains (e.g., docs.example.com -> example.com)
        parts = domain.split(".")
        for i in range(len(parts)):
            check = ".".join(parts[i:])
            if check in DOMAIN_TIERS:
                return DOMAIN_TIERS[check]
        return SourceTier.LOW
    except Exception:
        return SourceTier.LOW


def rank_and_filter_sources(
    raw_results: List[dict],
    min_tier: SourceTier = SourceTier.LOW,
    max_results: int = 3,
) -> List[RankedSource]:
    """
    Score sources by authority + content quality.
    Returns top N after filtering out blocked/low-tier sources.
    """
    ranked: List[RankedSource] = []

    for r in raw_results:
        url = r.get("url", "")
        tier = get_source_tier(url)

        if tier < min_tier:
            continue

        content = r.get("content", "")
        # Content quality bonus: longer, substantive content scores higher
        content_bonus = min(len(content) / 2000, 5.0)

        score = tier * 10 + content_bonus

        ranked.append(RankedSource(
            title=r.get("title", ""),
            url=url,
            content=content,
            tier=tier,
            score=score,
        ))

    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked[:max_results]


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search Tavily, rank by quality, return top sources."""
    response = client.search(
        query=query,
        max_results=max_results * 3,  # Fetch extra for filtering
        search_depth="advanced",
    )

    raw = response.get("results", [])
    ranked = rank_and_filter_sources(raw, max_results=max_results)

    # Log tier breakdown
    tier_counts = {}
    for r in ranked:
        tier_counts[r.tier.name] = tier_counts.get(r.tier.name, 0) + 1
    print(f"   📊 Source tiers: {tier_counts}")

    # Return top max_results as plain dicts for backward compatibility
    return [
        {"title": r.title, "url": r.url, "content": r.content}
        for r in ranked[:max_results]
    ]