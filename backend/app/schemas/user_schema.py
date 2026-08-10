"""User/Doctor/Receptionist schemas (PRD Ch7.12/7.13, Ch13.3, Ch16.6/16.13)."""

import uuid

from pydantic import BaseModel, EmailStr

from app.models.enums import RoleName, UserStatus


class DoctorCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    department_id: uuid.UUID
    employee_id: str | None = None
    qualification: str | None = None
    specialization: str | None = None
    medical_registration_number: str | None = None
    experience_years: int | None = None


class ReceptionistCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    department_id: uuid.UUID | None = None
    employee_id: str | None = None


class UserStatusUpdate(BaseModel):
    status: UserStatus


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    department_id: uuid.UUID | None = None
    qualification: str | None = None
    specialization: str | None = None
    medical_registration_number: str | None = None
    experience_years: int | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    hospital_id: uuid.UUID | None
    department_id: uuid.UUID | None
    role: RoleName
    full_name: str
    email: str
    phone: str
    profile_photo_url: str | None
    employee_id: str | None
    qualification: str | None
    specialization: str | None
    medical_registration_number: str | None
    experience_years: int | None
    status: UserStatus
