"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
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
    backend_cors_origins: str | list[str] = ["http://localhost:3000", "http://localhost:9501"]

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        return v

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://axonhis:changeme@localhost:5432/axonhis"
    )

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    # Security
    secret_key: str = "insecure-dev-secret-please-change"
    access_token_expire_minutes: int = 480  # 8 hours for clinical shift
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    
    # Encryption (HIPAA/ABDM)
    # Must be exactly 32 url-safe base64-encoded bytes for Fernet
    abdm_encryption_key: str = "v-X8HlY-Tbz12c3qB5x8-9zY1D7hX9oP1vB_zM0W4C8="

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # AI / Voice
    openai_api_key: str = ""
    llm_model: str = "gpt-4o"
    stt_provider: Literal["whisper", "deepgram"] = "whisper"

    # Phase 9 – Grok / Groq LLM
    grok_api_key: str = "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"
    grok_model: str = "llama-3.3-70b-versatile"
    grok_base_url: str = "https://api.groq.com/openai/v1"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
