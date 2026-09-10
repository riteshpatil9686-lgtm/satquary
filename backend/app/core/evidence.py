"""
Evidence provenance builder.
Enforces the no-fabrication rule at creation time:
  - Real Mode: only model output coordinates are accepted
  - Demo Mode: only scenario-defined evidence is accepted
  - Spatial grounding unavailable: returns [], never fabricated boxes
"""
from dataclasses import dataclass
from typing import Optional
import uuid


VALID_PROVENANCES = {"real-specialist-model", "demo-scenario", "derived-computation"}


@dataclass
class EvidenceItem:
    id: str
    type: str           # "bounding_box" | "mask" | "point" | "text" | "none"
    provenance: str     # "real-specialist-model" | "demo-scenario" | "derived-computation"
    coordinates: Optional[list]   # [x1,y1,x2,y2] for bounding_box; [x,y] for point
    label: Optional[str]
    roi_confidence: Optional[float]  # from model's localization score; None if unavailable

    def __post_init__(self):
        assert self.provenance in VALID_PROVENANCES, (
            f"Invalid evidence provenance '{self.provenance}'. "
            f"Must be one of: {VALID_PROVENANCES}"
        )
        if self.type == "bounding_box" and self.coordinates:
            assert len(self.coordinates) == 4, (
                "Bounding box coordinates must be [x1, y1, x2, y2]"
            )
        # roi_confidence must come from the model — not invented
        if self.roi_confidence is not None:
            assert 0.0 <= self.roi_confidence <= 1.0, "roi_confidence must be in [0, 1]"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "provenance": self.provenance,
            "coordinates": self.coordinates,
            "label": self.label,
            "roi_confidence": self.roi_confidence,
        }


def build_demo_evidence(scenario_evidence: list[dict]) -> list[EvidenceItem]:
    """Build evidence list from a deterministic demo scenario definition."""
    items = []
    for e in scenario_evidence:
        items.append(EvidenceItem(
            id=e.get("id", str(uuid.uuid4())),
            type=e["type"],
            provenance="demo-scenario",
            coordinates=e.get("coordinates"),
            label=e.get("label"),
            roi_confidence=None,  # Demo scenarios never claim model confidence for localization
        ))
    return items


def build_real_evidence(model_detections: list[dict]) -> list[EvidenceItem]:
    """
    Build evidence from actual model output.
    model_detections must come from the model's actual inference output.
    This function REJECTS any entry without a real model_output_id.
    """
    items = []
    for det in model_detections:
        if not det.get("from_model_inference", False):
            raise ValueError(
                "Real Mode evidence must originate from model inference. "
                "Set 'from_model_inference': True in the detection dict."
            )
        items.append(EvidenceItem(
            id=det.get("id", str(uuid.uuid4())),
            type=det.get("type", "bounding_box"),
            provenance="real-specialist-model",
            coordinates=det.get("coordinates"),
            label=det.get("label"),
            roi_confidence=det.get("roi_confidence"),
        ))
    return items


def no_spatial_evidence_available() -> list[EvidenceItem]:
    """
    Explicitly return empty evidence with a sentinel item for the frontend.
    Frontend renders LimitationNotice when it receives this.
    """
    return []
