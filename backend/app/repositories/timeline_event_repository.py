"""Timeline event repository (PRD Ch15.5.5 — always read newest-first)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import TimelineEvent


class TimelineEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_patient(self, patient_id: uuid.UUID) -> list[TimelineEvent]:
        result = await self.db.execute(
            select(TimelineEvent)
            .where(TimelineEvent.patient_id == patient_id)
            .order_by(TimelineEvent.event_date.desc())
        )
        return list(result.scalars().all())

    async def create(self, event: TimelineEvent) -> TimelineEvent:
        self.db.add(event)
        await self.db.flush()
        return event
