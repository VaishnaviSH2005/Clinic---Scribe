"""OpenAI-compatible chat-completions client (Gemini, NVIDIA NIM, ...).

Drop-in alternative to `ClaudeClient`: same `generate_structured(prompt_name,
context, required_keys=...)` contract, same prompt templates, same JSON
validation, and the same `ClaudeProviderError` on failure — so the LangGraph
orchestrator and the backend pipeline need no changes.

Both Google Gemini (`.../v1beta/openai`) and NVIDIA (`integrate.api.nvidia.com/v1`)
expose the OpenAI `POST {base_url}/chat/completions` API, so one client serves both.
Uses `httpx` (already a dependency of the Anthropic SDK) — nothing extra to install.

`FallbackClient` tries several clients in order (e.g. Gemini, then NVIDIA) so a
rate limit or outage on the first provider does not fail the consultation.
"""

import asyncio

import httpx

from prompts.loader import load_prompt
from providers.claude import ClaudeClient, ClaudeProviderError

# Gemini 2.5 models spend part of the token budget on internal reasoning, so leave headroom.
_MAX_OUTPUT_TOKENS = 4096


class OpenAICompatClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        provider_name: str = "openai-compatible",
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
    ):
        if not api_key:
            raise ClaudeProviderError(f"No API key is configured for {provider_name}.")
        self._api_key = api_key
        self.model = model
        self.provider_name = provider_name
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._timeout = timeout_seconds
        self.max_retries = max_retries

    async def _post(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as http:
            response = await http.post(
                self._url,
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
            )
        if response.status_code >= 400:
            raise _HttpStatusError(response.status_code, response.text[:300])
        return response.json()

    async def generate_structured(
        self, prompt_name: str, context: dict, *, required_keys: tuple[str, ...]
    ) -> dict:
        template = load_prompt(prompt_name)
        payload = {
            "model": self.model,
            "max_tokens": _MAX_OUTPUT_TOKENS,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": template.system_prompt},
                {"role": "user", "content": ClaudeClient._build_user_message(template, context)},
            ],
        }

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                data = await self._post(payload)
                raw_text = (data["choices"][0]["message"].get("content") or "").strip()
                if not raw_text:
                    raise ClaudeProviderError(f"{self.provider_name} returned an empty response.")
                parsed = ClaudeClient._parse_json(raw_text)
                missing = [key for key in required_keys if key not in parsed]
                if missing:
                    raise ClaudeProviderError(f"{self.provider_name} response missing required keys: {missing}")
                return parsed
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
            except _HttpStatusError as exc:
                last_error = exc
                # 429 (rate limit) and 5xx are transient; other 4xx (bad key, bad model) are not.
                if exc.status_code != 429 and exc.status_code < 500:
                    break
            except (ClaudeProviderError, ValueError, KeyError, IndexError, TypeError) as exc:
                last_error = exc

            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (2**attempt))

        raise ClaudeProviderError(
            f"{self.provider_name} request for '{prompt_name}' failed after retries: "
            f"{type(last_error).__name__}: {last_error}"
        )


class _HttpStatusError(Exception):
    def __init__(self, status_code: int, body: str):
        super().__init__(f"HTTP {status_code}: {body}")
        self.status_code = status_code


class FallbackClient:
    """Tries each client in order; raises only if every one of them fails."""

    def __init__(self, clients: list):
        if not clients:
            raise ClaudeProviderError("No AI provider is configured.")
        self._clients = clients

    async def generate_structured(
        self, prompt_name: str, context: dict, *, required_keys: tuple[str, ...]
    ) -> dict:
        errors: list[str] = []
        for client in self._clients:
            try:
                return await client.generate_structured(prompt_name, context, required_keys=required_keys)
            except ClaudeProviderError as exc:
                errors.append(str(exc))
        raise ClaudeProviderError("All AI providers failed: " + " | ".join(errors))
