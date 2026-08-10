"""Consultation schemas (PRD Ch9, Ch16.9)."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ConsultationStatus
from app.schemas.ai_schema import (
    AiEntityOut,
    AiRecommendationOut,
    AiStatusOut,
    ClinicalSummaryOut,
    SoapNoteOut,
)


class ConsultationStartRequest(BaseModel):
    patient_id: uuid.UUID
    appointment_id: uuid.UUID | None = None
    chief_complaint: str | None = None


class ConsultationUpdateRequest(BaseModel):
    chief_complaint: str | None = None
    doctor_notes: str | None = None


class TranscriptOut(BaseModel):
    id: uuid.UUID
    raw_transcript: list
    cleaned_transcript: list | None
    audio_file_url: str | None
    audio_duration_seconds: int | None
    manually_edited: bool

    model_config = {"from_attributes": True}


class ConsultationOut(BaseModel):
    id: uuid.UUID
    hospital_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_id: uuid.UUID | None
    department_id: uuid.UUID
    status: ConsultationStatus
    chief_complaint: str | None
    doctor_notes: str | None
    started_at: datetime | None
    ended_at: datetime | None
    approved_at: datetime | None
    approved_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MedicalAlertsOut(BaseModel):
    known_allergies: list[str] = []
    chronic_diseases: list[str] = []
    current_medications: list[str] = []


class PreviousConsultationOut(BaseModel):
    id: uuid.UUID
    started_at: datetime | None
    chief_complaint: str | None
    status: ConsultationStatus

    model_config = {"from_attributes": True}


class PatientContextOut(BaseModel):
    id: uuid.UUID
    full_name: str
    uhid: str
    age: int
    gender: str
    blood_group: str | None
    medical_alerts: MedicalAlertsOut
    previous_consultations: list[PreviousConsultationOut]


class ConsultationWorkspaceOut(BaseModel):
    consultation: ConsultationOut
    transcript: TranscriptOut
    patient: PatientContextOut
    ai_status: AiStatusOut
    entities: AiEntityOut | None = None
    soap: SoapNoteOut | None = None
    summary: ClinicalSummaryOut | None = None
    recommendations: list[AiRecommendationOut] = []
