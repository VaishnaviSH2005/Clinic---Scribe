"""Hospital & Organization API (PRD Ch16.4)."""

import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import RoleName
from app.schemas.hospital_schema import HospitalCreate, HospitalOut, HospitalStatusUpdate, HospitalUpdate
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.services import hospital_service

router = APIRouter(prefix="/hospitals", tags=["hospitals"])


def _to_out(hospital) -> HospitalOut:
    return HospitalOut.model_validate(hospital)


@router.post("")
async def create_hospital(
    body: HospitalCreate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.super_admin)),
) -> ApiResponse[HospitalOut]:
    hospital = await hospital_service.create_hospital(db, data=body, actor_id=current.user.id)
    await db.commit()
    return ApiResponse(data=_to_out(hospital), message="Hospital created successfully.")


@router.get("")
async def list_hospitals(
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    _current: CurrentUser = Depends(require_roles(RoleName.super_admin)),
) -> ApiListResponse[HospitalOut]:
    hospitals, total = await hospital_service.list_hospitals(
        db, page=pagination.page, page_size=pagination.pageSize
    )
    return ApiListResponse(
        data=[_to_out(h) for h in hospitals],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )


def _ensure_hospital_access(current: CurrentUser, hospital_id: uuid.UUID) -> None:
    if current.role == RoleName.super_admin:
        return
    if current.role == RoleName.hospital_admin and current.hospital_id == hospital_id:
        return
    raise ForbiddenError("You do not have permission to access this resource.", error_code="FORBIDDEN")


@router.get("/{hospital_id}")
async def get_hospital(
    hospital_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.super_admin, RoleName.hospital_admin)),
) -> ApiResponse[HospitalOut]:
    _ensure_hospital_access(current, hospital_id)
    hospital = await hospital_service.get_hospital(db, hospital_id=hospital_id)
    return ApiResponse(data=_to_out(hospital))


@router.patch("/{hospital_id}")
async def update_hospital(
    hospital_id: uuid.UUID,
    body: HospitalUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.super_admin, RoleName.hospital_admin)),
) -> ApiResponse[HospitalOut]:
    _ensure_hospital_access(current, hospital_id)
    hospital = await hospital_service.update_hospital(
        db, hospital_id=hospital_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(hospital), message="Hospital updated successfully.")


@router.post("/{hospital_id}/logo")
async def upload_hospital_logo(
    hospital_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.super_admin)),
) -> ApiResponse[HospitalOut]:
    hospital = await hospital_service.upload_logo(db, hospital_id=hospital_id, file=file, actor_id=current.user.id)
    await db.commit()
    return ApiResponse(data=_to_out(hospital), message="Hospital logo updated successfully.")


@router.patch("/{hospital_id}/status")
async def update_hospital_status(
    hospital_id: uuid.UUID,
    body: HospitalStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.super_admin)),
) -> ApiResponse[HospitalOut]:
    hospital = await hospital_service.set_hospital_status(
        db, hospital_id=hospital_id, status=body.status, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(hospital), message="Hospital status updated successfully.")
