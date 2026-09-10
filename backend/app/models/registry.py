"""
Model Registry — declares all specialist models and their capabilities.
The registry selects the best model for a given task type and input constraints.
Future fine-tuned models plug in here without modifying the pipeline.
"""
from app.config import settings
from app.models.base import BaseSpecialistModel
from app.models.rsvqa import RSVQAModel
from app.models.grounding import GroundingModel
from app.models.change_vqa import ChangeVQAModel
from app.models.fusion_model import OpticalSARFusionModel


class ModelRegistry:
    """
    Central registry of all registered specialist models.
    Models are instantiated at startup and selected by the controller.
    """

    def __init__(self):
        mode = settings.MODE
        self._specialists: dict[str, BaseSpecialistModel] = {
            "rsvqa": RSVQAModel(mode=mode, checkpoint_path=settings.RS_VQA_MODEL_PATH),
            "grounding": GroundingModel(mode=mode, checkpoint_path=settings.GROUNDING_MODEL_PATH),
            "change_vqa": ChangeVQAModel(mode=mode, checkpoint_path=settings.CHANGE_VQA_MODEL_PATH),
            "fusion": OpticalSARFusionModel(mode=mode, checkpoint_path=settings.FUSION_MODEL_PATH),
        }
        # Task → specialist key mapping
        self._task_routing: dict[str, str] = {
            "rs-vqa-binary": "rsvqa",
            "rs-vqa-mcq": "rsvqa",
            "captioning": "rsvqa",
            "grounding": "grounding",
            "change-vqa": "change_vqa",
            "fusion": "fusion",
        }

    def get_model_for_task(self, task_type: str) -> BaseSpecialistModel:
        """Return the registered specialist for the given task type."""
        key = self._task_routing.get(task_type)
        if not key:
            raise ValueError(f"No specialist registered for task type '{task_type}'")
        return self._specialists[key]

    def list_all(self) -> list[dict]:
        """List all registered models with their declared capabilities."""
        return [model.model_info.to_dict() for model in self._specialists.values()]

    def get_specialist_key(self, task_type: str) -> str:
        return self._task_routing.get(task_type, "rsvqa")


# Singleton — instantiated once on startup
registry = ModelRegistry()
