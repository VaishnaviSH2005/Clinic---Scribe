"""AI-extracted medical entity repository (PRD Ch15.7.3)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import AiEntity


class AiEntityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_consultation_id(self, consultation_id: uuid.UUID) -> AiEntity | None:
        result = await self.db.execute(select(AiEntity).where(AiEntity.consultation_id == consultation_id))
        return result.scalar_one_or_none()

    async def create(self, entity: AiEntity) -> AiEntity:
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def save(self, entity: AiEntity) -> AiEntity:
        await self.db.flush()
        return entity
