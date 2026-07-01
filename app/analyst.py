# app/analyst.py
"""Analyst agent: merges claims, detects conflicts, scores confidence."""

import logging
from typing import List

from app.llm import generate
from app.schemas import (
    WorkerOutput,
    ResearchFinding,
    Claim,
    Conflict,
    Evidence,
    SourceTier,
)
from app.search import get_source_tier
from app.utils import extract_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Semantic Deduplication (replaces exact string matching)
# ---------------------------------------------------------

def _jaccard_similarity(a: str, b: str) -> float:
    """Fast Jaccard similarity using word sets."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    return intersection / union if union > 0 else 0.0


def _is_semantic_duplicate(claim_a: Claim, claim_b: Claim, threshold: float = 0.75) -> bool:
    """
    Determine if two claims are semantic duplicates.
    Uses Jaccard similarity on word sets.
    Threshold 0.75 = ~75% word overlap.
    """
    sim = _jaccard_similarity(claim_a.statement, claim_b.statement)
    return sim >= threshold


def merge_claims(workers: List[WorkerOutput]) -> List[Claim]:
    """
    Merge duplicate claims across all workers using semantic similarity.
    Preserves the highest confidence and merges evidence.
    """
    merged: List[Claim] = []

    for worker in workers:
        for claim in worker.claims:
            # Try to find an existing merged claim that is semantically similar
            found_match = False
            for existing in merged:
                if _is_semantic_duplicate(claim, existing):
                    # Merge evidence (deduplicated by URL)
                    existing_urls = {str(e.url) for e in existing.evidence}
                    for ev in claim.evidence:
                        if str(ev.url) not in existing_urls:
                            existing.evidence.append(ev)
                            existing_urls.add(str(ev.url))

                    # Take highest confidence
                    existing.confidence = max(existing.confidence, claim.confidence)

                    # Quantified if either is quantified
                    existing.is_quantified = existing.is_quantified or claim.is_quantified

                    found_match = True
                    break

            if not found_match:
                merged.append(claim)

    return merged


# ---------------------------------------------------------
# Confidence Scoring v2 (tier-weighted)
# ---------------------------------------------------------

def score_confidence(claims: List[Claim], conflicts: List[Conflict]) -> float:
    """
    Evidence-based confidence scoring.
    Weights: source tier, cross-verification, quantification.
    """
    if not claims:
        return 0.0

    scores = []
    for claim in claims:
        # Base: worker-assigned confidence
        base = claim.confidence

        # Source quality multiplier (0.5 to 1.0)
        if claim.evidence:
            avg_tier = sum(e.tier.value for e in claim.evidence) / len(claim.evidence)
            tier_mult = 0.5 + (avg_tier / 6.0)  # LOW=0.67, EST=0.83, OFF=1.0
        else:
            tier_mult = 0.5

        # Cross-verification bonus: multiple independent sources
        unique_sources = len(set(str(e.url) for e in claim.evidence))
        cross_bonus = min((unique_sources - 1) * 0.05, 0.15)

        # Quantification bonus
        quant_bonus = 0.1 if claim.is_quantified else 0.0

        final = min(base * tier_mult + cross_bonus + quant_bonus, 1.0)
        scores.append(final)

    average = sum(scores) / len(scores)

    # Penalty for unresolved conflicts
    penalty = min(len(conflicts) * 0.10, 0.40)

    return round(max(average - penalty, 0.0), 2)


# ---------------------------------------------------------
# Conflict Detection v2 (agreement vs duplication vs contradiction)
# ---------------------------------------------------------

def _claims_agree(a: Claim, b: Claim) -> bool:
    """Check if two claims are semantically similar (agreement)."""
    return _jaccard_similarity(a.statement, b.statement) >= 0.65


def _claims_contradict(a: Claim, b: Claim) -> bool:
    """
    Detect contradiction: similar topic but opposite meaning.
    Heuristic: high word overlap (>0.5) but presence of negation words
    in one and not the other.
    """
    sim = _jaccard_similarity(a.statement, b.statement)
    if sim < 0.4 or sim > 0.85:
        return False  # Too different or too similar

    negation = {"not", "no", "never", "cannot", "doesn't", "isn't", "aren't",
                "won't", "wouldn't", "shouldn't", "don't", "didn't", "lack",
                "absence", "without", "fails", "broken", "limitation"}

    words_a = set(a.statement.lower().split())
    words_b = set(b.statement.lower().split())

    has_neg_a = bool(words_a & negation)
    has_neg_b = bool(words_b & negation)

    # Contradiction: one has negation, the other doesn't, on same topic
    return has_neg_a != has_neg_b


def detect_conflicts(claims: List[Claim]) -> List[Conflict]:
    """
    Distinguish agreement, duplication, and contradiction.
    Only reports actual contradictions (not duplicates or agreements).
    """
    if len(claims) < 2:
        return []

    conflicts: List[Conflict] = []
    seen_pairs = set()

    for i, claim_a in enumerate(claims):
        for j, claim_b in enumerate(claims):
            if i >= j:
                continue

            pair_key = tuple(sorted([claim_a.id, claim_b.id]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            # Skip if they're just duplicates (high similarity, same meaning)
            if _is_semantic_duplicate(claim_a, claim_b, threshold=0.80):
                continue

            # Skip if they agree (similar meaning, no negation difference)
            if _claims_agree(claim_a, claim_b) and not _claims_contradict(claim_a, claim_b):
                continue

            # Only flag actual contradictions
            if _claims_contradict(claim_a, claim_b):
                # Extract topic from overlapping words
                words_a = set(claim_a.statement.lower().split())
                words_b = set(claim_b.statement.lower().split())
                topic_words = words_a & words_b
                topic = " ".join(sorted(topic_words))[:60] if topic_words else "general"

                severity = "moderate"
                if claim_a.is_quantified and claim_b.is_quantified:
                    severity = "severe"  # Numbers disagreeing is worse

                conflicts.append(Conflict(
                    topic=topic,
                    conflicting_claim_ids=[claim_a.id, claim_b.id],
                    explanation=(
                        f"Claim A: {claim_a.statement[:100]}... "
                        f"vs Claim B: {claim_b.statement[:100]}..."
                    ),
                    severity=severity,
                ))

    return conflicts


# ---------------------------------------------------------
# Summary Generation
# ---------------------------------------------------------

def summarize(question: str, claims: List[Claim]) -> str:
    """Generate a concise summary from verified claims."""
    if not claims:
        return "No verified claims were extracted."

    bullets = "\n".join(f"- {c.statement}" for c in claims[:8])

    prompt = f"""Question: {question}

Verified Claims:
{bullets}

Write a concise 2-3 sentence summary. Do not invent facts."""

    summary = generate(prompt, model="fast", max_tokens=512)

    if not summary or not summary.strip():
        logger.warning("Summary model returned empty response.")
        return "Summary generation failed."

    return summary.strip()


# ---------------------------------------------------------
# Main Analyst Entry Point
# ---------------------------------------------------------

def analyze_findings(
    question: str,
    workers: List[WorkerOutput],
) -> ResearchFinding:
    """
    Analyze all worker outputs:
    1. Semantic deduplication of claims
    2. Conflict detection (contradictions only)
    3. Tier-weighted confidence scoring
    4. Summary generation
    """
    claims = merge_claims(workers)
    conflicts = detect_conflicts(claims)
    summary = summarize(question, claims)
    confidence = score_confidence(claims, conflicts)

    return ResearchFinding(
        question=question,
        summary=summary,
        claims=claims,
        conflicts=conflicts,
        overall_confidence=confidence,
    )