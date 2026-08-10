"""Patient repository (PRD Ch15.5.1)."""

import uuid
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient


class PatientRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self, patient_id: uuid.UUID, *, hospital_id: uuid.UUID, include_deleted: bool = False
    ) -> Patient | None:
        stmt = select(Patient).where(Patient.id == patient_id, Patient.hospital_id == hospital_id)
        if not include_deleted:
            stmt = stmt.where(Patient.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_uhid(self, uhid: str) -> Patient | None:
        result = await self.db.execute(select(Patient).where(Patient.uhid == uhid))
        return result.scalar_one_or_none()

    async def find_duplicate(
        self, hospital_id: uuid.UUID, *, mobile_number: str, date_of_birth: date
    ) -> Patient | None:
        """PRD Ch8.25 — duplicate detection via mobile number + date of birth."""
        result = await self.db.execute(
            select(Patient).where(
                Patient.hospital_id == hospital_id,
                Patient.mobile_number == mobile_number,
                Patient.date_of_birth == date_of_birth,
                Patient.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def count_this_year(self, hospital_id: uuid.UUID, year: int) -> int:
        """Used to derive the sequential portion of the UHID (Ch8.4: CLN-YYYY-NNNNNN)."""
        result = await self.db.execute(
            select(func.count()).select_from(Patient).where(
                Patient.hospital_id == hospital_id,
                func.extract("year", Patient.created_at) == year,
            )
        )
        return result.scalar_one()

    async def list_by_hospital(
        self,
        hospital_id: uuid.UUID,
        *,
        search: str | None = None,
        include_archived: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Patient], int]:
        stmt = select(Patient).where(Patient.hospital_id == hospital_id)
        if not include_archived:
            stmt = stmt.where(Patient.deleted_at.is_(None))
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Patient.full_name.ilike(like),
                    Patient.uhid.ilike(like),
                    Patient.mobile_number.ilike(like),
                    Patient.aadhaar_number.ilike(like),
                )
            )

        count_result = await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        total = count_result.scalar_one()

        stmt = stmt.order_by(Patient.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, patient: Patient) -> Patient:
        self.db.add(patient)
        await self.db.flush()
        return patient

    async def save(self, patient: Patient) -> Patient:
        await self.db.flush()
        return patient
