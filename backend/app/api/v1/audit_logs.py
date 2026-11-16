"""Audit Log API. Read-only; entries are only ever written internally via
`audit_service.record_audit_event`.

- Super Admin (PRD Ch6.3 "View Audit Logs"): the platform-wide trail.
- Hospital Admin (PRD Ch13.8): their own hospital's login/logout/report-approval/
  user-creation/user-deactivation events only.
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
    current: CurrentUser = Depends(require_roles(RoleName.super_admin, RoleName.hospital_admin)),
) -> ApiListResponse[AuditLogOut]:
    logs, total = await audit_service.list_audit_logs(
        db,
        page=pagination.page,
        page_size=pagination.pageSize,
        hospital_id=current.hospital if current.role == RoleName.hospital_admin else None,
    )
    users, hospitals = await audit_service.resolve_display_names(db, logs)
    items: list[AuditLogOut] = []
    for log in logs:
        item = AuditLogOut.model_validate(log)
        if log.user_id in users:
            item.user_name, item.user_email = users[log.user_id]
        if log.hospital_id in hospitals:
            item.hospital_name = hospitals[log.hospital_id]
        items.append(item)
    return ApiListResponse(
        data=items,
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )
