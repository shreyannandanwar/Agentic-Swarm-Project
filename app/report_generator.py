# app/report_generator.py
"""Final report synthesis with optimized prompts."""

from app.llm import generate
from app.schemas import ResearchFinding, Claim


REPORT_PROMPT = """Synthesize into a decision report.

Question: {query}

Findings:
{findings}

Format:
# Executive Summary (2-3 sentences, clear verdict)
# Key Findings (bullets with citations [n])
# Analysis (tradeoffs, conflicts noted if any)
# Recommendation (actionable, specific)

Sources:
{bibliography}"""


def _classify_strength(claim: Claim) -> str:
    """Classify claim strength based on evidence quality."""
    if not claim.evidence:
        return "weak"
    
    sources = len(set(str(e.url) for e in claim.evidence))
    from app.search import SourceTier
    has_official = any(e.tier == SourceTier.OFFICIAL for e in claim.evidence)
    
    if sources >= 2 and has_official:
        return "strong"
    elif sources >= 2 or has_official:
        return "moderate"
    else:
        return "weak"


def generate_report(query: str, findings: list[ResearchFinding]) -> str:
    """Generate final report from structured findings."""

    # Build unified source numbering
    url_to_num = {}
    num = 1
    for finding in findings:
        for claim in finding.claims:
            for ev in claim.evidence:
                url = str(ev.url)
                if url and url not in url_to_num:
                    url_to_num[url] = num
                    num += 1

    # Build claims text with citations and strength tags
    claims_lines = []
    for finding in findings:
        for claim in finding.claims:
            cite_nums = [f"[{url_to_num[str(ev.url)]}]" for ev in claim.evidence if str(ev.url) in url_to_num]
            citation = " ".join(cite_nums) if cite_nums else "[?]"
            strength = _classify_strength(claim)
            claims_lines.append(
                f"- {claim.statement} (confidence={claim.confidence:.2f}, strength={strength}) {citation}"
            )

    claims_text = "\n".join(claims_lines)

    # Build bibliography
    bibliography = "\n".join(
        f"[{n}] {url}"
        for url, n in sorted(url_to_num.items(), key=lambda x: x[1])
    )

    # Count conflicts for prompt context
    conflict_count = sum(len(f.conflicts) for f in findings)

    prompt = REPORT_PROMPT.format(
        query=query,
        findings=claims_text,
        bibliography=bibliography,
    )

    # Add conflict note if present (kept concise)
    if conflict_count > 0:
        prompt += f"\n\nNote: {conflict_count} conflict(s) detected. Address in Analysis."

    return generate(prompt, model="deep", max_tokens=2048)