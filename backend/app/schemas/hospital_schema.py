"""Hospital schemas (PRD Ch7.10, Ch16.4)."""

import uuid

from pydantic import BaseModel, EmailStr

from app.models.enums import HospitalStatus


class HospitalCreate(BaseModel):
    name: str
    registration_number: str
    email: EmailStr
    phone: str
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    logo_url: str | None = None
    working_hours: dict | None = None


class HospitalUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    logo_url: str | None = None
    working_hours: dict | None = None


class HospitalStatusUpdate(BaseModel):
    status: HospitalStatus


class HospitalOut(BaseModel):
    id: uuid.UUID
    name: str
    registration_number: str
    email: str
    phone: str
    address_line: str | None
    city: str | None
    state: str | None
    country: str | None
    logo_url: str | None
    status: HospitalStatus
    working_hours: dict | None

    model_config = {"from_attributes": True}
