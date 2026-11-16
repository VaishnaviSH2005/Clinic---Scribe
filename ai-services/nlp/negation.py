"""Mention-level negation assessment shared by the symptom and medication /
allergy / history extractors (PRD Ch10.6, Ch17 clinical safety).

A term can be mentioned several times in a consultation — typically first in
the doctor's question ("Do you have any fever or cough?") and then in the
patient's answer ("No fever, but I feel dizzy"). Looking only at the first
mention (the earlier behaviour) recorded absent symptoms as present, and a
fixed look-back window let a negation leak across clauses ("no fever, but ...
dizzy" negated "dizzy"). This module evaluates *every* mention instead.

Resolution order for one term (safest reading wins):

1. any mention in a statement that is not negated  -> present
2. otherwise any negated mention in a statement    -> absent (negated)
3. otherwise (only mentioned inside questions)     -> present

Rule 3 keeps a symptom or allergy that was only asked about flagged for the
clinician rather than silently dropping it: a false "present" is reviewable,
a false "absent" is a clinical-safety miss.
"""

import re

from .vocab import NEGATION_TRIGGERS

_CLAUSE_BREAK = re.compile(r"[.?!;:]|\b(?:but|however|although|except)\b")
_SENTENCE_END = re.compile(r"[.?!]")
_NEGATION = re.compile(
    r"\b(?:" + "|".join(re.escape(trigger.strip()) for trigger in NEGATION_TRIGGERS) + r")\s"
)
_LOOKBACK_CHARS = 30


def _is_negated(text: str, start: int) -> bool:
    prefix = text[:start]
    breaks = list(_CLAUSE_BREAK.finditer(prefix))
    clause = prefix[breaks[-1].end() :] if breaks else prefix
    return _NEGATION.search(clause[-_LOOKBACK_CHARS:]) is not None


def _in_question(text: str, end: int) -> bool:
    boundary = _SENTENCE_END.search(text, end)
    return boundary is not None and boundary.group() == "?"


def assess_term(text: str, term: str) -> tuple[bool, int] | None:
    """Return `(negated, index_of_deciding_mention)` for `term` in the
    already-lowercased `text`, or `None` if the term never occurs."""
    affirmed: int | None = None
    negated_at: int | None = None
    asked: int | None = None
    for match in re.finditer(re.escape(term), text):
        index = match.start()
        if _in_question(text, match.end()):
            asked = index if asked is None else asked
        elif _is_negated(text, index):
            negated_at = index if negated_at is None else negated_at
        else:
            affirmed = index if affirmed is None else affirmed
    if affirmed is not None:
        return False, affirmed
    if negated_at is not None:
        return True, negated_at
    if asked is not None:
        return False, asked
    return None
