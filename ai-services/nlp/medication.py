"""Medication + allergy extraction (PRD Ch10.6). Keyword/phrase matching
over the cleaned transcript text — see `entity_extractor.py` docstring for
why this substitutes for SciSpaCy/MedCAT here. Negation is resolved across
every mention of a term — see `negation.py`.
"""

from .negation import assess_term
from .vocab import ALLERGIES, CHRONIC_CONDITIONS, MEDICATIONS


def _extract(text: str, vocabulary: list[str]) -> list[dict]:
    lowered = text.lower()
    found: list[dict] = []
    for term in vocabulary:
        assessment = assess_term(lowered, term)
        if assessment is None:
            continue
        found.append({"text": term, "negated": assessment[0]})
    return found


def extract_medications(text: str) -> list[dict]:
    return _extract(text, MEDICATIONS)


def extract_allergies(text: str) -> list[dict]:
    return _extract(text, ALLERGIES)


def extract_medical_history(text: str) -> list[dict]:
    return _extract(text, CHRONIC_CONDITIONS)
