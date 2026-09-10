"""
BigEarthNet.txt Dataset Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMPLETELY DECOUPLED from backend inference. This package is a standalone
training/evaluation library for the BigEarthNet.txt benchmark.

License: CDLA-Permissive 1.0
Paper:   arXiv:2603.29630
Source:  https://huggingface.co/datasets/BIFOLD-BigEarthNetv2-0/BigEarthNet.txt

── Dataset Configuration ──────────────────────────────────────────────────────
"""

from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class BigEarthNetTxtConfig:
    """Central configuration for the BigEarthNet.txt dataset loader."""

    # Path to the dataset root (set via BEN_TXT_DATASET_PATH env var)
    dataset_root: str = field(default_factory=lambda: os.environ.get("BEN_TXT_DATASET_PATH", ""))

    # Split: "benchmark" (standard) | "full" | custom
    split: str = field(default_factory=lambda: os.environ.get("BEN_TXT_SPLIT", "benchmark"))

    # Annotation task types supported by the dataset
    TASK_TYPES: tuple = (
        "rs-vqa-binary",      # Binary yes/no VQA
        "rs-vqa-mcq",         # Multiple-choice VQA
        "captioning",         # LLM-augmented LULC captions
        "grounding",          # Referring expression detection (CLC bbox source)
    )

    # BigEarthNet.txt modality
    MODALITIES: tuple = ("S1", "S2", "S1+S2")

    # CLC class vocabulary (abbreviated — full list in BigEarthNet paper)
    CLC_CLASSES: tuple = (
        "Continuous urban fabric",
        "Discontinuous urban fabric",
        "Industrial or commercial units",
        "Arable land",
        "Permanently irrigated land",
        "Rice fields",
        "Vineyards",
        "Fruit trees and berry plantations",
        "Olive groves",
        "Pastures",
        "Complex cultivation patterns",
        "Land principally occupied by agriculture, with areas of natural vegetation",
        "Agro-forestry areas",
        "Broad-leaved forest",
        "Coniferous forest",
        "Mixed forest",
        "Natural grasslands",
        "Moors and heathland",
        "Transitional woodland-shrub",
        "Beaches, dunes, sands",
        "Inland marshes",
        "Peat bogs",
        "Salt marshes",
        "Water bodies",
        "Water courses",
        "Sea and ocean",
    )

    # IMPORTANT: Bounding boxes in BigEarthNet.txt are derived from CLC 2018 reference maps.
    # They are GROUND-TRUTH ANNOTATIONS for training — not inference outputs.
    # The backend inference pipeline must NEVER expose these as its own detections.
    BBOX_PROVENANCE_NOTE: str = (
        "Bounding boxes in BigEarthNet.txt originate from CLC 2018 pixel-level "
        "LULC reference maps (Corine Land Cover). They are ground-truth training targets "
        "and must NEVER be exposed as model-generated detections in inference results."
    )

    def validate(self) -> None:
        if not self.dataset_root:
            raise ValueError(
                "BEN_TXT_DATASET_PATH is not set. "
                "Download the dataset with: huggingface-cli download BIFOLD-BigEarthNetv2-0/BigEarthNet.txt"
            )
        root = Path(self.dataset_root)
        if not root.exists():
            raise FileNotFoundError(f"Dataset root not found: {root}")
