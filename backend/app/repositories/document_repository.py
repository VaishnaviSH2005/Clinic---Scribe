"""Document repository (PRD Ch15.5.4)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Document


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self, document_id: uuid.UUID, *, hospital_id: uuid.UUID, patient_id: uuid.UUID | None = None
    ) -> Document | None:
        stmt = select(Document).where(
            Document.id == document_id, Document.hospital_id == hospital_id, Document.deleted_at.is_(None)
        )
        if patient_id is not None:
            stmt = stmt.where(Document.patient_id == patient_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_patient(self, patient_id: uuid.UUID) -> list[Document]:
        result = await self.db.execute(
            select(Document)
            .where(Document.patient_id == patient_id, Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, document: Document) -> Document:
        self.db.add(document)
        await self.db.flush()
        return document
