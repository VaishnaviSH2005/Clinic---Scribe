"""Transcript cleaning (PRD Ch17.2 `clean_transcript` stage): strips filler
words/false starts from the raw STT output before it is handed to entity
extraction and Claude. Purely textual — never drops or reorders segments,
since the raw transcript remains the source of truth (Ch10.4).
"""

import re

from .provider import TranscriptSegment

_FILLER_RE = re.compile(r"\b(um+|uh+|erm+|you know|i mean)\b[,.]?", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


def clean_transcript(raw_transcript: list[TranscriptSegment]) -> list[TranscriptSegment]:
    cleaned: list[TranscriptSegment] = []
    for segment in raw_transcript:
        text = _FILLER_RE.sub("", segment["text"])
        text = _WHITESPACE_RE.sub(" ", text).strip(" ,")
        if not text:
            continue
        cleaned.append({**segment, "text": text})
    return cleaned
