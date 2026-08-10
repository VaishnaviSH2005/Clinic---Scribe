"""License / Subscription API (PRD Ch1.8/Ch6.10/Ch15.4.2 — Super Admin
"Manage Licenses"). Super Admin only.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.common import PaginationParams, pagination_params
from app.models.enums import RoleName
from app.schemas.response import ApiListResponse, ApiResponse, Pagination
from app.schemas.subscription_schema import SubscriptionCreate, SubscriptionOut, SubscriptionUpdate
from app.services import subscription_service

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def _to_out(subscription) -> SubscriptionOut:
    return SubscriptionOut.model_validate(subscription)


@router.post("")
async def create_subscription(
    body: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.super_admin)),
) -> ApiResponse[SubscriptionOut]:
    subscription = await subscription_service.create_subscription(db, data=body, actor_id=current.user.id)
    await db.commit()
    return ApiResponse(data=_to_out(subscription), message="License created successfully.")


@router.get("")
async def list_subscriptions(
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    _current: CurrentUser = Depends(require_roles(RoleName.super_admin)),
) -> ApiListResponse[SubscriptionOut]:
    subscriptions, total = await subscription_service.list_subscriptions(
        db, page=pagination.page, page_size=pagination.pageSize
    )
    return ApiListResponse(
        data=[_to_out(s) for s in subscriptions],
        pagination=Pagination(page=pagination.page, pageSize=pagination.pageSize, total=total),
    )


@router.patch("/{subscription_id}")
async def update_subscription(
    subscription_id: uuid.UUID,
    body: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_roles(RoleName.super_admin)),
) -> ApiResponse[SubscriptionOut]:
    subscription = await subscription_service.update_subscription(
        db, subscription_id=subscription_id, data=body, actor_id=current.user.id
    )
    await db.commit()
    return ApiResponse(data=_to_out(subscription), message="License updated successfully.")
