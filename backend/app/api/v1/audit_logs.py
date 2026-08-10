"""Audit Log API (PRD Ch6.3 — Super Admin "View Audit Logs"). Read-only;
entries are only ever written internally via `audit_service.record_audit_event`.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import RoleName
from app.schemas.audit_log_schema import AuditLogOut
from app.schemas.response import ApiListResponse, Pagination
from app.services import audit_service

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("")
async def list_audit_logs(
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    _current: CurrentUser = Depends(require_roles(RoleName.super_admin)),
) -> ApiListResponse[AuditLogOut]:
    logs, total = await audit_service.list_audit_logs(db, page=pagination.page, page_size=pagination.pageSize)
    return ApiListResponse(
        data=[AuditLogOut.model_validate(log) for log in logs],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )
