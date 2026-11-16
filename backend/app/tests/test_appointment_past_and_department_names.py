"""Past-dated appointments need explicit confirmation ("book anyway"), and
department names are unique per hospital, case-insensitively (owner decisions on
behaviour the PRD leaves open)."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from app.services import department_service
from app.services.appointment_service import AppointmentInPastError, _ensure_not_in_past

NOW = datetime.now(timezone.utc)


def test_future_time_is_fine() -> None:
    assert _ensure_not_in_past(NOW + timedelta(hours=1), allow_past=False) is False


def test_time_within_the_grace_window_is_not_treated_as_past() -> None:
    assert _ensure_not_in_past(NOW - timedelta(minutes=2), allow_past=False) is False


def test_past_time_is_refused_without_confirmation() -> None:
    with pytest.raises(AppointmentInPastError) as err:
        _ensure_not_in_past(NOW - timedelta(days=1), allow_past=False)
    assert err.value.error_code == "APPOINTMENT_IN_PAST"


def test_confirmed_past_time_is_accepted_and_flagged_as_backdated() -> None:
    assert _ensure_not_in_past(NOW - timedelta(days=1), allow_past=True) is True


def test_naive_timestamps_are_treated_as_utc() -> None:
    naive_past = (NOW - timedelta(days=2)).replace(tzinfo=None)
    with pytest.raises(AppointmentInPastError):
        _ensure_not_in_past(naive_past, allow_past=False)


class _Repo:
    def __init__(self, exists: bool):
        self.exists = exists
        self.seen: tuple[Any, ...] = ()

    async def name_exists(self, hospital_id: uuid.UUID, name: str, *, exclude_id: uuid.UUID | None = None) -> bool:
        self.seen = (hospital_id, name, exclude_id)
        return self.exists


async def test_duplicate_department_name_is_rejected(monkeypatch) -> None:
    repo = _Repo(exists=True)
    monkeypatch.setattr(department_service, "DepartmentRepository", lambda _db: repo)
    data = type("D", (), {"name": "  Cardiology ", "head_of_department_id": None})()
    fake_db: Any = None  # never touched: the duplicate check runs first
    with pytest.raises(department_service.DuplicateDepartmentError):
        await department_service.create_department(
            fake_db, hospital_id=uuid.uuid4(), data=data, actor_id=uuid.uuid4()
        )
    assert repo.seen[1] == "Cardiology"  # trimmed before the check
