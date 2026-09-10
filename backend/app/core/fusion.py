"""
Heuristic confidence estimator and evidence provenance builder.
Formula (from spec):
  final_confidence = 0.25 * query_confidence
                   + 0.20 * compatibility_score
                   + 0.35 * model_confidence
                   + 0.20 * evidence_consistency

All values must come from actual pipeline outputs — never fabricated.
"""
from dataclasses import dataclass
from typing import Optional


CONFIDENCE_LABEL = "Estimated confidence (heuristic, uncalibrated)"
WARNING_CAP = 0.60


@dataclass
class HeuristicConfidence:
    query_confidence: float
    compatibility_score: float      # 1.0 | 0.6 | 0.0
    model_confidence: Optional[float]   # None if unavailable
    evidence_consistency: Optional[float]  # None if unavailable
    final_confidence: float
    capped: bool
    cap_reason: Optional[str]
    label: str = CONFIDENCE_LABEL

    def to_dict(self) -> dict:
        return {
            "query_confidence": self.query_confidence,
            "compatibility_score": self.compatibility_score,
            "model_confidence": self.model_confidence,
            "evidence_consistency": self.evidence_consistency,
            "final_confidence": self.final_confidence,
            "capped": self.capped,
            "cap_reason": self.cap_reason,
            "label": self.label,
        }


def compute_confidence(
    query_confidence: float,
    compatibility_score: float,
    model_confidence: Optional[float],
    evidence_consistency: Optional[float],
    compatibility_warning: bool = False,
    warning_reason: Optional[str] = None,
) -> HeuristicConfidence:
    """
    Compute heuristic confidence from actual pipeline outputs.
    If model_confidence or evidence_consistency is None (unavailable),
    use 0.5 as a neutral placeholder but mark it as such in the result.
    """
    mc = model_confidence if model_confidence is not None else 0.5
    ec = evidence_consistency if evidence_consistency is not None else 0.5

    raw = (
        0.25 * query_confidence
        + 0.20 * compatibility_score
        + 0.35 * mc
        + 0.20 * ec
    )
    raw = round(min(1.0, max(0.0, raw)), 4)

    capped = False
    cap_reason = None
    if compatibility_warning and raw > WARNING_CAP:
        raw = WARNING_CAP
        capped = True
        cap_reason = warning_reason or "Compatibility warning: confidence capped at 60%"

    return HeuristicConfidence(
        query_confidence=round(query_confidence, 4),
        compatibility_score=round(compatibility_score, 4),
        model_confidence=round(model_confidence, 4) if model_confidence is not None else None,
        evidence_consistency=round(evidence_consistency, 4) if evidence_consistency is not None else None,
        final_confidence=raw,
        capped=capped,
        cap_reason=cap_reason,
    )
