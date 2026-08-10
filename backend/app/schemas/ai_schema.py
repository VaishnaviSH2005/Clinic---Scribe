"""AI pipeline schemas (PRD Ch15.7.3-15.7.6, Ch16.10)."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ConfidenceLevel, ConsultationStatus, RecommendationType


class AiEntityOut(BaseModel):
    id: uuid.UUID
    symptoms: list
    medications: list
    allergies: list
    medical_history: list
    vitals: dict | None
    extraction_confidence: ConfidenceLevel | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SoapNoteOut(BaseModel):
    id: uuid.UUID
    subjective: str | None
    objective: str | None
    assessment: str | None
    plan: str | None
    ai_generated: bool
    edited_by_doctor: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SoapEditRequest(BaseModel):
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None


class ClinicalSummaryOut(BaseModel):
    id: uuid.UUID
    chief_complaint: str | None
    history_of_present_illness: str | None
    key_findings: str | None
    assessment: str | None
    plan: str | None
    word_count: int | None
    edited_by_doctor: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SummaryEditRequest(BaseModel):
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    key_findings: str | None = None
    assessment: str | None = None
    plan: str | None = None


class AiRecommendationOut(BaseModel):
    id: uuid.UUID
    type: RecommendationType
    content: str
    explanation: str | None
    confidence: ConfidenceLevel | None
    is_red_flag: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AiStatusOut(BaseModel):
    """Computed, not persisted (PRD Ch9's ConsultationStatus enum only has
    a single `ai_processing` state) — derived from consultation.status plus
    which AI result rows exist plus the latest AI-related audit log entry."""

    consultation_status: ConsultationStatus
    stage: str
    degraded: bool
    reason: str | None = None
    failed_stage: str | None = None
    retry_available: bool = False


class AiHistoryEntryOut(BaseModel):
    action: str
    created_at: datetime
    user_id: uuid.UUID | None
    metadata: dict | None


class RetryRequest(BaseModel):
    stage: str
