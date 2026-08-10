"""Shared field validators (PRD Ch7.11 — password policy)."""

import re

_PASSWORD_RULE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


def validate_password_strength(password: str) -> str:
    if not _PASSWORD_RULE.match(password):
        raise ValueError(
            "Password must be at least 8 characters and include an uppercase letter, "
            "a lowercase letter, a digit, and a special character."
        )
    return password
