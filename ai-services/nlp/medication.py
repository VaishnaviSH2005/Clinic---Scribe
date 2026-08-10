"""Medication + allergy extraction (PRD Ch10.6). Keyword/phrase matching
over the cleaned transcript text — see `entity_extractor.py` docstring for
why this substitutes for SciSpaCy/MedCAT here.
"""

from .vocab import ALLERGIES, CHRONIC_CONDITIONS, MEDICATIONS, NEGATION_TRIGGERS


def _is_negated(text: str, match_start: int) -> bool:
    window = text[max(0, match_start - 25) : match_start]
    return any(trigger in window for trigger in NEGATION_TRIGGERS)


def _extract(text: str, vocabulary: list[str]) -> list[dict]:
    lowered = text.lower()
    found: dict[str, dict] = {}
    for term in vocabulary:
        index = lowered.find(term)
        if index == -1 or term in found:
            continue
        found[term] = {"text": term, "negated": _is_negated(lowered, index)}
    return list(found.values())


def extract_medications(text: str) -> list[dict]:
    return _extract(text, MEDICATIONS)


def extract_allergies(text: str) -> list[dict]:
    return _extract(text, ALLERGIES)


def extract_medical_history(text: str) -> list[dict]:
    return _extract(text, CHRONIC_CONDITIONS)
