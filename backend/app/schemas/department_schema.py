"""Department schemas (PRD Ch7.11, Ch16.5)."""

import uuid

from pydantic import BaseModel

from app.models.enums import DepartmentStatus


class DepartmentCreate(BaseModel):
    name: str
    head_of_department_id: uuid.UUID | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    head_of_department_id: uuid.UUID | None = None


class DepartmentStatusUpdate(BaseModel):
    status: DepartmentStatus


class DepartmentOut(BaseModel):
    id: uuid.UUID
    hospital_id: uuid.UUID
    name: str
    head_of_department_id: uuid.UUID | None
    status: DepartmentStatus

    model_config = {"from_attributes": True}
