"""Hospital repository (PRD Ch15.4.1)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hospital import Hospital


class HospitalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, hospital_id: uuid.UUID) -> Hospital | None:
        result = await self.db.execute(
            select(Hospital).where(Hospital.id == hospital_id, Hospital.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_registration_number(self, registration_number: str) -> Hospital | None:
        result = await self.db.execute(
            select(Hospital).where(
                Hospital.registration_number == registration_number, Hospital.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, page: int = 1, page_size: int = 20) -> tuple[list[Hospital], int]:
        base = select(Hospital).where(Hospital.deleted_at.is_(None))
        count_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar_one()
        stmt = base.order_by(Hospital.name).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, hospital: Hospital) -> Hospital:
        self.db.add(hospital)
        await self.db.flush()
        return hospital

    async def save(self, hospital: Hospital) -> Hospital:
        await self.db.flush()
        return hospital
