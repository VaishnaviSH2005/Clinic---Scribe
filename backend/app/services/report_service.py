"""Report generation and versioning (PRD Ch11/Ch15.8).

A report is created automatically once a consultation is approved
(`consultation_service.approve_consultation` calls `generate_report`) from
the approved SOAP note, clinical summary, and AI recommendations — the same
approved data already produced by the AI pipeline (Ch10), never a second
independent clinical-documentation system. Only approved consultations may
ever have a report generated for them (Ch11.10 — a report always represents
finalized clinical information).

Every PDF render is version-snapshotted (`ReportVersion.snapshot`) so a
later doctor-remarks/follow-up edit never rewrites history — it creates a
new version and a new PDF, leaving prior versions downloadable exactly as
they were generated.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.models.consultation import Consultation
from app.models.enums import ConsultationStatus, ReportType
from app.models.report import Report, ReportVersion
from app.repositories.ai_recommendation_repository import AiRecommendationRepository
from app.repositories.clinical_summary_repository import ClinicalSummaryRepository
from app.repositories.hospital_repository import HospitalRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.report_version_repository import ReportVersionRepository
from app.repositories.soap_note_repository import SoapNoteRepository
from app.repositories.user_repository import UserRepository
from app.schemas.report_schema import ReportUpdateRequest
from app.services.audit_service import record_audit_event
from app.services.notification_service import notify_user
from app.services.patient_service import patient_age
from app.utils.file_storage import save_bytes
from app.utils.report_pdf import render_report_pdf


class ReportNotFoundError(NotFoundError):
    error_code = "REPORT_NOT_FOUND"


class ReportGenerationError(AppError):
    status_code = 409
    error_code = "REPORT_GENERATION_FAILED"


async def _build_snapshot(db: AsyncSession, *, consultation: Consultation, report: Report) -> dict:
    patient = await PatientRepository(db).get_by_id(consultation.patient_id, hospital_id=consultation.hospital_id)
    doctor = await UserRepository(db).get_by_id(consultation.doctor_id, hospital_id=consultation.hospital_id)
    hospital = await HospitalRepository(db).get_by_id(consultation.hospital_id)
    soap = await SoapNoteRepository(db).get_by_consultation_id(consultation.id)
    summary = await ClinicalSummaryRepository(db).get_by_consultation_id(consultation.id)
    recommendations = await AiRecommendationRepository(db).list_by_consultation_id(consultation.id)

    return {
        "hospital": {"name": hospital.name if hospital else None},
        "patient": {
            "full_name": patient.full_name if patient else None,
            "uhid": patient.uhid if patient else None,
            "age": patient_age(patient) if patient else None,
            "gender": patient.gender.value if patient else None,
        },
        "doctor": {"full_name": doctor.full_name if doctor else None},
        "consultation": {
            "started_at": consultation.started_at.isoformat() if consultation.started_at else None,
            "chief_complaint": consultation.chief_complaint,
        },
        "soap": {
            "subjective": soap.subjective,
            "objective": soap.objective,
            "assessment": soap.assessment,
            "plan": soap.plan,
        }
        if soap
        else None,
        "summary": {
            "chief_complaint": summary.chief_complaint,
            "history_of_present_illness": summary.history_of_present_illness,
            "key_findings": summary.key_findings,
            "assessment": summary.assessment,
            "plan": summary.plan,
        }
        if summary
        else None,
        "recommendations": [
            {
                "type": row.type.value,
                "content": row.content,
                "explanation": row.explanation,
                "confidence": row.confidence.value if row.confidence else None,
            }
            for row in recommendations
        ],
        "doctor_remarks": report.doctor_remarks,
        "follow_up_date": report.follow_up_date.isoformat() if report.follow_up_date else None,
        "follow_up_notes": report.follow_up_notes,
    }


async def _write_version(
    db: AsyncSession, *, report: Report, consultation: Consultation, doctor_id: uuid.UUID
) -> ReportVersion:
    snapshot = await _build_snapshot(db, consultation=consultation, report=report)
    pdf_bytes = render_report_pdf(snapshot)
    now = datetime.now(timezone.utc)
    filename = f"{report.id}_v{report.current_version}.pdf"
    relative_url = save_bytes(pdf_bytes, subdir=f"reports/{report.id}", filename=filename)

    report.pdf_url = relative_url
    version = ReportVersion(
        report_id=report.id,
        version_number=report.current_version,
        snapshot=snapshot,
        pdf_url=relative_url,
        created_by=doctor_id,
        created_at=now,
    )
    await ReportVersionRepository(db).create(version)
    return version


async def generate_report(db: AsyncSession, *, consultation: Consultation, doctor_id: uuid.UUID) -> Report:
    """Called from `consultation_service.approve_consultation` right after
    a consultation is approved. Idempotent — re-approval can never happen
    (approval is a one-way transition), but a defensive check still guards
    against generating a duplicate report for the same consultation."""
    if consultation.status != ConsultationStatus.approved:
        raise ReportGenerationError("A report can only be generated for an approved consultation.")

    existing = await ReportRepository(db).get_by_consultation_id(consultation.id)
    if existing is not None:
        return existing

    report = Report(
        hospital_id=consultation.hospital_id,
        patient_id=consultation.patient_id,
        consultation_id=consultation.id,
        report_type=ReportType.consultation_report,
        current_version=1,
        is_locked=False,
        created_by=doctor_id,
        updated_by=doctor_id,
    )
    await ReportRepository(db).create(report)
    await _write_version(db, report=report, consultation=consultation, doctor_id=doctor_id)
    await ReportRepository(db).save(report)

    await record_audit_event(
        db,
        action="report_generated",
        user_id=doctor_id,
        hospital_id=consultation.hospital_id,
        entity_type="report",
        entity_id=report.id,
        metadata={"consultation_id": str(consultation.id)},
    )
    await notify_user(
        db,
        user_id=doctor_id,
        notification_type="report_generated",
        title="Report ready",
        message="The consultation report has been generated and is ready to view.",
        reference_id=report.id,
    )
    return report


async def get_report(db: AsyncSession, *, report_id: uuid.UUID, hospital_id: uuid.UUID) -> Report:
    report = await ReportRepository(db).get_by_id(report_id, hospital_id=hospital_id)
    if report is None:
        raise ReportNotFoundError("The requested report could not be located.")
    return report


async def list_reports(
    db: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    doctor_id: uuid.UUID | None,
    patient_id: uuid.UUID | None,
    page: int,
    page_size: int,
) -> tuple[list[Report], int]:
    return await ReportRepository(db).list_by_hospital(
        hospital_id, doctor_id=doctor_id, patient_id=patient_id, page=page, page_size=page_size
    )


async def list_versions(db: AsyncSession, *, report: Report) -> list[ReportVersion]:
    return await ReportVersionRepository(db).list_by_report_id(report.id)


async def get_version(db: AsyncSession, *, report: Report, version_number: int) -> ReportVersion:
    version = await ReportVersionRepository(db).get_by_report_and_version(report.id, version_number)
    if version is None:
        raise ReportNotFoundError("The requested report version could not be located.")
    return version


async def update_report(
    db: AsyncSession,
    *,
    report_id: uuid.UUID,
    hospital_id: uuid.UUID,
    doctor_id: uuid.UUID,
    data: ReportUpdateRequest,
) -> Report:
    """Doctor remarks / follow-up are the only editable fields after
    generation (the clinical content itself is frozen at approval time,
    Ch11.10) — each edit produces a new version and a re-rendered PDF."""
    from app.repositories.consultation_repository import ConsultationRepository

    report = await get_report(db, report_id=report_id, hospital_id=hospital_id)
    if report.created_by != doctor_id:
        raise ForbiddenError("You do not have permission to edit this report.", error_code="FORBIDDEN")

    consultation = await ConsultationRepository(db).get_by_id(report.consultation_id, hospital_id=hospital_id)
    if consultation is None:
        raise NotFoundError("The report's consultation could not be located.", error_code="CONSULTATION_NOT_FOUND")

    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(report, field, value)
    report.current_version += 1
    report.updated_by = doctor_id
    await _write_version(db, report=report, consultation=consultation, doctor_id=doctor_id)
    await ReportRepository(db).save(report)

    await record_audit_event(
        db,
        action="report_updated",
        user_id=doctor_id,
        hospital_id=hospital_id,
        entity_type="report",
        entity_id=report.id,
        metadata={"new_version": report.current_version, "changes": list(changes)},
    )
    return report
