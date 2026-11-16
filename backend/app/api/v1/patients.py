"""Patient API (PRD Ch16.7)."""

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, require_roles, resolve_hospital_scope
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import RoleName
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.appointment_schema import AppointmentOut
from app.schemas.patient_schema import (
    DocumentOut,
    MedicalProfileInput,
    MedicalProfileOut,
    PatientCreate,
    PatientOut,
    PatientUpdate,
    TimelineEventOut,
)
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.services import audit_service, patient_service

router = APIRouter(prefix="/patients", tags=["patients"])

HOSPITAL_ROLES = (RoleName.hospital_admin, RoleName.doctor, RoleName.receptionist)
# Super Admin may VIEW patients of one chosen hospital (PRD Ch6.15 matrix: Patients Yes,
# Ch6.3: cannot modify patient records) - so only GET endpoints use READ_ROLES.
READ_ROLES = (*HOSPITAL_ROLES, RoleName.super_admin)
REGISTER_ROLES = (RoleName.receptionist, RoleName.hospital_admin)
EDIT_ROLES = (RoleName.receptionist, RoleName.doctor, RoleName.hospital_admin)
DOCUMENT_ROLES = (RoleName.receptionist, RoleName.doctor)


async def _audit_platform_view(
    db: AsyncSession, current: CurrentUser, hospital_id: uuid.UUID, patient_id: uuid.UUID | None = None
) -> None:
    """Platform-staff reads of a hospital's patient data are always traceable."""
    if current.role != RoleName.super_admin:
        return
    await audit_service.record_audit_event(
        db,
        action="platform_admin_patient_view" if patient_id else "platform_admin_patient_list_view",
        user_id=current.user.id,
        hospital_id=hospital_id,
        entity_type="patient" if patient_id else "hospital",
        entity_id=patient_id or hospital_id,
    )
    await db.commit()


def _to_out(patient) -> PatientOut:
    return PatientOut(
        id=patient.id,
        hospital_id=patient.hospital_id,
        uhid=patient.uhid,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        age=patient_service.patient_age(patient),
        gender=patient.gender,
        blood_group=patient.blood_group,
        mobile_number=patient.mobile_number,
        email=patient.email,
        aadhaar_number=patient.aadhaar_number,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_number=patient.emergency_contact_number,
        address_line=patient.address_line,
        city=patient.city,
        state=patient.state,
        country=patient.country,
        pin_code=patient.pin_code,
        photo_url=patient.photo_url,
        status=patient_service.patient_status(patient),
        created_at=patient.created_at,
    )


@router.post("")
async def register_patient(
    body: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*REGISTER_ROLES)),
) -> ApiResponse[PatientOut]:
    patient = await patient_service.register_patient(
        db, hospital_id=current.hospital, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(patient), message="Patient registered successfully.")


@router.get("")
async def list_patients(
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    pagination: PaginationParams = Depends(pagination_params),
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> ApiListResponse[PatientOut]:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    await _audit_platform_view(db, current, scope_id)
    patients, total = await patient_service.list_patients(
        db,
        hospital_id=scope_id,
        search=search,
        include_archived=include_archived,
        page=pagination.page,
        page_size=pagination.pageSize,
    )
    return ApiListResponse(
        data=[_to_out(p) for p in patients],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )


@router.get("/search")
async def search_patients(
    q: str = Query(min_length=1),
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> ApiResponse[list[PatientOut]]:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    patients, _total = await patient_service.list_patients(
        db, hospital_id=scope_id, search=q, page=1, page_size=10
    )
    return ApiResponse(data=[_to_out(p) for p in patients])


@router.get("/{patient_id}")
async def get_patient(
    patient_id: uuid.UUID,
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> ApiResponse[PatientOut]:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    patient = await patient_service.get_patient(db, patient_id=patient_id, hospital_id=scope_id)
    await _audit_platform_view(db, current, scope_id, patient_id)
    return ApiResponse(data=_to_out(patient))


@router.patch("/{patient_id}")
async def update_patient(
    patient_id: uuid.UUID,
    body: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*EDIT_ROLES)),
) -> ApiResponse[PatientOut]:
    patient = await patient_service.update_patient(
        db, patient_id=patient_id, hospital_id=current.hospital, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(patient), message="Patient updated successfully.")


@router.delete("/{patient_id}")
async def archive_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[PatientOut]:
    patient = await patient_service.archive_patient(
        db, patient_id=patient_id, hospital_id=current.hospital, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(patient), message="Patient archived successfully.")


@router.post("/{patient_id}/restore")
async def restore_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin)),
) -> ApiResponse[PatientOut]:
    patient = await patient_service.restore_patient(
        db, patient_id=patient_id, hospital_id=current.hospital, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(patient), message="Patient restored successfully.")


@router.get("/{patient_id}/medical-profile")
async def get_medical_profile(
    patient_id: uuid.UUID,
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> ApiResponse[MedicalProfileOut | None]:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    await patient_service.get_patient(db, patient_id=patient_id, hospital_id=scope_id)
    profile = await patient_service.get_or_create_medical_profile(db, patient_id=patient_id)
    return ApiResponse(data=MedicalProfileOut.model_validate(profile) if profile else None)


@router.patch("/{patient_id}/medical-profile")
async def update_medical_profile(
    patient_id: uuid.UUID,
    body: MedicalProfileInput,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor, RoleName.hospital_admin)),
) -> ApiResponse[MedicalProfileOut]:
    profile = await patient_service.update_medical_profile(
        db, patient_id=patient_id, hospital_id=current.hospital, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(
        data=MedicalProfileOut.model_validate(profile), message="Medical profile updated successfully."
    )


@router.get("/{patient_id}/timeline")
async def get_timeline(
    patient_id: uuid.UUID,
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> ApiResponse[list[TimelineEventOut]]:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    events = await patient_service.list_timeline(db, patient_id=patient_id, hospital_id=scope_id)
    return ApiResponse(data=[TimelineEventOut.model_validate(e) for e in events])


@router.get("/{patient_id}/appointments")
async def get_patient_appointments(
    patient_id: uuid.UUID,
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> ApiResponse[list[AppointmentOut]]:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    await patient_service.get_patient(db, patient_id=patient_id, hospital_id=scope_id)
    appointments = await AppointmentRepository(db).list_by_patient(patient_id)
    return ApiResponse(data=[AppointmentOut.model_validate(a) for a in appointments])


@router.get("/{patient_id}/documents")
async def list_documents(
    patient_id: uuid.UUID,
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> ApiResponse[list[DocumentOut]]:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    documents = await patient_service.list_documents(db, patient_id=patient_id, hospital_id=scope_id)
    return ApiResponse(data=[DocumentOut.model_validate(d) for d in documents])


@router.post("/{patient_id}/documents")
async def upload_document(
    patient_id: uuid.UUID,
    file: UploadFile = File(...),
    category: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*DOCUMENT_ROLES)),
) -> ApiResponse[DocumentOut]:
    document = await patient_service.upload_document(
        db,
        patient_id=patient_id,
        hospital_id=current.hospital,
        file=file,
        uploaded_by=current.user.id,
        category=category,
    )
    await db.commit()
    return ApiResponse(data=DocumentOut.model_validate(document), message="Document uploaded successfully.")


@router.get("/{patient_id}/documents/{document_id}/download")
async def download_document(
    patient_id: uuid.UUID,
    document_id: uuid.UUID,
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> FileResponse:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    document, file_path = await patient_service.get_document_for_download(
        db, patient_id=patient_id, document_id=document_id, hospital_id=scope_id
    )
    return FileResponse(path=file_path, filename=document.file_name)
