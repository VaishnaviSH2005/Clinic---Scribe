"""Symptom + negation + severity extraction (PRD Ch10.6). Keyword/phrase
matching over the cleaned transcript text — see `entity_extractor.py`
docstring for why this substitutes for SciSpaCy/MedCAT here.
"""

from .severity import classify_severity
from .vocab import NEGATION_TRIGGERS, SYMPTOMS


def _is_negated(text: str, match_start: int) -> bool:
    window = text[max(0, match_start - 25) : match_start]
    return any(trigger in window for trigger in NEGATION_TRIGGERS)


def extract_symptoms(text: str) -> list[dict]:
    lowered = text.lower()
    found: dict[str, dict] = {}
    for symptom in SYMPTOMS:
        index = lowered.find(symptom)
        if index == -1:
            continue
        negated = _is_negated(lowered, index)
        if symptom in found and found[symptom]["negated"] and not negated:
            # A later, non-negated mention overrides an earlier negated one.
            pass
        elif symptom in found:
            continue
        found[symptom] = {
            "text": symptom,
            "negated": negated,
            "severity": None if negated else classify_severity(lowered, index),
        }
    return list(found.values())
