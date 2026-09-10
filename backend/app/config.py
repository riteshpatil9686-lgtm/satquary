import os
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    MODE: Literal["demo", "real"] = "demo"
    DEVICE: Literal["auto", "cuda", "cpu"] = "auto"
    PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    MAX_UPLOAD_SIZE_MB: int = 50
    QUERY_CONFIDENCE_THRESHOLD: float = 0.6

    # Real Mode model paths (empty = demo mode)
    RS_VQA_MODEL_PATH: str = ""
    GROUNDING_MODEL_PATH: str = ""
    CHANGE_VQA_MODEL_PATH: str = ""
    FUSION_MODEL_PATH: str = ""

    # Encoder HF Hub IDs
    REMOTE_CLIP_HF_ID: str = "chendelong/RemoteCLIP"
    CLIP_FALLBACK_HF_ID: str = "openai/clip-vit-base-patch32"

    # Dataset (training/eval only — not required for demo)
    BEN_TXT_DATASET_PATH: str = ""
    BEN_TXT_SPLIT: str = "benchmark"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
