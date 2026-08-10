"""Loads the versioned prompt templates from this directory (PRD Ch4.6 —
prompts are never hardcoded in application code). Each template file has a
"System: ..." paragraph followed by an "## Output schema" fenced JSON block;
this module extracts both so callers can build a Claude request without
re-authoring prompt text.
"""

import re
from dataclasses import dataclass
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent

_SYSTEM_RE = re.compile(r"^System:\s*(.+?)(?=\n\n)", re.DOTALL | re.MULTILINE)
_SCHEMA_RE = re.compile(r"Output schema:\s*```json\s*(.+?)\s*```", re.DOTALL)


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    system_prompt: str
    schema_json: str
    full_text: str


def load_prompt(name: str) -> PromptTemplate:
    """`name` is one of soap, summary, reasoning, risk (matches the .md filename)."""
    path = PROMPTS_DIR / f"{name}.md"
    text = path.read_text(encoding="utf-8")

    system_match = _SYSTEM_RE.search(text)
    schema_match = _SCHEMA_RE.search(text)
    if not system_match or not schema_match:
        raise ValueError(f"Prompt template '{name}' is missing a System/Output schema section.")

    system_prompt = " ".join(system_match.group(1).split())
    schema_json = schema_match.group(1).strip()
    return PromptTemplate(name=name, system_prompt=system_prompt, schema_json=schema_json, full_text=text)
