"""Centralized application configuration (PRD Ch4.12).

Environment variables must never be read directly inside business logic —
always import `settings` from this module instead.
"""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "change-me-in-production"
_DEV_ENVIRONMENTS = frozenset({"development", "dev", "local", "test"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # General
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+psycopg://cliniscribe:cliniscribe@localhost:5432/cliniscribe"
    redis_url: str = "redis://localhost:6379/0"

    # Auth (PRD Ch7 / Ch20)
    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    reset_token_expire_minutes: int = 15
    access_token_cookie_name: str = "access_token"
    refresh_token_cookie_name: str = "refresh_token"
    cookie_secure: bool = False  # true in production (HTTPS only, PRD Ch20)
    frontend_base_url: str = "http://localhost:3000"

    # Rate limiting (PRD Ch16.3)
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_minutes: int = 15
    password_reset_rate_limit_attempts: int = 3
    password_reset_rate_limit_window_minutes: int = 60

    # CORS
    cors_origins: str = "http://localhost:3000"

    # AI (PRD Ch3.6 / Ch17)
    stt_provider: str = "faster_whisper"
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-5"
    claude_max_retries: int = 2
    claude_timeout_seconds: float = 30.0
    whisper_model_size: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    ai_queue_key: str = "cliniscribe:ai_pipeline_queue"
    ai_stage_timeout_seconds: int = 120

    # Storage (PRD Ch3.9) — local disk in development, S3 in production.
    aws_s3_bucket: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    local_storage_dir: str = "storage"
    max_upload_size_mb: int = 10
    max_audio_upload_size_mb: int = 100

    # Email (PRD Ch3.14)
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.environment.lower() in _DEV_ENVIRONMENTS

    @model_validator(mode="after")
    def _reject_insecure_non_development_config(self) -> "Settings":
        """Refuse to start outside development with development defaults."""
        if self.is_development:
            return self
        problems = []
        if self.jwt_secret == _DEFAULT_JWT_SECRET or len(self.jwt_secret) < 32:
            problems.append("JWT_SECRET must be a random value of at least 32 characters")
        if self.debug:
            problems.append("DEBUG must be false")
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE must be true")
        if problems:
            detail = "; ".join(problems)
            raise ValueError(f"Insecure configuration for ENVIRONMENT={self.environment!r}: {detail}")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
