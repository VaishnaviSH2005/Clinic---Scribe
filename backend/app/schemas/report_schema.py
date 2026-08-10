"""Report schemas (PRD Ch15.8, Ch16.11)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import ReportType


class ReportOut(BaseModel):
    id: uuid.UUID
    hospital_id: uuid.UUID
    patient_id: uuid.UUID
    consultation_id: uuid.UUID
    report_type: ReportType
    doctor_remarks: str | None
    follow_up_date: date | None
    follow_up_notes: str | None
    pdf_url: str | None
    current_version: int
    is_locked: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportVersionOut(BaseModel):
    id: uuid.UUID
    version_number: int
    pdf_url: str | None
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportUpdateRequest(BaseModel):
    doctor_remarks: str | None = None
    follow_up_date: date | None = None
    follow_up_notes: str | None = None
