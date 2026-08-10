"""Patient schemas (PRD Ch8.4/8.16, Ch16.7)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import DocumentFileType, Gender


class MedicalProfileInput(BaseModel):
    known_allergies: list[str] = []
    chronic_diseases: list[str] = []
    current_medications: list[str] = []
    previous_surgeries: list[str] = []
    family_history: str | None = None
    lifestyle_smoking: bool | None = None
    lifestyle_alcohol: bool | None = None
    lifestyle_tobacco: bool | None = None
    height_cm: float | None = None
    weight_kg: float | None = None


class MedicalProfileOut(MedicalProfileInput):
    model_config = {"from_attributes": True}


class PatientCreate(BaseModel):
    full_name: str
    date_of_birth: date
    gender: Gender
    blood_group: str | None = None
    mobile_number: str
    email: EmailStr | None = None
    aadhaar_number: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_number: str | None = None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pin_code: str | None = None
    medical_info: MedicalProfileInput | None = None


class PatientUpdate(BaseModel):
    """Editable fields only (PRD Ch8.16) — UHID, date_of_birth, and
    historical consultation records are intentionally absent."""

    mobile_number: str | None = None
    email: EmailStr | None = None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pin_code: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_number: str | None = None


class PatientOut(BaseModel):
    id: uuid.UUID
    hospital_id: uuid.UUID
    uhid: str
    full_name: str
    date_of_birth: date
    age: int
    gender: Gender
    blood_group: str | None
    mobile_number: str
    email: str | None
    aadhaar_number: str | None
    emergency_contact_name: str | None
    emergency_contact_number: str | None
    address_line: str | None
    city: str | None
    state: str | None
    country: str | None
    pin_code: str | None
    photo_url: str | None
    status: str  # "active" | "archived", derived from deleted_at
    created_at: datetime


class DocumentOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    consultation_id: uuid.UUID | None
    file_name: str
    file_type: DocumentFileType
    file_url: str
    file_size_bytes: int
    document_category: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TimelineEventOut(BaseModel):
    id: uuid.UUID
    event_type: str
    event_date: datetime
    title: str
    description: str | None
    reference_id: uuid.UUID | None

    model_config = {"from_attributes": True}
