"""Clinical red-flag detection via Claude, renders prompts/risk.md
(PRD Ch10.12/Ch17.5.1). Rendered by the frontend as visually distinct
warning cards; never triggers an automatic clinical decision.
"""

from providers.claude import ClaudeClient


async def generate_risk_flags(claude: ClaudeClient, context: dict) -> dict:
    return await claude.generate_structured("risk", context, required_keys=("red_flags",))
