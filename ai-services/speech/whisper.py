"""Faster-Whisper (local) implementation of the Transcriber interface
(PRD Ch3.6 — default MVP provider, no external API cost).

The model is loaded lazily and cached at module scope so repeated
transcriptions within the same worker process do not reload weights.
"""

from functools import lru_cache

from .provider import Transcriber, TranscriptSegment


@lru_cache(maxsize=1)
def _load_model(model_size: str, device: str, compute_type: str):
    from faster_whisper import WhisperModel

    return WhisperModel(model_size, device=device, compute_type=compute_type)


class WhisperTranscriber(Transcriber):
    """PRD Ch17.3 — STT provider is a config value, never a code branch.

    Faster-Whisper has no speaker-diarization output on its own, so every
    segment is labelled "unknown" (PRD Ch10.4 allows this — indicating
    uncertainty is preferred over inventing a speaker label).
    """

    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

    def transcribe(self, audio_file: str) -> list[TranscriptSegment]:
        model = _load_model(self.model_size, self.device, self.compute_type)
        segments, _info = model.transcribe(audio_file, beam_size=5, vad_filter=True)

        result: list[TranscriptSegment] = []
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue
            word_probs = [word.probability for word in (segment.words or []) if word.probability is not None]
            confidence = sum(word_probs) / len(word_probs) if word_probs else 0.5
            result.append(
                TranscriptSegment(
                    speaker="unknown",
                    text=text,
                    timestamp_start=round(segment.start, 2),
                    timestamp_end=round(segment.end, 2),
                    confidence=round(confidence, 3),
                )
            )
        return result
