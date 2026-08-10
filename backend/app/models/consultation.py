"""Consultation tables (PRD Ch15.7)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, UUIDPKMixin
from app.models.enums import ConfidenceLevel, ConsultationStatus, RecommendationType


class Consultation(UUIDPKMixin, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "consultations"
    __table_args__ = (
        Index("ix_consultations_patient_created", "patient_id", "created_at"),
        Index("ix_consultations_doctor_status", "doctor_id", "status"),
    )

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("appointments.id"))
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False
    )
    status: Mapped[ConsultationStatus] = mapped_column(
        Enum(ConsultationStatus, name="consultation_status"),
        nullable=False,
        default=ConsultationStatus.in_progress,
    )
    chief_complaint: Mapped[str | None] = mapped_column(Text)
    doctor_notes: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))


class ConsultationTranscript(UUIDPKMixin, Base):
    __tablename__ = "consultation_transcripts"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    raw_transcript: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    cleaned_transcript: Mapped[list | None] = mapped_column(JSONB)
    audio_file_url: Mapped[str | None] = mapped_column(String(500))
    audio_duration_seconds: Mapped[int | None]
    stt_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="faster_whisper")
    manually_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AiEntity(UUIDPKMixin, Base):
    __tablename__ = "ai_entities"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    symptoms: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    medications: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    allergies: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    medical_history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    vitals: Mapped[dict | None] = mapped_column(JSONB)
    extraction_confidence: Mapped[ConfidenceLevel | None] = mapped_column(
        Enum(ConfidenceLevel, name="confidence_level")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SoapNote(UUIDPKMixin, Base):
    __tablename__ = "soap_notes"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    subjective: Mapped[str | None] = mapped_column(Text)
    objective: Mapped[str | None] = mapped_column(Text)
    assessment: Mapped[str | None] = mapped_column(Text)
    plan: Mapped[str | None] = mapped_column(Text)
    ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    edited_by_doctor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ClinicalSummary(UUIDPKMixin, Base):
    __tablename__ = "clinical_summaries"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    chief_complaint: Mapped[str | None] = mapped_column(Text)
    history_of_present_illness: Mapped[str | None] = mapped_column(Text)
    key_findings: Mapped[str | None] = mapped_column(Text)
    assessment: Mapped[str | None] = mapped_column(Text)
    plan: Mapped[str | None] = mapped_column(Text)
    word_count: Mapped[int | None] = mapped_column(SmallInteger)
    edited_by_doctor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AiRecommendation(UUIDPKMixin, Base):
    __tablename__ = "ai_recommendations"
    __table_args__ = (Index("ix_ai_recommendations_consultation_type", "consultation_id", "type"),)

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[RecommendationType] = mapped_column(
        Enum(RecommendationType, name="recommendation_type"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[ConfidenceLevel | None] = mapped_column(Enum(ConfidenceLevel, name="confidence_level"))
    is_red_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
