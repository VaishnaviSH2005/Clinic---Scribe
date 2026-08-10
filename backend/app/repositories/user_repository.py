"""User repository (PRD Ch15.4.4). All queries filter by hospital_id in
addition to the primary key per Ch15.2 tenant-isolation convention, except
for platform-level lookups (email uniqueness, Super Admin access) which are
intentionally global.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RoleName, UserStatus
from app.models.hospital import Role
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID, *, hospital_id: uuid.UUID | None = None) -> User | None:
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        if hospital_id is not None:
            stmt = stmt.where(User.hospital_id == hospital_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.lower(), User.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_role(self, role_id: uuid.UUID) -> Role | None:
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def list_by_hospital(
        self,
        hospital_id: uuid.UUID,
        *,
        role_name: RoleName | None = None,
        department_id: uuid.UUID | None = None,
        status: UserStatus | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        stmt = select(User).join(Role, User.role_id == Role.id).where(
            User.hospital_id == hospital_id, User.deleted_at.is_(None)
        )
        if role_name is not None:
            stmt = stmt.where(Role.name == role_name)
        if department_id is not None:
            stmt = stmt.where(User.department_id == department_id)
        if status is not None:
            stmt = stmt.where(User.status == status)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(User.full_name.ilike(like), User.email.ilike(like)))

        count_result = await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        total = count_result.scalar_one()

        stmt = stmt.order_by(User.full_name).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def count_active_by_department(self, department_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(User)
            .where(
                User.department_id == department_id,
                User.status == UserStatus.active,
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def save(self, user: User) -> User:
        user.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return user
