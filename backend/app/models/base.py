"""
Base specialist model interface.
All specialist models must subclass BaseSpecialistModel and declare
their capabilities, encoder, training_status, and spatial grounding support.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelCapabilities:
    """Declared capabilities — must be accurate. Never claim unsupported features."""
    tasks: list[str]                 # e.g. ["rs-vqa-binary", "rs-vqa-mcq", "captioning"]
    accepts_modalities: list[str]    # ["optical", "sar"]
    requires_temporal_pair: bool
    grounding_supported: bool        # True only if model produces real spatial output
    counting_supported: bool         # True only if model has instance detection
    min_bands: int
    max_bands: int
    preferred_gsd_min_m: Optional[float]
    preferred_gsd_max_m: Optional[float]


@dataclass
class ModelInfo:
    name: str
    checkpoint: str
    model_mode: str                  # "real" | "demo"
    encoder: str                     # "RemoteCLIP" | "generic-fallback" | "demo-encoder"
    training_status: str             # "pretrained" | "fine-tuned" | "demo"
    capabilities: ModelCapabilities
    inference_provenance: str        # descriptive string of what produces the output

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "checkpoint": self.checkpoint,
            "model_mode": self.model_mode,
            "encoder": self.encoder,
            "training_status": self.training_status,
            "capabilities": {
                "tasks": self.capabilities.tasks,
                "accepts_modalities": self.capabilities.accepts_modalities,
                "requires_temporal_pair": self.capabilities.requires_temporal_pair,
                "grounding_supported": self.capabilities.grounding_supported,
                "counting_supported": self.capabilities.counting_supported,
                "min_bands": self.capabilities.min_bands,
                "max_bands": self.capabilities.max_bands,
                "preferred_gsd_min_m": self.capabilities.preferred_gsd_min_m,
                "preferred_gsd_max_m": self.capabilities.preferred_gsd_max_m,
            },
            "inference_provenance": self.inference_provenance,
            "grounding_supported": self.capabilities.grounding_supported,
        }


@dataclass
class ModelOutput:
    """
    Structured output from a specialist model.
    All fields must originate from actual inference or deterministic demo scenario.
    Never populate answer/evidence/confidence without running inference.
    """
    answer: Optional[str]
    model_confidence: Optional[float]      # from model's softmax/logit; None if unavailable
    evidence: list[dict]                   # raw detection dicts (passed to evidence.py)
    grounding_supported: bool
    counting_result: Optional[dict]        # {count: int|None, note: str}
    subtask_outputs: list[dict]            # for multi-part queries
    raw_output: Optional[dict]             # full model output for transparency


class BaseSpecialistModel(ABC):
    """
    Abstract base for all specialist models.
    Subclasses must implement run_inference() and declare info via model_info property.
    """

    @property
    @abstractmethod
    def model_info(self) -> ModelInfo:
        """Return model metadata. Must be accurate."""
        ...

    @abstractmethod
    def run_inference(
        self,
        image_paths: list[str],
        query: str,
        task_type: str,
        subtasks: list[dict],
        mode: str,   # "demo" | "real"
        scenario_id: Optional[str] = None,
    ) -> ModelOutput:
        """
        Run inference and return ModelOutput.
        In demo mode, return deterministic scenario output.
        In real mode, load checkpoint and run actual inference.
        Never fabricate output.
        """
        ...
