"""Consultation API (PRD Ch16.9). AI-dependent endpoints (/summary, /report)
are intentionally omitted this milestone — see services/consultation_service.py.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppError
from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import RoleName
from app.repositories.ai_entity_repository import AiEntityRepository
from app.repositories.ai_recommendation_repository import AiRecommendationRepository
from app.repositories.clinical_summary_repository import ClinicalSummaryRepository
from app.repositories.soap_note_repository import SoapNoteRepository
from app.schemas.ai_schema import AiEntityOut, AiRecommendationOut, ClinicalSummaryOut, SoapNoteOut
from app.schemas.consultation_schema import (
    ConsultationOut,
    ConsultationStartRequest,
    ConsultationUpdateRequest,
    ConsultationWorkspaceOut,
    TranscriptOut,
)
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.services import ai_pipeline_service, consultation_service

router = APIRouter(prefix="/consultations", tags=["consultations"])


class DepartmentRequiredError(AppError):
    status_code = 422
    error_code = "DEPARTMENT_REQUIRED"


@router.post("/start")
async def start_consultation(
    body: ConsultationStartRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ConsultationOut]:
    if current.user.department_id is None and body.appointment_id is None:
        raise DepartmentRequiredError("Your account has no assigned department and no appointment was provided.")

    consultation = await consultation_service.start_consultation(
        db,
        hospital_id=current.hospital_id,
        doctor_id=current.user.id,
        department_id=current.user.department_id,
        data=body,
    )
    await db.commit()
    return ApiResponse(data=ConsultationOut.model_validate(consultation), message="Consultation started.")


@router.get("")
async def list_consultations(
    scope: str = Query(default="active", pattern="^(active|previous|drafts)$"),
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor, RoleName.hospital_admin)),
) -> ApiListResponse[ConsultationOut]:
    doctor_id = current.user.id if current.role == RoleName.doctor else None
    consultations, total = await consultation_service.list_consultations(
        db,
        hospital_id=current.hospital_id,
        doctor_id=doctor_id,
        scope=scope,
        page=pagination.page,
        page_size=pagination.pageSize,
    )
    return ApiListResponse(
        data=[ConsultationOut.model_validate(c) for c in consultations],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )


@router.get("/{consultation_id}")
async def get_consultation_workspace(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ConsultationWorkspaceOut]:
    consultation, transcript, patient = await consultation_service.get_workspace(
        db, consultation_id=consultation_id, hospital_id=current.hospital_id, doctor_id=current.user.id
    )
    ai_status = await ai_pipeline_service.get_ai_status(db, consultation=consultation)
    entities = await AiEntityRepository(db).get_by_consultation_id(consultation.id)
    soap = await SoapNoteRepository(db).get_by_consultation_id(consultation.id)
    summary = await ClinicalSummaryRepository(db).get_by_consultation_id(consultation.id)
    recommendations = await AiRecommendationRepository(db).list_by_consultation_id(consultation.id)

    return ApiResponse(
        data=ConsultationWorkspaceOut(
            consultation=ConsultationOut.model_validate(consultation),
            transcript=TranscriptOut.model_validate(transcript),
            patient=patient,
            ai_status=ai_status,
            entities=AiEntityOut.model_validate(entities) if entities else None,
            soap=SoapNoteOut.model_validate(soap) if soap else None,
            summary=ClinicalSummaryOut.model_validate(summary) if summary else None,
            recommendations=[AiRecommendationOut.model_validate(row) for row in recommendations],
        )
    )


@router.patch("/{consultation_id}")
async def update_consultation(
    consultation_id: uuid.UUID,
    body: ConsultationUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ConsultationOut]:
    consultation = await consultation_service.update_consultation(
        db, consultation_id=consultation_id, hospital_id=current.hospital_id, doctor_id=current.user.id, data=body
    )
    await db.commit()
    return ApiResponse(data=ConsultationOut.model_validate(consultation), message="Consultation updated.")


@router.post("/{consultation_id}/pause")
async def pause_consultation(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ConsultationOut]:
    consultation = await consultation_service.pause_consultation(
        db, consultation_id=consultation_id, hospital_id=current.hospital_id, doctor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=ConsultationOut.model_validate(consultation), message="Recording paused.")


@router.post("/{consultation_id}/resume")
async def resume_consultation(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ConsultationOut]:
    consultation = await consultation_service.resume_consultation(
        db, consultation_id=consultation_id, hospital_id=current.hospital_id, doctor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=ConsultationOut.model_validate(consultation), message="Recording resumed.")


@router.post("/{consultation_id}/draft")
async def save_draft(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ConsultationOut]:
    consultation = await consultation_service.save_draft(
        db, consultation_id=consultation_id, hospital_id=current.hospital_id, doctor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=ConsultationOut.model_validate(consultation), message="Consultation saved as draft.")


@router.post("/{consultation_id}/stop")
async def stop_consultation(
    consultation_id: uuid.UUID,
    audio_file: UploadFile | None = File(default=None),
    audio_duration_seconds: int | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ConsultationOut]:
    consultation = await consultation_service.stop_consultation(
        db,
        consultation_id=consultation_id,
        hospital_id=current.hospital_id,
        doctor_id=current.user.id,
        audio_file=audio_file,
        audio_duration_seconds=audio_duration_seconds,
    )
    await db.commit()
    return ApiResponse(
        data=ConsultationOut.model_validate(consultation), message="Consultation recording stopped."
    )


@router.post("/{consultation_id}/approve")
async def approve_consultation(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ConsultationOut]:
    consultation = await consultation_service.approve_consultation(
        db, consultation_id=consultation_id, hospital_id=current.hospital_id, doctor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=ConsultationOut.model_validate(consultation), message="Consultation approved.")


@router.post("/{consultation_id}/cancel")
async def cancel_consultation(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[None]:
    await consultation_service.cancel_consultation(
        db, consultation_id=consultation_id, hospital_id=current.hospital_id, doctor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=None, message="Consultation cancelled.")
