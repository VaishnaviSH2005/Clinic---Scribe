"""Dashboard schemas (PRD Ch5.16 + role-specific dashboard chapters)."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AppointmentStatus, ConsultationStatus


class DashboardCard(BaseModel):
    key: str
    label: str
    value: int
    hint: str | None = None


class AppointmentSummaryOut(BaseModel):
    id: uuid.UUID
    patient_name: str
    scheduled_at: datetime
    status: AppointmentStatus


class ConsultationSummaryOut(BaseModel):
    id: uuid.UUID
    patient_name: str
    status: ConsultationStatus
    created_at: datetime


class DashboardOut(BaseModel):
    role: str
    cards: list[DashboardCard]
    appointments_today: list[AppointmentSummaryOut] = []
    recent_consultations: list[ConsultationSummaryOut] = []
