"""Receptionist API (PRD Ch7.13, Ch16.6)."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import RoleName, UserStatus
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.schemas.user_schema import ReceptionistCreate, UserOut, UserStatusUpdate, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/receptionists", tags=["receptionists"])


def _to_out(user) -> UserOut:
    return UserOut(
        id=user.id,
        hospital_id=user.hospital_id,
        department_id=user.department_id,
        role=RoleName.receptionist,
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
async def create_receptionist(
    body: ReceptionistCreate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[UserOut]:
    receptionist = await user_service.create_receptionist(
        db, hospital_id=current.hospital_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(receptionist), message="Receptionist created successfully.")


@router.get("")
async def list_receptionists(
    pagination: PaginationParams = Depends(pagination_params),
    status: UserStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiListResponse[UserOut]:
    receptionists, total = await user_service.list_users(
        db,
        hospital_id=current.hospital_id,
        role_name=RoleName.receptionist,
        status=status,
        search=search,
        page=pagination.page,
        page_size=pagination.pageSize,
    )
    return ApiListResponse(
        data=[_to_out(r) for r in receptionists],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )


@router.patch("/{receptionist_id}")
async def update_receptionist(
    receptionist_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[UserOut]:
    receptionist = await user_service.update_user(
        db, user_id=receptionist_id, hospital_id=current.hospital_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(receptionist), message="Receptionist updated successfully.")


@router.patch("/{receptionist_id}/status")
async def update_receptionist_status(
    receptionist_id: uuid.UUID,
    body: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[UserOut]:
    receptionist = await user_service.set_user_status(
        db, user_id=receptionist_id, hospital_id=current.hospital_id, status=body.status, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(receptionist), message="Receptionist status updated successfully.")
