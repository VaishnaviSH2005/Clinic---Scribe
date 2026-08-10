"""License / subscription repository (PRD Ch15.4.2)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hospital import Subscription


class SubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, subscription: Subscription) -> Subscription:
        self.db.add(subscription)
        await self.db.flush()
        return subscription

    async def get_by_id(self, subscription_id: uuid.UUID) -> Subscription | None:
        result = await self.db.execute(select(Subscription).where(Subscription.id == subscription_id))
        return result.scalar_one_or_none()

    async def list_all(self, *, page: int = 1, page_size: int = 20) -> tuple[list[Subscription], int]:
        base = select(Subscription)
        count_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar_one()
        stmt = base.order_by(Subscription.expires_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def save(self, subscription: Subscription) -> Subscription:
        await self.db.flush()
        return subscription

    async def counts_by_status(self) -> dict[str, int]:
        result = await self.db.execute(select(Subscription.status, func.count()).group_by(Subscription.status))
        return {status.value: count for status, count in result.all()}
