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


async def list_audit_logs(db: AsyncSession, *, page: int = 1, page_size: int = 20) -> tuple[list[AuditLog], int]:
    """Platform-wide audit trail (PRD Ch6.3 — Super Admin "View Audit Logs")."""
    return await AuditLogRepository(db).list_all(page=page, page_size=page_size)
