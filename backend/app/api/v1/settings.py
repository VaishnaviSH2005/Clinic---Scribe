"""User settings API (PRD Ch15.9.3) — notification and application
preferences only; hospital/department/user management already lives in
`hospitals.py`/`departments.py`/`users.py` from Milestone 2, not duplicated
here.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.response import ApiResponse
from app.schemas.settings_schema import ApplicationPreferences, NotificationPreferences, UserSettingsOut
from app.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/me")
async def get_my_settings(
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[UserSettingsOut]:
    data = await settings_service.get_user_settings(db, user_id=current.user.id)
    return ApiResponse(data=data)


@router.patch("/me/notification-preferences")
async def update_notification_preferences(
    body: NotificationPreferences,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[NotificationPreferences]:
    data = await settings_service.update_notification_preferences(db, user_id=current.user.id, data=body)
    await db.commit()
    return ApiResponse(data=data, message="Notification preferences updated.")


@router.patch("/me/application-preferences")
async def update_application_preferences(
    body: ApplicationPreferences,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ApplicationPreferences]:
    data = await settings_service.update_application_preferences(db, user_id=current.user.id, data=body)
    await db.commit()
    return ApiResponse(data=data, message="Application preferences updated.")
