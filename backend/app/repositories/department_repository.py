"""Department repository (PRD Ch15.4.7)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hospital import Department


class DepartmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self, department_id: uuid.UUID, *, hospital_id: uuid.UUID | None = None
    ) -> Department | None:
        stmt = select(Department).where(Department.id == department_id, Department.deleted_at.is_(None))
        if hospital_id is not None:
            stmt = stmt.where(Department.hospital_id == hospital_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_hospital(
        self, hospital_id: uuid.UUID, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[Department], int]:
        base = select(Department).where(Department.hospital_id == hospital_id, Department.deleted_at.is_(None))
        count_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar_one()
        stmt = base.order_by(Department.name).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, department: Department) -> Department:
        self.db.add(department)
        await self.db.flush()
        return department

    async def save(self, department: Department) -> Department:
        await self.db.flush()
        return department
