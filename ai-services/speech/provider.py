"""Speech-to-text provider interface (PRD Ch3.6/Ch3.20/Ch17.3).

Provider selection is a configuration value (STT_PROVIDER), never a code
branch — swapping providers (Faster-Whisper, OpenAI Whisper API, Deepgram,
Azure Speech, Google STT) means adding a new class here and pointing
config at it, not touching calling code.
"""

from abc import ABC, abstractmethod
from typing import Literal, TypedDict


class TranscriptSegment(TypedDict):
    speaker: Literal["doctor", "patient", "unknown"]
    text: str
    timestamp_start: float
    timestamp_end: float
    confidence: float


class Transcriber(ABC):
    """Implemented once per provider (see whisper.py). The consultation
    pipeline (workers/speech_worker.py) depends only on this interface."""

    @abstractmethod
    def transcribe(self, audio_file: str) -> list[TranscriptSegment]:
        """Return the raw transcript matching consultation_transcripts.raw_transcript
        (PRD Ch15.7.2). Low-confidence segments are retained, not dropped
        (Ch10.4 — indicate uncertainty rather than invent words)."""
        raise NotImplementedError
