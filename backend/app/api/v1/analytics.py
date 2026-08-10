"""Analytics API. Super Admin has no single-hospital analytics view in this
module (platform-wide figures belong to Ch5.16's Super Admin dashboard,
already covered by `/dashboard`) — Analytics here is Hospital
Admin/Doctor only, both hospital-isolated via `current.hospital_id`.
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
    current: CurrentUser = Depends(require_roles(RoleName.hospital_admin, RoleName.doctor)),
) -> ApiResponse[AnalyticsOut]:
    if current.hospital_id is None:
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
