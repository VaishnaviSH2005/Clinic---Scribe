"""SOAP note generation via Claude (PRD Ch10.9/Ch17.5). Renders prompts/soap.md
with the context payload and returns the structured JSON response; the
caller (backend service layer) validates it against a Pydantic schema
before persisting to `soap_notes` (Ch15.7.4).
"""

from providers.claude import ClaudeClient


async def generate_soap(claude: ClaudeClient, context: dict) -> dict:
    return await claude.generate_structured(
        "soap", context, required_keys=("subjective", "objective", "assessment", "plan")
    )
