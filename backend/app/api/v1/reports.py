"""Report API (PRD Ch16.11). Reports are read/download/versions plus a
narrow doctor-remarks/follow-up edit — generation itself is a side effect
of consultation approval (`consultation_service.approve_consultation`),
never a directly-callable creation endpoint, so a report can never exist
for anything but an approved consultation.

Access follows the PRD Ch6.15 matrix: Doctor, Hospital Admin and Super Admin
have access, Receptionist is "View Only" (all read endpoints below; only a
Doctor can edit — Ch6.3: receptionists cannot edit consultation reports).
A doctor may only access reports for consultations they themselves approved;
Hospital Admin and Receptionist see every report within their own hospital;
Super Admin has no hospital of their own, so they must name one
(`?hospital_id=`) and only ever read that hospital's reports.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.dependencies.auth import CurrentUser, require_roles, resolve_hospital_scope
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import RoleName
from app.models.report import Report
from app.schemas.report_schema import ReportOut, ReportUpdateRequest, ReportVersionOut
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.services import audit_service, report_service

router = APIRouter(prefix="/reports", tags=["reports"])

# Everyone the PRD matrix allows to *view* reports. Editing stays Doctor-only.
READ_ROLES = (RoleName.doctor, RoleName.hospital_admin, RoleName.receptionist, RoleName.super_admin)


async def _audit_platform_view(
    db: AsyncSession, current: CurrentUser, hospital_id: uuid.UUID, report_id: uuid.UUID | None = None
) -> None:
    """Platform-staff reads of a hospital's reports are always traceable."""
    if current.role != RoleName.super_admin:
        return
    await audit_service.record_audit_event(
        db,
        action="platform_admin_report_view" if report_id else "platform_admin_report_list_view",
        user_id=current.user.id,
        hospital_id=hospital_id,
        entity_type="report" if report_id else "hospital",
        entity_id=report_id or hospital_id,
    )
    await db.commit()


def _ensure_can_view(report: Report, current: CurrentUser) -> None:
    if current.role == RoleName.doctor and report.created_by != current.user.id:
        raise ForbiddenError("You do not have permission to access this report.", error_code="FORBIDDEN")


@router.get("")
async def list_reports(
    patient_id: uuid.UUID | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> ApiListResponse[ReportOut]:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    await _audit_platform_view(db, current, scope_id)
    doctor_id = current.user.id if current.role == RoleName.doctor else None
    reports, total = await report_service.list_reports(
        db,
        hospital_id=scope_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        page=pagination.page,
        page_size=pagination.pageSize,
    )
    return ApiListResponse(
        data=[ReportOut.model_validate(r) for r in reports],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )


@router.get("/{report_id}")
async def get_report(
    report_id: uuid.UUID,
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> ApiResponse[ReportOut]:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    report = await report_service.get_report(db, report_id=report_id, hospital_id=scope_id)
    _ensure_can_view(report, current)
    await _audit_platform_view(db, current, scope_id, report.id)
    return ApiResponse(data=ReportOut.model_validate(report))


@router.patch("/{report_id}")
async def update_report(
    report_id: uuid.UUID,
    body: ReportUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ReportOut]:
    report = await report_service.update_report(
        db, report_id=report_id, hospital_id=current.hospital, doctor_id=current.user.id, data=body
    )
    await db.commit()
    return ApiResponse(data=ReportOut.model_validate(report), message="Report updated.")


@router.get("/{report_id}/versions")
async def list_versions(
    report_id: uuid.UUID,
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> ApiResponse[list[ReportVersionOut]]:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    report = await report_service.get_report(db, report_id=report_id, hospital_id=scope_id)
    _ensure_can_view(report, current)
    versions = await report_service.list_versions(db, report=report)
    return ApiResponse(data=[ReportVersionOut.model_validate(v) for v in versions])


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> FileResponse:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    """Authenticated download, not an unauthenticated static mount (same
    posture as patient document downloads) — avoids leaking clinical PDFs."""
    report = await report_service.get_report(db, report_id=report_id, hospital_id=scope_id)
    _ensure_can_view(report, current)
    if not report.pdf_url:
        raise NotFoundError("This report has no generated PDF yet.", error_code="REPORT_PDF_NOT_FOUND")

    file_path = Path(report.pdf_url.lstrip("/")).resolve()
    if not file_path.is_file():
        raise NotFoundError("The report file could not be located.", error_code="REPORT_PDF_NOT_FOUND")

    return FileResponse(file_path, media_type="application/pdf", filename=f"consultation-report-{report.id}.pdf")


@router.get("/{report_id}/versions/{version_number}/download")
async def download_report_version(
    report_id: uuid.UUID,
    version_number: int,
    hospital_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> FileResponse:
    scope_id = await resolve_hospital_scope(db, current, hospital_id)
    report = await report_service.get_report(db, report_id=report_id, hospital_id=scope_id)
    _ensure_can_view(report, current)
    version = await report_service.get_version(db, report=report, version_number=version_number)
    if not version.pdf_url:
        raise NotFoundError("This report version has no generated PDF.", error_code="REPORT_PDF_NOT_FOUND")

    file_path = Path(version.pdf_url.lstrip("/")).resolve()
    if not file_path.is_file():
        raise NotFoundError("The report file could not be located.", error_code="REPORT_PDF_NOT_FOUND")

    return FileResponse(
        file_path, media_type="application/pdf", filename=f"consultation-report-{report.id}-v{version_number}.pdf"
    )
