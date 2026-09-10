"""
BigEarthNet.txt Parser — all 4 annotation categories.
═══════════════════════════════════════════════════════

IMPORTANT PROVENANCE NOTE:
  Bounding boxes parsed here originate from CLC 2018 pixel-level reference maps.
  They are TRAINING TARGETS ONLY. This parser is used exclusively by the dataset
  layer for training/evaluation — NEVER by the backend inference pipeline.
  Any use of parsed bounding boxes as inference results would violate evidence integrity.

Annotation categories (from arXiv:2603.29630):
  1. Binary VQA         — yes/no questions about LULC presence/count/size/adjacency
  2. MCQ VQA            — multiple-choice: country, season, climate, land cover type
  3. Captioning         — LLM-augmented, template-grounded LULC descriptions
  4. Referring Expr Det — "ground" a referring expression to a CLC-derived bounding box
"""
import json
import csv
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Iterator, Any
from dataset.config import BigEarthNetTxtConfig


@dataclass
class BinaryVQASample:
    sample_id: str
    image_path: str           # path to S1 or S2 patch
    question: str
    answer: str               # "yes" | "no"
    modality: str             # "S1" | "S2" | "S1+S2"
    clc_labels: list[str]
    provenance: str = "bigearth-net-txt-binary-vqa"


@dataclass
class MCQVQASample:
    sample_id: str
    image_path: str
    question: str
    answer: str
    choices: list[str]
    category: str             # "country" | "season" | "climate" | "lulc"
    modality: str
    clc_labels: list[str]
    provenance: str = "bigearth-net-txt-mcq-vqa"


@dataclass
class CaptioningSample:
    sample_id: str
    image_path: str
    caption: str              # LLM-augmented LULC-grounded caption
    template_caption: str     # Template-based base caption (before LLM augmentation)
    modality: str
    clc_labels: list[str]
    provenance: str = "bigearth-net-txt-captioning"


@dataclass
class GroundingSample:
    sample_id: str
    image_path: str
    expression: str           # Referring expression (e.g. "the forest region in the top left")
    bbox: list[int]           # [x1, y1, x2, y2] — CLC 2018 reference source
    label: str                # CLC class name
    modality: str
    clc_labels: list[str]
    # CRITICAL: This bbox comes from CLC 2018 pixel-level LULC reference maps.
    # It is a training target, NOT a model-generated detection.
    bbox_provenance: str = "CLC-2018-LULC-reference-map"
    task_provenance: str = "bigearth-net-txt-referring-expression-detection"


class BigEarthNetTxtParser:
    """
    Parser for all 4 BigEarthNet.txt annotation categories.
    Reads from the dataset directory structure expected by the benchmark.

    DECOUPLING GUARANTEE: This class must NEVER be imported by any backend
    inference module. It is a training/evaluation utility only.
    """

    def __init__(self, config: Optional[BigEarthNetTxtConfig] = None):
        self.config = config or BigEarthNetTxtConfig()
        self.config.validate()
        self.root = Path(self.config.dataset_root)

    def _annotation_path(self, filename: str) -> Path:
        """Resolve annotation file relative to dataset root."""
        path = self.root / "annotations" / filename
        if not path.exists():
            path = self.root / filename
        return path

    def iter_binary_vqa(self) -> Iterator[BinaryVQASample]:
        """Iterate over binary VQA samples."""
        ann_file = self._annotation_path("binary_vqa.json")
        if not ann_file.exists():
            raise FileNotFoundError(f"Binary VQA annotations not found: {ann_file}")
        with open(ann_file) as f:
            data = json.load(f)
        for item in data:
            yield BinaryVQASample(
                sample_id=str(item["id"]),
                image_path=str(self.root / item["image"]),
                question=item["question"],
                answer=item["answer"],
                modality=item.get("modality", "S2"),
                clc_labels=item.get("clc_labels", []),
            )

    def iter_mcq_vqa(self) -> Iterator[MCQVQASample]:
        """Iterate over MCQ VQA samples."""
        ann_file = self._annotation_path("mcq_vqa.json")
        if not ann_file.exists():
            raise FileNotFoundError(f"MCQ VQA annotations not found: {ann_file}")
        with open(ann_file) as f:
            data = json.load(f)
        for item in data:
            yield MCQVQASample(
                sample_id=str(item["id"]),
                image_path=str(self.root / item["image"]),
                question=item["question"],
                answer=item["answer"],
                choices=item.get("choices", []),
                category=item.get("category", "lulc"),
                modality=item.get("modality", "S2"),
                clc_labels=item.get("clc_labels", []),
            )

    def iter_captioning(self) -> Iterator[CaptioningSample]:
        """Iterate over captioning samples."""
        ann_file = self._annotation_path("captioning.json")
        if not ann_file.exists():
            raise FileNotFoundError(f"Captioning annotations not found: {ann_file}")
        with open(ann_file) as f:
            data = json.load(f)
        for item in data:
            yield CaptioningSample(
                sample_id=str(item["id"]),
                image_path=str(self.root / item["image"]),
                caption=item.get("caption", ""),
                template_caption=item.get("template_caption", ""),
                modality=item.get("modality", "S2"),
                clc_labels=item.get("clc_labels", []),
            )

    def iter_grounding(self) -> Iterator[GroundingSample]:
        """
        Iterate over referring expression detection samples.
        BBOX PROVENANCE: All bounding boxes come from CLC 2018 reference maps.
        These are ground-truth training targets — NOT model outputs.
        """
        ann_file = self._annotation_path("grounding.json")
        if not ann_file.exists():
            raise FileNotFoundError(f"Grounding annotations not found: {ann_file}")
        with open(ann_file) as f:
            data = json.load(f)
        for item in data:
            yield GroundingSample(
                sample_id=str(item["id"]),
                image_path=str(self.root / item["image"]),
                expression=item["expression"],
                bbox=item["bbox"],        # [x1,y1,x2,y2] — CLC 2018 source
                label=item.get("label", ""),
                modality=item.get("modality", "S2"),
                clc_labels=item.get("clc_labels", []),
            )

    def count_all(self) -> dict[str, int]:
        """Count samples in each category."""
        counts = {}
        for task, method in [
            ("binary_vqa", self.iter_binary_vqa),
            ("mcq_vqa", self.iter_mcq_vqa),
            ("captioning", self.iter_captioning),
            ("grounding", self.iter_grounding),
        ]:
            try:
                counts[task] = sum(1 for _ in method())
            except FileNotFoundError:
                counts[task] = 0
        return counts
