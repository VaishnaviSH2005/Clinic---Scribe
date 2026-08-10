"""Department management (PRD Ch7.11, Ch16.5)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.enums import DepartmentStatus
from app.models.hospital import Department
from app.repositories.department_repository import DepartmentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.department_schema import DepartmentCreate, DepartmentUpdate
from app.services.audit_service import record_audit_event


class DepartmentHasActiveDoctorsError(AppError):
    status_code = 409
    error_code = "DEPARTMENT_HAS_ACTIVE_DOCTORS"


async def create_department(
    db: AsyncSession, *, hospital_id: uuid.UUID, data: DepartmentCreate, actor_id: uuid.UUID
) -> Department:
    department = Department(
        hospital_id=hospital_id,
        name=data.name,
        head_of_department_id=data.head_of_department_id,
        status=DepartmentStatus.active,
        created_by=actor_id,
        updated_by=actor_id,
    )
    await DepartmentRepository(db).create(department)
    await record_audit_event(
        db,
        action="department_created",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="department",
        entity_id=department.id,
    )
    return department


async def get_department(db: AsyncSession, *, department_id: uuid.UUID, hospital_id: uuid.UUID) -> Department:
    department = await DepartmentRepository(db).get_by_id(department_id, hospital_id=hospital_id)
    if department is None:
        raise NotFoundError("The requested department could not be located.", error_code="DEPARTMENT_NOT_FOUND")
    return department


async def list_departments(
    db: AsyncSession, *, hospital_id: uuid.UUID, page: int = 1, page_size: int = 20
) -> tuple[list[Department], int]:
    return await DepartmentRepository(db).list_by_hospital(hospital_id, page=page, page_size=page_size)


async def update_department(
    db: AsyncSession,
    *,
    department_id: uuid.UUID,
    hospital_id: uuid.UUID,
    data: DepartmentUpdate,
    actor_id: uuid.UUID,
) -> Department:
    department = await get_department(db, department_id=department_id, hospital_id=hospital_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(department, field, value)
    department.updated_by = actor_id
    await DepartmentRepository(db).save(department)
    await record_audit_event(
        db,
        action="department_updated",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="department",
        entity_id=department.id,
    )
    return department


async def set_department_status(
    db: AsyncSession,
    *,
    department_id: uuid.UUID,
    hospital_id: uuid.UUID,
    status: DepartmentStatus,
    actor_id: uuid.UUID,
) -> Department:
    department = await get_department(db, department_id=department_id, hospital_id=hospital_id)

    if status == DepartmentStatus.inactive:
        active_doctors = await UserRepository(db).count_active_by_department(department_id)
        if active_doctors > 0:
            raise DepartmentHasActiveDoctorsError(
                "This department has active doctors assigned and cannot be disabled."
            )

    department.status = status
    department.updated_by = actor_id
    await DepartmentRepository(db).save(department)
    await record_audit_event(
        db,
        action="department_status_changed",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="department",
        entity_id=department.id,
        metadata={"status": status.value},
    )
    return department
