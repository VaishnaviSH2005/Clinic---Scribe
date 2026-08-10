"""Patient tables (PRD Ch15.5)."""

import uuid
from datetime import date, datetime

from sqlalchemy import DECIMAL, Date, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, UUIDPKMixin
from app.models.enums import DocumentFileType, Gender, TimelineEventType


class Patient(UUIDPKMixin, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "patients"
    __table_args__ = (Index("ix_patients_hospital_mobile", "hospital_id", "mobile_number"),)

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    uhid: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, name="gender"), nullable=False)
    blood_group: Mapped[str | None] = mapped_column(String(5))
    mobile_number: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    aadhaar_number: Mapped[str | None] = mapped_column(String(20))
    emergency_contact_name: Mapped[str | None] = mapped_column(String(255))
    emergency_contact_number: Mapped[str | None] = mapped_column(String(20))
    address_line: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    pin_code: Mapped[str | None] = mapped_column(String(10))
    photo_url: Mapped[str | None] = mapped_column(String(500))


class MedicalProfile(UUIDPKMixin, Base):
    __tablename__ = "medical_profiles"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, unique=True
    )
    known_allergies: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    chronic_diseases: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    current_medications: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    previous_surgeries: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    family_history: Mapped[str | None] = mapped_column(Text)
    lifestyle_smoking: Mapped[bool | None]
    lifestyle_alcohol: Mapped[bool | None]
    lifestyle_tobacco: Mapped[bool | None]
    height_cm: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    weight_kg: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PatientAiSummary(UUIDPKMixin, Base):
    __tablename__ = "patient_ai_summaries"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, unique=True
    )
    primary_complaints: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    frequently_prescribed_medicines: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    significant_diagnoses: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    high_risk_alerts: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    source_consultation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Document(UUIDPKMixin, SoftDeleteMixin, Base):
    __tablename__ = "documents"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    consultation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("consultations.id"))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[DocumentFileType] = mapped_column(
        Enum(DocumentFileType, name="document_file_type"), nullable=False
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False)
    document_category: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TimelineEvent(UUIDPKMixin, Base):
    __tablename__ = "timeline_events"
    __table_args__ = (Index("ix_timeline_events_patient_date", "patient_id", "event_date"),)

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    event_type: Mapped[TimelineEventType] = mapped_column(
        Enum(TimelineEventType, name="timeline_event_type"), nullable=False
    )
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
