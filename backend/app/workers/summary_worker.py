"""Background worker stages 4-8: build_context -> generate_soap ->
generate_summary -> generate_recommendations -> mark_ready_for_review
(PRD Ch17.2). Consumed by `pipeline_worker.py`'s process loop; the actual
stage logic lives in `app.services.ai_pipeline_service` (single source of
truth shared with the doctor-triggered retry endpoints) — this module is
the thin, named entrypoint the PRD's worker layout expects.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import AiEntity
from app.models.enums import ConsultationStatus
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.consultation_transcript_repository import ConsultationTranscriptRepository
from app.services import ai_pipeline_service
from app.services.audit_service import record_audit_event
from app.services.notification_service import notify_user


async def run(db: AsyncSession, *, consultation_id: uuid.UUID, entities: AiEntity | None) -> None:
    """Runs build_context -> generate_soap -> generate_summary ->
    generate_recommendations -> mark_ready_for_review for `consultation_id`."""
    consultation = await ConsultationRepository(db).get_by_id_any_hospital(consultation_id)
    if consultation is None:
        return
    transcript = await ConsultationTranscriptRepository(db).get_by_consultation_id(consultation_id)
    if transcript is None:
        return

    if transcript.cleaned_transcript:
        context = await ai_pipeline_service._build_context(
            db, consultation=consultation, transcript=transcript, entities=entities
        )
        await ai_pipeline_service._stage_generate_soap(db, consultation=consultation, context=context, force=False)
        await ai_pipeline_service._stage_generate_summary(
            db, consultation=consultation, context=context, force=False
        )
        await ai_pipeline_service._stage_generate_recommendations(
            db, consultation=consultation, context=context, force=False
        )

    consultation.status = ConsultationStatus.pending_review
    consultation.updated_by = consultation.doctor_id
    await ConsultationRepository(db).save(consultation)
    await record_audit_event(
        db,
        action="ai_pipeline_completed",
        user_id=None,
        hospital_id=consultation.hospital_id,
        entity_type="consultation",
        entity_id=consultation.id,
    )
    await notify_user(
        db,
        user_id=consultation.doctor_id,
        notification_type="ai_processing_complete",
        title="AI processing complete",
        message="AI-generated documentation is ready for your review.",
        reference_id=consultation.id,
    )
