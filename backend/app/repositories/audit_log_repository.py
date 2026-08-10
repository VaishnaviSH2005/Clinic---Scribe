"""Audit log repository (PRD Ch15.9.2 — append-only)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import AuditLog


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, entry: AuditLog) -> AuditLog:
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def list_by_hospital(
        self, hospital_id: uuid.UUID, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[AuditLog], int]:
        base = select(AuditLog).where(AuditLog.hospital_id == hospital_id)
        count_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar_one()
        stmt = base.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def list_all(self, *, page: int = 1, page_size: int = 20) -> tuple[list[AuditLog], int]:
        base = select(AuditLog)
        count_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar_one()
        stmt = base.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_entity(
        self, *, entity_type: str, entity_id: uuid.UUID, action_prefix: str | None = None
    ) -> list[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
        if action_prefix:
            stmt = stmt.where(AuditLog.action.like(f"{action_prefix}%"))
        stmt = stmt.order_by(AuditLog.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_by_entity(
        self, *, entity_type: str, entity_id: uuid.UUID, action_prefix: str
    ) -> AuditLog | None:
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
                AuditLog.action.like(f"{action_prefix}%"),
            )
            .order_by(AuditLog.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
