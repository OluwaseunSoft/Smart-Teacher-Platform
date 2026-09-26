from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # AI providers
    LLM_PROVIDER: str = "ollama"
    EMBEDDING_PROVIDER: str = "ollama"
    LLM_MODEL: str = ""
    EMBEDDING_MODEL: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # App
    DATABASE_URL: str = "sqlite:///./suhail.db"
    CORS_ORIGINS: str = "http://localhost:5173"
    RETRIEVAL_TOP_K: int = 5
    MAX_UPLOAD_MB: int = 20

    # Auth
    AUTH_SECRET_KEY: str = "dev-insecure-change-me-please-set-a-real-secret"
    AUTH_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    RESET_TOKEN_EXPIRE_MINUTES: int = 30
    AUTH_EXPOSE_RESET_TOKEN: bool = True
    DEFAULT_ADMIN_EMAIL: str = ""
    DEFAULT_ADMIN_PASSWORD: str = ""

    # Demo/seed data (see app/seed.py)
    SEED_DEMO_STUDENT_EMAIL: str = "student@suhail.demo"
    SEED_DEMO_STUDENT_PASSWORD: str = "password123"
    SEED_DEMO_ADMIN_EMAIL: str = "admin@suhail.demo"
    SEED_DEMO_ADMIN_PASSWORD: str = "password123"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
