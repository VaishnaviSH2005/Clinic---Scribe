"""Hospital management (PRD Ch7.10, Ch16.4)."""

import uuid
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import DepartmentStatus, HospitalStatus, SettingsScope
from app.models.hospital import Department, Hospital
from app.repositories.department_repository import DepartmentRepository
from app.repositories.hospital_repository import HospitalRepository
from app.repositories.settings_repository import SettingsRepository
from app.schemas.hospital_schema import HospitalCreate, HospitalUpdate
from app.services import user_service
from app.services.audit_service import record_audit_event
from app.utils.file_storage import save_upload

# A new hospital's Setting row (scope=hospital) exists so hospital-level
# configuration has a real row to update in place from day one, mirroring
# how user-scope settings work (PRD Ch15.9.3) — no keys are invented beyond
# this initialization marker since no hospital-scope setting is consumed
# anywhere yet.
DEFAULT_HOSPITAL_SETTINGS_KEY = "hospital_defaults"

# A newly created hospital starts with a single default department so it is
# immediately usable; further departments are added via Department
# Management (Ch13.4). The PRD (Ch7.10) requires "generates default
# departments" without enumerating names, so a single sensible default is
# used rather than inventing a list not specified anywhere in the PRD.
DEFAULT_DEPARTMENT_NAME = "General Medicine"


async def create_hospital(db: AsyncSession, *, data: HospitalCreate, actor_id: uuid.UUID) -> Hospital:
    repo = HospitalRepository(db)
    if await repo.get_by_registration_number(data.registration_number) is not None:
        raise ConflictError(
            "A hospital with this registration number already exists.", error_code="DUPLICATE_HOSPITAL"
        )

    hospital = Hospital(**data.model_dump(), created_by=actor_id, updated_by=actor_id)
    await repo.create(hospital)

    await DepartmentRepository(db).create(
        Department(
            hospital_id=hospital.id,
            name=DEFAULT_DEPARTMENT_NAME,
            status=DepartmentStatus.active,
            created_by=actor_id,
            updated_by=actor_id,
        )
    )

    await SettingsRepository(db).upsert(
        scope=SettingsScope.hospital,
        user_id=None,
        hospital_id=hospital.id,
        key=DEFAULT_HOSPITAL_SETTINGS_KEY,
        value={"initialized": True},
        updated_at=datetime.now(timezone.utc),
    )

    # Hospital Admin account for the new hospital (PRD Ch6.3 Super Admin
    # "Manage Hospitals" / Ch16.4), provisioned through the same
    # invitation-email flow already used for doctors/receptionists rather
    # than a new mechanism. The hospital's own contact email is reused as
    # the admin's login so no additional field is required on hospital
    # registration; a duplicate email here (someone already registered with
    # it) surfaces as the same DUPLICATE_USER conflict and aborts hospital
    # creation before anything is committed.
    await user_service.create_hospital_admin(
        db,
        hospital_id=hospital.id,
        full_name=f"{hospital.name} Admin",
        email=hospital.email,
        phone=hospital.phone,
        actor_id=actor_id,
    )

    await record_audit_event(
        db,
        action="hospital_created",
        user_id=actor_id,
        hospital_id=hospital.id,
        entity_type="hospital",
        entity_id=hospital.id,
    )
    return hospital


async def get_hospital(db: AsyncSession, *, hospital_id: uuid.UUID) -> Hospital:
    hospital = await HospitalRepository(db).get_by_id(hospital_id)
    if hospital is None:
        raise NotFoundError("The requested hospital could not be located.", error_code="HOSPITAL_NOT_FOUND")
    return hospital


async def list_hospitals(db: AsyncSession, *, page: int = 1, page_size: int = 20) -> tuple[list[Hospital], int]:
    return await HospitalRepository(db).list_all(page=page, page_size=page_size)


async def update_hospital(
    db: AsyncSession, *, hospital_id: uuid.UUID, data: HospitalUpdate, actor_id: uuid.UUID
) -> Hospital:
    hospital = await get_hospital(db, hospital_id=hospital_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(hospital, field, value)
    hospital.updated_by = actor_id
    await HospitalRepository(db).save(hospital)
    await record_audit_event(
        db,
        action="hospital_updated",
        user_id=actor_id,
        hospital_id=hospital.id,
        entity_type="hospital",
        entity_id=hospital.id,
    )
    return hospital


async def upload_logo(db: AsyncSession, *, hospital_id: uuid.UUID, file: UploadFile, actor_id: uuid.UUID) -> Hospital:
    hospital = await get_hospital(db, hospital_id=hospital_id)
    relative_url, _extension, _size_bytes = await save_upload(file, subdir="hospital-logos")
    hospital.logo_url = relative_url
    hospital.updated_by = actor_id
    await HospitalRepository(db).save(hospital)
    await record_audit_event(
        db,
        action="hospital_logo_updated",
        user_id=actor_id,
        hospital_id=hospital.id,
        entity_type="hospital",
        entity_id=hospital.id,
    )
    return hospital


async def set_hospital_status(
    db: AsyncSession, *, hospital_id: uuid.UUID, status: HospitalStatus, actor_id: uuid.UUID
) -> Hospital:
    hospital = await get_hospital(db, hospital_id=hospital_id)
    hospital.status = status
    hospital.updated_by = actor_id
    await HospitalRepository(db).save(hospital)
    await record_audit_event(
        db,
        action="hospital_status_changed",
        user_id=actor_id,
        hospital_id=hospital.id,
        entity_type="hospital",
        entity_id=hospital.id,
        metadata={"status": status.value},
    )
    return hospital
