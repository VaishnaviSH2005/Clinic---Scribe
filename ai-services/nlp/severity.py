"""Severity classification (mild/moderate/severe) for extracted symptoms
(PRD Ch10.6), by looking for a qualifier word near the symptom mention.
"""

from .vocab import SEVERITY_QUALIFIERS


def classify_severity(text: str, match_start: int, window_chars: int = 30) -> str | None:
    window = text[max(0, match_start - window_chars) : match_start + window_chars]
    for level, qualifiers in SEVERITY_QUALIFIERS.items():
        if any(qualifier in window for qualifier in qualifiers):
            return level
    return None
