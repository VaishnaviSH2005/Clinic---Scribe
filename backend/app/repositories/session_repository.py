"""Session repository (PRD Ch15.4.5, extended per Ch7.13/Ch18)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Session as SessionModel


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, session_id: uuid.UUID) -> SessionModel | None:
        result = await self.db.execute(select(SessionModel).where(SessionModel.id == session_id))
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[SessionModel]:
        result = await self.db.execute(
            select(SessionModel).where(SessionModel.user_id == user_id).order_by(SessionModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, session: SessionModel) -> SessionModel:
        self.db.add(session)
        await self.db.flush()
        return session

    async def save(self, session: SessionModel) -> SessionModel:
        await self.db.flush()
        return session

    async def touch(self, session: SessionModel) -> None:
        session.last_activity_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def delete(self, session_id: uuid.UUID) -> None:
        await self.db.execute(delete(SessionModel).where(SessionModel.id == session_id))

    async def delete_all_for_user(self, user_id: uuid.UUID, *, except_session_id: uuid.UUID | None = None) -> None:
        stmt = delete(SessionModel).where(SessionModel.user_id == user_id)
        if except_session_id is not None:
            stmt = stmt.where(SessionModel.id != except_session_id)
        await self.db.execute(stmt)
