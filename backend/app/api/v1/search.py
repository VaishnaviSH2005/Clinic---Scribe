"""Global search API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.dependencies.auth import CurrentUser, get_current_user
from app.models.enums import RoleName
from app.schemas.response import ApiResponse
from app.schemas.search_schema import SearchResultsOut
from app.services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str = Query(default="", min_length=0, max_length=200),
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[SearchResultsOut]:
    if current.hospital_id is None:
        if current.role == RoleName.super_admin:
            # No hospital of their own and platform staff browse patients/reports one
            # chosen hospital at a time on those pages — nothing to search globally.
            return ApiResponse(data=SearchResultsOut(query=q, results=[]))
        raise ForbiddenError("This account has no assigned hospital.", error_code="FORBIDDEN")

    data = await search_service.global_search(
        db, hospital_id=current.hospital_id, role=current.role, user_id=current.user.id, query=q
    )
    return ApiResponse(data=data)
