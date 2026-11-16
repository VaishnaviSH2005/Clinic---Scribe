"""Regression: saved notification preferences must actually suppress
notifications (found in the A-to-Z run: the toggle saved but was ignored)."""

import uuid

import pytest

from app.schemas.settings_schema import NotificationPreferences
from app.services import notification_service


class _Recorder:
    created: list = []

    def __init__(self, _db):
        pass

    async def create(self, notification):
        _Recorder.created.append(notification)
        return notification


def _prefs(**overrides):
    async def fake(_db, *, user_id):
        return type("S", (), {"notification_preferences": NotificationPreferences(**overrides)})()

    return fake


@pytest.fixture(autouse=True)
def _patch(monkeypatch):
    _Recorder.created = []
    monkeypatch.setattr(notification_service, "NotificationRepository", _Recorder)


async def _send(ntype: str):
    return await notification_service.notify_user(
        None,  # type: ignore[arg-type]
        user_id=uuid.uuid4(),
        notification_type=ntype,
        title="t",
        message="m",
        reference_id=None,  # type: ignore[arg-type]
    )


async def test_disabled_type_is_not_created(monkeypatch) -> None:
    monkeypatch.setattr(
        notification_service.settings_service, "get_user_settings", _prefs(ai_processing_complete=False)
    )
    assert await _send("ai_processing_complete") is None
    assert _Recorder.created == []


async def test_enabled_type_is_created(monkeypatch) -> None:
    monkeypatch.setattr(notification_service.settings_service, "get_user_settings", _prefs())
    assert await _send("report_generated") is not None
    assert len(_Recorder.created) == 1


async def test_only_the_switched_off_type_is_suppressed(monkeypatch) -> None:
    monkeypatch.setattr(
        notification_service.settings_service, "get_user_settings", _prefs(ai_processing_complete=False)
    )
    assert await _send("report_generated") is not None
    assert await _send("consultation_pending") is not None


async def test_types_without_a_toggle_are_always_delivered(monkeypatch) -> None:
    monkeypatch.setattr(
        notification_service.settings_service,
        "get_user_settings",
        _prefs(ai_processing_complete=False, report_generated=False, consultation_pending=False),
    )
    assert await _send("system") is not None
    assert await _send("appointment_reminder") is not None
