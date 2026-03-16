"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: Literal["development", "staging", "production"] = "development"
    backend_cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://axonhis:changeme@localhost:5432/axonhis"
    )

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    # Security
    secret_key: str = "insecure-dev-secret-please-change"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # AI / Voice
    openai_api_key: str = ""
    llm_model: str = "gpt-4o"
    stt_provider: Literal["whisper", "deepgram"] = "whisper"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
