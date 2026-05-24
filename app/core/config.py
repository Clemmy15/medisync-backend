from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import ConfigurationError

INSECURE_SECRET_PLACEHOLDER = "change-me-in-production-use-openssl-rand-hex-32"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "MedisyncAI"
    app_version: str = "1.0.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    database_url: str = "postgresql+asyncpg://medisync:medisync@localhost:5432/medisync"
    database_echo: bool = False

    secret_key: str = INSECURE_SECRET_PLACEHOLDER
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"

    llm_provider: Literal["openai", "gemini", "mock"] = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    chroma_persist_dir: str = "./data/chroma"
    chroma_collection: str = "medisync_memories"

    admin_email: str = "admin@medisync.ai"
    admin_password: str = "admin123!"

    enable_docs: bool = True
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 120
    rate_limit_auth_per_minute: int = 10

    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> str:
        if isinstance(value, list):
            return ",".join(value)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def validate_runtime(self) -> None:
        """Warn or fail on insecure production configuration."""
        if self.debug:
            return
        if self.secret_key == INSECURE_SECRET_PLACEHOLDER:
            raise ConfigurationError(
                "SECRET_KEY must be set to a secure value in production"
            )
        if len(self.secret_key) < 32:
            raise ConfigurationError(
                "SECRET_KEY should be at least 32 characters in production"
            )
        if "*" in self.cors_origin_list:
            raise ConfigurationError(
                "CORS_ORIGINS must not use wildcard in production"
            )
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self.llm_provider == "gemini" and not self.gemini_api_key:
            raise ConfigurationError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        if self.admin_password in ("admin123!", "changeme", "password"):
            raise ConfigurationError(
                "ADMIN_PASSWORD must be changed from default in production"
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
