"""Provider factory: resolves the configured STT_PROVIDER to a Transcriber
implementation (PRD Ch17.3). Only configuration changes are needed to swap
providers — never code changes at the call site.
"""

from .provider import Transcriber


def get_transcriber(provider_name: str) -> Transcriber:
    if provider_name == "faster_whisper":
        from .whisper import WhisperTranscriber

        return WhisperTranscriber()
    raise ValueError(f"Unknown STT provider: {provider_name}")
