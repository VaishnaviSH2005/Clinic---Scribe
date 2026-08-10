"""Dashboard API (PRD Ch5.16). A single role-aware endpoint — the backend
decides what data a role is entitled to see; the frontend never assembles
or filters dashboard data itself.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.dashboard_schema import DashboardOut
from app.schemas.response import ApiResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[DashboardOut]:
    data = await dashboard_service.get_dashboard(
        db, role=current.role, hospital_id=current.hospital_id, user_id=current.user.id
    )
    return ApiResponse(data=data)
