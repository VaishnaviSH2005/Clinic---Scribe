"""Notification creation/retrieval (PRD Ch15.9.1). Notifications are created
only for the concrete triggers already wired into the system — never a
generic catch-all — so every row traces back to a real event:

- `ai_processing_complete` — the AI pipeline finishes for a consultation
  (`ai_pipeline_service`), notifying the assigned doctor.
- `report_generated` — a consultation report finishes rendering
  (`report_service`), notifying the approving doctor.
- `consultation_pending` — a consultation reaches `pending_review`
  without AI content (no audio captured), notifying the doctor that manual
  review is needed.

`appointment_reminder` is a scheduled/time-based notification type defined
in the PRD's enum, but no scheduler/cron infrastructure exists in this
codebase (Ch3 defines Redis/queue infra, not a job scheduler) — creating it
here would require inventing a component outside this milestone's scope, so
it is intentionally not triggered.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.enums import NotificationType
from app.models.platform import Notification
from app.repositories.notification_repository import NotificationRepository


class NotificationNotFoundError(NotFoundError):
    error_code = "NOTIFICATION_NOT_FOUND"


async def notify_user(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    message: str | None,
    reference_id: uuid.UUID | None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=NotificationType(notification_type),
        title=title,
        message=message,
        reference_id=reference_id,
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    return await NotificationRepository(db).create(notification)


async def list_notifications(
    db: AsyncSession, *, user_id: uuid.UUID, unread_only: bool, page: int, page_size: int
) -> tuple[list[Notification], int]:
    return await NotificationRepository(db).list_by_user(
        user_id, unread_only=unread_only, page=page, page_size=page_size
    )


async def count_unread(db: AsyncSession, *, user_id: uuid.UUID) -> int:
    return await NotificationRepository(db).count_unread(user_id)


async def mark_read(db: AsyncSession, *, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
    repo = NotificationRepository(db)
    notification = await repo.get_by_id(notification_id, user_id=user_id)
    if notification is None:
        raise NotificationNotFoundError("The requested notification could not be located.")
    return await repo.mark_read(notification)


async def mark_all_read(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    await NotificationRepository(db).mark_all_read(user_id)
