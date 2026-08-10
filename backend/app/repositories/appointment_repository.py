"""Appointment repository (PRD Ch15.6.1)."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus


class AppointmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, appointment_id: uuid.UUID, *, hospital_id: uuid.UUID) -> Appointment | None:
        result = await self.db.execute(
            select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.hospital_id == hospital_id,
                Appointment.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_patient(self, patient_id: uuid.UUID) -> list[Appointment]:
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.patient_id == patient_id, Appointment.deleted_at.is_(None))
            .order_by(Appointment.scheduled_at.desc())
        )
        return list(result.scalars().all())

    async def find_conflict(
        self, doctor_id: uuid.UUID, scheduled_at: datetime, *, exclude_id: uuid.UUID | None = None
    ) -> Appointment | None:
        """Business rule: a doctor cannot have two active appointments at the
        exact same time (Ch9 assumes one consultation at a time)."""
        stmt = select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_at == scheduled_at,
            Appointment.status.in_([AppointmentStatus.upcoming, AppointmentStatus.checked_in]),
            Appointment.deleted_at.is_(None),
        )
        if exclude_id is not None:
            stmt = stmt.where(Appointment.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_hospital(
        self,
        hospital_id: uuid.UUID,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        doctor_id: uuid.UUID | None = None,
        department_id: uuid.UUID | None = None,
        status: AppointmentStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Appointment], int]:
        stmt = select(Appointment).where(Appointment.hospital_id == hospital_id, Appointment.deleted_at.is_(None))
        if date_from is not None:
            stmt = stmt.where(Appointment.scheduled_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(Appointment.scheduled_at < date_to)
        if doctor_id is not None:
            stmt = stmt.where(Appointment.doctor_id == doctor_id)
        if department_id is not None:
            stmt = stmt.where(Appointment.department_id == department_id)
        if status is not None:
            stmt = stmt.where(Appointment.status == status)

        count_result = await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        total = count_result.scalar_one()

        stmt = stmt.order_by(Appointment.scheduled_at.asc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        await self.db.flush()
        return appointment

    async def save(self, appointment: Appointment) -> Appointment:
        await self.db.flush()
        return appointment
