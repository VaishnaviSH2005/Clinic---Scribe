"""Regression: a custom validator failure (weak password) must be a clean 422
with the policy message — it used to crash the error handler with a 500
("Object of type ValueError is not JSON serializable"). Found in the A-to-Z run."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_weak_password_on_reset_is_422_with_policy_message() -> None:
    r = client.post("/api/v1/auth/reset-password", json={"token": "x", "password": "weak"})
    assert r.status_code == 422
    body = r.json()
    assert body["errorCode"] == "VALIDATION_ERROR"
    assert any("uppercase" in e["msg"] for e in body["errors"])


def test_weak_password_on_change_password_is_422_not_500() -> None:
    # Validation runs before authentication, so no session is needed to prove the handler is safe.
    r = client.post("/api/v1/auth/change-password", json={"current_password": "x", "new_password": "weak"})
    assert r.status_code in (401, 422)


def test_default_cookie_names_match_the_frontend_middleware() -> None:
    """frontend/middleware.ts keys off `cliniscribe_access`; the backend default must be identical,
    otherwise a deployment without explicit env vars logs users in and bounces them to /login."""
    from app.core.config import Settings

    fields = Settings.model_fields
    assert fields["access_token_cookie_name"].default == "cliniscribe_access"
    assert fields["refresh_token_cookie_name"].default == "cliniscribe_refresh"
