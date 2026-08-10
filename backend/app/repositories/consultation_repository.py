"""Consultation repository (PRD Ch15.7.1)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import Consultation
from app.models.enums import ConsultationStatus


class ConsultationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, consultation_id: uuid.UUID, *, hospital_id: uuid.UUID) -> Consultation | None:
        result = await self.db.execute(
            select(Consultation).where(
                Consultation.id == consultation_id,
                Consultation.hospital_id == hospital_id,
                Consultation.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_any_hospital(self, consultation_id: uuid.UUID) -> Consultation | None:
        """Used by the AI pipeline worker, which only has a consultation id
        from the queue (no authenticated hospital context to scope by)."""
        result = await self.db.execute(
            select(Consultation).where(Consultation.id == consultation_id, Consultation.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_by_patient(self, patient_id: uuid.UUID, *, limit: int = 5) -> list[Consultation]:
        result = await self.db.execute(
            select(Consultation)
            .where(Consultation.patient_id == patient_id, Consultation.deleted_at.is_(None))
            .order_by(Consultation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_hospital(
        self,
        hospital_id: uuid.UUID,
        *,
        doctor_id: uuid.UUID | None = None,
        statuses: list[ConsultationStatus] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Consultation], int]:
        stmt = select(Consultation).where(
            Consultation.hospital_id == hospital_id, Consultation.deleted_at.is_(None)
        )
        if doctor_id is not None:
            stmt = stmt.where(Consultation.doctor_id == doctor_id)
        if statuses:
            stmt = stmt.where(Consultation.status.in_(statuses))

        count_result = await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        total = count_result.scalar_one()

        stmt = stmt.order_by(Consultation.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, consultation: Consultation) -> Consultation:
        self.db.add(consultation)
        await self.db.flush()
        return consultation

    async def save(self, consultation: Consultation) -> Consultation:
        await self.db.flush()
        return consultation
