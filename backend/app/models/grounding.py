"""
Grounding Specialist — referring expression detection.
Corresponds to BigEarthNet.txt referring expression detection task category.
In Demo Mode: returns deterministic scenario bounding boxes only when matched.
In Real Mode: requires a model with actual spatial localization capability.
"""
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models.base import BaseSpecialistModel, ModelInfo, ModelCapabilities, ModelOutput

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


class GroundingModel(BaseSpecialistModel):
    """Referring expression detection / spatial grounding specialist."""

    def __init__(self, mode: str = "demo", checkpoint_path: str = ""):
        self._mode = mode
        self._checkpoint_path = checkpoint_path

    @property
    def model_info(self) -> ModelInfo:
        has_real_checkpoint = bool(self._mode == "real" and self._checkpoint_path)
        if self._mode == "demo":
            encoder = "demo-encoder"
            training_status = "demo"
            checkpoint = "demo-scenario"
            provenance = "Deterministic demo scenario output (not model inference)"
            grounding_supported = True
            tasks = ["grounding"]
        elif has_real_checkpoint:
            encoder = "RemoteCLIP"
            training_status = "pretrained"
            checkpoint = self._checkpoint_path
            provenance = "Real spatial grounding inference"
            grounding_supported = True
            tasks = ["grounding"]
        else:
            encoder = "generic-fallback"
            training_status = "pretrained"
            checkpoint = settings.CLIP_FALLBACK_HF_ID
            provenance = "Generic fallback — not a remote-sensing grounding specialist"
            grounding_supported = False
            tasks = ["image-text-similarity"]

        return ModelInfo(
            name="Grounding Specialist",
            checkpoint=checkpoint,
            model_mode=self._mode,
            encoder=encoder,
            training_status=training_status,
            capabilities=ModelCapabilities(
                tasks=tasks,
                accepts_modalities=["optical", "unknown"],
                requires_temporal_pair=False,
                grounding_supported=grounding_supported,
                counting_supported=False,
                min_bands=1,
                max_bands=13,
                preferred_gsd_min_m=None,
                preferred_gsd_max_m=30.0,
            ),
            inference_provenance=provenance,
        )

    def run_inference(
        self,
        image_paths: list[str],
        query: str,
        task_type: str,
        subtasks: list[dict],
        mode: str,
        scenario_data: Optional[dict] = None,
    ) -> ModelOutput:
        if mode == "demo":
            if not scenario_data:
                return ModelOutput(
                    answer=None,
                    model_confidence=None,
                    evidence=[],
                    grounding_supported=False,
                    counting_result=None,
                    subtask_outputs=[],
                    raw_output={"error": "No matching Demo Scenario is available for this query/input combination.", "supported": False},
                )
            return ModelOutput(
                answer=scenario_data["answer"],
                model_confidence=scenario_data.get("model_confidence"),
                evidence=scenario_data.get("evidence", []),
                grounding_supported=True,
                counting_result=scenario_data.get("counting_result"),
                subtask_outputs=[],
                raw_output=scenario_data,
            )
        return self._run_real(image_paths, query)

    def _run_real(self, image_paths: list[str], query: str) -> ModelOutput:
        """Honest stub — real grounding requires loaded checkpoint with spatial output."""
        enc = "RemoteCLIP" if self._checkpoint_path else "generic-fallback"
        return ModelOutput(
            answer=None,
            model_confidence=None,
            evidence=[],
            grounding_supported=False,
            counting_result=None,
            subtask_outputs=[],
            raw_output={
                "error": f"Spatial grounding is unsupported by the loaded {enc} checkpoint. Set a dedicated GROUNDING_MODEL_PATH.",
                "supported": False,
            },
        )
