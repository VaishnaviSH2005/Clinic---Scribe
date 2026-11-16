"""Global search (PRD search chapter). Composes existing per-entity
repositories — never a second query layer — and narrows what's searched by
role so, e.g., a receptionist's search never surfaces clinical
consultations or reports (Ch6 RBAC), and a doctor only ever sees their own
consultations/reports even though patients are hospital-wide.
"""

import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RoleName
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.user_repository import UserRepository
from app.schemas.search_schema import SearchResultItem, SearchResultsOut

_MAX_PER_CATEGORY = 5
# A full or partial UUID as printed in the UI (hex digits and dashes, 6+ characters).
_ID_FRAGMENT = re.compile(r"^[0-9a-fA-F-]{6,36}$")


async def global_search(
    db: AsyncSession, *, hospital_id: uuid.UUID, role: RoleName, user_id: uuid.UUID, query: str
) -> SearchResultsOut:
    if len(query.strip()) < 2:
        return SearchResultsOut(query=query, results=[])

    results: list[SearchResultItem] = []

    # PRD Ch6.13: search also finds an Appointment ID or Consultation ID directly.
    fragment = query.strip().lower()
    if _ID_FRAGMENT.match(fragment):
        if role in (RoleName.hospital_admin, RoleName.receptionist, RoleName.doctor):
            for appt in await AppointmentRepository(db).find_by_id_prefix(fragment, hospital_id=hospital_id):
                results.append(
                    SearchResultItem(
                        id=appt.id,
                        type="appointment",
                        title=f"Appointment {str(appt.id)[:8]} · {appt.scheduled_at:%d %b %Y %H:%M}",
                        subtitle=appt.status.value.replace("_", " ").title(),
                        href="/appointments",
                    )
                )
        if role == RoleName.doctor:  # Consultation module is Doctor-only (PRD Ch6.15)
            for consultation in await ConsultationRepository(db).find_by_id_prefix(
                fragment, hospital_id=hospital_id, doctor_id=user_id
            ):
                results.append(
                    SearchResultItem(
                        id=consultation.id,
                        type="consultation",
                        title=f"Consultation {str(consultation.id)[:8]}",
                        subtitle=consultation.status.value.replace("_", " ").title(),
                        href=f"/consultations/{consultation.id}",
                    )
                )

    patients, _ = await PatientRepository(db).list_by_hospital(
        hospital_id, search=query, page=1, page_size=_MAX_PER_CATEGORY
    )
    for patient in patients:
        results.append(
            SearchResultItem(
                id=patient.id,
                type="patient",
                title=patient.full_name,
                subtitle=f"{patient.uhid} · {patient.mobile_number}",
                href=f"/patients/{patient.id}",
            )
        )

    matched_patient_ids = [p.id for p in patients]

    if role in (RoleName.hospital_admin, RoleName.receptionist, RoleName.doctor):
        appointment_repo = AppointmentRepository(db)
        for patient_id in matched_patient_ids[:_MAX_PER_CATEGORY]:
            appointments = await appointment_repo.list_by_patient(patient_id)
            for appt in appointments[:2]:
                results.append(
                    SearchResultItem(
                        id=appt.id,
                        type="appointment",
                        title=f"Appointment · {appt.scheduled_at:%d %b %Y %H:%M}",
                        subtitle=appt.status.value.replace("_", " ").title(),
                        href="/appointments",
                    )
                )

    if role in (RoleName.hospital_admin, RoleName.doctor, RoleName.receptionist):
        consultation_repo = ConsultationRepository(db)
        report_repo = ReportRepository(db)
        for patient_id in matched_patient_ids[:_MAX_PER_CATEGORY]:
            # Consultations are Doctor-only (PRD Ch6.15); reports are viewable by Hospital
            # Admin and Receptionist too (view only).
            consultations = (
                await consultation_repo.list_by_patient(patient_id, limit=2) if role == RoleName.doctor else []
            )
            for consultation in consultations:
                if consultation.doctor_id != user_id:
                    continue
                results.append(
                    SearchResultItem(
                        id=consultation.id,
                        type="consultation",
                        title=f"Consultation · {consultation.status.value.replace('_', ' ').title()}",
                        subtitle=consultation.chief_complaint,
                        href=f"/consultations/{consultation.id}",
                    )
                )

            reports, _ = await report_repo.list_by_hospital(
                hospital_id,
                doctor_id=user_id if role == RoleName.doctor else None,
                patient_id=patient_id,
                page=1,
                page_size=2,
            )
            for report in reports:
                results.append(
                    SearchResultItem(
                        id=report.id,
                        type="report",
                        title="Consultation report",
                        subtitle=report.report_type.value.replace("_", " ").title(),
                        href=f"/reports/{report.id}",
                    )
                )

    if role == RoleName.hospital_admin:
        users, _ = await UserRepository(db).list_by_hospital(
            hospital_id, search=query, page=1, page_size=_MAX_PER_CATEGORY
        )
        for user in users:
            results.append(
                SearchResultItem(
                    id=user.id, type="user", title=user.full_name, subtitle=user.email, href="/settings"
                )
            )

    return SearchResultsOut(query=query, results=results)
