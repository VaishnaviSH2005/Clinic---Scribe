"""Centralized application configuration (PRD Ch4.12).

Environment variables must never be read directly inside business logic —
always import `settings` from this module instead.
"""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_JWT_SECRETS = {
    "change-me-in-production",
    "secret",
    "changeme",
    "development",
    "",
}
_MIN_JWT_SECRET_LEN = 32


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
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    reset_token_expire_minutes: int = 15
    access_token_cookie_name: str = "cliniscribe_access"
    refresh_token_cookie_name: str = "cliniscribe_refresh"
    cookie_secure: bool = False  # must be True in production (HTTPS only, PRD Ch20)
    frontend_base_url: str = "http://localhost:3000"

    @model_validator(mode="after")
    def _enforce_production_security(self) -> "Settings":
        """Refuse to start in production with an insecure JWT secret or without
        secure cookies. In non-production environments a warning is logged instead
        so local development is not blocked (PRD Ch20 / security audit T2-T3)."""
        is_prod = self.environment == "production"
        jwt_weak = self.jwt_secret.lower() in _INSECURE_JWT_SECRETS or len(self.jwt_secret) < _MIN_JWT_SECRET_LEN
        if jwt_weak:
            msg = (
                "JWT_SECRET is insecure (known default or fewer than "
                f"{_MIN_JWT_SECRET_LEN} characters). "
                "Set a cryptographically random secret in your environment."
            )
            if is_prod:
                raise ValueError(msg)
            # Non-production: import lazily to avoid import-time side-effects
            import warnings

            warnings.warn(f"[CliniScribe] {msg}", stacklevel=2)

        if is_prod and not self.cookie_secure:
            raise ValueError(
                "COOKIE_SECURE must be True in production to protect session cookies. "
                "Set COOKIE_SECURE=true in your environment."
            )
        return self

    # Rate limiting (PRD Ch16.3)
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_minutes: int = 15
    password_reset_rate_limit_attempts: int = 3
    password_reset_rate_limit_window_minutes: int = 60

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Live (near-real-time) captions during a consultation (PRD Ch9.6). A separate worker
    # process transcribes short audio chunks with a tiny, fast model; the accurate
    # full-file transcript is still produced by the pipeline worker after Stop.
    # Whisper always encodes a fixed 30 s window, so cost per chunk does not shrink with
    # chunk length: measured on a laptop CPU, `small` needs ~10 s per chunk (far slower than
    # real time), `base` ~2.7 s, `tiny` ~1.3 s. `tiny` keeps captions ~4 s behind speech.
    live_audio_key: str = "cliniscribe:live:audio"
    live_whisper_model_size: str = "tiny"
    live_chunk_seconds: float = 2.5
    live_language: str = ""  # "" = auto-detect (same as the final transcript)

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
