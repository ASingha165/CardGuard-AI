"""Application configuration loaded from environment variables."""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "CardGuard AI"
    APP_VERSION: str = "4.2.0"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "sqlite:///./cardguard.db"
    API_KEY_SECRET: str = "cardguard-dev-key-change-in-prod"
    REQUIRE_AUTH: bool = False

    MAX_UPLOAD_MB: int = 10
    MAX_UPLOAD_ROWS: int = 50000

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    MODEL_DIR: str = "./data/models"
    UPLOAD_DIR: str = "./data/uploads"

    # Default ML hyperparameters
    DEFAULT_CONTAMINATION: float = 0.035
    DEFAULT_XGB_THRESHOLD: float = 0.50
    RANDOM_STATE: int = 42

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    def ensure_dirs(self) -> None:
        Path(self.MODEL_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
