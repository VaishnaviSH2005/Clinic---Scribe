"""AI clinical documentation pipeline (PRD Ch10/Ch17.2).

Fixed stage order: transcribe -> clean_transcript -> extract_entities ->
build_context -> generate_soap -> generate_summary -> generate_recommendations
-> mark_ready_for_review. Runs exclusively in a worker process (never inline
in an HTTP request — see `app/workers/pipeline_worker.py`).

Design invariants (Ch17.6 / Ch10.15):
- Every stage is independently resumable: a stage whose result already
  exists is skipped unless `force=True` (doctor-triggered regenerate).
- A stage failure is recorded to `audit_logs` (never raised past this
  module) and never deletes/invalidates anything already persisted.
- `run_pipeline` always reaches `pending_review` at the end, regardless of
  which individual stages succeeded — the doctor is never permanently
  blocked by an AI failure; a failed stage is surfaced as "Retry Available"
  via `get_ai_status` (computed from audit history) and can be regenerated
  on demand, including after the consultation reaches `pending_review`
  (blocked only once `approved`, matching the read-only-after-approval rule
  enforced by `consultation_service`).
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import ai_bridge  # noqa: F401  (adds ai-services/ to sys.path)
from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError
from app.core.logging import logger
from app.models.consultation import (
    AiEntity,
    AiRecommendation,
    ClinicalSummary,
    Consultation,
    ConsultationTranscript,
    SoapNote,
)
from app.models.enums import ConfidenceLevel, ConsultationStatus, RecommendationType
from app.repositories.ai_entity_repository import AiEntityRepository
from app.repositories.ai_recommendation_repository import AiRecommendationRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.clinical_summary_repository import ClinicalSummaryRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.consultation_transcript_repository import ConsultationTranscriptRepository
from app.repositories.medical_profile_repository import MedicalProfileRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.soap_note_repository import SoapNoteRepository
from app.schemas.ai_schema import AiHistoryEntryOut, AiStatusOut, SoapEditRequest, SummaryEditRequest
from app.services.audit_service import record_audit_event

STAGE_TRANSCRIBE = "transcribe"
STAGE_CLEAN_TRANSCRIPT = "clean_transcript"
STAGE_EXTRACT_ENTITIES = "extract_entities"
STAGE_GENERATE_SOAP = "generate_soap"
STAGE_GENERATE_SUMMARY = "generate_summary"
STAGE_GENERATE_RECOMMENDATIONS = "generate_recommendations"

RETRYABLE_STAGES = (
    STAGE_TRANSCRIBE,
    STAGE_EXTRACT_ENTITIES,
    STAGE_GENERATE_SOAP,
    STAGE_GENERATE_SUMMARY,
    STAGE_GENERATE_RECOMMENDATIONS,
)


class InvalidStageError(AppError):
    status_code = 422
    error_code = "INVALID_AI_STAGE"


class AiPipelineNotAvailableError(AppError):
    status_code = 409
    error_code = "AI_PIPELINE_NOT_AVAILABLE"


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _audit(
    db: AsyncSession, *, consultation: Consultation, action: str, user_id: uuid.UUID | None, metadata: dict | None
) -> None:
    await record_audit_event(
        db,
        action=action,
        user_id=user_id,
        hospital_id=consultation.hospital_id,
        entity_type="consultation",
        entity_id=consultation.id,
        metadata=metadata,
    )


def _resolve_audio_path(audio_file_url: str) -> Path:
    return Path(audio_file_url.lstrip("/")).resolve()


async def _stage_transcribe(
    db: AsyncSession, *, consultation: Consultation, transcript: ConsultationTranscript, force: bool
) -> bool:
    """Returns True if the stage ran (success or documented failure), False if skipped."""
    if transcript.raw_transcript and not force:
        return False
    if not transcript.audio_file_url:
        return False

    from speech.transcriber import get_transcriber

    try:
        transcriber = get_transcriber(settings.stt_provider)
        audio_path = _resolve_audio_path(transcript.audio_file_url)
        segments = transcriber.transcribe(str(audio_path))
        transcript.raw_transcript = list(segments)
        transcript.cleaned_transcript = None  # force re-clean below
        transcript.updated_at = _now()
        await ConsultationTranscriptRepository(db).save(transcript)
        await _audit(
            db,
            consultation=consultation,
            action="ai_stage_completed",
            user_id=None,
            metadata={"stage": STAGE_TRANSCRIBE, "segment_count": len(transcript.raw_transcript)},
        )
    except Exception as exc:  # noqa: BLE001 - provider errors are heterogeneous, must never crash the worker
        logger.warning("AI stage 'transcribe' failed for consultation %s: %s", consultation.id, exc)
        await _audit(
            db,
            consultation=consultation,
            action="ai_stage_failed",
            user_id=None,
            metadata={"stage": STAGE_TRANSCRIBE, "error": str(exc)},
        )
    return True


async def _stage_clean_transcript(db: AsyncSession, *, transcript: ConsultationTranscript, force: bool) -> bool:
    if not transcript.raw_transcript:
        return False
    if transcript.cleaned_transcript is not None and not force:
        return False

    from speech.cleaner import clean_transcript

    transcript.cleaned_transcript = clean_transcript(transcript.raw_transcript)
    transcript.updated_at = _now()
    await ConsultationTranscriptRepository(db).save(transcript)
    return True


async def _stage_extract_entities(
    db: AsyncSession, *, consultation: Consultation, transcript: ConsultationTranscript, force: bool
) -> AiEntity | None:
    repo = AiEntityRepository(db)
    existing = await repo.get_by_consultation_id(consultation.id)
    if existing is not None and not force:
        return existing
    if not transcript.cleaned_transcript:
        return existing

    from nlp.entity_extractor import extract_entities

    try:
        extracted = extract_entities(transcript.cleaned_transcript)
        has_findings = any(extracted[key] for key in ("symptoms", "medications", "allergies", "medical_history"))
        confidence = ConfidenceLevel.medium if has_findings else ConfidenceLevel.low
        now = _now()
        if existing is None:
            existing = AiEntity(
                consultation_id=consultation.id,
                symptoms=extracted["symptoms"],
                medications=extracted["medications"],
                allergies=extracted["allergies"],
                medical_history=extracted["medical_history"],
                vitals=extracted["vitals"],
                extraction_confidence=confidence,
                created_at=now,
                updated_at=now,
            )
            await repo.create(existing)
        else:
            existing.symptoms = extracted["symptoms"]
            existing.medications = extracted["medications"]
            existing.allergies = extracted["allergies"]
            existing.medical_history = extracted["medical_history"]
            existing.vitals = extracted["vitals"]
            existing.extraction_confidence = confidence
            existing.updated_at = now
            await repo.save(existing)
        await _audit(
            db,
            consultation=consultation,
            action="ai_stage_completed",
            user_id=None,
            metadata={"stage": STAGE_EXTRACT_ENTITIES},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI stage 'extract_entities' failed for consultation %s: %s", consultation.id, exc)
        await _audit(
            db,
            consultation=consultation,
            action="ai_stage_failed",
            user_id=None,
            metadata={"stage": STAGE_EXTRACT_ENTITIES, "error": str(exc)},
        )
    return existing


async def _build_context(
    db: AsyncSession, *, consultation: Consultation, transcript: ConsultationTranscript, entities: AiEntity | None
) -> dict:
    patient = await PatientRepository(db).get_by_id(consultation.patient_id, hospital_id=consultation.hospital_id)
    if patient is None:
        raise NotFoundError("The consultation's patient could not be located.", error_code="PATIENT_NOT_FOUND")
    profile = await MedicalProfileRepository(db).get_by_patient_id(patient.id)

    previous = await ConsultationRepository(db).list_by_patient(patient.id, limit=5)
    previous_summary = None
    for prior in previous:
        if prior.id == consultation.id or prior.status != ConsultationStatus.approved:
            continue
        summary_row = await ClinicalSummaryRepository(db).get_by_consultation_id(prior.id)
        if summary_row is not None:
            previous_summary = summary_row.key_findings
            break

    return {
        "patient": {
            "age": None,
            "gender": patient.gender.value if patient.gender else None,
            "blood_group": patient.blood_group,
        },
        "medical_profile": {
            "chronic_diseases": profile.chronic_diseases if profile else [],
            "current_medications": profile.current_medications if profile else [],
            "known_allergies": profile.known_allergies if profile else [],
        },
        "previous_consultation_summary": previous_summary,
        "current_transcript": transcript.cleaned_transcript or [],
        "extracted_entities": {
            "symptoms": entities.symptoms if entities else [],
            "medications": entities.medications if entities else [],
            "allergies": entities.allergies if entities else [],
            "medical_history": entities.medical_history if entities else [],
            "vitals": entities.vitals if entities else None,
        },
    }


def _build_claude_client():
    from providers.claude import ClaudeClient

    return ClaudeClient(
        api_key=settings.claude_api_key,
        model=settings.claude_model,
        timeout_seconds=settings.claude_timeout_seconds,
        max_retries=settings.claude_max_retries,
    )


async def _stage_generate_soap(
    db: AsyncSession, *, consultation: Consultation, context: dict, force: bool
) -> None:
    repo = SoapNoteRepository(db)
    existing = await repo.get_by_consultation_id(consultation.id)
    if existing is not None and not force:
        return

    from providers.claude import ClaudeProviderError
    from summarization.soap_generator import generate_soap

    try:
        claude = _build_claude_client()
        result = await generate_soap(claude, context)
        now = _now()
        if existing is None:
            await repo.create(
                SoapNote(
                    consultation_id=consultation.id,
                    subjective=result.get("subjective"),
                    objective=result.get("objective"),
                    assessment=result.get("assessment"),
                    plan=result.get("plan"),
                    ai_generated=True,
                    edited_by_doctor=False,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            await _audit(
                db,
                consultation=consultation,
                action="ai_content_regenerated",
                user_id=None,
                metadata={
                    "stage": STAGE_GENERATE_SOAP,
                    "previous": {
                        "subjective": existing.subjective,
                        "objective": existing.objective,
                        "assessment": existing.assessment,
                        "plan": existing.plan,
                    },
                },
            )
            existing.subjective = result.get("subjective")
            existing.objective = result.get("objective")
            existing.assessment = result.get("assessment")
            existing.plan = result.get("plan")
            existing.ai_generated = True
            existing.edited_by_doctor = False
            existing.updated_at = now
            await repo.save(existing)
        await _audit(
            db,
            consultation=consultation,
            action="ai_stage_completed",
            user_id=None,
            metadata={"stage": STAGE_GENERATE_SOAP},
        )
    except ClaudeProviderError as exc:
        logger.warning("AI stage 'generate_soap' failed for consultation %s: %s", consultation.id, exc)
        await _audit(
            db,
            consultation=consultation,
            action="ai_stage_failed",
            user_id=None,
            metadata={"stage": STAGE_GENERATE_SOAP, "error": str(exc)},
        )


async def _stage_generate_summary(
    db: AsyncSession, *, consultation: Consultation, context: dict, force: bool
) -> None:
    repo = ClinicalSummaryRepository(db)
    existing = await repo.get_by_consultation_id(consultation.id)
    if existing is not None and not force:
        return

    from providers.claude import ClaudeProviderError
    from summarization.clinical_summary import generate_summary

    try:
        claude = _build_claude_client()
        result, was_truncated = await generate_summary(claude, context)
        now = _now()
        word_count = sum(
            len(str(result.get(field, "")).split())
            for field in ("chief_complaint", "history_of_present_illness", "key_findings", "assessment", "plan")
        )
        if existing is None:
            await repo.create(
                ClinicalSummary(
                    consultation_id=consultation.id,
                    chief_complaint=result.get("chief_complaint"),
                    history_of_present_illness=result.get("history_of_present_illness"),
                    key_findings=result.get("key_findings"),
                    assessment=result.get("assessment"),
                    plan=result.get("plan"),
                    word_count=word_count,
                    edited_by_doctor=False,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            await _audit(
                db,
                consultation=consultation,
                action="ai_content_regenerated",
                user_id=None,
                metadata={"stage": STAGE_GENERATE_SUMMARY, "previous": {"key_findings": existing.key_findings}},
            )
            existing.chief_complaint = result.get("chief_complaint")
            existing.history_of_present_illness = result.get("history_of_present_illness")
            existing.key_findings = result.get("key_findings")
            existing.assessment = result.get("assessment")
            existing.plan = result.get("plan")
            existing.word_count = word_count
            existing.edited_by_doctor = False
            existing.updated_at = now
            await repo.save(existing)
        await _audit(
            db,
            consultation=consultation,
            action="ai_stage_completed",
            user_id=None,
            metadata={"stage": STAGE_GENERATE_SUMMARY, "truncated": was_truncated},
        )
    except ClaudeProviderError as exc:
        logger.warning("AI stage 'generate_summary' failed for consultation %s: %s", consultation.id, exc)
        await _audit(
            db,
            consultation=consultation,
            action="ai_stage_failed",
            user_id=None,
            metadata={"stage": STAGE_GENERATE_SUMMARY, "error": str(exc)},
        )


async def _stage_generate_recommendations(
    db: AsyncSession, *, consultation: Consultation, context: dict, force: bool
) -> None:
    repo = AiRecommendationRepository(db)
    existing = await repo.list_by_consultation_id(consultation.id)
    if existing and not force:
        return

    from providers.claude import ClaudeProviderError
    from reasoning.diagnosis import generate_recommendations
    from reasoning.risk import generate_risk_flags

    now = _now()
    rows: list[AiRecommendation] = []
    failed_substages: list[str] = []

    try:
        reasoning_result = await generate_recommendations(_build_claude_client(), context)
        for item in reasoning_result.get("possible_diagnoses", []):
            rows.append(
                AiRecommendation(
                    consultation_id=consultation.id,
                    type=RecommendationType.possible_diagnosis,
                    content=item.get("content", ""),
                    explanation=item.get("explanation"),
                    confidence=ConfidenceLevel(item["confidence"]) if item.get("confidence") else None,
                    is_red_flag=False,
                    created_at=now,
                )
            )
        for item in reasoning_result.get("recommended_tests", []):
            rows.append(
                AiRecommendation(
                    consultation_id=consultation.id,
                    type=RecommendationType.recommended_test,
                    content=item.get("content", ""),
                    explanation=item.get("explanation"),
                    confidence=ConfidenceLevel(item["confidence"]) if item.get("confidence") else None,
                    is_red_flag=False,
                    created_at=now,
                )
            )
    except ClaudeProviderError as exc:
        failed_substages.append(f"reasoning: {exc}")

    try:
        risk_result = await generate_risk_flags(_build_claude_client(), context)
        for item in risk_result.get("red_flags", []):
            rows.append(
                AiRecommendation(
                    consultation_id=consultation.id,
                    type=RecommendationType.red_flag,
                    content=item.get("content", ""),
                    explanation=item.get("explanation"),
                    confidence=ConfidenceLevel(item["confidence"]) if item.get("confidence") else None,
                    is_red_flag=True,
                    created_at=now,
                )
            )
    except ClaudeProviderError as exc:
        failed_substages.append(f"risk: {exc}")

    if rows:
        if existing:
            await repo.delete_by_types(consultation.id, [row.type for row in rows] or list(RecommendationType))
        await repo.create_many(rows)
        await _audit(
            db,
            consultation=consultation,
            action="ai_stage_completed",
            user_id=None,
            metadata={"stage": STAGE_GENERATE_RECOMMENDATIONS, "count": len(rows)},
        )
    if failed_substages:
        logger.warning(
            "AI stage 'generate_recommendations' partially failed for consultation %s: %s",
            consultation.id,
            failed_substages,
        )
        await _audit(
            db,
            consultation=consultation,
            action="ai_stage_failed",
            user_id=None,
            metadata={"stage": STAGE_GENERATE_RECOMMENDATIONS, "error": "; ".join(failed_substages)},
        )


async def run_pipeline(db: AsyncSession, *, consultation_id: uuid.UUID) -> None:
    """Full pipeline run after `POST /consultations/{id}/stop`, delegating
    to `workers/speech_worker.py` (stages 1-3) then `workers/summary_worker.py`
    (stages 4-8, PRD Ch17.2). Always ends with the consultation in
    `pending_review`, whatever the outcome of the individual AI stages —
    see module docstring."""
    from app.workers import speech_worker, summary_worker

    consultation = await ConsultationRepository(db).get_by_id_any_hospital(consultation_id)
    if consultation is None:
        logger.warning("AI pipeline: consultation %s no longer exists, dropping job.", consultation_id)
        return
    if consultation.status != ConsultationStatus.ai_processing:
        logger.info(
            "AI pipeline: consultation %s is not in ai_processing (%s), skipping.",
            consultation_id,
            consultation.status,
        )
        return

    transcript = await ConsultationTranscriptRepository(db).get_by_consultation_id(consultation.id)
    if transcript is None:
        logger.error("AI pipeline: consultation %s has no transcript record.", consultation_id)
        consultation.status = ConsultationStatus.pending_review
        await ConsultationRepository(db).save(consultation)
        await db.commit()
        return

    entities = await speech_worker.run(db, consultation_id=consultation_id)
    await summary_worker.run(db, consultation_id=consultation_id, entities=entities)
    await db.commit()


async def run_single_stage_from_queue(db: AsyncSession, *, consultation_id: uuid.UUID, stage: str) -> None:
    """Worker-side entrypoint for a queued retry/regenerate job. Authorization
    (doctor ownership, hospital scope) was already enforced by the API
    handler before the job was enqueued (`app/api/v1/ai.py`), so this
    resolves the consultation's own hospital/doctor ids and delegates to
    `run_single_stage` — safe because a queued job only ever exists as a
    result of that prior check."""
    consultation = await ConsultationRepository(db).get_by_id_any_hospital(consultation_id)
    if consultation is None:
        logger.warning("AI retry: consultation %s no longer exists, dropping job.", consultation_id)
        return
    await run_single_stage(
        db,
        consultation_id=consultation_id,
        hospital_id=consultation.hospital_id,
        doctor_id=consultation.doctor_id,
        stage=stage,
    )


async def run_single_stage(
    db: AsyncSession, *, consultation_id: uuid.UUID, hospital_id: uuid.UUID, doctor_id: uuid.UUID, stage: str
) -> None:
    """Doctor-triggered retry/regenerate of one stage (Ch10.15/Ch16.10).
    Allowed while the consultation is in `ai_processing` or `pending_review`;
    blocked once `approved` (read-only, matching consultation_service)."""
    if stage not in RETRYABLE_STAGES:
        raise InvalidStageError(f"Unknown AI stage: {stage}")

    consultation = await ConsultationRepository(db).get_by_id(consultation_id, hospital_id=hospital_id)
    if consultation is None:
        raise NotFoundError(
            "The requested consultation could not be located.", error_code="CONSULTATION_NOT_FOUND"
        )
    if consultation.doctor_id != doctor_id:
        raise AiPipelineNotAvailableError("You do not have permission to access this consultation.")
    if consultation.status not in (ConsultationStatus.ai_processing, ConsultationStatus.pending_review):
        raise AiPipelineNotAvailableError("AI content can only be regenerated while the consultation is active.")

    transcript = await ConsultationTranscriptRepository(db).get_by_consultation_id(consultation.id)
    if transcript is None:
        raise NotFoundError("Consultation transcript record is missing.", error_code="TRANSCRIPT_NOT_FOUND")

    if stage == STAGE_TRANSCRIBE:
        # Retrying transcription re-drives the rest of the pipeline too,
        # since summary/SOAP/recommendations all depend on it (e.g. after a
        # transient STT or queue failure — see consultation_service.stop_consultation).
        await _stage_transcribe(db, consultation=consultation, transcript=transcript, force=True)
        await _stage_clean_transcript(db, transcript=transcript, force=True)
        entities = await _stage_extract_entities(db, consultation=consultation, transcript=transcript, force=True)
        if transcript.cleaned_transcript:
            context = await _build_context(db, consultation=consultation, transcript=transcript, entities=entities)
            await _stage_generate_soap(db, consultation=consultation, context=context, force=True)
            await _stage_generate_summary(db, consultation=consultation, context=context, force=True)
            await _stage_generate_recommendations(db, consultation=consultation, context=context, force=True)
        await db.commit()
        return

    if stage == STAGE_EXTRACT_ENTITIES:
        await _stage_extract_entities(db, consultation=consultation, transcript=transcript, force=True)
        await db.commit()
        return

    entities = await AiEntityRepository(db).get_by_consultation_id(consultation.id)
    context = await _build_context(db, consultation=consultation, transcript=transcript, entities=entities)

    if stage == STAGE_GENERATE_SOAP:
        await _stage_generate_soap(db, consultation=consultation, context=context, force=True)
    elif stage == STAGE_GENERATE_SUMMARY:
        await _stage_generate_summary(db, consultation=consultation, context=context, force=True)
    elif stage == STAGE_GENERATE_RECOMMENDATIONS:
        await _stage_generate_recommendations(db, consultation=consultation, context=context, force=True)
    await db.commit()


async def get_ai_status(db: AsyncSession, *, consultation: Consultation) -> AiStatusOut:
    """Computed AI sub-status — see module docstring for why this is
    derived rather than a stored column."""
    if consultation.status in (ConsultationStatus.draft, ConsultationStatus.in_progress):
        return AiStatusOut(consultation_status=consultation.status, stage="recording", degraded=False)

    logs = await AuditLogRepository(db).list_by_entity(
        entity_type="consultation", entity_id=consultation.id, action_prefix="ai_"
    )
    failed_stages: dict[str, str] = {}
    completed_stages: set[str] = set()
    for entry in logs:
        meta = entry.audit_metadata or {}
        stage = meta.get("stage")
        if not stage:
            continue
        if entry.action == "ai_stage_failed" and stage not in completed_stages:
            failed_stages.setdefault(stage, meta.get("error", "Unknown error"))
        elif entry.action == "ai_stage_completed":
            completed_stages.add(stage)
            failed_stages.pop(stage, None)

    if consultation.status == ConsultationStatus.ai_processing:
        if not completed_stages and not failed_stages:
            return AiStatusOut(consultation_status=consultation.status, stage="queued", degraded=False)
        last_stage = (
            STAGE_GENERATE_RECOMMENDATIONS if STAGE_GENERATE_SOAP in completed_stages else STAGE_TRANSCRIBE
        )
        return AiStatusOut(
            consultation_status=consultation.status, stage=f"processing:{last_stage}", degraded=bool(failed_stages)
        )

    if failed_stages:
        return AiStatusOut(
            consultation_status=consultation.status,
            stage="failed",
            degraded=True,
            reason="; ".join(f"{stage}: {error}" for stage, error in failed_stages.items()),
            failed_stage=next(iter(failed_stages)),
            retry_available=True,
        )

    if not completed_stages:
        return AiStatusOut(
            consultation_status=consultation.status,
            stage="no_ai_content",
            degraded=True,
            reason="No audio was captured for this consultation, or AI processing has not run.",
        )

    return AiStatusOut(consultation_status=consultation.status, stage="completed", degraded=False)


async def get_ai_history(db: AsyncSession, *, consultation_id: uuid.UUID) -> list[AiHistoryEntryOut]:
    logs = await AuditLogRepository(db).list_by_entity(
        entity_type="consultation", entity_id=consultation_id, action_prefix="ai_"
    )
    return [
        AiHistoryEntryOut(
            action=log.action, created_at=log.created_at, user_id=log.user_id, metadata=log.audit_metadata
        )
        for log in logs
    ]


async def validate_retry_request(
    db: AsyncSession, *, consultation_id: uuid.UUID, hospital_id: uuid.UUID, doctor_id: uuid.UUID, stage: str
) -> Consultation:
    """Authorization + state check performed synchronously by the API
    handler before enqueueing a retry/regenerate job (Ch16.10) — the actual
    stage run happens later, in the worker, via `run_single_stage_from_queue`."""
    if stage not in RETRYABLE_STAGES:
        raise InvalidStageError(f"Unknown AI stage: {stage}")

    consultation = await ConsultationRepository(db).get_by_id(consultation_id, hospital_id=hospital_id)
    if consultation is None:
        raise NotFoundError(
            "The requested consultation could not be located.", error_code="CONSULTATION_NOT_FOUND"
        )
    if consultation.doctor_id != doctor_id:
        raise AiPipelineNotAvailableError("You do not have permission to access this consultation.")
    if consultation.status not in (ConsultationStatus.ai_processing, ConsultationStatus.pending_review):
        raise AiPipelineNotAvailableError("AI content can only be regenerated while the consultation is active.")
    return consultation


async def edit_soap(
    db: AsyncSession,
    *,
    consultation_id: uuid.UUID,
    hospital_id: uuid.UUID,
    doctor_id: uuid.UUID,
    data: SoapEditRequest,
) -> SoapNote:
    consultation = await ConsultationRepository(db).get_by_id(consultation_id, hospital_id=hospital_id)
    if consultation is None:
        raise NotFoundError(
            "The requested consultation could not be located.", error_code="CONSULTATION_NOT_FOUND"
        )
    if consultation.doctor_id != doctor_id:
        raise AiPipelineNotAvailableError("You do not have permission to access this consultation.")
    if consultation.status == ConsultationStatus.approved:
        raise AiPipelineNotAvailableError("This consultation has already been approved and is read-only.")

    repo = SoapNoteRepository(db)
    note = await repo.get_by_consultation_id(consultation_id)
    if note is None:
        raise NotFoundError(
            "No AI-generated SOAP note exists yet for this consultation.", error_code="SOAP_NOT_FOUND"
        )

    changes = data.model_dump(exclude_unset=True)
    await _audit(
        db,
        consultation=consultation,
        action="ai_content_edited",
        user_id=doctor_id,
        metadata={
            "stage": STAGE_GENERATE_SOAP,
            "previous": {field: getattr(note, field) for field in changes},
            "new": changes,
        },
    )
    for field, value in changes.items():
        setattr(note, field, value)
    note.edited_by_doctor = True
    note.updated_at = _now()
    await repo.save(note)
    await db.commit()
    return note


async def edit_summary(
    db: AsyncSession,
    *,
    consultation_id: uuid.UUID,
    hospital_id: uuid.UUID,
    doctor_id: uuid.UUID,
    data: SummaryEditRequest,
) -> ClinicalSummary:
    consultation = await ConsultationRepository(db).get_by_id(consultation_id, hospital_id=hospital_id)
    if consultation is None:
        raise NotFoundError(
            "The requested consultation could not be located.", error_code="CONSULTATION_NOT_FOUND"
        )
    if consultation.doctor_id != doctor_id:
        raise AiPipelineNotAvailableError("You do not have permission to access this consultation.")
    if consultation.status == ConsultationStatus.approved:
        raise AiPipelineNotAvailableError("This consultation has already been approved and is read-only.")

    repo = ClinicalSummaryRepository(db)
    summary = await repo.get_by_consultation_id(consultation_id)
    if summary is None:
        raise NotFoundError(
            "No AI-generated clinical summary exists yet for this consultation.", error_code="SUMMARY_NOT_FOUND"
        )

    changes = data.model_dump(exclude_unset=True)
    await _audit(
        db,
        consultation=consultation,
        action="ai_content_edited",
        user_id=doctor_id,
        metadata={
            "stage": STAGE_GENERATE_SUMMARY,
            "previous": {field: getattr(summary, field) for field in changes},
            "new": changes,
        },
    )
    for field, value in changes.items():
        setattr(summary, field, value)
    summary.edited_by_doctor = True
    summary.word_count = sum(
        len(str(getattr(summary, field) or "").split())
        for field in ("chief_complaint", "history_of_present_illness", "key_findings", "assessment", "plan")
    )
    summary.updated_at = _now()
    await repo.save(summary)
    await db.commit()
    return summary
