"""Report repository (PRD Ch15.8.1)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report


class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, report_id: uuid.UUID, *, hospital_id: uuid.UUID) -> Report | None:
        result = await self.db.execute(
            select(Report).where(
                Report.id == report_id, Report.hospital_id == hospital_id, Report.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_consultation_id(self, consultation_id: uuid.UUID) -> Report | None:
        result = await self.db.execute(
            select(Report).where(Report.consultation_id == consultation_id, Report.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_by_hospital(
        self,
        hospital_id: uuid.UUID,
        *,
        doctor_id: uuid.UUID | None = None,
        patient_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Report], int]:
        stmt = select(Report).where(Report.hospital_id == hospital_id, Report.deleted_at.is_(None))
        if patient_id is not None:
            stmt = stmt.where(Report.patient_id == patient_id)
        if doctor_id is not None:
            stmt = stmt.where(Report.created_by == doctor_id)

        count_result = await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        total = count_result.scalar_one()

        stmt = stmt.order_by(Report.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, report: Report) -> Report:
        self.db.add(report)
        await self.db.flush()
        return report

    async def save(self, report: Report) -> Report:
        await self.db.flush()
        return report

    async def count_by_hospital(self, hospital_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(Report.hospital_id == hospital_id, Report.deleted_at.is_(None))
        )
        return result.scalar_one()
