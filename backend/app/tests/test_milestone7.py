"""Regression tests for Milestone 7: Production Hardening.

Tests cover the three confirmed issues fixed in this milestone:
  T2 — JWT secret startup validation (config.py)
  T3 — cookie_secure production enforcement (config.py)
  T5 — ai_processing status included in 'active' consultation scope

No live database or external services required.
"""

import pytest  # noqa: I001


# ── T2 / T3: Settings startup validation ──────────────────────────────────


def _make_settings(**overrides):
    """Build a Settings instance from keyword overrides, bypassing .env."""
    from app.core.config import Settings

    # pydantic-settings reads .env by default; pass _env_file=None to isolate.
    return Settings.model_validate(
        {
            "environment": "development",
            "jwt_secret": "A" * 32,  # valid default for most tests
            "cookie_secure": False,
            **overrides,
        }
    )


class TestJwtSecretValidation:
    def test_known_insecure_default_raises_in_production(self) -> None:
        with pytest.raises(ValueError, match="JWT_SECRET is insecure"):
            _make_settings(environment="production", jwt_secret="change-me-in-production", cookie_secure=True)

    def test_short_secret_raises_in_production(self) -> None:
        with pytest.raises(ValueError, match="JWT_SECRET is insecure"):
            _make_settings(environment="production", jwt_secret="short", cookie_secure=True)

    def test_empty_secret_raises_in_production(self) -> None:
        with pytest.raises(ValueError, match="JWT_SECRET is insecure"):
            _make_settings(environment="production", jwt_secret="", cookie_secure=True)

    def test_strong_secret_passes_in_production(self) -> None:
        s = _make_settings(
            environment="production",
            jwt_secret="x" * 64,
            cookie_secure=True,
        )
        assert s.jwt_secret == "x" * 64

    def test_insecure_default_issues_warning_in_development(self) -> None:
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _make_settings(environment="development", jwt_secret="change-me-in-production")
        assert any("JWT_SECRET is insecure" in str(warning.message) for warning in w)

    def test_insecure_secret_does_not_raise_in_development(self) -> None:
        # Local dev must not be blocked; only a warning is issued.
        _make_settings(environment="development", jwt_secret="change-me-in-production")

    def test_exactly_32_character_secret_passes(self) -> None:
        s = _make_settings(
            environment="production",
            jwt_secret="a" * 32,
            cookie_secure=True,
        )
        assert len(s.jwt_secret) == 32

    def test_31_character_secret_raises(self) -> None:
        with pytest.raises(ValueError, match="JWT_SECRET is insecure"):
            _make_settings(environment="production", jwt_secret="a" * 31, cookie_secure=True)


class TestCookieSecureValidation:
    def test_cookie_secure_false_raises_in_production(self) -> None:
        with pytest.raises(ValueError, match="COOKIE_SECURE must be True"):
            _make_settings(environment="production", jwt_secret="x" * 32, cookie_secure=False)

    def test_cookie_secure_true_passes_in_production(self) -> None:
        s = _make_settings(environment="production", jwt_secret="x" * 32, cookie_secure=True)
        assert s.cookie_secure is True

    def test_cookie_secure_false_allowed_in_development(self) -> None:
        s = _make_settings(environment="development", cookie_secure=False)
        assert s.cookie_secure is False

    def test_cookie_secure_false_allowed_in_staging(self) -> None:
        # Staging may intentionally use HTTP for internal testing.
        s = _make_settings(environment="staging", cookie_secure=False)
        assert s.cookie_secure is False


# ── T5: Consultation scope includes ai_processing ─────────────────────────


class TestConsultationScopeStatuses:
    def test_active_scope_includes_ai_processing(self) -> None:
        from app.models.enums import ConsultationStatus
        from app.services.consultation_service import SCOPE_STATUSES

        assert ConsultationStatus.ai_processing in SCOPE_STATUSES["active"], (
            "ai_processing must be in the active scope so consultations remain "
            "visible while the AI pipeline is running after recording stops."
        )

    def test_active_scope_includes_in_progress(self) -> None:
        from app.models.enums import ConsultationStatus
        from app.services.consultation_service import SCOPE_STATUSES

        assert ConsultationStatus.in_progress in SCOPE_STATUSES["active"]

    def test_drafts_scope_contains_only_draft(self) -> None:
        from app.models.enums import ConsultationStatus
        from app.services.consultation_service import SCOPE_STATUSES

        assert SCOPE_STATUSES["drafts"] == [ConsultationStatus.draft]

    def test_previous_scope_contains_completed_statuses(self) -> None:
        from app.models.enums import ConsultationStatus
        from app.services.consultation_service import SCOPE_STATUSES

        assert ConsultationStatus.pending_review in SCOPE_STATUSES["previous"]
        assert ConsultationStatus.approved in SCOPE_STATUSES["previous"]

    def test_active_scope_does_not_include_approved(self) -> None:
        from app.models.enums import ConsultationStatus
        from app.services.consultation_service import SCOPE_STATUSES

        assert ConsultationStatus.approved not in SCOPE_STATUSES["active"]

    def test_active_scope_does_not_include_draft(self) -> None:
        from app.models.enums import ConsultationStatus
        from app.services.consultation_service import SCOPE_STATUSES

        assert ConsultationStatus.draft not in SCOPE_STATUSES["active"]

    def test_scopes_are_mutually_exclusive(self) -> None:
        """No status should appear in more than one scope to avoid
        ambiguous list membership for a consultation."""
        from app.services.consultation_service import SCOPE_STATUSES

        seen: set = set()
        for _scope, statuses in SCOPE_STATUSES.items():
            for s in statuses:
                assert s not in seen, f"{s} appears in multiple scopes"
                seen.add(s)


# ── Cookie name consistency ────────────────────────────────────────────────


class TestCookieNameConsistency:
    """Verify that the cookie name used when setting and reading tokens
    is always sourced from the same settings key (no hardcoded literals)."""

    def test_cookies_module_uses_settings_names(self) -> None:
        import inspect

        import app.core.cookies as cookies_mod

        src = inspect.getsource(cookies_mod)
        # Neither of these hardcoded names should appear in the source.
        assert '"access_token"' not in src, "Cookie name hardcoded in cookies.py — use settings"
        assert '"refresh_token"' not in src, "Cookie name hardcoded in cookies.py — use settings"

    def test_auth_dependency_uses_settings_names(self) -> None:
        import inspect

        import app.dependencies.auth as auth_dep

        src = inspect.getsource(auth_dep)
        # The dependency must read the name from settings, not a literal.
        assert (
            'cookies.get("access_token")' not in src
        ), "Hardcoded cookie name in auth dependency — use settings.access_token_cookie_name"
