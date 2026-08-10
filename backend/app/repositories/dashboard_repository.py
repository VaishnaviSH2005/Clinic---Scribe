"""Aggregate read queries backing the role-aware Dashboard (PRD Ch5.16 /
role-specific dashboard chapters). Every query is real — computed straight
from the same tables the rest of the application writes to — never a
hardcoded or fabricated statistic.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.consultation import Consultation
from app.models.enums import AppointmentStatus, ConsultationStatus, HospitalStatus
from app.models.hospital import Hospital
from app.models.patient import Patient
from app.models.report import Report
from app.models.user import User


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def platform_hospital_counts(self) -> dict[str, int]:
        result = await self.db.execute(select(Hospital.status, func.count()).group_by(Hospital.status))
        counts = {status.value: count for status, count in result.all()}
        return {
            "total": sum(counts.values()),
            "active": counts.get(HospitalStatus.active.value, 0),
            "inactive": counts.get(HospitalStatus.inactive.value, 0),
            "suspended": counts.get(HospitalStatus.suspended.value, 0),
        }

    async def platform_user_count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(User).where(User.deleted_at.is_(None)))
        return result.scalar_one()

    async def hospital_patient_count(self, hospital_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(Patient.hospital_id == hospital_id, Patient.deleted_at.is_(None))
        )
        return result.scalar_one()

    async def hospital_appointments_today(self, hospital_id: uuid.UUID) -> int:
        today = date.today()
        result = await self.db.execute(
            select(func.count()).where(
                Appointment.hospital_id == hospital_id,
                func.date(Appointment.scheduled_at) == today,
                Appointment.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def hospital_active_consultations(self, hospital_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                Consultation.hospital_id == hospital_id,
                Consultation.status.in_([ConsultationStatus.in_progress, ConsultationStatus.ai_processing]),
                Consultation.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def hospital_pending_reviews(self, hospital_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                Consultation.hospital_id == hospital_id,
                Consultation.status == ConsultationStatus.pending_review,
                Consultation.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def hospital_staff_count(self, hospital_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(User.hospital_id == hospital_id, User.deleted_at.is_(None))
        )
        return result.scalar_one()

    async def doctor_appointments_today(self, doctor_id: uuid.UUID) -> list[Appointment]:
        today = date.today()
        result = await self.db.execute(
            select(Appointment)
            .where(
                Appointment.doctor_id == doctor_id,
                func.date(Appointment.scheduled_at) == today,
                Appointment.deleted_at.is_(None),
            )
            .order_by(Appointment.scheduled_at)
        )
        return list(result.scalars().all())

    async def doctor_pending_consultations(self, doctor_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                Consultation.doctor_id == doctor_id,
                Consultation.status == ConsultationStatus.pending_review,
                Consultation.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def doctor_drafts(self, doctor_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                Consultation.doctor_id == doctor_id,
                Consultation.status == ConsultationStatus.draft,
                Consultation.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def doctor_reports_this_month(self, doctor_id: uuid.UUID) -> int:
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(func.count()).where(
                Report.created_by == doctor_id, Report.created_at >= month_start, Report.deleted_at.is_(None)
            )
        )
        return result.scalar_one()

    async def recent_consultations(
        self, *, hospital_id: uuid.UUID, doctor_id: uuid.UUID | None, limit: int = 5
    ) -> list[Consultation]:
        stmt = select(Consultation).where(
            Consultation.hospital_id == hospital_id, Consultation.deleted_at.is_(None)
        )
        if doctor_id is not None:
            stmt = stmt.where(Consultation.doctor_id == doctor_id)
        stmt = stmt.order_by(Consultation.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def receptionist_checkins_today(self, hospital_id: uuid.UUID) -> int:
        today = date.today()
        result = await self.db.execute(
            select(func.count()).where(
                Appointment.hospital_id == hospital_id,
                Appointment.status == AppointmentStatus.checked_in,
                func.date(Appointment.scheduled_at) == today,
                Appointment.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def receptionist_upcoming_today(self, hospital_id: uuid.UUID) -> list[Appointment]:
        today = date.today()
        result = await self.db.execute(
            select(Appointment)
            .where(
                Appointment.hospital_id == hospital_id,
                func.date(Appointment.scheduled_at) == today,
                Appointment.status.in_([AppointmentStatus.upcoming, AppointmentStatus.checked_in]),
                Appointment.deleted_at.is_(None),
            )
            .order_by(Appointment.scheduled_at)
        )
        return list(result.scalars().all())
