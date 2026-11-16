"""Regression tests for multi-mention negation handling in the NLP entity
extractor (clinical-safety defect found during the live end-to-end run: the
doctor's question "do you have any fever or cough?" was the first mention, so
the patient's later "no fever" was never evaluated and absent symptoms were
recorded as present).
"""

import pytest

from app.core import ai_bridge  # noqa: F401  (adds ai-services/ to sys.path)


def _symptoms(text: str) -> dict[str, dict]:
    from nlp.entity_extractor import extract_entities

    result = extract_entities([{"text": text}])
    return {s["text"]: s for s in result["symptoms"]}


def test_later_patient_denial_overrides_doctor_question() -> None:
    # Exact shape of the live-run transcript.
    symptoms = _symptoms(
        "Doctor, do you have any fever or cough? Patient, no fever, but I feel weak. "
        "I have chest pain for three days."
    )
    assert symptoms["fever"]["negated"] is True
    assert symptoms["chest pain"]["negated"] is False


def test_negation_does_not_leak_across_but() -> None:
    symptoms = _symptoms("No fever, but I feel dizziness and fatigue.")
    assert symptoms["fever"]["negated"] is True
    assert symptoms["dizziness"]["negated"] is False
    assert symptoms["fatigue"]["negated"] is False


def test_negation_covers_a_list_within_one_clause() -> None:
    symptoms = _symptoms("Patient denies fever, cough or chills.")
    assert all(symptoms[name]["negated"] is True for name in ("fever", "cough", "chills"))


def test_affirmed_statement_wins_over_earlier_denial() -> None:
    symptoms = _symptoms("No fever yesterday. Today I have fever and headache.")
    assert symptoms["fever"]["negated"] is False


def test_question_only_mention_stays_flagged_present() -> None:
    # Safe default: a symptom that was only asked about is never silently dropped.
    symptoms = _symptoms("Do you have chest pain?")
    assert symptoms["chest pain"]["negated"] is False


def test_know_is_not_treated_as_the_word_no() -> None:
    symptoms = _symptoms("I know I have a cough.")
    assert symptoms["cough"]["negated"] is False


def test_severity_is_taken_from_the_affirmed_mention() -> None:
    symptoms = _symptoms("Do you have a headache? Yes, it is a severe headache.")
    assert symptoms["headache"]["negated"] is False
    assert symptoms["headache"]["severity"] == "severe"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("She is allergic to penicillin.", False),
        ("No known penicillin allergy, no allergy to penicillin.", True),
        ("Are you allergic to penicillin? No penicillin allergy.", True),
    ],
)
def test_allergy_negation(text: str, expected: bool) -> None:
    from nlp.entity_extractor import extract_entities

    allergies = {a["text"]: a for a in extract_entities([{"text": text}])["allergies"]}
    assert allergies["penicillin"]["negated"] is expected
