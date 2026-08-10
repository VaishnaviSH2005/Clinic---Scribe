"""Background worker stages 1-3: transcribe -> clean_transcript ->
extract_entities (PRD Ch17.2). Consumed by `pipeline_worker.py`'s process
loop; the actual stage logic lives in `app.services.ai_pipeline_service`
(single source of truth shared with the doctor-triggered retry endpoints)
— this module is the thin, named entrypoint the PRD's worker layout expects.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import AiEntity
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.consultation_transcript_repository import ConsultationTranscriptRepository
from app.services import ai_pipeline_service


async def run(db: AsyncSession, *, consultation_id: uuid.UUID) -> AiEntity | None:
    """Runs transcribe -> clean_transcript -> extract_entities for
    `consultation_id`. Returns the persisted `AiEntity` row (or None if
    there was nothing to transcribe, e.g. no audio was ever captured)."""
    consultation = await ConsultationRepository(db).get_by_id_any_hospital(consultation_id)
    if consultation is None:
        return None
    transcript = await ConsultationTranscriptRepository(db).get_by_consultation_id(consultation_id)
    if transcript is None:
        return None

    await ai_pipeline_service._stage_transcribe(db, consultation=consultation, transcript=transcript, force=False)
    await ai_pipeline_service._stage_clean_transcript(db, transcript=transcript, force=False)
    return await ai_pipeline_service._stage_extract_entities(
        db, consultation=consultation, transcript=transcript, force=False
    )
