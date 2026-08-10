# AI Services

Isolated AI/ML layer (PRD Ch4.6 / Ch17). Consumed by the backend's
`workers/` (speech_worker.py, summary_worker.py) — never called directly
from the frontend or from business logic outside the worker layer.

```
ai-services/
├── speech/         Speech-to-text provider interface (Ch17.3)
├── nlp/            Medical entity extraction — SciSpaCy/MedCAT (Ch17.4)
├── summarization/  SOAP + clinical summary generation (Ch17.5)
├── reasoning/       Possible diagnoses / red flags (Ch10.11-10.12)
├── prompts/         Versioned prompt templates — never hardcoded (Ch4.6)
├── embeddings/      pgvector embeddings (reserved, unused in Version 1)
└── providers/        Shared provider interfaces
```

No business modules (transcription pipeline wiring, entity extraction
logic, prompt content) are implemented in this milestone — structure only.
