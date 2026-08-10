"""Notification API (PRD Ch16.12). Every route is scoped to the
authenticated user — a user only ever sees/marks their own notifications,
no cross-user or cross-hospital access is possible since the repository
filters on `user_id` directly from the session, never a client-supplied id.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.dependencies.common import PaginationParams, pagination_params
from app.schemas.notification_schema import NotificationOut, UnreadCountOut
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    unread_only: bool = Query(default=False),
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiListResponse[NotificationOut]:
    notifications, total = await notification_service.list_notifications(
        db,
        user_id=current.user.id,
        unread_only=unread_only,
        page=pagination.page,
        page_size=pagination.pageSize,
    )
    return ApiListResponse(
        data=[NotificationOut.model_validate(n) for n in notifications],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[UnreadCountOut]:
    count = await notification_service.count_unread(db, user_id=current.user.id)
    return ApiResponse(data=UnreadCountOut(count=count))


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[NotificationOut]:
    notification = await notification_service.mark_read(
        db, notification_id=notification_id, user_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=NotificationOut.model_validate(notification))


@router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[None]:
    await notification_service.mark_all_read(db, user_id=current.user.id)
    await db.commit()
    return ApiResponse(data=None, message="All notifications marked as read.")
