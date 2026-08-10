"""Report version repository (PRD Ch15.8.2) — append-only snapshot history."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import ReportVersion


class ReportVersionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_report_id(self, report_id: uuid.UUID) -> list[ReportVersion]:
        result = await self.db.execute(
            select(ReportVersion)
            .where(ReportVersion.report_id == report_id)
            .order_by(ReportVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def get_by_report_and_version(self, report_id: uuid.UUID, version_number: int) -> ReportVersion | None:
        result = await self.db.execute(
            select(ReportVersion).where(
                ReportVersion.report_id == report_id, ReportVersion.version_number == version_number
            )
        )
        return result.scalar_one_or_none()

    async def create(self, version: ReportVersion) -> ReportVersion:
        self.db.add(version)
        await self.db.flush()
        return version
