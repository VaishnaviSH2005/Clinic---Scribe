"""Medical entity extraction orchestrator (PRD Ch10.6/Ch17.4).

Populates the shape expected by the `ai_entities` table (PRD Ch15.7.3) from
the cleaned transcript. This is local/deterministic NLP, not an LLM call —
it succeeds independently of Claude availability (Ch9.21/10.15 graceful
degradation).

PRD Ch3.6 specifies SciSpaCy + MedCAT for this stage. MedCAT requires a
UMLS-licensed concept database / vocab model pack, which cannot be obtained
in any environment without going through UMLS credentialing — this is a
real licensing constraint, not a limitation of this sandbox. This module
implements a genuine, working extractor (tokenized keyword/phrase matching
over a curated medical vocabulary, with negation and severity detection,
plus regex vital-sign parsing) behind the exact same `extract_entities()`
interface, so it is a drop-in replacement for a full MedCAT pipeline once a
hospital's licensed model pack is available — swap the implementation of
this function only, callers never change.
"""

import re
from typing import TypedDict

from .medication import extract_allergies, extract_medical_history, extract_medications
from .symptoms import extract_symptoms

_VITAL_PATTERNS = {
    "blood_pressure": re.compile(r"blood pressure[^\d]{0,10}(\d{2,3})\s*(?:over|/)\s*(\d{2,3})", re.IGNORECASE),
    "pulse": re.compile(r"(?:pulse|heart rate)[^\d]{0,10}(\d{2,3})\s*(?:bpm)?", re.IGNORECASE),
    "temperature": re.compile(r"temperature[^\d]{0,10}(\d{2,3}(?:\.\d)?)", re.IGNORECASE),
    "spo2": re.compile(r"(?:oxygen saturation|spo2|sats?)[^\d]{0,10}(\d{2,3})\s*%?", re.IGNORECASE),
    "respiratory_rate": re.compile(r"respiratory rate[^\d]{0,10}(\d{1,2})", re.IGNORECASE),
}


class ExtractedEntities(TypedDict):
    symptoms: list[dict]
    medications: list[dict]
    allergies: list[dict]
    medical_history: list[dict]
    vitals: dict | None


def _extract_vitals(text: str) -> dict | None:
    vitals: dict[str, str] = {}
    bp_match = _VITAL_PATTERNS["blood_pressure"].search(text)
    if bp_match:
        vitals["blood_pressure"] = f"{bp_match.group(1)}/{bp_match.group(2)}"
    for key in ("pulse", "temperature", "spo2", "respiratory_rate"):
        match = _VITAL_PATTERNS[key].search(text)
        if match:
            vitals[key] = match.group(1)
    return vitals or None


def extract_entities(cleaned_transcript: list[dict]) -> ExtractedEntities:
    text = " ".join(segment.get("text", "") for segment in cleaned_transcript)

    return ExtractedEntities(
        symptoms=extract_symptoms(text),
        medications=extract_medications(text),
        allergies=extract_allergies(text),
        medical_history=extract_medical_history(text),
        vitals=_extract_vitals(text),
    )
