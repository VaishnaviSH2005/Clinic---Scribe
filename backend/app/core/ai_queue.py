"""Redis-backed queue for the AI clinical documentation pipeline (PRD
Ch3.5/Ch17.2). `POST /consultations/{id}/stop` and the doctor-triggered
retry/regenerate endpoints (`app/api/v1/ai.py`) push a job here rather than
running the pipeline inline, so a long-running AI stage never blocks an
HTTP request and the API process never needs the heavy ML dependencies
(those live only in the `worker` container/process — see
`ai-services/README.md`). The standalone `app/workers/pipeline_worker.py`
process consumes this queue.

Unlike `core/rate_limit.py` (which fails open because it protects a
security control with a second layer of defense), a queue failure here must
not be silently swallowed — losing an enqueue means a consultation would be
stuck in `ai_processing` forever. Callers are expected to let `RedisError`
propagate so it surfaces as a clear error rather than a silently dropped job
(`consultation_service.stop_consultation` is the one deliberate exception —
see its docstring for why it degrades instead of failing the stop request).
"""

import json
import uuid
from typing import TypedDict

from app.core.config import settings
from app.core.redis import get_redis


class AiJob(TypedDict):
    consultation_id: str
    stage: str | None  # None => run the full pipeline; otherwise a single-stage retry/regenerate


async def enqueue_ai_job(consultation_id: uuid.UUID, *, stage: str | None = None) -> None:
    redis = get_redis()
    job: AiJob = {"consultation_id": str(consultation_id), "stage": stage}
    await redis.lpush(settings.ai_queue_key, json.dumps(job))


async def dequeue_ai_job(timeout_seconds: int = 5) -> AiJob | None:
    """Blocking pop used by the standalone worker loop. Returns None on a
    timeout (no job available) so the caller's loop can check for shutdown."""
    redis = get_redis()
    result = await redis.brpop([settings.ai_queue_key], timeout=timeout_seconds)
    if result is None:
        return None
    _key, value = result
    return json.loads(value)


async def queue_depth() -> int:
    redis = get_redis()
    return await redis.llen(settings.ai_queue_key)
