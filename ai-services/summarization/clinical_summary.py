"""Clinical summary generation via Claude, capped at 300 words (PRD Ch9.9/10.10).

The word cap is enforced twice per Ch17.5.1: once as a prompt instruction
(prompts/summary.md) and once here as a hard truncation-with-warning check,
since LLM output length is not perfectly deterministic.
"""

from providers.claude import ClaudeClient

MAX_WORDS = 300
_SUMMARY_FIELDS = ("chief_complaint", "history_of_present_illness", "key_findings", "assessment", "plan")


def _word_count(result: dict) -> int:
    return sum(len(str(result.get(field, "")).split()) for field in _SUMMARY_FIELDS)


def _truncate_to_word_limit(result: dict, limit: int) -> dict:
    total = _word_count(result)
    if total <= limit:
        return result

    truncated = dict(result)
    budget = limit
    for field in _SUMMARY_FIELDS:
        words = str(truncated.get(field, "")).split()
        take = min(len(words), budget)
        truncated[field] = " ".join(words[:take])
        budget -= take
    return truncated


async def generate_summary(claude: ClaudeClient, context: dict) -> tuple[dict, bool]:
    """Returns (summary, was_truncated)."""
    result = await claude.generate_structured("summary", context, required_keys=_SUMMARY_FIELDS)
    was_truncated = _word_count(result) > MAX_WORDS
    return _truncate_to_word_limit(result, MAX_WORDS), was_truncated
