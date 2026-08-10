"""Department API (PRD Ch16.5)."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user, require_hospital_scope, require_roles
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import RoleName
from app.schemas.department_schema import DepartmentCreate, DepartmentOut, DepartmentStatusUpdate, DepartmentUpdate
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.services import department_service

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("")
async def create_department(
    body: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[DepartmentOut]:
    department = await department_service.create_department(
        db, hospital_id=current.hospital_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=DepartmentOut.model_validate(department), message="Department created successfully.")


@router.get("")
async def list_departments(
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    hospital_id: uuid.UUID = Depends(require_hospital_scope()),
    _current: CurrentUser = Depends(get_current_user),
) -> ApiListResponse[DepartmentOut]:
    departments, total = await department_service.list_departments(
        db, hospital_id=hospital_id, page=pagination.page, page_size=pagination.pageSize
    )
    return ApiListResponse(
        data=[DepartmentOut.model_validate(d) for d in departments],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )


@router.patch("/{department_id}")
async def update_department(
    department_id: uuid.UUID,
    body: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[DepartmentOut]:
    department = await department_service.update_department(
        db, department_id=department_id, hospital_id=current.hospital_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=DepartmentOut.model_validate(department), message="Department updated successfully.")


@router.patch("/{department_id}/status")
async def update_department_status(
    department_id: uuid.UUID,
    body: DepartmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[DepartmentOut]:
    department = await department_service.set_department_status(
        db,
        department_id=department_id,
        hospital_id=current.hospital_id,
        status=body.status,
        actor_id=current.user.id,
    )
    await db.commit()
    return ApiResponse(
        data=DepartmentOut.model_validate(department), message="Department status updated successfully."
    )
