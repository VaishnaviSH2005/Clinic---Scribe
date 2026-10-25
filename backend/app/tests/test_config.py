import pytest
from pydantic import ValidationError

from app.core.config import Settings

STRONG_SECRET = "x" * 40


def make_settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_development_defaults_are_allowed() -> None:
    settings = make_settings(environment="development")
    assert settings.is_development


def test_non_development_rejects_default_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        make_settings(environment="production", debug=False, cookie_secure=True)


def test_non_development_rejects_short_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        make_settings(environment="production", jwt_secret="short", debug=False, cookie_secure=True)


def test_non_development_rejects_debug_and_insecure_cookie() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_settings(environment="production", jwt_secret=STRONG_SECRET)
    message = str(excinfo.value)
    assert "DEBUG" in message
    assert "COOKIE_SECURE" in message


def test_non_development_accepts_hardened_config() -> None:
    settings = make_settings(
        environment="production", jwt_secret=STRONG_SECRET, debug=False, cookie_secure=True
    )
    assert not settings.is_development
