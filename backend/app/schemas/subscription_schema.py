"""License / subscription schemas (PRD Ch1.8/Ch6.10/Ch15.4.2 — Super Admin
'Manage Licenses'). Backed by the `subscriptions` table already defined in
the schema; nothing new to migrate.
"""

import uuid
from datetime import date

from pydantic import BaseModel

from app.models.enums import SubscriptionStatus


class SubscriptionCreate(BaseModel):
    hospital_id: uuid.UUID
    plan_name: str
    status: SubscriptionStatus = SubscriptionStatus.trial
    starts_at: date
    expires_at: date


class SubscriptionUpdate(BaseModel):
    plan_name: str | None = None
    status: SubscriptionStatus | None = None
    starts_at: date | None = None
    expires_at: date | None = None


class SubscriptionOut(BaseModel):
    id: uuid.UUID
    hospital_id: uuid.UUID
    plan_name: str
    status: SubscriptionStatus
    starts_at: date
    expires_at: date

    model_config = {"from_attributes": True}
