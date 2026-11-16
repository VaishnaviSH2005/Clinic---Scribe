"""Symptom + negation + severity extraction (PRD Ch10.6). Keyword/phrase
matching over the cleaned transcript text — see `entity_extractor.py`
docstring for why this substitutes for SciSpaCy/MedCAT here. Negation is
resolved across every mention of a symptom — see `negation.py`.
"""

from .negation import assess_term
from .severity import classify_severity
from .vocab import SYMPTOMS


def extract_symptoms(text: str) -> list[dict]:
    lowered = text.lower()
    found: list[dict] = []
    for symptom in SYMPTOMS:
        assessment = assess_term(lowered, symptom)
        if assessment is None:
            continue
        negated, index = assessment
        found.append(
            {
                "text": symptom,
                "negated": negated,
                "severity": None if negated else classify_severity(lowered, index),
            }
        )
    return found
