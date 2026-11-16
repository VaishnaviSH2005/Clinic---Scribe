"""A consultation stranded in `ai_processing` (worker crash, Redis restart, lost
job) must be re-queued instead of hanging forever (PRD Ch9.21: a consultation is
never lost because of an AI failure)."""

import uuid
from typing import Any

from app.services import ai_pipeline_service


class _Result:
    def __init__(self, ids: list[uuid.UUID]):
        self._ids = ids

    def scalars(self) -> "_Result":
        return self

    def all(self) -> list[uuid.UUID]:
        return self._ids


class _Db:
    def __init__(self, ids: list[uuid.UUID]):
        self.ids = ids

    async def execute(self, _stmt: Any) -> _Result:
        return _Result(self.ids)


async def test_stuck_consultations_are_requeued(monkeypatch) -> None:
    queued: list[uuid.UUID] = []

    async def fake_enqueue(consultation_id: uuid.UUID, *, stage: str | None = None) -> None:
        queued.append(consultation_id)

    monkeypatch.setattr(ai_pipeline_service, "enqueue_ai_job", fake_enqueue)
    ids = [uuid.uuid4(), uuid.uuid4()]
    assert await ai_pipeline_service.recover_stuck_consultations(_Db(ids)) == 2  # type: ignore[arg-type]
    assert queued == ids


async def test_nothing_stuck_means_nothing_queued(monkeypatch) -> None:
    queued: list[uuid.UUID] = []

    async def fake_enqueue(consultation_id: uuid.UUID, *, stage: str | None = None) -> None:
        queued.append(consultation_id)

    monkeypatch.setattr(ai_pipeline_service, "enqueue_ai_job", fake_enqueue)
    assert await ai_pipeline_service.recover_stuck_consultations(_Db([])) == 0  # type: ignore[arg-type]
    assert queued == []
