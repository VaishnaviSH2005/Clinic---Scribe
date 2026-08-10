"""Standalone AI pipeline worker process (PRD Ch3.5/Ch17.2).

Run as its own process/container, separate from the API server, so a
long-running AI stage never competes with request handling:

    python -m app.workers.pipeline_worker

Consumes `app/core/ai_queue.py`'s Redis list (pushed by
`consultation_service.stop_consultation` and the doctor-triggered retry
endpoints) and runs `app.services.ai_pipeline_service.run_pipeline` for
each consultation id, one at a time. Import order matters here: the
`ai_bridge` sys.path bootstrap must run before `ai_pipeline_service` (or
anything under `ai-services/`) is imported.
"""

import asyncio
import signal
import uuid

from app.core import ai_bridge  # noqa: F401  (adds ai-services/ to sys.path)
from app.core.ai_queue import AiJob, dequeue_ai_job
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.services.ai_pipeline_service import run_pipeline, run_single_stage_from_queue

_shutdown = asyncio.Event()


def _handle_shutdown_signal(*_args: object) -> None:
    _shutdown.set()


async def _process_one(job: AiJob) -> None:
    consultation_id = uuid.UUID(job["consultation_id"])
    stage = job.get("stage")
    async with AsyncSessionLocal() as db:
        try:
            if stage:
                await run_single_stage_from_queue(db, consultation_id=consultation_id, stage=stage)
            else:
                await run_pipeline(db, consultation_id=consultation_id)
        except Exception:  # noqa: BLE001 - a single bad job must not kill the worker loop
            logger.exception("AI pipeline worker: unhandled error processing consultation %s", consultation_id)
            await db.rollback()


async def main() -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_shutdown_signal)
        except NotImplementedError:
            pass  # signal handlers are not available on Windows event loops

    logger.info("AI pipeline worker started.")
    while not _shutdown.is_set():
        job = await dequeue_ai_job(timeout_seconds=5)
        if job is None:
            continue
        await _process_one(job)
    logger.info("AI pipeline worker shutting down.")


if __name__ == "__main__":
    asyncio.run(main())
