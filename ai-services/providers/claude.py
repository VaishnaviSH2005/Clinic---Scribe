"""Claude API client wrapper (PRD Ch3.6). Reads `CLAUDE_API_KEY` via the
backend's `app.core.config.settings` — never accessed directly as an env var
inside business logic (PRD Ch4.12), and never exposed to the frontend.

Every call renders one of the versioned `prompts/*.md` templates, sends the
system instruction + a JSON context payload, and validates that the response
is well-formed JSON matching the expected top-level keys before returning it
to the caller. Timeouts, transient provider errors, and malformed JSON are
retried with backoff up to `max_retries`; a `ClaudeProviderError` is raised
only after retries are exhausted, so the pipeline can record a clean,
documented per-stage failure (Ch17.6) instead of crashing or silently
inventing content.
"""

import asyncio
import json
import re

import anthropic

from prompts.loader import PromptTemplate, load_prompt

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


class ClaudeProviderError(Exception):
    """Raised when Claude is unreachable, times out, or returns output that
    cannot be parsed into the requested schema after all retries."""


class ClaudeClient:
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5",
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
    ):
        if not api_key:
            raise ClaudeProviderError("No Claude API key is configured.")
        self._client = anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout_seconds)
        self.model = model
        self.max_retries = max_retries

    async def generate_structured(
        self, prompt_name: str, context: dict, *, required_keys: tuple[str, ...]
    ) -> dict:
        """Renders `prompts/{prompt_name}.md`, calls Claude, and returns the
        parsed JSON object. `required_keys` are validated as present in the
        top-level response before it is accepted."""
        template = load_prompt(prompt_name)
        user_message = self._build_user_message(template, context)

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=template.system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                )
                raw_text = "".join(block.text for block in response.content if block.type == "text")
                parsed = self._parse_json(raw_text)
                missing = [key for key in required_keys if key not in parsed]
                if missing:
                    raise ClaudeProviderError(f"Claude response missing required keys: {missing}")
                return parsed
            except (anthropic.APITimeoutError, anthropic.APIConnectionError, anthropic.RateLimitError) as exc:
                last_error = exc
            except (anthropic.APIStatusError, ClaudeProviderError, ValueError) as exc:
                last_error = exc
                if isinstance(exc, anthropic.APIStatusError) and exc.status_code < 500:
                    break  # client errors (bad request, auth) are not retryable

            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (2**attempt))

        raise ClaudeProviderError(f"Claude request for '{prompt_name}' failed after retries: {last_error}")

    @staticmethod
    def _build_user_message(template: PromptTemplate, context: dict) -> str:
        return (
            f"Output schema:\n{template.schema_json}\n\n"
            f"Context:\n{json.dumps(context, default=str)}\n\n"
            "Return only the JSON object described by the schema above. No prose, no markdown fences."
        )

    @staticmethod
    def _parse_json(raw_text: str) -> dict:
        text = raw_text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = _JSON_BLOCK_RE.search(text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise ClaudeProviderError(f"Claude returned malformed JSON: {exc}") from exc
        raise ClaudeProviderError("Claude response did not contain a JSON object.")
