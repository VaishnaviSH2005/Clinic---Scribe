"""Patient API (PRD Ch16.7)."""

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, require_roles
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
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["patients"])

HOSPITAL_ROLES = (RoleName.hospital_admin, RoleName.doctor, RoleName.receptionist)
REGISTER_ROLES = (RoleName.receptionist, RoleName.hospital_admin)
EDIT_ROLES = (RoleName.receptionist, RoleName.doctor, RoleName.hospital_admin)
DOCUMENT_ROLES = (RoleName.receptionist, RoleName.doctor)


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
        db, hospital_id=current.hospital_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(patient), message="Patient registered successfully.")


@router.get("")
async def list_patients(
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*HOSPITAL_ROLES)),
) -> ApiListResponse[PatientOut]:
    patients, total = await patient_service.list_patients(
        db,
        hospital_id=current.hospital_id,
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
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*HOSPITAL_ROLES)),
) -> ApiResponse[list[PatientOut]]:
    patients, _total = await patient_service.list_patients(
        db, hospital_id=current.hospital_id, search=q, page=1, page_size=10
    )
    return ApiResponse(data=[_to_out(p) for p in patients])


@router.get("/{patient_id}")
async def get_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*HOSPITAL_ROLES)),
) -> ApiResponse[PatientOut]:
    patient = await patient_service.get_patient(db, patient_id=patient_id, hospital_id=current.hospital_id)
    return ApiResponse(data=_to_out(patient))


@router.patch("/{patient_id}")
async def update_patient(
    patient_id: uuid.UUID,
    body: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*EDIT_ROLES)),
) -> ApiResponse[PatientOut]:
    patient = await patient_service.update_patient(
        db, patient_id=patient_id, hospital_id=current.hospital_id, data=body, actor_id=current.user.id
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
        db, patient_id=patient_id, hospital_id=current.hospital_id, actor_id=current.user.id
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
        db, patient_id=patient_id, hospital_id=current.hospital_id, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(patient), message="Patient restored successfully.")


@router.get("/{patient_id}/medical-profile")
async def get_medical_profile(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*HOSPITAL_ROLES)),
) -> ApiResponse[MedicalProfileOut | None]:
    await patient_service.get_patient(db, patient_id=patient_id, hospital_id=current.hospital_id)
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
        db, patient_id=patient_id, hospital_id=current.hospital_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(
        data=MedicalProfileOut.model_validate(profile), message="Medical profile updated successfully."
    )


@router.get("/{patient_id}/timeline")
async def get_timeline(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*HOSPITAL_ROLES)),
) -> ApiResponse[list[TimelineEventOut]]:
    events = await patient_service.list_timeline(db, patient_id=patient_id, hospital_id=current.hospital_id)
    return ApiResponse(data=[TimelineEventOut.model_validate(e) for e in events])


@router.get("/{patient_id}/appointments")
async def get_patient_appointments(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*HOSPITAL_ROLES)),
) -> ApiResponse[list[AppointmentOut]]:
    await patient_service.get_patient(db, patient_id=patient_id, hospital_id=current.hospital_id)
    appointments = await AppointmentRepository(db).list_by_patient(patient_id)
    return ApiResponse(data=[AppointmentOut.model_validate(a) for a in appointments])


@router.get("/{patient_id}/documents")
async def list_documents(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*HOSPITAL_ROLES)),
) -> ApiResponse[list[DocumentOut]]:
    documents = await patient_service.list_documents(db, patient_id=patient_id, hospital_id=current.hospital_id)
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
        hospital_id=current.hospital_id,
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
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*HOSPITAL_ROLES)),
) -> FileResponse:
    document, file_path = await patient_service.get_document_for_download(
        db, patient_id=patient_id, document_id=document_id, hospital_id=current.hospital_id
    )
    return FileResponse(path=file_path, filename=document.file_name)
