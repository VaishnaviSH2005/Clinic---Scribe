"""Analytics module (PRD analytics chapters). Hospital-scoped for Hospital
Admin, further doctor-scoped for Doctor (consultation/appointment figures
only ever cover their own patients) — enforced here, not in the frontend,
per the "backend remains authoritative" security requirement.
"""

import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RoleName
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics_schema import AnalyticsOut, NamedCount, TimeSeriesPoint


async def get_analytics(
    db: AsyncSession,
    *,
    role: RoleName,
    hospital_id: uuid.UUID,
    user_id: uuid.UUID,
    date_from: date | None,
    date_to: date | None,
) -> AnalyticsOut:
    date_to = date_to or date.today()
    date_from = date_from or (date_to - timedelta(days=29))

    doctor_id = user_id if role == RoleName.doctor else None
    repo = AnalyticsRepository(db)

    consultations_by_status = await repo.consultations_by_status(
        hospital_id, date_from=date_from, date_to=date_to, doctor_id=doctor_id
    )
    consultations_per_day = await repo.consultations_per_day(
        hospital_id, date_from=date_from, date_to=date_to, doctor_id=doctor_id
    )
    appointments_by_status = await repo.appointments_by_status(
        hospital_id, date_from=date_from, date_to=date_to, doctor_id=doctor_id
    )

    # Doctor-department breakdowns and platform-facing rates stay
    # Hospital-Admin-only — a doctor never sees other doctors' volumes.
    if role == RoleName.doctor:
        new_patients_per_day: list[tuple] = []
        ai_outcomes: dict[str, int] = {}
        by_doctor: list[tuple] = []
        by_department: list[tuple] = []
        reports_generated = 0
        missed_rate = 0.0
    else:
        new_patients_per_day = await repo.new_patients_per_day(hospital_id, date_from=date_from, date_to=date_to)
        ai_outcomes = await repo.ai_processing_outcomes(hospital_id, date_from=date_from, date_to=date_to)
        by_doctor = await repo.consultations_by_doctor(hospital_id, date_from=date_from, date_to=date_to)
        by_department = await repo.consultations_by_department(hospital_id, date_from=date_from, date_to=date_to)
        reports_generated = await repo.reports_generated(hospital_id, date_from=date_from, date_to=date_to)
        missed_rate = await repo.missed_appointment_rate(hospital_id, date_from=date_from, date_to=date_to)

    return AnalyticsOut(
        date_from=date_from,
        date_to=date_to,
        consultations_by_status=consultations_by_status,
        consultations_per_day=[TimeSeriesPoint(date=d, count=c) for d, c in consultations_per_day],
        appointments_by_status=appointments_by_status,
        new_patients_per_day=[TimeSeriesPoint(date=d, count=c) for d, c in new_patients_per_day],
        ai_processing_outcomes=ai_outcomes,
        consultations_by_doctor=[NamedCount(name=n, count=c) for n, c in by_doctor],
        consultations_by_department=[NamedCount(name=n, count=c) for n, c in by_department],
        reports_generated=reports_generated,
        missed_appointment_rate=missed_rate,
    )
