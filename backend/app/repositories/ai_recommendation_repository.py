"""AI recommendation repository (PRD Ch15.7.6) — possible diagnoses,
recommended tests, follow-ups, and red flags. Multiple rows per
consultation; regeneration replaces the full set for a given `type` (or all
types on a full pipeline regenerate) rather than accumulating duplicates.
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import AiRecommendation
from app.models.enums import RecommendationType


class AiRecommendationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_consultation_id(self, consultation_id: uuid.UUID) -> list[AiRecommendation]:
        result = await self.db.execute(
            select(AiRecommendation)
            .where(AiRecommendation.consultation_id == consultation_id)
            .order_by(AiRecommendation.created_at)
        )
        return list(result.scalars().all())

    async def create_many(self, recommendations: list[AiRecommendation]) -> list[AiRecommendation]:
        self.db.add_all(recommendations)
        await self.db.flush()
        return recommendations

    async def delete_by_types(self, consultation_id: uuid.UUID, types: list[RecommendationType]) -> None:
        await self.db.execute(
            delete(AiRecommendation).where(
                AiRecommendation.consultation_id == consultation_id,
                AiRecommendation.type.in_(types),
            )
        )
        await self.db.flush()
