"""License / subscription management (PRD Ch1.8/Ch6.10/Ch15.4.2 — Super
Admin "Manage Licenses"). Reuses the `subscriptions` table already defined
in the schema; no new tables.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.hospital import Subscription
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.subscription_schema import SubscriptionCreate, SubscriptionUpdate
from app.services.audit_service import record_audit_event


async def create_subscription(db: AsyncSession, *, data: SubscriptionCreate, actor_id: uuid.UUID) -> Subscription:
    subscription = Subscription(**data.model_dump())
    await SubscriptionRepository(db).create(subscription)
    await record_audit_event(
        db,
        action="subscription_created",
        user_id=actor_id,
        hospital_id=subscription.hospital_id,
        entity_type="subscription",
        entity_id=subscription.id,
        metadata={"plan_name": subscription.plan_name, "status": subscription.status.value},
    )
    return subscription


async def list_subscriptions(
    db: AsyncSession, *, page: int = 1, page_size: int = 20
) -> tuple[list[Subscription], int]:
    return await SubscriptionRepository(db).list_all(page=page, page_size=page_size)


async def get_subscription(db: AsyncSession, *, subscription_id: uuid.UUID) -> Subscription:
    subscription = await SubscriptionRepository(db).get_by_id(subscription_id)
    if subscription is None:
        raise NotFoundError("The requested license could not be located.", error_code="SUBSCRIPTION_NOT_FOUND")
    return subscription


async def update_subscription(
    db: AsyncSession, *, subscription_id: uuid.UUID, data: SubscriptionUpdate, actor_id: uuid.UUID
) -> Subscription:
    subscription = await get_subscription(db, subscription_id=subscription_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(subscription, field, value)
    await SubscriptionRepository(db).save(subscription)
    await record_audit_event(
        db,
        action="subscription_updated",
        user_id=actor_id,
        hospital_id=subscription.hospital_id,
        entity_type="subscription",
        entity_id=subscription.id,
        metadata={"status": subscription.status.value},
    )
    return subscription
