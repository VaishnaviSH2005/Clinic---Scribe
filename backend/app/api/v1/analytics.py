"""Analytics API (PRD Ch6.15: Super Admin, Hospital Admin, Doctor "personal";
Receptionist none). Super Admin gets platform-wide aggregate counts; Hospital
Admin and Doctor are hospital-isolated via `current.hospital_id`.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.dependencies.auth import CurrentUser, require_roles
from app.models.enums import RoleName
from app.schemas.analytics_schema import AnalyticsOut
from app.schemas.response import ApiResponse
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
async def get_analytics(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.super_admin, RoleName.hospital_admin, RoleName.doctor)),
) -> ApiResponse[AnalyticsOut]:
    if current.hospital_id is None and current.role != RoleName.super_admin:
        raise ForbiddenError("This account has no assigned hospital.", error_code="FORBIDDEN")

    data = await analytics_service.get_analytics(
        db,
        role=current.role,
        hospital_id=current.hospital_id,
        user_id=current.user.id,
        date_from=date_from,
        date_to=date_to,
    )
    return ApiResponse(data=data)
