"""Live-caption worker (PRD Ch9.6): turns streamed consultation audio into captions.

Run as its own process, separate from the AI pipeline worker, so a long
post-consultation job never delays live captions:

    python -m app.workers.live_worker

Consumes the Redis list written by the API's live WebSocket
(`app/core/live_audio.py`), transcribes each consultation's audio in short
chunks and publishes every caption on that consultation's pub/sub channel.
"""

import asyncio
import signal
import time
from typing import Any

from app.core import ai_bridge  # noqa: F401  (adds ai-services/ to sys.path)
from app.core.config import settings
from app.core.live_audio import LiveBuffer, caption_channel, caption_message, decode_frame
from app.core.logging import logger
from app.core.redis import get_redis_bytes, resolve

_shutdown = asyncio.Event()
IDLE_SECONDS = 60  # forget a consultation that has stopped sending audio


def _handle_shutdown_signal(*_args: object) -> None:
    _shutdown.set()


async def _caption(redis: Any, consultation_id: Any, buffer: LiveBuffer, flush: bool = False) -> None:
    """Transcribe every full chunk currently buffered (and the tail when flushing)."""
    from speech.live import transcribe_chunk

    while (chunk := buffer.take_chunk(flush=flush)) is not None:
        start, pcm = chunk
        try:
            # Whisper is CPU-bound and blocking: run it off the event loop.
            text = await asyncio.to_thread(
                transcribe_chunk,
                pcm,
                model_size=settings.live_whisper_model_size,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
                language=settings.live_language,
                prompt=buffer.prompt,
            )
        except Exception:  # noqa: BLE001 - one bad chunk must never stop live captions
            logger.exception("Live captions: transcription failed for consultation %s", consultation_id)
            continue
        if not text:
            continue
        buffer.remember(text)
        buffer.seq += 1
        duration = len(pcm) / 2 / 16_000
        await redis.publish(
            caption_channel(consultation_id), caption_message(buffer.seq, start, start + duration, text)
        )


async def main() -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_shutdown_signal)
        except NotImplementedError:
            pass  # signal handlers are not available on Windows event loops

    redis = get_redis_bytes()
    buffers: dict[Any, LiveBuffer] = {}
    last_seen: dict[Any, float] = {}
    logger.info("Live caption worker started.")

    while not _shutdown.is_set():
        try:
            item = await resolve(redis.brpop([settings.live_audio_key], timeout=1))
        except Exception:  # noqa: BLE001 - Redis hiccup: back off and keep running
            logger.exception("Live captions: Redis read failed")
            await asyncio.sleep(1)
            continue

        now = time.monotonic()
        if item is not None:
            try:
                consultation_id, pcm = decode_frame(item[1])
            except ValueError:
                continue
            buffer = buffers.setdefault(consultation_id, LiveBuffer(chunk_seconds=settings.live_chunk_seconds))
            last_seen[consultation_id] = now
            if pcm:
                buffer.append(pcm)
                await _caption(redis, consultation_id, buffer)
            else:  # end-of-audio marker: caption whatever is left, then forget the consultation
                await _caption(redis, consultation_id, buffer, flush=True)
                buffers.pop(consultation_id, None)
                last_seen.pop(consultation_id, None)

        for consultation_id in [cid for cid, seen in last_seen.items() if now - seen > IDLE_SECONDS]:
            buffers.pop(consultation_id, None)
            last_seen.pop(consultation_id, None)

    logger.info("Live caption worker shutting down.")


if __name__ == "__main__":
    asyncio.run(main())
