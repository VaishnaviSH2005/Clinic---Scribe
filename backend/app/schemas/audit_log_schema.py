"""Audit log read schema (PRD Ch6.3 — Super Admin "View Audit Logs")."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: uuid.UUID
    hospital_id: uuid.UUID | None
    user_id: uuid.UUID | None
    action: str
    entity_type: str | None
    entity_id: uuid.UUID | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
