from app.schemas import Evidence
from app.search import SourceTier


TIER_SCORE = {
    SourceTier.BLOCKED: 0.0,
    SourceTier.LOW: 0.35,
    SourceTier.ESTABLISHED: 0.70,
    SourceTier.OFFICIAL: 0.95,
}


def score(evidence: Evidence) -> float:

    return TIER_SCORE[evidence.tier]