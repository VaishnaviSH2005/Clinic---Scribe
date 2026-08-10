"""AI pipeline unit tests — no live Postgres/Redis/Claude in this
environment (consistent with every other test module here), so these cover
what's genuinely testable in isolation: entity extraction correctness,
transcript cleaning, prompt loading, the Claude client's JSON
parsing/validation/retry behavior (HTTP layer mocked, not business logic),
clinical summary word-cap enforcement, and the AI queue's job payload
shape. DB-backed integration coverage (hospital isolation, doctor
ownership, full pipeline persistence) would require a live database, which
this sandbox does not have — see the final milestone report.
"""

import pytest

from app.core import ai_bridge  # noqa: F401  (adds ai-services/ to sys.path)

# --- NLP entity extraction ---------------------------------------------


def test_extract_entities_detects_symptoms_severity_and_negation() -> None:
    from nlp.entity_extractor import extract_entities

    transcript = [
        {"text": "Patient reports severe chest pain radiating to the arm."},
        {"text": "Denies fever. No history of diabetes mentioned here."},
        {"text": "Currently taking metformin. Allergic to penicillin."},
        {"text": "Blood pressure 130 over 85, pulse 92 bpm, temperature 101.2"},
    ]
    result = extract_entities(transcript)

    symptom_names = {s["text"] for s in result["symptoms"]}
    assert "chest pain" in symptom_names
    assert "fever" in symptom_names
    chest_pain = next(s for s in result["symptoms"] if s["text"] == "chest pain")
    assert chest_pain["negated"] is False
    assert chest_pain["severity"] == "severe"
    fever = next(s for s in result["symptoms"] if s["text"] == "fever")
    assert fever["negated"] is True

    assert {m["text"] for m in result["medications"]} == {"metformin"}
    assert {a["text"] for a in result["allergies"]} == {"penicillin"}
    assert result["vitals"]["blood_pressure"] == "130/85"
    assert result["vitals"]["pulse"] == "92"
    assert result["vitals"]["temperature"] == "101.2"


def test_extract_entities_handles_empty_transcript() -> None:
    from nlp.entity_extractor import extract_entities

    result = extract_entities([])
    assert result == {
        "symptoms": [],
        "medications": [],
        "allergies": [],
        "medical_history": [],
        "vitals": None,
    }


# --- Transcript cleaning -------------------------------------------------


def test_clean_transcript_strips_filler_words() -> None:
    from speech.cleaner import clean_transcript

    raw = [
        {
            "speaker": "unknown",
            "text": "um so, I have uh a headache you know",
            "timestamp_start": 0.0,
            "timestamp_end": 2.0,
            "confidence": 0.9,
        },
        {"speaker": "unknown", "text": "um uh", "timestamp_start": 2.0, "timestamp_end": 2.5, "confidence": 0.4},
    ]
    cleaned = clean_transcript(raw)
    assert len(cleaned) == 1  # the second segment becomes empty after cleaning and is dropped
    assert "um" not in cleaned[0]["text"].lower()
    assert "headache" in cleaned[0]["text"]


# --- Prompt loader ---------------------------------------------------------


@pytest.mark.parametrize("name", ["soap", "summary", "reasoning", "risk"])
def test_load_prompt_extracts_system_and_schema(name: str) -> None:
    from prompts.loader import load_prompt

    template = load_prompt(name)
    assert template.system_prompt.startswith("You are a")
    # The schema block documents its shape with `"high" | "medium" | "low"`
    # union hints for Claude to read — not itself parseable JSON — so this
    # only checks it was extracted (non-empty, braces present), matching
    # what `ClaudeClient._build_user_message` actually sends downstream.
    assert template.schema_json.startswith("{")
    assert template.schema_json.endswith("}")
    assert len(template.schema_json) > 10


# --- Claude client ---------------------------------------------------------


class _FakeTextBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, text: str):
        self.content = [_FakeTextBlock(text)]


def _make_claude_client(monkeypatch: pytest.MonkeyPatch):
    from providers.claude import ClaudeClient

    client = ClaudeClient(api_key="test-key", model="claude-test", timeout_seconds=1, max_retries=2)
    return client


async def test_claude_client_parses_valid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_claude_client(monkeypatch)

    async def fake_create(**_kwargs):
        return _FakeResponse('{"subjective": "a", "objective": "b", "assessment": "c", "plan": "d"}')

    monkeypatch.setattr(client._client.messages, "create", fake_create)
    result = await client.generate_structured(
        "soap", {"foo": "bar"}, required_keys=("subjective", "objective", "assessment", "plan")
    )
    assert result["subjective"] == "a"


async def test_claude_client_extracts_json_from_prose(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_claude_client(monkeypatch)

    async def fake_create(**_kwargs):
        return _FakeResponse('Here is the result:\n{"red_flags": []}\nLet me know if you need more.')

    monkeypatch.setattr(client._client.messages, "create", fake_create)
    result = await client.generate_structured("risk", {}, required_keys=("red_flags",))
    assert result["red_flags"] == []


async def test_claude_client_raises_after_retries_on_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.claude import ClaudeProviderError

    client = _make_claude_client(monkeypatch)
    call_count = 0

    async def fake_create(**_kwargs):
        nonlocal call_count
        call_count += 1
        return _FakeResponse("not valid json at all")

    monkeypatch.setattr(client._client.messages, "create", fake_create)
    with pytest.raises(ClaudeProviderError):
        await client.generate_structured("risk", {}, required_keys=("red_flags",))
    assert call_count == client.max_retries + 1  # every attempt was used


async def test_claude_client_raises_on_missing_required_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.claude import ClaudeProviderError

    client = _make_claude_client(monkeypatch)

    async def fake_create(**_kwargs):
        return _FakeResponse('{"unexpected": "shape"}')

    monkeypatch.setattr(client._client.messages, "create", fake_create)
    with pytest.raises(ClaudeProviderError):
        await client.generate_structured("risk", {}, required_keys=("red_flags",))


async def test_claude_client_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    import anthropic

    client = _make_claude_client(monkeypatch)
    attempts = 0

    async def fake_create(**_kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise anthropic.APITimeoutError(request=None)
        return _FakeResponse('{"red_flags": [{"content": "x", "explanation": "y", "confidence": "high"}]}')

    monkeypatch.setattr(client._client.messages, "create", fake_create)
    monkeypatch.setattr("providers.claude.asyncio.sleep", _instant_sleep)
    result = await client.generate_structured("risk", {}, required_keys=("red_flags",))
    assert attempts == 2
    assert len(result["red_flags"]) == 1


async def _instant_sleep(_seconds: float) -> None:
    return None


# --- Clinical summary word cap -------------------------------------------


async def test_generate_summary_truncates_to_word_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    from summarization.clinical_summary import MAX_WORDS, generate_summary

    long_text = " ".join(["word"] * 350)
    client = _make_claude_client(monkeypatch)

    async def fake_generate_structured(_prompt_name, _context, *, required_keys):
        return {
            "chief_complaint": long_text,
            "history_of_present_illness": "",
            "key_findings": "",
            "assessment": "",
            "plan": "",
        }

    monkeypatch.setattr(client, "generate_structured", fake_generate_structured)
    result, was_truncated = await generate_summary(client, {})
    total_words = sum(len(str(result[field]).split()) for field in result if field != "confidence")
    assert was_truncated is True
    assert total_words <= MAX_WORDS


# --- AI queue payload shape (Redis calls faked, no live Redis needed) -----


class _FakeRedis:
    def __init__(self):
        self.list: list[str] = []

    async def lpush(self, _key: str, value: str) -> None:
        self.list.insert(0, value)

    async def brpop(self, _keys: list[str], timeout: int = 5):
        if not self.list:
            return None
        return ("key", self.list.pop())

    async def llen(self, _key: str) -> int:
        return len(self.list)


async def test_ai_queue_enqueue_dequeue_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import ai_queue

    fake = _FakeRedis()
    monkeypatch.setattr(ai_queue, "get_redis", lambda: fake)

    consultation_id = "11111111-1111-1111-1111-111111111111"
    await ai_queue.enqueue_ai_job(consultation_id, stage=None)
    job = await ai_queue.dequeue_ai_job(timeout_seconds=1)
    assert job == {"consultation_id": consultation_id, "stage": None}


async def test_ai_queue_carries_stage_for_single_stage_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import ai_queue

    fake = _FakeRedis()
    monkeypatch.setattr(ai_queue, "get_redis", lambda: fake)

    consultation_id = "22222222-2222-2222-2222-222222222222"
    await ai_queue.enqueue_ai_job(consultation_id, stage="generate_soap")
    job = await ai_queue.dequeue_ai_job(timeout_seconds=1)
    assert job == {"consultation_id": consultation_id, "stage": "generate_soap"}


async def test_ai_queue_dequeue_returns_none_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import ai_queue

    fake = _FakeRedis()
    monkeypatch.setattr(ai_queue, "get_redis", lambda: fake)
    assert await ai_queue.dequeue_ai_job(timeout_seconds=1) is None
