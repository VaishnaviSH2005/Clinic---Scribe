"""Consultation Workspace business logic (PRD Ch9).

Stopping a consultation with a captured recording moves it into
`ai_processing` and enqueues the AI clinical documentation pipeline
(Ch10/17) — the pipeline itself runs in a separate worker process
(`app/workers/pipeline_worker.py`), never inline here, so this request
never blocks on AI. A consultation stopped without any audio (recording
failed, or the doctor chose not to record) skips the AI phase entirely and
goes straight to `pending_review`, matching the graceful-degradation
posture the PRD mandates for AI being unavailable (Ch9.21).
"""

import uuid
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_queue import enqueue_ai_job
from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.core.logging import logger
from app.models.consultation import Consultation, ConsultationTranscript
from app.models.enums import AppointmentStatus, ConsultationStatus, TimelineEventType
from app.models.patient import TimelineEvent
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.consultation_transcript_repository import ConsultationTranscriptRepository
from app.repositories.medical_profile_repository import MedicalProfileRepository
from app.repositories.timeline_event_repository import TimelineEventRepository
from app.schemas.consultation_schema import (
    ConsultationStartRequest,
    ConsultationUpdateRequest,
    MedicalAlertsOut,
    PatientContextOut,
    PreviousConsultationOut,
)
from app.services.audit_service import record_audit_event
from app.services.patient_service import get_patient, patient_age
from app.utils.file_storage import save_audio_upload

ACTIVE_STATUSES = [ConsultationStatus.draft, ConsultationStatus.in_progress]
COMPLETED_STATUSES = [ConsultationStatus.pending_review, ConsultationStatus.approved]


class ConsultationStateError(AppError):
    status_code = 409
    error_code = "INVALID_CONSULTATION_STATE"


class ConsultationAlreadyApprovedError(AppError):
    status_code = 409
    error_code = "CONSULTATION_ALREADY_APPROVED"


def _ensure_owner(consultation: Consultation, doctor_id: uuid.UUID) -> None:
    """PRD Ch9.24 — only the assigned doctor may access an active consultation."""
    if consultation.doctor_id != doctor_id:
        raise ForbiddenError("You do not have permission to access this consultation.", error_code="FORBIDDEN")


async def start_consultation(
    db: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    doctor_id: uuid.UUID,
    department_id: uuid.UUID,
    data: ConsultationStartRequest,
) -> Consultation:
    await get_patient(db, patient_id=data.patient_id, hospital_id=hospital_id, include_archived=False)

    appointment = None
    if data.appointment_id is not None:
        appointment = await AppointmentRepository(db).get_by_id(data.appointment_id, hospital_id=hospital_id)
        if appointment is None:
            raise NotFoundError(
                "The requested appointment could not be located.", error_code="APPOINTMENT_NOT_FOUND"
            )

    now = datetime.now(timezone.utc)
    consultation = Consultation(
        hospital_id=hospital_id,
        patient_id=data.patient_id,
        doctor_id=doctor_id,
        appointment_id=data.appointment_id,
        department_id=appointment.department_id if appointment else department_id,
        status=ConsultationStatus.in_progress,
        chief_complaint=data.chief_complaint,
        started_at=now,
        created_by=doctor_id,
        updated_by=doctor_id,
    )
    await ConsultationRepository(db).create(consultation)

    await ConsultationTranscriptRepository(db).create(
        ConsultationTranscript(
            consultation_id=consultation.id,
            raw_transcript=[],
            created_at=now,
            updated_at=now,
        )
    )

    # The linked appointment stays `checked_in` until the consultation is
    # approved (Ch6.6) — it transitions to `completed` in approve_consultation.

    await TimelineEventRepository(db).create(
        TimelineEvent(
            patient_id=data.patient_id,
            event_type=TimelineEventType.consultation,
            event_date=now,
            title="Consultation started",
            reference_id=consultation.id,
            created_at=now,
        )
    )

    await record_audit_event(
        db,
        action="consultation_started",
        user_id=doctor_id,
        hospital_id=hospital_id,
        entity_type="consultation",
        entity_id=consultation.id,
    )
    return consultation


async def get_consultation(
    db: AsyncSession, *, consultation_id: uuid.UUID, hospital_id: uuid.UUID
) -> Consultation:
    consultation = await ConsultationRepository(db).get_by_id(consultation_id, hospital_id=hospital_id)
    if consultation is None:
        raise NotFoundError(
            "The requested consultation could not be located.", error_code="CONSULTATION_NOT_FOUND"
        )
    return consultation


async def get_workspace(
    db: AsyncSession, *, consultation_id: uuid.UUID, hospital_id: uuid.UUID, doctor_id: uuid.UUID
) -> tuple[Consultation, ConsultationTranscript, PatientContextOut]:
    consultation = await get_consultation(db, consultation_id=consultation_id, hospital_id=hospital_id)
    _ensure_owner(consultation, doctor_id)

    transcript = await ConsultationTranscriptRepository(db).get_by_consultation_id(consultation.id)
    if transcript is None:
        raise NotFoundError("Consultation transcript record is missing.", error_code="TRANSCRIPT_NOT_FOUND")

    patient = await get_patient(db, patient_id=consultation.patient_id, hospital_id=hospital_id)
    medical_profile = await MedicalProfileRepository(db).get_by_patient_id(patient.id)
    previous = await ConsultationRepository(db).list_by_patient(patient.id, limit=5)
    previous = [c for c in previous if c.id != consultation.id]

    patient_context = PatientContextOut(
        id=patient.id,
        full_name=patient.full_name,
        uhid=patient.uhid,
        age=patient_age(patient),
        gender=patient.gender.value,
        blood_group=patient.blood_group,
        medical_alerts=MedicalAlertsOut(
            known_allergies=medical_profile.known_allergies if medical_profile else [],
            chronic_diseases=medical_profile.chronic_diseases if medical_profile else [],
            current_medications=medical_profile.current_medications if medical_profile else [],
        ),
        previous_consultations=[PreviousConsultationOut.model_validate(c) for c in previous],
    )
    return consultation, transcript, patient_context


SCOPE_STATUSES: dict[str, list[ConsultationStatus]] = {
    "active": [ConsultationStatus.in_progress],
    "drafts": [ConsultationStatus.draft],
    "previous": COMPLETED_STATUSES,
}


async def list_consultations(
    db: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    doctor_id: uuid.UUID | None,
    scope: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Consultation], int]:
    statuses = SCOPE_STATUSES.get(scope)
    return await ConsultationRepository(db).list_by_hospital(
        hospital_id, doctor_id=doctor_id, statuses=statuses, page=page, page_size=page_size
    )


async def update_consultation(
    db: AsyncSession,
    *,
    consultation_id: uuid.UUID,
    hospital_id: uuid.UUID,
    doctor_id: uuid.UUID,
    data: ConsultationUpdateRequest,
) -> Consultation:
    consultation = await get_consultation(db, consultation_id=consultation_id, hospital_id=hospital_id)
    _ensure_owner(consultation, doctor_id)
    if consultation.status == ConsultationStatus.approved:
        raise ConsultationAlreadyApprovedError("This consultation has already been approved and is read-only.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(consultation, field, value)
    consultation.updated_by = doctor_id
    await ConsultationRepository(db).save(consultation)

    await record_audit_event(
        db,
        action="consultation_updated",
        user_id=doctor_id,
        hospital_id=hospital_id,
        entity_type="consultation",
        entity_id=consultation.id,
    )
    return consultation


async def pause_consultation(
    db: AsyncSession, *, consultation_id: uuid.UUID, hospital_id: uuid.UUID, doctor_id: uuid.UUID
) -> Consultation:
    """Recording pause (PRD Ch9.11). The active/in_progress status is
    unchanged — pausing is a client-side recording-session concept; this
    endpoint exists so the pause event is still audited server-side."""
    consultation = await get_consultation(db, consultation_id=consultation_id, hospital_id=hospital_id)
    _ensure_owner(consultation, doctor_id)
    if consultation.status != ConsultationStatus.in_progress:
        raise ConsultationStateError("Only an in-progress consultation can be paused.")

    await record_audit_event(
        db,
        action="consultation_recording_paused",
        user_id=doctor_id,
        hospital_id=hospital_id,
        entity_type="consultation",
        entity_id=consultation.id,
    )
    return consultation


async def resume_consultation(
    db: AsyncSession, *, consultation_id: uuid.UUID, hospital_id: uuid.UUID, doctor_id: uuid.UUID
) -> Consultation:
    consultation = await get_consultation(db, consultation_id=consultation_id, hospital_id=hospital_id)
    _ensure_owner(consultation, doctor_id)

    if consultation.status == ConsultationStatus.draft:
        # Resuming a previously saved draft (PRD Ch9.12/Consultation Management).
        consultation.status = ConsultationStatus.in_progress
        consultation.updated_by = doctor_id
        await ConsultationRepository(db).save(consultation)
    elif consultation.status != ConsultationStatus.in_progress:
        raise ConsultationStateError("Only an in-progress or draft consultation can be resumed.")

    await record_audit_event(
        db,
        action="consultation_recording_resumed",
        user_id=doctor_id,
        hospital_id=hospital_id,
        entity_type="consultation",
        entity_id=consultation.id,
    )
    return consultation


async def save_draft(
    db: AsyncSession, *, consultation_id: uuid.UUID, hospital_id: uuid.UUID, doctor_id: uuid.UUID
) -> Consultation:
    consultation = await get_consultation(db, consultation_id=consultation_id, hospital_id=hospital_id)
    _ensure_owner(consultation, doctor_id)
    if consultation.status not in ACTIVE_STATUSES:
        raise ConsultationStateError("Only an active consultation can be saved as a draft.")

    consultation.status = ConsultationStatus.draft
    consultation.updated_by = doctor_id
    await ConsultationRepository(db).save(consultation)

    await record_audit_event(
        db,
        action="consultation_draft_saved",
        user_id=doctor_id,
        hospital_id=hospital_id,
        entity_type="consultation",
        entity_id=consultation.id,
    )
    return consultation


async def stop_consultation(
    db: AsyncSession,
    *,
    consultation_id: uuid.UUID,
    hospital_id: uuid.UUID,
    doctor_id: uuid.UUID,
    audio_file: UploadFile | None,
    audio_duration_seconds: int | None,
) -> Consultation:
    consultation = await get_consultation(db, consultation_id=consultation_id, hospital_id=hospital_id)
    _ensure_owner(consultation, doctor_id)
    if consultation.status not in ACTIVE_STATUSES:
        raise ConsultationStateError("Only an active consultation can be stopped.")

    transcript_repo = ConsultationTranscriptRepository(db)
    transcript = await transcript_repo.get_by_consultation_id(consultation.id)
    if transcript is None:
        raise NotFoundError("Consultation transcript record is missing.", error_code="TRANSCRIPT_NOT_FOUND")

    has_audio = audio_file is not None
    if audio_file is not None:
        relative_url, _extension, _size = await save_audio_upload(
            audio_file, subdir=f"consultations/{consultation.id}"
        )
        transcript.audio_file_url = relative_url
        transcript.audio_duration_seconds = audio_duration_seconds
        transcript.updated_at = datetime.now(timezone.utc)
        await transcript_repo.save(transcript)

    now = datetime.now(timezone.utc)
    consultation.ended_at = now
    # A captured recording moves the consultation into the AI pipeline
    # (Ch10/17); no audio skips straight to doctor review (Ch9.21).
    consultation.status = ConsultationStatus.ai_processing if has_audio else ConsultationStatus.pending_review
    consultation.updated_by = doctor_id
    await ConsultationRepository(db).save(consultation)

    await record_audit_event(
        db,
        action="consultation_stopped",
        user_id=doctor_id,
        hospital_id=hospital_id,
        entity_type="consultation",
        entity_id=consultation.id,
    )

    if has_audio:
        await record_audit_event(
            db,
            action="ai_pipeline_queued",
            user_id=doctor_id,
            hospital_id=hospital_id,
            entity_type="consultation",
            entity_id=consultation.id,
        )
        await db.flush()
        try:
            await enqueue_ai_job(consultation.id)
        except Exception as exc:  # noqa: BLE001 - Redis unreachable must not fail the stop request
            logger.warning("Could not enqueue AI pipeline for consultation %s: %s", consultation.id, exc)
            await record_audit_event(
                db,
                action="ai_stage_failed",
                user_id=doctor_id,
                hospital_id=hospital_id,
                entity_type="consultation",
                entity_id=consultation.id,
                metadata={"stage": "transcribe", "error": f"Could not queue AI processing: {exc}"},
            )
    else:
        from app.services.notification_service import notify_user

        await notify_user(
            db,
            user_id=doctor_id,
            notification_type="consultation_pending",
            title="Consultation awaiting review",
            message="No recording was captured, so this consultation needs manual review.",
            reference_id=consultation.id,
        )

    return consultation


async def approve_consultation(
    db: AsyncSession, *, consultation_id: uuid.UUID, hospital_id: uuid.UUID, doctor_id: uuid.UUID
) -> Consultation:
    consultation = await get_consultation(db, consultation_id=consultation_id, hospital_id=hospital_id)
    _ensure_owner(consultation, doctor_id)
    if consultation.status == ConsultationStatus.approved:
        raise ConsultationAlreadyApprovedError("This consultation has already been approved.")
    if consultation.status != ConsultationStatus.pending_review:
        raise ConsultationStateError("Only a consultation pending review can be approved.")

    now = datetime.now(timezone.utc)
    consultation.status = ConsultationStatus.approved
    consultation.approved_at = now
    consultation.approved_by = doctor_id
    consultation.updated_by = doctor_id
    await ConsultationRepository(db).save(consultation)

    if consultation.appointment_id is not None:
        appointment_repo = AppointmentRepository(db)
        appointment = await appointment_repo.get_by_id(consultation.appointment_id, hospital_id=hospital_id)
        if appointment is not None and appointment.status != AppointmentStatus.cancelled:
            appointment.status = AppointmentStatus.completed
            appointment.updated_by = doctor_id
            await appointment_repo.save(appointment)

    await TimelineEventRepository(db).create(
        TimelineEvent(
            patient_id=consultation.patient_id,
            event_type=TimelineEventType.consultation,
            event_date=now,
            title="Consultation completed",
            description=consultation.chief_complaint,
            reference_id=consultation.id,
            created_at=now,
        )
    )

    await record_audit_event(
        db,
        action="consultation_approved",
        user_id=doctor_id,
        hospital_id=hospital_id,
        entity_type="consultation",
        entity_id=consultation.id,
    )

    from app.services.report_service import generate_report

    # Report PDF generation is a downstream side effect of approval, not a
    # precondition for it — a rendering/storage failure here must never
    # block the doctor's core action (approving) or roll back the
    # already-recorded approval. Isolated in a SAVEPOINT so only the report
    # write is discarded on failure; the approval itself always survives.
    try:
        async with db.begin_nested():
            await generate_report(db, consultation=consultation, doctor_id=doctor_id)
    except Exception as exc:  # noqa: BLE001 - report generation must never fail the approval
        logger.warning("Report generation failed for consultation %s: %s", consultation.id, exc)
        await record_audit_event(
            db,
            action="report_generation_failed",
            user_id=doctor_id,
            hospital_id=hospital_id,
            entity_type="consultation",
            entity_id=consultation.id,
            metadata={"error": str(exc)},
        )

    return consultation


async def cancel_consultation(
    db: AsyncSession, *, consultation_id: uuid.UUID, hospital_id: uuid.UUID, doctor_id: uuid.UUID
) -> None:
    """Cancelling is a soft delete (PRD Ch15.2) — an approved consultation is
    a permanent medical record and can never be cancelled (Ch11.10)."""
    consultation = await get_consultation(db, consultation_id=consultation_id, hospital_id=hospital_id)
    _ensure_owner(consultation, doctor_id)
    if consultation.status == ConsultationStatus.approved:
        raise ConsultationAlreadyApprovedError("An approved consultation cannot be cancelled.")

    consultation.deleted_at = datetime.now(timezone.utc)
    consultation.updated_by = doctor_id
    await ConsultationRepository(db).save(consultation)

    await record_audit_event(
        db,
        action="consultation_cancelled",
        user_id=doctor_id,
        hospital_id=hospital_id,
        entity_type="consultation",
        entity_id=consultation.id,
    )
