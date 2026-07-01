# app/schemas.py
"""Structured data models for the research pipeline."""

from pydantic import BaseModel, Field, HttpUrl
from typing import List
from enum import Enum


class SourceTier(int, Enum):
    """Authority tier for a source."""
    BLOCKED = 0
    LOW = 1
    ESTABLISHED = 2
    OFFICIAL = 3


class Evidence(BaseModel):
    """
    A single piece of evidence supporting a claim.
    Replaces the bare `sources: List[HttpUrl]` with structured provenance.
    """
    url: HttpUrl = Field(..., description="Source URL")
    title: str = Field(default="", description="Source title")
    snippet: str = Field(default="", description="Relevant text snippet from source")
    tier: SourceTier = Field(default=SourceTier.LOW, description="Authority tier")
    trust_score: float = Field(
        default=0.5,
        ge=0.0, le=1.0,
        description="Computed trust score (0-1) based on domain authority"
    )

    def __hash__(self):
        return hash(str(self.url))

    def __eq__(self, other):
        if isinstance(other, Evidence):
            return str(self.url) == str(other.url)
        return False


class Claim(BaseModel):
    """A single factual statement extracted during research."""
    id: str = Field(default="")
    statement: str = Field(..., description="The factual statement")
    evidence: List[Evidence] = Field(
        default_factory=list,
        description="Structured evidence supporting this claim"
    )
    is_quantified: bool = Field(default=False)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @property
    def sources(self) -> List[str]:
        """Backward-compat: return list of URLs."""
        return [str(e.url) for e in self.evidence]


class Conflict(BaseModel):
    """A contradiction or disagreement between sources."""
    topic: str = Field(..., description="Subject of the conflict")
    conflicting_claim_ids: List[str] = Field(default_factory=list)
    explanation: str = Field(..., description="Description of disagreement")
    severity: str = Field(default="minor", description="minor|moderate|severe")


class ResearchFinding(BaseModel):
    """The structured output summarizing a research area."""
    question: str = Field(..., description="The research question")
    summary: str = Field(..., description="Cohesive summary")
    claims: List[Claim] = Field(default_factory=list)
    conflicts: List[Conflict] = Field(default_factory=list)
    overall_confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class WorkerOutput(BaseModel):
    """Output from a single research worker."""
    question: str = Field(..., description="Sub-question researched")
    summary: str = Field(..., description="Summary of findings")
    claims: List[Claim] = Field(default_factory=list)