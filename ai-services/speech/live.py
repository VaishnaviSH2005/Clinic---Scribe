"""Chunk-level speech recognition for live captions (PRD Ch9.6).

Uses a small, fast Faster-Whisper model (config `LIVE_WHISPER_MODEL_SIZE`) on
short in-memory chunks of 16 kHz mono PCM — no files, no ffmpeg. This is a
preview only; the accurate transcript comes from `whisper.py` over the whole
recording after the consultation is stopped.
"""

from functools import lru_cache

from .whisper import _load_model


@lru_cache(maxsize=1)
def _model(model_size: str, device: str, compute_type: str):
    return _load_model(model_size, device, compute_type)


def transcribe_chunk(
    pcm_s16le: bytes,
    *,
    model_size: str = "base",
    device: str = "cpu",
    compute_type: str = "int8",
    language: str | None = None,
    prompt: str = "",
) -> str:
    """Text spoken in one chunk of signed 16-bit little-endian 16 kHz mono PCM ('' if silence)."""
    import numpy as np

    audio = np.frombuffer(pcm_s16le, dtype="<i2").astype(np.float32) / 32768.0
    model = _model(model_size, device, compute_type)
    segments, _info = model.transcribe(
        audio,
        beam_size=1,
        language=language or None,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300},
        condition_on_previous_text=False,
        initial_prompt=prompt or None,
    )
    return " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
