"""Shared plumbing for live (near-real-time) captions during a consultation
(PRD Ch9.6 "Live Transcript", Ch9.22 transcript delay target).

Flow:  browser --PCM frames--> API WebSocket --Redis list--> live worker
       browser <--captions---- API WebSocket <--Redis pub/sub-- live worker

Frame format (API -> worker, one Redis list entry): 16-byte consultation UUID
followed by raw PCM — signed 16-bit little-endian, mono, 16 kHz. An entry with
no PCM after the UUID is an "end of audio" marker.

Live captions are a best-effort preview. The authoritative transcript is still
produced from the full recording by the pipeline worker after the doctor presses
Stop, so a dropped frame or a missing live worker never loses clinical data.
"""

import json
import uuid
from dataclasses import dataclass, field

SAMPLE_RATE = 16_000
BYTES_PER_SAMPLE = 2
MAX_FRAME_BYTES = 128 * 1024  # ~4 seconds of audio; larger frames are rejected
MAX_QUEUED_FRAMES = 600  # if the worker falls behind, the oldest audio is dropped
CAPTION_CHANNEL_PREFIX = "cliniscribe:live:captions:"


def caption_channel(consultation_id: uuid.UUID) -> str:
    return f"{CAPTION_CHANNEL_PREFIX}{consultation_id}"


def encode_frame(consultation_id: uuid.UUID, pcm: bytes) -> bytes:
    return consultation_id.bytes + pcm


def decode_frame(raw: bytes) -> tuple[uuid.UUID, bytes]:
    if len(raw) < 16:
        raise ValueError("live audio frame is shorter than its header")
    return uuid.UUID(bytes=raw[:16]), raw[16:]


def valid_pcm(data: bytes) -> bool:
    """A usable PCM frame: non-empty, whole 16-bit samples, within the size cap."""
    return 0 < len(data) <= MAX_FRAME_BYTES and len(data) % BYTES_PER_SAMPLE == 0


def caption_message(seq: int, start: float, end: float, text: str) -> bytes:
    return json.dumps(
        {"type": "caption", "seq": seq, "start": round(start, 2), "end": round(end, 2), "text": text}
    ).encode()


@dataclass
class LiveBuffer:
    """Accumulates one consultation's PCM and hands out fixed-size chunks to transcribe."""

    chunk_seconds: float = 3.0
    pending: bytearray = field(default_factory=bytearray)
    consumed_samples: int = 0  # samples already handed out (for caption timestamps)
    seq: int = 0
    prompt: str = ""  # tail of the previous captions, fed to Whisper for continuity

    @property
    def chunk_bytes(self) -> int:
        return int(self.chunk_seconds * SAMPLE_RATE) * BYTES_PER_SAMPLE

    def append(self, pcm: bytes) -> None:
        self.pending += pcm

    def take_chunk(self, *, flush: bool = False, min_flush_seconds: float = 0.5) -> tuple[float, bytes] | None:
        """Next `chunk_seconds` of audio as `(start_seconds, pcm)`, or None if not enough yet.
        With `flush=True` the remaining tail is returned too, if it is long enough to be speech."""
        size = self.chunk_bytes
        if len(self.pending) >= size:
            data = bytes(self.pending[:size])
            del self.pending[:size]
        elif flush and len(self.pending) >= int(min_flush_seconds * SAMPLE_RATE) * BYTES_PER_SAMPLE:
            data = bytes(self.pending)
            self.pending.clear()
        else:
            return None
        start = self.consumed_samples / SAMPLE_RATE
        self.consumed_samples += len(data) // BYTES_PER_SAMPLE
        return start, data

    def remember(self, text: str, max_chars: int = 200) -> None:
        self.prompt = (self.prompt + " " + text).strip()[-max_chars:]
