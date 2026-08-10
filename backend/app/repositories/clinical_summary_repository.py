"""Clinical summary repository (PRD Ch15.7.5)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import ClinicalSummary


class ClinicalSummaryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_consultation_id(self, consultation_id: uuid.UUID) -> ClinicalSummary | None:
        result = await self.db.execute(
            select(ClinicalSummary).where(ClinicalSummary.consultation_id == consultation_id)
        )
        return result.scalar_one_or_none()

    async def create(self, summary: ClinicalSummary) -> ClinicalSummary:
        self.db.add(summary)
        await self.db.flush()
        return summary

    async def save(self, summary: ClinicalSummary) -> ClinicalSummary:
        await self.db.flush()
        return summary
