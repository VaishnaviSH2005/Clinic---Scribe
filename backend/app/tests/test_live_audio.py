"""Live-caption plumbing (PRD Ch9.6): frame format, validation and chunking."""

import uuid

import pytest

from app.core.live_audio import (
    MAX_FRAME_BYTES,
    SAMPLE_RATE,
    LiveBuffer,
    caption_channel,
    decode_frame,
    encode_frame,
    valid_pcm,
)

SECOND = SAMPLE_RATE * 2  # bytes of PCM per second


def test_frame_roundtrip_keeps_the_consultation_and_audio() -> None:
    cid = uuid.uuid4()
    decoded_cid, pcm = decode_frame(encode_frame(cid, b"\x01\x02\x03\x04"))
    assert decoded_cid == cid and pcm == b"\x01\x02\x03\x04"


def test_end_marker_is_a_frame_with_no_audio() -> None:
    cid = uuid.uuid4()
    assert decode_frame(encode_frame(cid, b"")) == (cid, b"")


def test_truncated_frame_is_rejected() -> None:
    with pytest.raises(ValueError):
        decode_frame(b"short")


@pytest.mark.parametrize(
    ("size", "ok"),
    [(0, False), (1, False), (2, True), (MAX_FRAME_BYTES, True), (MAX_FRAME_BYTES + 2, False)],
)
def test_pcm_validation(size: int, ok: bool) -> None:
    assert valid_pcm(b"\x00" * size) is ok


def test_each_consultation_has_its_own_caption_channel() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    assert caption_channel(a) != caption_channel(b)
    assert str(a) in caption_channel(a)


def test_no_chunk_until_enough_audio_has_arrived() -> None:
    buf = LiveBuffer(chunk_seconds=3)
    buf.append(b"\x00" * (SECOND * 2))
    assert buf.take_chunk() is None


def test_full_chunks_are_handed_out_in_order_with_timestamps() -> None:
    buf = LiveBuffer(chunk_seconds=3)
    buf.append(b"\x00" * (SECOND * 7))  # 7 s -> two 3 s chunks, 1 s left over
    first, second = buf.take_chunk(), buf.take_chunk()
    assert first is not None and second is not None
    assert first[0] == 0.0 and len(first[1]) == SECOND * 3
    assert second[0] == 3.0
    assert buf.take_chunk() is None
    assert len(buf.pending) == SECOND


def test_flush_returns_the_remaining_tail_but_ignores_a_blip() -> None:
    buf = LiveBuffer(chunk_seconds=3)
    buf.append(b"\x00" * SECOND)  # 1 s tail
    tail = buf.take_chunk(flush=True)
    assert tail is not None and len(tail[1]) == SECOND

    tiny = LiveBuffer(chunk_seconds=3)
    tiny.append(b"\x00" * (SECOND // 10))  # 0.1 s: too short to be speech
    assert tiny.take_chunk(flush=True) is None


def test_prompt_keeps_only_the_recent_tail() -> None:
    buf = LiveBuffer()
    buf.remember("a" * 150)
    buf.remember("b" * 150)
    assert len(buf.prompt) == 200 and buf.prompt.endswith("b" * 150)
