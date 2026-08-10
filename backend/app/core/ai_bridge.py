"""Adds the sibling `ai-services/` package directory to `sys.path` so
backend worker code can import its `speech`/`nlp`/`providers`/
`summarization`/`reasoning` packages directly (PRD Ch4.6 — `ai-services` is
a separate top-level directory, kept out of the API container image; its
folder name contains a hyphen so it can never be a dotted Python import).

Import this module before any `from speech...` / `from providers...` style
import used by the AI pipeline — `app/workers/pipeline_worker.py` and
`app/services/ai_pipeline_service.py` do this at the top of the file.
"""

import sys
from pathlib import Path

AI_SERVICES_DIR = Path(__file__).resolve().parents[3] / "ai-services"

if AI_SERVICES_DIR.is_dir() and str(AI_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICES_DIR))
