"""Consultation transcript repository (PRD Ch15.7.2)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import ConsultationTranscript


class ConsultationTranscriptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_consultation_id(self, consultation_id: uuid.UUID) -> ConsultationTranscript | None:
        result = await self.db.execute(
            select(ConsultationTranscript).where(ConsultationTranscript.consultation_id == consultation_id)
        )
        return result.scalar_one_or_none()

    async def create(self, transcript: ConsultationTranscript) -> ConsultationTranscript:
        self.db.add(transcript)
        await self.db.flush()
        return transcript

    async def save(self, transcript: ConsultationTranscript) -> ConsultationTranscript:
        await self.db.flush()
        return transcript
