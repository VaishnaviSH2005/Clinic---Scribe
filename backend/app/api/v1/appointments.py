"""Appointment API (PRD Ch16.8)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import AppointmentStatus, RoleName
from app.schemas.appointment_schema import AppointmentCreate, AppointmentOut, AppointmentReschedule
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.services import appointment_service

router = APIRouter(prefix="/appointments", tags=["appointments"])

ALL_STAFF = (RoleName.hospital_admin, RoleName.doctor, RoleName.receptionist)
CREATE_ROLES = (RoleName.receptionist, RoleName.doctor, RoleName.hospital_admin)
MANAGE_ROLES = (RoleName.receptionist, RoleName.hospital_admin)


@router.post("")
async def create_appointment(
    body: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*CREATE_ROLES)),
) -> ApiResponse[AppointmentOut]:
    appointment = await appointment_service.create_appointment(
        db, hospital_id=current.hospital_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(
        data=AppointmentOut.model_validate(appointment), message="Appointment created successfully."
    )


@router.get("")
async def list_appointments(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    doctor_id: uuid.UUID | None = Query(default=None),
    department_id: uuid.UUID | None = Query(default=None),
    status: AppointmentStatus | None = Query(default=None),
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*ALL_STAFF)),
) -> ApiListResponse[AppointmentOut]:
    appointments, total = await appointment_service.list_appointments(
        db,
        hospital_id=current.hospital_id,
        date_from=date_from,
        date_to=date_to,
        doctor_id=doctor_id,
        department_id=department_id,
        status=status,
        page=pagination.page,
        page_size=pagination.pageSize,
    )
    return ApiListResponse(
        data=[AppointmentOut.model_validate(a) for a in appointments],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )


@router.get("/{appointment_id}")
async def get_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*ALL_STAFF)),
) -> ApiResponse[AppointmentOut]:
    appointment = await appointment_service.get_appointment(
        db, appointment_id=appointment_id, hospital_id=current.hospital_id
    )
    return ApiResponse(data=AppointmentOut.model_validate(appointment))


@router.patch("/{appointment_id}")
async def reschedule_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentReschedule,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*MANAGE_ROLES)),
) -> ApiResponse[AppointmentOut]:
    appointment = await appointment_service.reschedule_appointment(
        db,
        appointment_id=appointment_id,
        hospital_id=current.hospital_id,
        scheduled_at=body.scheduled_at,
        actor_id=current.user.id,
    )
    await db.commit()
    return ApiResponse(
        data=AppointmentOut.model_validate(appointment), message="Appointment rescheduled successfully."
    )


@router.patch("/{appointment_id}/check-in")
async def check_in_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.receptionist)),
) -> ApiResponse[AppointmentOut]:
    appointment = await appointment_service.check_in_appointment(
        db, appointment_id=appointment_id, hospital_id=current.hospital_id, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=AppointmentOut.model_validate(appointment), message="Patient checked in successfully.")


@router.patch("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*MANAGE_ROLES)),
) -> ApiResponse[AppointmentOut]:
    appointment = await appointment_service.cancel_appointment(
        db, appointment_id=appointment_id, hospital_id=current.hospital_id, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(
        data=AppointmentOut.model_validate(appointment), message="Appointment cancelled successfully."
    )
