"""Key-value settings repository (PRD Ch15.9.3)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SettingsScope
from app.models.platform import Setting


class SettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(
        self, *, scope: SettingsScope, user_id: uuid.UUID | None, hospital_id: uuid.UUID | None, key: str
    ) -> Setting | None:
        result = await self.db.execute(
            select(Setting).where(
                Setting.scope == scope,
                Setting.user_id == user_id,
                Setting.hospital_id == hospital_id,
                Setting.key == key,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        scope: SettingsScope,
        user_id: uuid.UUID | None,
        hospital_id: uuid.UUID | None,
        key: str,
        value: dict,
        updated_at,
    ) -> Setting:
        existing = await self.get(scope=scope, user_id=user_id, hospital_id=hospital_id, key=key)
        if existing is not None:
            existing.value = value
            existing.updated_at = updated_at
            await self.db.flush()
            return existing

        setting = Setting(
            scope=scope, user_id=user_id, hospital_id=hospital_id, key=key, value=value, updated_at=updated_at
        )
        self.db.add(setting)
        await self.db.flush()
        return setting
