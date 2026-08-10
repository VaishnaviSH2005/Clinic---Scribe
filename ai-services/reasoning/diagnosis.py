"""Possible-diagnosis / recommended-test suggestions via Claude, renders
prompts/reasoning.md (PRD Ch10.11/Ch17.5.1). Always labeled "AI Suggestion
— Requires Doctor Review" by the frontend; never persisted or presented as
a final diagnosis.
"""

from providers.claude import ClaudeClient


async def generate_recommendations(claude: ClaudeClient, context: dict) -> dict:
    return await claude.generate_structured(
        "reasoning", context, required_keys=("possible_diagnoses", "recommended_tests")
    )
