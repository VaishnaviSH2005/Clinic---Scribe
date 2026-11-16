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
    # A time that has already passed is refused unless the user explicitly confirms
    # ("book anyway"), e.g. to back-fill a visit that already happened.
    allow_past: bool = False


class AppointmentReschedule(BaseModel):
    scheduled_at: datetime
    allow_past: bool = False


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
