"""Audit logging service (PRD Ch7.16/Ch16.3/Ch20 — every authentication and
administrative event must be recorded). Never logs patient content or secrets.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


async def record_audit_event(
    db: AsyncSession,
    *,
    action: str,
    user_id: uuid.UUID | None,
    hospital_id: uuid.UUID | None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
) -> None:
    entry = AuditLog(
        hospital_id=hospital_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        audit_metadata=metadata,
        created_at=datetime.now(timezone.utc),
    )
    await AuditLogRepository(db).create(entry)


# PRD Ch13.8: a Hospital Admin sees login, logout, report approval, user creation
# and user deactivation events of their own hospital ("detailed audit history is
# reserved for future versions"), not the full platform trail.
HOSPITAL_ADMIN_VISIBLE_ACTIONS = frozenset(
    {
        "login_success",
        "logout",
        "consultation_approved",
        "report_generated",
        "user_created",
        "user_status_changed",
    }
)


async def list_audit_logs(
    db: AsyncSession, *, page: int = 1, page_size: int = 20, hospital_id: uuid.UUID | None = None
) -> tuple[list[AuditLog], int]:
    """Super Admin (`hospital_id=None`): platform-wide trail (PRD Ch6.3 "View Audit
    Logs"). Hospital Admin: only their own hospital's PRD-listed events (Ch13.8)."""
    repo = AuditLogRepository(db)
    if hospital_id is None:
        return await repo.list_all(page=page, page_size=page_size)
    return await repo.list_by_hospital(
        hospital_id, page=page, page_size=page_size, actions=HOSPITAL_ADMIN_VISIBLE_ACTIONS
    )


async def resolve_display_names(
    db: AsyncSession, logs: list[AuditLog]
) -> tuple[dict[uuid.UUID, tuple[str, str]], dict[uuid.UUID, str]]:
    """Bulk lookup (two queries, not one per row) of the users and hospitals
    referenced by a page of audit entries: `({user_id: (name, email)}, {hospital_id: name})`."""
    from sqlalchemy import select

    from app.models.hospital import Hospital
    from app.models.user import User

    user_ids = {log.user_id for log in logs if log.user_id}
    hospital_ids = {log.hospital_id for log in logs if log.hospital_id}
    users: dict[uuid.UUID, tuple[str, str]] = {}
    hospitals: dict[uuid.UUID, str] = {}
    if user_ids:
        rows = await db.execute(select(User.id, User.full_name, User.email).where(User.id.in_(user_ids)))
        users = {row.id: (row.full_name, row.email) for row in rows}
    if hospital_ids:
        rows = await db.execute(select(Hospital.id, Hospital.name).where(Hospital.id.in_(hospital_ids)))
        hospitals = {row.id: row.name for row in rows}
    return users, hospitals
