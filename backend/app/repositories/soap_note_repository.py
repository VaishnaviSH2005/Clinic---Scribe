"""SOAP note repository (PRD Ch15.7.4)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import SoapNote


class SoapNoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_consultation_id(self, consultation_id: uuid.UUID) -> SoapNote | None:
        result = await self.db.execute(select(SoapNote).where(SoapNote.consultation_id == consultation_id))
        return result.scalar_one_or_none()

    async def create(self, note: SoapNote) -> SoapNote:
        self.db.add(note)
        await self.db.flush()
        return note

    async def save(self, note: SoapNote) -> SoapNote:
        await self.db.flush()
        return note
