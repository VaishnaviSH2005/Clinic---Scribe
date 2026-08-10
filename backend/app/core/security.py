"""Password hashing and JWT primitives (PRD Ch7.11 / Ch20 — Argon2id + JWT).

This module provides the cryptographic primitives only. Session lifecycle,
RBAC, and endpoint wiring are implemented with the Authentication module.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jwt import InvalidTokenError

from app.core.config import settings

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def generate_secure_token() -> str:
    """Cryptographically secure opaque token (refresh tokens, password
    reset tokens). Only its SHA-256 hash is ever persisted (PRD Ch7.11/Ch20)."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(subject: str, session_id: str, extra_claims: dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "sid": session_id, "exp": expire, "type": "access"}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError:
        return None


def encode_refresh_cookie_value(session_id: str, raw_token: str) -> str:
    """Refresh tokens are opaque, so the session id is embedded alongside the
    token in the cookie value (`<session_id>.<token>`) to avoid a table scan
    on refresh. Session-existence + hash-match is still what's authoritative;
    the embedded id is only a lookup hint."""
    return f"{session_id}.{raw_token}"


def decode_refresh_cookie_value(value: str) -> tuple[str, str] | None:
    session_id, _, raw_token = value.partition(".")
    if not session_id or not raw_token:
        return None
    return session_id, raw_token
