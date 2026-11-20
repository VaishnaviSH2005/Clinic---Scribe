"""Gemini / NVIDIA (OpenAI-compatible) LLM client + provider selection tests.

The HTTP call (`OpenAICompatClient._post`) is mocked; parsing, retry, fallback and
provider-selection logic are real.
"""

import pytest

from app.core import ai_bridge  # noqa: F401  (adds ai-services/ to sys.path)

SOAP_KEYS = ("subjective", "objective", "assessment", "plan")
SOAP_JSON = '{"subjective": "a", "objective": "b", "assessment": "c", "plan": "d"}'


def _reply(text: str | None) -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": text}}]}


def _client(provider_name: str = "Gemini", max_retries: int = 2):
    from providers.openai_compat import OpenAICompatClient

    return OpenAICompatClient(
        api_key="test-key",
        model="test-model",
        base_url="https://example.test/v1/",
        provider_name=provider_name,
        timeout_seconds=1,
        max_retries=max_retries,
    )


async def _instant_sleep(_seconds: float) -> None:
    return None


async def test_parses_plain_json(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    sent: dict = {}

    async def fake_post(payload):
        sent.update(payload)
        return _reply(SOAP_JSON)

    monkeypatch.setattr(client, "_post", fake_post)
    result = await client.generate_structured("soap", {"x": 1}, required_keys=SOAP_KEYS)
    assert result["plan"] == "d"
    assert sent["model"] == "test-model"
    assert sent["messages"][0]["role"] == "system"
    assert client._url == "https://example.test/v1/chat/completions"


async def test_extracts_json_from_markdown_fence(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()

    async def fake_post(_payload):
        return _reply("```json\n" + SOAP_JSON + "\n```")

    monkeypatch.setattr(client, "_post", fake_post)
    result = await client.generate_structured("soap", {}, required_keys=SOAP_KEYS)
    assert result["subjective"] == "a"


async def test_retries_rate_limit_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.openai_compat import _HttpStatusError

    client = _client()
    monkeypatch.setattr("providers.openai_compat.asyncio.sleep", _instant_sleep)
    calls = 0

    async def fake_post(_payload):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise _HttpStatusError(429, "rate limited")
        return _reply(SOAP_JSON)

    monkeypatch.setattr(client, "_post", fake_post)
    result = await client.generate_structured("soap", {}, required_keys=SOAP_KEYS)
    assert result["objective"] == "b"
    assert calls == 2


async def test_bad_key_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.claude import ClaudeProviderError
    from providers.openai_compat import _HttpStatusError

    client = _client()
    monkeypatch.setattr("providers.openai_compat.asyncio.sleep", _instant_sleep)
    calls = 0

    async def fake_post(_payload):
        nonlocal calls
        calls += 1
        raise _HttpStatusError(401, "invalid api key")

    monkeypatch.setattr(client, "_post", fake_post)
    with pytest.raises(ClaudeProviderError):
        await client.generate_structured("soap", {}, required_keys=SOAP_KEYS)
    assert calls == 1


async def test_malformed_json_uses_all_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.claude import ClaudeProviderError

    client = _client()
    monkeypatch.setattr("providers.openai_compat.asyncio.sleep", _instant_sleep)
    calls = 0

    async def fake_post(_payload):
        nonlocal calls
        calls += 1
        return _reply("sorry, I cannot do that")

    monkeypatch.setattr(client, "_post", fake_post)
    with pytest.raises(ClaudeProviderError):
        await client.generate_structured("soap", {}, required_keys=SOAP_KEYS)
    assert calls == client.max_retries + 1


async def test_empty_content_and_missing_keys_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.claude import ClaudeProviderError

    client = _client(max_retries=0)

    async def empty(_payload):
        return _reply(None)

    monkeypatch.setattr(client, "_post", empty)
    with pytest.raises(ClaudeProviderError):
        await client.generate_structured("soap", {}, required_keys=SOAP_KEYS)

    async def partial(_payload):
        return _reply('{"subjective": "a"}')

    monkeypatch.setattr(client, "_post", partial)
    with pytest.raises(ClaudeProviderError):
        await client.generate_structured("soap", {}, required_keys=SOAP_KEYS)


async def test_fallback_uses_second_provider_when_first_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.claude import ClaudeProviderError
    from providers.openai_compat import FallbackClient

    gemini, nvidia = _client("Gemini", max_retries=0), _client("NVIDIA", max_retries=0)

    async def gemini_down(_payload):
        raise ClaudeProviderError("boom")  # retried as a provider error, then raised

    async def nvidia_ok(_payload):
        return _reply(SOAP_JSON)

    monkeypatch.setattr(gemini, "_post", gemini_down)
    monkeypatch.setattr(nvidia, "_post", nvidia_ok)
    result = await FallbackClient([gemini, nvidia]).generate_structured("soap", {}, required_keys=SOAP_KEYS)
    assert result["plan"] == "d"


async def test_fallback_reports_every_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.claude import ClaudeProviderError
    from providers.openai_compat import FallbackClient

    a, b = _client("Gemini", max_retries=0), _client("NVIDIA", max_retries=0)

    async def bad(_payload):
        return _reply("nope")

    monkeypatch.setattr(a, "_post", bad)
    monkeypatch.setattr(b, "_post", bad)
    with pytest.raises(ClaudeProviderError) as exc:
        await FallbackClient([a, b]).generate_structured("soap", {}, required_keys=SOAP_KEYS)
    assert "Gemini" in str(exc.value) and "NVIDIA" in str(exc.value)


# --- provider selection (settings -> client) -----------------------------------


def _set(monkeypatch: pytest.MonkeyPatch, **values: str) -> None:
    from app.core.config import settings

    base = {"llm_provider": "anthropic", "claude_api_key": "", "gemini_api_key": "", "nvidia_api_key": ""}
    base.update(values)
    for name, value in base.items():
        monkeypatch.setattr(settings, name, value)


def test_default_provider_is_still_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.claude import ClaudeClient

    from app.services.ai_pipeline_service import _build_claude_client

    _set(monkeypatch, claude_api_key="sk-ant-test")
    assert isinstance(_build_claude_client(), ClaudeClient)


def test_anthropic_without_key_keeps_original_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.claude import ClaudeProviderError

    from app.services.ai_pipeline_service import _build_claude_client

    _set(monkeypatch)
    with pytest.raises(ClaudeProviderError, match="No Claude API key"):
        _build_claude_client()


def test_gemini_then_nvidia_builds_fallback_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.openai_compat import FallbackClient

    from app.services.ai_pipeline_service import _build_claude_client

    _set(monkeypatch, llm_provider="gemini,nvidia", gemini_api_key="g", nvidia_api_key="n")
    client = _build_claude_client()
    assert isinstance(client, FallbackClient)
    assert [c.provider_name for c in client._clients] == ["Gemini", "NVIDIA"]


def test_missing_gemini_key_skips_to_nvidia(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.openai_compat import OpenAICompatClient

    from app.services.ai_pipeline_service import _build_claude_client

    _set(monkeypatch, llm_provider="gemini,nvidia", nvidia_api_key="n")
    client = _build_claude_client()
    assert isinstance(client, OpenAICompatClient) and client.provider_name == "NVIDIA"


def test_no_keys_or_unknown_provider_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.claude import ClaudeProviderError

    from app.services.ai_pipeline_service import _build_claude_client

    _set(monkeypatch, llm_provider="gemini,nvidia")
    with pytest.raises(ClaudeProviderError, match="No API key"):
        _build_claude_client()
    _set(monkeypatch, llm_provider="banana", gemini_api_key="g")
    with pytest.raises(ClaudeProviderError, match="Unknown LLM_PROVIDER"):
        _build_claude_client()
