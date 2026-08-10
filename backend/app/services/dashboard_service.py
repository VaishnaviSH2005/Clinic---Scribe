"""Role-aware Dashboard (PRD Ch5.16). Every card and list is computed from
real application data via `DashboardRepository` — never hardcoded or
fabricated. Composition differs by role; each branch only queries what that
role is entitled to see (super_admin never sees a single hospital's
clinical detail, doctor never sees platform-wide figures).
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RoleName
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.dashboard_schema import AppointmentSummaryOut, ConsultationSummaryOut, DashboardCard, DashboardOut


async def _appointment_summaries(db: AsyncSession, appointments) -> list[AppointmentSummaryOut]:
    patient_repo = PatientRepository(db)
    summaries = []
    for appt in appointments:
        patient = await patient_repo.get_by_id(appt.patient_id, hospital_id=appt.hospital_id, include_deleted=True)
        summaries.append(
            AppointmentSummaryOut(
                id=appt.id,
                patient_name=patient.full_name if patient else "Unknown patient",
                scheduled_at=appt.scheduled_at,
                status=appt.status,
            )
        )
    return summaries


async def _consultation_summaries(db: AsyncSession, consultations) -> list[ConsultationSummaryOut]:
    patient_repo = PatientRepository(db)
    summaries = []
    for c in consultations:
        patient = await patient_repo.get_by_id(c.patient_id, hospital_id=c.hospital_id, include_deleted=True)
        summaries.append(
            ConsultationSummaryOut(
                id=c.id,
                patient_name=patient.full_name if patient else "Unknown patient",
                status=c.status,
                created_at=c.created_at,
            )
        )
    return summaries


async def get_dashboard(
    db: AsyncSession, *, role: RoleName, hospital_id: uuid.UUID | None, user_id: uuid.UUID
) -> DashboardOut:
    repo = DashboardRepository(db)

    if role == RoleName.super_admin:
        hospitals = await repo.platform_hospital_counts()
        users = await repo.platform_user_count()
        license_counts = await SubscriptionRepository(db).counts_by_status()
        active_licenses = license_counts.get("active", 0) + license_counts.get("trial", 0)
        # Platform Health (PRD Ch6.10) as the share of onboarded hospitals
        # that are actually active — a real, computed figure rather than a
        # fabricated uptime/SLA number nothing in the schema tracks yet.
        # "Revenue" (also listed in Ch6.10) is intentionally omitted: the
        # `subscriptions` table (Ch15.4.2, itself a "derived" addition) has
        # no price/amount field, so there is no real figure to compute
        # without inventing pricing data that exists nowhere in the schema.
        platform_health = round((hospitals["active"] / hospitals["total"]) * 100) if hospitals["total"] else 100
        return DashboardOut(
            role=role.value,
            cards=[
                DashboardCard(key="hospitals_total", label="Hospitals", value=hospitals["total"]),
                DashboardCard(key="hospitals_active", label="Active hospitals", value=hospitals["active"]),
                DashboardCard(
                    key="hospitals_suspended", label="Suspended hospitals", value=hospitals["suspended"]
                ),
                DashboardCard(key="platform_users", label="Platform users", value=users),
                DashboardCard(key="licenses_active", label="Active licenses", value=active_licenses),
                DashboardCard(key="platform_health", label="Platform health", value=platform_health),
            ],
        )

    if hospital_id is None:
        return DashboardOut(role=role.value, cards=[])

    if role == RoleName.hospital_admin:
        patients = await repo.hospital_patient_count(hospital_id)
        appointments_today = await repo.hospital_appointments_today(hospital_id)
        active_consultations = await repo.hospital_active_consultations(hospital_id)
        pending_reviews = await repo.hospital_pending_reviews(hospital_id)
        staff = await repo.hospital_staff_count(hospital_id)
        recent = await repo.recent_consultations(hospital_id=hospital_id, doctor_id=None, limit=5)
        return DashboardOut(
            role=role.value,
            cards=[
                DashboardCard(key="patients", label="Total patients", value=patients),
                DashboardCard(key="appointments_today", label="Appointments today", value=appointments_today),
                DashboardCard(
                    key="active_consultations", label="Active consultations", value=active_consultations
                ),
                DashboardCard(key="pending_reviews", label="Pending doctor review", value=pending_reviews),
                DashboardCard(key="staff", label="Staff members", value=staff),
            ],
            recent_consultations=await _consultation_summaries(db, recent),
        )

    if role == RoleName.doctor:
        appointments_today = await repo.doctor_appointments_today(user_id)
        pending = await repo.doctor_pending_consultations(user_id)
        drafts = await repo.doctor_drafts(user_id)
        reports_this_month = await repo.doctor_reports_this_month(user_id)
        recent = await repo.recent_consultations(hospital_id=hospital_id, doctor_id=user_id, limit=5)
        return DashboardOut(
            role=role.value,
            cards=[
                DashboardCard(key="appointments_today", label="Appointments today", value=len(appointments_today)),
                DashboardCard(key="pending_review", label="Pending your review", value=pending),
                DashboardCard(key="drafts", label="Saved drafts", value=drafts),
                DashboardCard(key="reports_this_month", label="Reports this month", value=reports_this_month),
            ],
            appointments_today=await _appointment_summaries(db, appointments_today),
            recent_consultations=await _consultation_summaries(db, recent),
        )

    # receptionist
    checkins_today = await repo.receptionist_checkins_today(hospital_id)
    upcoming_today = await repo.receptionist_upcoming_today(hospital_id)
    return DashboardOut(
        role=role.value,
        cards=[
            DashboardCard(key="appointments_today", label="Appointments today", value=len(upcoming_today)),
            DashboardCard(key="checked_in_today", label="Checked in today", value=checkins_today),
        ],
        appointments_today=await _appointment_summaries(db, upcoming_today),
    )
