"""Generic User Management API (PRD Ch13.3, Ch16.13). Doctor/Receptionist
creation with role-specific fields lives in doctors.py/receptionists.py;
this router lists all hospital staff together and provides generic edit/
status endpoints, matching the "User Management" screen in Ch13.3/13.9.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import RoleName, UserStatus
from app.repositories.user_repository import UserRepository
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.schemas.user_schema import UserOut, UserStatusUpdate, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


async def _to_out(db: AsyncSession, user) -> UserOut:
    role = await UserRepository(db).get_role(user.role_id)
    return UserOut(
        id=user.id,
        hospital_id=user.hospital_id,
        department_id=user.department_id,
        role=role.name if role else RoleName.receptionist,
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


@router.get("")
async def list_users(
    pagination: PaginationParams = Depends(pagination_params),
    role: RoleName | None = Query(default=None),
    department_id: uuid.UUID | None = Query(default=None),
    status: UserStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiListResponse[UserOut]:
    users, total = await user_service.list_users(
        db,
        hospital_id=current.hospital_id,
        role_name=role,
        department_id=department_id,
        status=status,
        search=search,
        page=pagination.page,
        page_size=pagination.pageSize,
    )
    return ApiListResponse(
        data=[await _to_out(db, u) for u in users],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )


@router.patch("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[UserOut]:
    user = await user_service.update_user(
        db, user_id=user_id, hospital_id=current.hospital_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=await _to_out(db, user), message="User updated successfully.")


@router.patch("/{user_id}/status")
async def update_user_status(
    user_id: uuid.UUID,
    body: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[UserOut]:
    user = await user_service.set_user_status(
        db, user_id=user_id, hospital_id=current.hospital_id, status=body.status, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=await _to_out(db, user), message="User status updated successfully.")
