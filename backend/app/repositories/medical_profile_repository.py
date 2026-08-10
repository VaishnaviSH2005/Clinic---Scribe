"""Medical profile repository (PRD Ch15.5.2)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import MedicalProfile


class MedicalProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_patient_id(self, patient_id: uuid.UUID) -> MedicalProfile | None:
        result = await self.db.execute(select(MedicalProfile).where(MedicalProfile.patient_id == patient_id))
        return result.scalar_one_or_none()

    async def create(self, profile: MedicalProfile) -> MedicalProfile:
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def save(self, profile: MedicalProfile) -> MedicalProfile:
        await self.db.flush()
        return profile
