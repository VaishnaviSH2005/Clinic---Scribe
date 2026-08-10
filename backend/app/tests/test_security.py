"""Unit tests for core auth primitives — no database required."""

import pytest

from app.core.security import (
    create_access_token,
    decode_refresh_cookie_value,
    decode_token,
    encode_refresh_cookie_value,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.schemas.validators import validate_password_strength


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("Sup3r$ecret!")
    assert hashed != "Sup3r$ecret!"
    assert verify_password("Sup3r$ecret!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip() -> None:
    token = create_access_token("user-123", "session-456", extra_claims={"role": "doctor"})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["sid"] == "session-456"
    assert payload["type"] == "access"
    assert payload["role"] == "doctor"


def test_decode_token_rejects_garbage() -> None:
    assert decode_token("not-a-real-token") is None


def test_refresh_cookie_value_roundtrip() -> None:
    raw_token = generate_secure_token()
    cookie_value = encode_refresh_cookie_value("session-789", raw_token)
    decoded = decode_refresh_cookie_value(cookie_value)
    assert decoded == ("session-789", raw_token)


def test_refresh_cookie_value_rejects_malformed() -> None:
    assert decode_refresh_cookie_value("no-dot-here") is None


def test_hash_token_is_deterministic_and_one_way() -> None:
    token = "example-token"
    assert hash_token(token) == hash_token(token)
    assert hash_token(token) != token


@pytest.mark.parametrize(
    "password,valid",
    [
        ("Sup3r$ecret!", True),
        ("short1!A", True),
        ("alllowercase1!", False),  # no uppercase
        ("ALLUPPERCASE1!", False),  # no lowercase
        ("NoDigitsHere!", False),  # no digit
        ("NoSpecialChar1", False),  # no special char
        ("Sh0rt!", False),  # under 8 chars
    ],
)
def test_password_strength_validator(password: str, valid: bool) -> None:
    if valid:
        assert validate_password_strength(password) == password
    else:
        with pytest.raises(ValueError):
            validate_password_strength(password)
