"""Report API (PRD Ch16.11). Reports are read/download/versions plus a
narrow doctor-remarks/follow-up edit — generation itself is a side effect
of consultation approval (`consultation_service.approve_consultation`),
never a directly-callable creation endpoint, so a report can never exist
for anything but an approved consultation.

Reports carry clinical content, so receptionists never get a route here
(Ch6 RBAC — front-desk role, not clinical). A doctor may only access
reports for consultations they themselves approved; Hospital Admin may
access every report within their hospital.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import RoleName
from app.models.report import Report
from app.schemas.report_schema import ReportOut, ReportUpdateRequest, ReportVersionOut
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


def _ensure_can_view(report: Report, current: CurrentUser) -> None:
    if current.role == RoleName.doctor and report.created_by != current.user.id:
        raise ForbiddenError("You do not have permission to access this report.", error_code="FORBIDDEN")


@router.get("")
async def list_reports(
    patient_id: uuid.UUID | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor, RoleName.hospital_admin)),
) -> ApiListResponse[ReportOut]:
    doctor_id = current.user.id if current.role == RoleName.doctor else None
    reports, total = await report_service.list_reports(
        db,
        hospital_id=current.hospital_id,
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
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor, RoleName.hospital_admin)),
) -> ApiResponse[ReportOut]:
    report = await report_service.get_report(db, report_id=report_id, hospital_id=current.hospital_id)
    _ensure_can_view(report, current)
    return ApiResponse(data=ReportOut.model_validate(report))


@router.patch("/{report_id}")
async def update_report(
    report_id: uuid.UUID,
    body: ReportUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor)),
) -> ApiResponse[ReportOut]:
    report = await report_service.update_report(
        db, report_id=report_id, hospital_id=current.hospital_id, doctor_id=current.user.id, data=body
    )
    await db.commit()
    return ApiResponse(data=ReportOut.model_validate(report), message="Report updated.")


@router.get("/{report_id}/versions")
async def list_versions(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor, RoleName.hospital_admin)),
) -> ApiResponse[list[ReportVersionOut]]:
    report = await report_service.get_report(db, report_id=report_id, hospital_id=current.hospital_id)
    _ensure_can_view(report, current)
    versions = await report_service.list_versions(db, report=report)
    return ApiResponse(data=[ReportVersionOut.model_validate(v) for v in versions])


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor, RoleName.hospital_admin)),
) -> FileResponse:
    """Authenticated download, not an unauthenticated static mount (same
    posture as patient document downloads) — avoids leaking clinical PDFs."""
    report = await report_service.get_report(db, report_id=report_id, hospital_id=current.hospital_id)
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
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.doctor, RoleName.hospital_admin)),
) -> FileResponse:
    report = await report_service.get_report(db, report_id=report_id, hospital_id=current.hospital_id)
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
