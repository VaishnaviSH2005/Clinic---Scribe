"""Doctor API (PRD Ch7.12, Ch16.6)."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import RoleName, UserStatus
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.schemas.user_schema import DoctorCreate, UserOut, UserStatusUpdate, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/doctors", tags=["doctors"])


def _to_out(user, role: RoleName = RoleName.doctor) -> UserOut:
    return UserOut(
        id=user.id,
        hospital_id=user.hospital_id,
        department_id=user.department_id,
        role=role,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        profile_photo_url=user.profile_photo_url,
        employee_id=user.employee_id,
        qualification=user.qualification,
        specialization=user.specialization,
        medical_registration_number=user.medical_registration_number,
        experience_years=user.experience_years,
        status=user.status,
    )


@router.post("")
async def create_doctor(
    body: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[UserOut]:
    doctor = await user_service.create_doctor(
        db, hospital_id=current.hospital_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(doctor), message="Doctor created successfully.")


@router.get("")
async def list_doctors(
    pagination: PaginationParams = Depends(pagination_params),
    department_id: uuid.UUID | None = Query(default=None),
    status: UserStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiListResponse[UserOut]:
    doctors, total = await user_service.list_users(
        db,
        hospital_id=current.hospital_id,
        role_name=RoleName.doctor,
        department_id=department_id,
        status=status,
        search=search,
        page=pagination.page,
        page_size=pagination.pageSize,
    )
    return ApiListResponse(
        data=[_to_out(d) for d in doctors],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )


@router.patch("/{doctor_id}")
async def update_doctor(
    doctor_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[UserOut]:
    doctor = await user_service.update_user(
        db, user_id=doctor_id, hospital_id=current.hospital_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(doctor), message="Doctor updated successfully.")


@router.patch("/{doctor_id}/status")
async def update_doctor_status(
    doctor_id: uuid.UUID,
    body: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[UserOut]:
    doctor = await user_service.set_user_status(
        db, user_id=doctor_id, hospital_id=current.hospital_id, status=body.status, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(doctor), message="Doctor status updated successfully.")
