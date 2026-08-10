"""Appointment table (PRD Ch15.6)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, UUIDPKMixin
from app.models.enums import AppointmentStatus


class Appointment(UUIDPKMixin, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_hospital_scheduled", "hospital_id", "scheduled_at"),
        Index("ix_appointments_doctor_scheduled", "doctor_id", "scheduled_at"),
    )

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"), nullable=False, default=AppointmentStatus.upcoming
    )
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
