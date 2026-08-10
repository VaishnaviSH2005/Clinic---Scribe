"""Appointment Management business logic (PRD Ch6.2/Ch8.10, Ch16.8)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus, TimelineEventType
from app.models.patient import TimelineEvent
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.timeline_event_repository import TimelineEventRepository
from app.repositories.user_repository import UserRepository
from app.schemas.appointment_schema import AppointmentCreate
from app.services.audit_service import record_audit_event
from app.services.patient_service import get_patient


class DoctorUnavailableError(AppError):
    status_code = 409
    error_code = "DOCTOR_UNAVAILABLE"


class InvalidAppointmentStateError(AppError):
    status_code = 409
    error_code = "INVALID_APPOINTMENT_STATE"


async def _validate_references(
    db: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    department_id: uuid.UUID,
) -> None:
    await get_patient(db, patient_id=patient_id, hospital_id=hospital_id, include_archived=False)

    doctor = await UserRepository(db).get_by_id(doctor_id, hospital_id=hospital_id)
    if doctor is None:
        raise NotFoundError("The selected doctor could not be found.", error_code="DOCTOR_NOT_FOUND")

    department = await DepartmentRepository(db).get_by_id(department_id, hospital_id=hospital_id)
    if department is None:
        raise NotFoundError("The selected department could not be found.", error_code="DEPARTMENT_NOT_FOUND")


async def create_appointment(
    db: AsyncSession, *, hospital_id: uuid.UUID, data: AppointmentCreate, actor_id: uuid.UUID
) -> Appointment:
    await _validate_references(
        db,
        hospital_id=hospital_id,
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        department_id=data.department_id,
    )

    repo = AppointmentRepository(db)
    if await repo.find_conflict(data.doctor_id, data.scheduled_at):
        raise DoctorUnavailableError("This doctor already has an appointment scheduled at that time.")

    now = datetime.now(timezone.utc)
    appointment = Appointment(
        hospital_id=hospital_id,
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        department_id=data.department_id,
        scheduled_at=data.scheduled_at,
        status=AppointmentStatus.upcoming,
        created_by=actor_id,
        updated_by=actor_id,
    )
    await repo.create(appointment)

    await TimelineEventRepository(db).create(
        TimelineEvent(
            patient_id=data.patient_id,
            event_type=TimelineEventType.appointment,
            event_date=data.scheduled_at,
            title="Appointment scheduled",
            reference_id=appointment.id,
            created_at=now,
        )
    )

    await record_audit_event(
        db,
        action="appointment_created",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="appointment",
        entity_id=appointment.id,
    )
    return appointment


async def get_appointment(db: AsyncSession, *, appointment_id: uuid.UUID, hospital_id: uuid.UUID) -> Appointment:
    appointment = await AppointmentRepository(db).get_by_id(appointment_id, hospital_id=hospital_id)
    if appointment is None:
        raise NotFoundError("The requested appointment could not be located.", error_code="APPOINTMENT_NOT_FOUND")
    return appointment


async def list_appointments(
    db: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    doctor_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    status: AppointmentStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Appointment], int]:
    return await AppointmentRepository(db).list_by_hospital(
        hospital_id,
        date_from=date_from,
        date_to=date_to,
        doctor_id=doctor_id,
        department_id=department_id,
        status=status,
        page=page,
        page_size=page_size,
    )


async def reschedule_appointment(
    db: AsyncSession,
    *,
    appointment_id: uuid.UUID,
    hospital_id: uuid.UUID,
    scheduled_at: datetime,
    actor_id: uuid.UUID,
) -> Appointment:
    repo = AppointmentRepository(db)
    appointment = await get_appointment(db, appointment_id=appointment_id, hospital_id=hospital_id)

    if appointment.status in (AppointmentStatus.completed, AppointmentStatus.cancelled):
        raise InvalidAppointmentStateError("Completed or cancelled appointments cannot be rescheduled.")

    if await repo.find_conflict(appointment.doctor_id, scheduled_at, exclude_id=appointment.id):
        raise DoctorUnavailableError("This doctor already has an appointment scheduled at that time.")

    appointment.scheduled_at = scheduled_at
    appointment.status = AppointmentStatus.upcoming
    appointment.updated_by = actor_id
    await repo.save(appointment)

    await record_audit_event(
        db,
        action="appointment_rescheduled",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="appointment",
        entity_id=appointment.id,
    )
    return appointment


async def check_in_appointment(
    db: AsyncSession, *, appointment_id: uuid.UUID, hospital_id: uuid.UUID, actor_id: uuid.UUID
) -> Appointment:
    appointment = await get_appointment(db, appointment_id=appointment_id, hospital_id=hospital_id)
    if appointment.status != AppointmentStatus.upcoming:
        raise InvalidAppointmentStateError("Only upcoming appointments can be checked in.")

    appointment.status = AppointmentStatus.checked_in
    appointment.checked_in_at = datetime.now(timezone.utc)
    appointment.updated_by = actor_id
    await AppointmentRepository(db).save(appointment)

    await record_audit_event(
        db,
        action="appointment_checked_in",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="appointment",
        entity_id=appointment.id,
    )
    return appointment


async def cancel_appointment(
    db: AsyncSession, *, appointment_id: uuid.UUID, hospital_id: uuid.UUID, actor_id: uuid.UUID
) -> Appointment:
    appointment = await get_appointment(db, appointment_id=appointment_id, hospital_id=hospital_id)
    if appointment.status == AppointmentStatus.completed:
        raise InvalidAppointmentStateError("Completed appointments cannot be cancelled.")

    appointment.status = AppointmentStatus.cancelled
    appointment.updated_by = actor_id
    await AppointmentRepository(db).save(appointment)

    await record_audit_event(
        db,
        action="appointment_cancelled",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="appointment",
        entity_id=appointment.id,
    )
    return appointment
