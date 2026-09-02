"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.paths import ENV_FILE


class Settings(BaseSettings):
    """Runtime settings for the Shared Persona Core service."""

    app_name: str = "Shared Persona Core"
    app_version: str = "0.1.0"
    environment: str = "development"
    access_password: str = "persona-core"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    world_id: str = "shared_world"
    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_history_limit: int = Field(default=20, ge=1, le=100)
    api_base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
