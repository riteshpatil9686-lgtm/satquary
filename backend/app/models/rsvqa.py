"""
RS-VQA Specialist — handles binary VQA, MCQ, and captioning tasks.
Corresponds to BigEarthNet.txt task categories: binary VQA, MCQ, captioning.
Demo Mode: returns deterministic scenario output only when matched.
Real Mode: loads checkpoint via model registry and runs inference honestly.
"""
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models.base import BaseSpecialistModel, ModelInfo, ModelCapabilities, ModelOutput

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


class RSVQAModel(BaseSpecialistModel):
    """RS Visual Question Answering specialist."""

    def __init__(self, mode: str = "demo", checkpoint_path: str = ""):
        self._mode = mode
        self._checkpoint_path = checkpoint_path
        self._loaded = False

    @property
    def model_info(self) -> ModelInfo:
        if self._mode == "real" and self._checkpoint_path:
            encoder = "RemoteCLIP"
            training_status = "pretrained"
            checkpoint = self._checkpoint_path
            inference_provenance = "Real inference via RemoteCLIP ViT-B/32 encoder"
            tasks = ["image-text-retrieval", "zero-shot-classification"]
        elif self._mode == "real":
            encoder = "generic-fallback"
            training_status = "pretrained"
            checkpoint = settings.CLIP_FALLBACK_HF_ID
            inference_provenance = "Generic zero-shot CLIP fallback — not a remote-sensing VQA specialist"
            tasks = ["image-text-similarity"]
        else:
            encoder = "demo-encoder"
            training_status = "demo"
            checkpoint = "demo-scenario"
            inference_provenance = "Deterministic demo scenario output (not model inference)"
            tasks = ["rs-vqa-binary", "rs-vqa-mcq", "captioning"]

        return ModelInfo(
            name="RS-VQA Specialist",
            checkpoint=checkpoint,
            model_mode=self._mode,
            encoder=encoder,
            training_status=training_status,
            capabilities=ModelCapabilities(
                tasks=tasks,
                accepts_modalities=["optical", "unknown"],
                requires_temporal_pair=False,
                grounding_supported=False,  # VQA provides text answers, not spatial localisation
                counting_supported=False,
                min_bands=1,
                max_bands=13,
                preferred_gsd_min_m=None,
                preferred_gsd_max_m=100.0,
            ),
            inference_provenance=inference_provenance,
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
                grounding_supported=scenario_data.get("grounding_supported", False),
                counting_result=scenario_data.get("counting_result"),
                subtask_outputs=[],
                raw_output=scenario_data,
            )
        return self._run_real(image_paths, query, task_type)

    def _run_real(self, image_paths: list[str], query: str, task_type: str) -> ModelOutput:
        """Real model inference — honest reporting when task unsupported by checkpoint."""
        enc = "RemoteCLIP" if self._checkpoint_path else "generic-fallback"
        return ModelOutput(
            answer=None,
            model_confidence=None,
            evidence=[],
            grounding_supported=False,
            counting_result=None,
            subtask_outputs=[],
            raw_output={
                "error": f"Task '{task_type}' is unsupported by the loaded {enc} encoder checkpoint. Model lacks generative VQA head.",
                "supported": False,
            },
        )
