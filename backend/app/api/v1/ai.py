"""AI clinical documentation pipeline API (PRD Ch16.10). Every endpoint here
is scoped to a single consultation, requires the assigned doctor, and never
runs a Claude/STT call inline — regenerate/retry endpoints enqueue a worker
job and return immediately; the frontend polls `GET .../status`.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_queue import enqueue_ai_job
from app.core.database import get_db
from app.dependencies.auth import CurrentUser, require_roles
from app.models.consultation import Consultation
from app.models.enums import RoleName
from app.repositories.ai_entity_repository import AiEntityRepository
from app.repositories.ai_recommendation_repository import AiRecommendationRepository
from app.repositories.clinical_summary_repository import ClinicalSummaryRepository
from app.repositories.soap_note_repository import SoapNoteRepository
from app.schemas.ai_schema import (
    AiEntityOut,
    AiHistoryEntryOut,
    AiRecommendationOut,
    AiStatusOut,
    ClinicalSummaryOut,
    SoapEditRequest,
    SoapNoteOut,
    SummaryEditRequest,
)
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.services import ai_pipeline_service, consultation_service

router = APIRouter(prefix="/consultations/{consultation_id}/ai", tags=["ai"])


async def _get_owned_consultation(
    db: AsyncSession, *, consultation_id: uuid.UUID, current: CurrentUser
) -> Consultation:
    """Every read/write in this router is scoped to a consultation the
    acting doctor owns (Ch9.24) — reused from consultation_service's
    private ownership check so this router never diverges from the same
    rule enforced on the main consultations endpoints."""
    consultation = await consultation_service.get_consultation(
        db, consultation_id=consultation_id, hospital_id=current.hospital_id
    )
    consultation_service._ensure_owner(consultation, current.user.id)  # noqa: SLF001
    return consultation


async def _enqueue_retry(
    consultation_id: uuid.UUID, stage: str, db: AsyncSession, current: CurrentUser
) -> ApiResponse[None]:
    await ai_pipeline_service.validate_retry_request(
        db,
        consultation_id=consultation_id,
        hospital_id=current.hospital_id,
        doctor_id=current.user.id,
        stage=stage,
    )
    await enqueue_ai_job(consultation_id, stage=stage)
    return ApiResponse(data=None, message=f"Regenerating {stage.replace('_', ' ')}.")


@router.post("/transcribe")
async def retry_transcribe(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[None]:
    return await _enqueue_retry(consultation_id, ai_pipeline_service.STAGE_TRANSCRIBE, db, current)


@router.post("/entities")
async def retry_entities(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[None]:
    return await _enqueue_retry(consultation_id, ai_pipeline_service.STAGE_EXTRACT_ENTITIES, db, current)


@router.post("/soap")
async def retry_soap(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[None]:
    return await _enqueue_retry(consultation_id, ai_pipeline_service.STAGE_GENERATE_SOAP, db, current)


@router.post("/summary")
async def retry_summary(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[None]:
    return await _enqueue_retry(consultation_id, ai_pipeline_service.STAGE_GENERATE_SUMMARY, db, current)


@router.post("/recommendations")
async def retry_recommendations(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[None]:
    return await _enqueue_retry(consultation_id, ai_pipeline_service.STAGE_GENERATE_RECOMMENDATIONS, db, current)


@router.get("/status")
async def get_status(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[AiStatusOut]:
    consultation = await _get_owned_consultation(db, consultation_id=consultation_id, current=current)
    status_out = await ai_pipeline_service.get_ai_status(db, consultation=consultation)
    return ApiResponse(data=status_out)


@router.get("/history")
async def get_history(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiListResponse[AiHistoryEntryOut]:
    await _get_owned_consultation(db, consultation_id=consultation_id, current=current)
    entries = await ai_pipeline_service.get_ai_history(db, consultation_id=consultation_id)
    return ApiListResponse(data=entries, pagination=Pagination(page=1, pageSize=len(entries), total=len(entries)))


@router.get("/entities")
async def get_entities(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[AiEntityOut | None]:
    await _get_owned_consultation(db, consultation_id=consultation_id, current=current)
    entity = await AiEntityRepository(db).get_by_consultation_id(consultation_id)
    return ApiResponse(data=AiEntityOut.model_validate(entity) if entity else None)


@router.get("/soap")
async def get_soap(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[SoapNoteOut | None]:
    await _get_owned_consultation(db, consultation_id=consultation_id, current=current)
    note = await SoapNoteRepository(db).get_by_consultation_id(consultation_id)
    return ApiResponse(data=SoapNoteOut.model_validate(note) if note else None)


@router.patch("/soap")
async def update_soap(
    consultation_id: uuid.UUID,
    body: SoapEditRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[SoapNoteOut]:
    note = await ai_pipeline_service.edit_soap(
        db,
        consultation_id=consultation_id,
        hospital_id=current.hospital_id,
        doctor_id=current.user.id,
        data=body,
    )
    return ApiResponse(data=SoapNoteOut.model_validate(note), message="SOAP note updated.")


@router.get("/summary")
async def get_summary(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ClinicalSummaryOut | None]:
    await _get_owned_consultation(db, consultation_id=consultation_id, current=current)
    summary = await ClinicalSummaryRepository(db).get_by_consultation_id(consultation_id)
    return ApiResponse(data=ClinicalSummaryOut.model_validate(summary) if summary else None)


@router.patch("/summary")
async def update_summary(
    consultation_id: uuid.UUID,
    body: SummaryEditRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ClinicalSummaryOut]:
    summary = await ai_pipeline_service.edit_summary(
        db,
        consultation_id=consultation_id,
        hospital_id=current.hospital_id,
        doctor_id=current.user.id,
        data=body,
    )
    return ApiResponse(data=ClinicalSummaryOut.model_validate(summary), message="Clinical summary updated.")


@router.get("/recommendations")
async def get_recommendations(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[list[AiRecommendationOut]]:
    await _get_owned_consultation(db, consultation_id=consultation_id, current=current)
    rows = await AiRecommendationRepository(db).list_by_consultation_id(consultation_id)
    return ApiResponse(data=[AiRecommendationOut.model_validate(row) for row in rows])
