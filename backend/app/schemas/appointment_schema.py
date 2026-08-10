"""Appointment schemas (PRD Ch16.8)."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AppointmentStatus


class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    department_id: uuid.UUID
    scheduled_at: datetime


class AppointmentReschedule(BaseModel):
    scheduled_at: datetime


class AppointmentOut(BaseModel):
    id: uuid.UUID
    hospital_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    department_id: uuid.UUID
    scheduled_at: datetime
    status: AppointmentStatus
    checked_in_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
