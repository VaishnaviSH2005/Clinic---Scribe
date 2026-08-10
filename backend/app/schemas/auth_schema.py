"""Authentication schemas (PRD Ch16.3)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import RoleName, UserStatus
from app.schemas.validators import validate_password_strength


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str

    _validate_password = field_validator("password")(validate_password_strength)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    _validate_password = field_validator("new_password")(validate_password_strength)


class MeOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: RoleName
    hospitalId: uuid.UUID | None


class ProfileOut(BaseModel):
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

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    """Editable fields only (PRD Ch7.14). Role, organization, and employee_id
    are intentionally absent — attempting to set them is a client error the
    frontend prevents by never rendering the fields, per Ch7.14."""

    full_name: str | None = None
    phone: str | None = None
    profile_photo_url: str | None = None


class SessionOut(BaseModel):
    id: uuid.UUID
    device_info: str | None
    ip_address: str | None
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    is_current: bool
