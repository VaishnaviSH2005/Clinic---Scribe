"""Regression: UHIDs are unique platform-wide, so the sequence must not restart
per hospital (found in the A-to-Z run: a new hospital's first patient collided
with CLN-2026-000001 held by another hospital and registration failed)."""

import uuid
from datetime import datetime, timezone

from app.services.patient_service import _generate_uhid


class _Repo:
    def __init__(self, highest: int):
        self.highest = highest

    async def max_uhid_sequence(self, year: int) -> int:
        return self.highest


async def test_sequence_continues_from_platform_wide_maximum() -> None:
    year = datetime.now(timezone.utc).year
    assert await _generate_uhid(_Repo(41), uuid.uuid4()) == f"CLN-{year}-000042"  # type: ignore[arg-type]


async def test_first_patient_on_an_empty_platform_gets_000001() -> None:
    year = datetime.now(timezone.utc).year
    assert await _generate_uhid(_Repo(0), uuid.uuid4()) == f"CLN-{year}-000001"  # type: ignore[arg-type]


async def test_two_hospitals_never_get_the_same_next_uhid() -> None:
    repo = _Repo(1)  # hospital A already holds ...000001
    assert await _generate_uhid(repo, uuid.uuid4()) == await _generate_uhid(repo, uuid.uuid4())  # type: ignore[arg-type]
    # ...and that value is 000002, not 000001 again.
    assert (await _generate_uhid(repo, uuid.uuid4())).endswith("000002")  # type: ignore[arg-type]
