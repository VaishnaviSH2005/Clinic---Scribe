"""Aggregate read queries backing the Analytics module (PRD analytics
chapters). Real database aggregates, hospital-scoped (and doctor-scoped
where the caller passes a `doctor_id`) — never fabricated figures.
"""

import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.consultation import Consultation
from app.models.enums import AppointmentStatus
from app.models.hospital import Department
from app.models.patient import Patient
from app.models.platform import AuditLog
from app.models.report import Report
from app.models.user import User


def _bounds(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    start = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end = datetime.combine(date_to, time.max, tzinfo=timezone.utc)
    return start, end


class AnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def consultations_by_status(
        self, hospital_id: uuid.UUID, *, date_from: date, date_to: date, doctor_id: uuid.UUID | None
    ) -> dict[str, int]:
        start, end = _bounds(date_from, date_to)
        stmt = (
            select(Consultation.status, func.count())
            .where(
                Consultation.hospital_id == hospital_id,
                Consultation.created_at >= start,
                Consultation.created_at <= end,
                Consultation.deleted_at.is_(None),
            )
            .group_by(Consultation.status)
        )
        if doctor_id is not None:
            stmt = stmt.where(Consultation.doctor_id == doctor_id)
        result = await self.db.execute(stmt)
        return {status.value: count for status, count in result.all()}

    async def consultations_per_day(
        self, hospital_id: uuid.UUID, *, date_from: date, date_to: date, doctor_id: uuid.UUID | None
    ) -> list[tuple[date, int]]:
        start, end = _bounds(date_from, date_to)
        day = func.date(Consultation.created_at)
        stmt = (
            select(day.label("day"), func.count())
            .where(
                Consultation.hospital_id == hospital_id,
                Consultation.created_at >= start,
                Consultation.created_at <= end,
                Consultation.deleted_at.is_(None),
            )
            .group_by(day)
            .order_by(day)
        )
        if doctor_id is not None:
            stmt = stmt.where(Consultation.doctor_id == doctor_id)
        result = await self.db.execute(stmt)
        return list(result.all())

    async def appointments_by_status(
        self, hospital_id: uuid.UUID, *, date_from: date, date_to: date, doctor_id: uuid.UUID | None
    ) -> dict[str, int]:
        start, end = _bounds(date_from, date_to)
        stmt = (
            select(Appointment.status, func.count())
            .where(
                Appointment.hospital_id == hospital_id,
                Appointment.scheduled_at >= start,
                Appointment.scheduled_at <= end,
                Appointment.deleted_at.is_(None),
            )
            .group_by(Appointment.status)
        )
        if doctor_id is not None:
            stmt = stmt.where(Appointment.doctor_id == doctor_id)
        result = await self.db.execute(stmt)
        return {status.value: count for status, count in result.all()}

    async def new_patients_per_day(
        self, hospital_id: uuid.UUID, *, date_from: date, date_to: date
    ) -> list[tuple[date, int]]:
        start, end = _bounds(date_from, date_to)
        day = func.date(Patient.created_at)
        result = await self.db.execute(
            select(day.label("day"), func.count())
            .where(
                Patient.hospital_id == hospital_id,
                Patient.created_at >= start,
                Patient.created_at <= end,
                Patient.deleted_at.is_(None),
            )
            .group_by(day)
            .order_by(day)
        )
        return list(result.all())

    async def ai_processing_outcomes(
        self, hospital_id: uuid.UUID, *, date_from: date, date_to: date
    ) -> dict[str, int]:
        start, end = _bounds(date_from, date_to)
        result = await self.db.execute(
            select(AuditLog.action, func.count())
            .where(
                AuditLog.hospital_id == hospital_id,
                AuditLog.action.in_(["ai_pipeline_completed", "ai_stage_failed"]),
                AuditLog.created_at >= start,
                AuditLog.created_at <= end,
            )
            .group_by(AuditLog.action)
        )
        return dict(result.all())

    async def consultations_by_doctor(
        self, hospital_id: uuid.UUID, *, date_from: date, date_to: date
    ) -> list[tuple[str, int]]:
        start, end = _bounds(date_from, date_to)
        result = await self.db.execute(
            select(User.full_name, func.count(Consultation.id))
            .join(User, User.id == Consultation.doctor_id)
            .where(
                Consultation.hospital_id == hospital_id,
                Consultation.created_at >= start,
                Consultation.created_at <= end,
                Consultation.deleted_at.is_(None),
            )
            .group_by(User.full_name)
            .order_by(func.count(Consultation.id).desc())
        )
        return list(result.all())

    async def consultations_by_department(
        self, hospital_id: uuid.UUID, *, date_from: date, date_to: date
    ) -> list[tuple[str, int]]:
        start, end = _bounds(date_from, date_to)
        result = await self.db.execute(
            select(Department.name, func.count(Consultation.id))
            .join(Department, Department.id == Consultation.department_id)
            .where(
                Consultation.hospital_id == hospital_id,
                Consultation.created_at >= start,
                Consultation.created_at <= end,
                Consultation.deleted_at.is_(None),
            )
            .group_by(Department.name)
            .order_by(func.count(Consultation.id).desc())
        )
        return list(result.all())

    async def reports_generated(self, hospital_id: uuid.UUID, *, date_from: date, date_to: date) -> int:
        start, end = _bounds(date_from, date_to)
        result = await self.db.execute(
            select(func.count()).where(
                Report.hospital_id == hospital_id,
                Report.created_at >= start,
                Report.created_at <= end,
                Report.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def missed_appointment_rate(self, hospital_id: uuid.UUID, *, date_from: date, date_to: date) -> float:
        counts = await self.appointments_by_status(
            hospital_id, date_from=date_from, date_to=date_to, doctor_id=None
        )
        total = sum(counts.values())
        if total == 0:
            return 0.0
        return round(counts.get(AppointmentStatus.missed.value, 0) / total * 100, 1)
