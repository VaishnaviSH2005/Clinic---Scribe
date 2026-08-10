"""Patient Management business logic (PRD Ch8)."""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.models.enums import DocumentFileType, TimelineEventType
from app.models.patient import Document, MedicalProfile, Patient, TimelineEvent
from app.repositories.document_repository import DocumentRepository
from app.repositories.medical_profile_repository import MedicalProfileRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.timeline_event_repository import TimelineEventRepository
from app.schemas.patient_schema import MedicalProfileInput, PatientCreate, PatientUpdate
from app.services.audit_service import record_audit_event
from app.utils.date_utils import calculate_age
from app.utils.file_storage import save_upload


class DuplicatePatientError(AppError):
    status_code = 409
    error_code = "DUPLICATE_PATIENT"


def patient_status(patient: Patient) -> str:
    return "archived" if patient.deleted_at is not None else "active"


def patient_age(patient: Patient) -> int:
    return calculate_age(patient.date_of_birth)


async def _generate_uhid(repo: PatientRepository, hospital_id: uuid.UUID) -> str:
    """PRD Ch8.4 — format CLN-YYYY-NNNNNN, permanent once assigned."""
    year = datetime.now(timezone.utc).year
    sequence = await repo.count_this_year(hospital_id, year) + 1
    return f"CLN-{year}-{sequence:06d}"


async def register_patient(
    db: AsyncSession, *, hospital_id: uuid.UUID, data: PatientCreate, actor_id: uuid.UUID
) -> Patient:
    repo = PatientRepository(db)

    if await repo.find_duplicate(hospital_id, mobile_number=data.mobile_number, date_of_birth=data.date_of_birth):
        raise DuplicatePatientError("A patient with this mobile number already exists.")

    now = datetime.now(timezone.utc)
    payload = data.model_dump(exclude={"medical_info"})

    # Retry once on a UHID race (two concurrent registrations in the same
    # hospital/year) rather than trusting count-then-insert to be atomic.
    for _ in range(3):
        uhid = await _generate_uhid(repo, hospital_id)
        patient = Patient(
            hospital_id=hospital_id,
            uhid=uhid,
            created_by=actor_id,
            updated_by=actor_id,
            **payload,
        )
        try:
            await repo.create(patient)
            break
        except IntegrityError:
            await db.rollback()
    else:
        raise ConflictError(
            "Unable to generate a unique patient ID. Please try again.", error_code="UHID_GENERATION_FAILED"
        )

    if data.medical_info:
        await MedicalProfileRepository(db).create(
            MedicalProfile(patient_id=patient.id, **data.medical_info.model_dump())
        )

    await TimelineEventRepository(db).create(
        TimelineEvent(
            patient_id=patient.id,
            event_type=TimelineEventType.registration,
            event_date=now,
            title="Patient registered",
            description=f"Registered with UHID {patient.uhid}.",
            created_at=now,
        )
    )

    await record_audit_event(
        db,
        action="patient_registered",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="patient",
        entity_id=patient.id,
    )
    return patient


async def get_patient(
    db: AsyncSession, *, patient_id: uuid.UUID, hospital_id: uuid.UUID, include_archived: bool = True
) -> Patient:
    patient = await PatientRepository(db).get_by_id(
        patient_id, hospital_id=hospital_id, include_deleted=include_archived
    )
    if patient is None:
        raise NotFoundError("The requested patient record could not be located.", error_code="PATIENT_NOT_FOUND")
    return patient


async def list_patients(
    db: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    search: str | None = None,
    include_archived: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Patient], int]:
    return await PatientRepository(db).list_by_hospital(
        hospital_id, search=search, include_archived=include_archived, page=page, page_size=page_size
    )


async def update_patient(
    db: AsyncSession, *, patient_id: uuid.UUID, hospital_id: uuid.UUID, data: PatientUpdate, actor_id: uuid.UUID
) -> Patient:
    patient = await get_patient(db, patient_id=patient_id, hospital_id=hospital_id, include_archived=False)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    patient.updated_by = actor_id
    await PatientRepository(db).save(patient)
    await record_audit_event(
        db,
        action="patient_updated",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="patient",
        entity_id=patient.id,
    )
    return patient


async def get_or_create_medical_profile(db: AsyncSession, *, patient_id: uuid.UUID) -> MedicalProfile | None:
    return await MedicalProfileRepository(db).get_by_patient_id(patient_id)


async def update_medical_profile(
    db: AsyncSession,
    *,
    patient_id: uuid.UUID,
    hospital_id: uuid.UUID,
    data: MedicalProfileInput,
    actor_id: uuid.UUID,
) -> MedicalProfile:
    await get_patient(db, patient_id=patient_id, hospital_id=hospital_id, include_archived=False)
    repo = MedicalProfileRepository(db)
    profile = await repo.get_by_patient_id(patient_id)

    now = datetime.now(timezone.utc)
    if profile is None:
        profile = MedicalProfile(patient_id=patient_id, **data.model_dump(), updated_at=now)
        await repo.create(profile)
    else:
        for field, value in data.model_dump().items():
            setattr(profile, field, value)
        profile.updated_at = now
        await repo.save(profile)

    await record_audit_event(
        db,
        action="patient_medical_profile_updated",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="patient",
        entity_id=patient_id,
    )
    return profile


async def archive_patient(
    db: AsyncSession, *, patient_id: uuid.UUID, hospital_id: uuid.UUID, actor_id: uuid.UUID
) -> Patient:
    patient = await get_patient(db, patient_id=patient_id, hospital_id=hospital_id, include_archived=False)
    patient.deleted_at = datetime.now(timezone.utc)
    patient.updated_by = actor_id
    await PatientRepository(db).save(patient)
    await record_audit_event(
        db,
        action="patient_archived",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="patient",
        entity_id=patient.id,
    )
    return patient


async def restore_patient(
    db: AsyncSession, *, patient_id: uuid.UUID, hospital_id: uuid.UUID, actor_id: uuid.UUID
) -> Patient:
    patient = await PatientRepository(db).get_by_id(patient_id, hospital_id=hospital_id, include_deleted=True)
    if patient is None:
        raise NotFoundError("The requested patient record could not be located.", error_code="PATIENT_NOT_FOUND")
    patient.deleted_at = None
    patient.updated_by = actor_id
    await PatientRepository(db).save(patient)
    await record_audit_event(
        db,
        action="patient_restored",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="patient",
        entity_id=patient.id,
    )
    return patient


async def list_timeline(db: AsyncSession, *, patient_id: uuid.UUID, hospital_id: uuid.UUID) -> list[TimelineEvent]:
    await get_patient(db, patient_id=patient_id, hospital_id=hospital_id)
    return await TimelineEventRepository(db).list_by_patient(patient_id)


async def list_documents(db: AsyncSession, *, patient_id: uuid.UUID, hospital_id: uuid.UUID) -> list[Document]:
    await get_patient(db, patient_id=patient_id, hospital_id=hospital_id)
    return await DocumentRepository(db).list_by_patient(patient_id)


async def upload_document(
    db: AsyncSession,
    *,
    patient_id: uuid.UUID,
    hospital_id: uuid.UUID,
    file: UploadFile,
    uploaded_by: uuid.UUID,
    category: str | None,
) -> Document:
    patient = await get_patient(db, patient_id=patient_id, hospital_id=hospital_id, include_archived=False)

    relative_url, extension, size_bytes = await save_upload(file, subdir=f"patients/{patient.id}")

    now = datetime.now(timezone.utc)
    document = Document(
        patient_id=patient.id,
        hospital_id=hospital_id,
        uploaded_by=uploaded_by,
        file_name=file.filename or f"document.{extension}",
        file_type=DocumentFileType(extension),
        file_url=relative_url,
        file_size_bytes=size_bytes,
        document_category=category,
        created_at=now,
    )
    await DocumentRepository(db).create(document)

    await TimelineEventRepository(db).create(
        TimelineEvent(
            patient_id=patient.id,
            event_type=TimelineEventType.uploaded_report,
            event_date=now,
            title=f"Document uploaded: {document.file_name}",
            reference_id=document.id,
            created_at=now,
        )
    )

    await record_audit_event(
        db,
        action="document_uploaded",
        user_id=uploaded_by,
        hospital_id=hospital_id,
        entity_type="document",
        entity_id=document.id,
    )
    return document


async def get_document_for_download(
    db: AsyncSession, *, patient_id: uuid.UUID, document_id: uuid.UUID, hospital_id: uuid.UUID
) -> tuple[Document, Path]:
    """Documents require authenticated access (PRD Ch9.24 principle applied
    to patient files) — never served through an unauthenticated static mount."""
    document = await DocumentRepository(db).get_by_id(document_id, hospital_id=hospital_id, patient_id=patient_id)
    if document is None:
        raise NotFoundError("The requested document could not be located.", error_code="DOCUMENT_NOT_FOUND")

    file_path = Path(settings.local_storage_dir) / document.file_url.removeprefix(
        f"/{settings.local_storage_dir}/"
    )
    if not file_path.is_file():
        raise NotFoundError("The requested document could not be located.", error_code="DOCUMENT_NOT_FOUND")
    return document, file_path
