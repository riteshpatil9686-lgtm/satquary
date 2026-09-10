"""
Change-VQA Specialist — bi-temporal change analysis.
"""
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models.base import BaseSpecialistModel, ModelInfo, ModelCapabilities, ModelOutput

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


class ChangeVQAModel(BaseSpecialistModel):

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
            provenance = "Deterministic demo scenario"
            grounding_supported = True
            requires_temporal = True
            tasks = ["change-vqa"]
        elif has_real_checkpoint:
            encoder = "RemoteCLIP"
            training_status = "pretrained"
            checkpoint = self._checkpoint_path
            provenance = "Bi-temporal change detection inference"
            grounding_supported = True
            requires_temporal = True
            tasks = ["change-vqa"]
        else:
            encoder = "generic-fallback"
            training_status = "pretrained"
            checkpoint = settings.CLIP_FALLBACK_HF_ID
            provenance = "Generic fallback — not a temporal change detection specialist"
            grounding_supported = False
            requires_temporal = False
            tasks = ["image-text-similarity"]

        return ModelInfo(
            name="Change-VQA Specialist",
            checkpoint=checkpoint,
            model_mode=self._mode,
            encoder=encoder,
            training_status=training_status,
            capabilities=ModelCapabilities(
                tasks=tasks,
                accepts_modalities=["optical", "unknown"],
                requires_temporal_pair=requires_temporal,
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
        enc = "RemoteCLIP" if self._checkpoint_path else "generic-fallback"
        return ModelOutput(
            answer=None,
            model_confidence=None,
            evidence=[],
            grounding_supported=False,
            counting_result=None,
            subtask_outputs=[],
            raw_output={
                "error": f"Temporal change analysis is unsupported by the loaded {enc} checkpoint. Set CHANGE_VQA_MODEL_PATH.",
                "supported": False,
            },
        )
