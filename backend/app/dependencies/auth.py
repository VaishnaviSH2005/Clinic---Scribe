"""Authentication + RBAC dependencies (PRD Ch7.12, Ch18 — authorization is
enforced exclusively by the backend; the frontend never determines permissions).
"""

import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppError, ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import decode_token
from app.models.enums import HospitalStatus, RoleName, UserStatus
from app.models.hospital import Hospital
from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository


class SessionInvalidError(UnauthorizedError):
    error_code = "SESSION_EXPIRED"


class AccountInactiveError(ForbiddenError):
    error_code = "ACCOUNT_INACTIVE"


class HospitalInactiveError(ForbiddenError):
    error_code = "HOSPITAL_INACTIVE"


@dataclass
class CurrentUser:
    user: User
    role: RoleName
    session_id: uuid.UUID
    hospital_id: uuid.UUID | None

    @property
    def hospital(self) -> uuid.UUID:
        """The user's own hospital. Every role except Super Admin belongs to one;
        endpoints that exclude Super Admin use this so the type is non-optional
        (and a hospital-less account is refused instead of reaching a query)."""
        if self.hospital_id is None:
            raise ForbiddenError("This action requires an assigned hospital.", error_code="FORBIDDEN")
        return self.hospital_id


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> CurrentUser:
    return await authenticate_access_token(db, request.cookies.get(settings.access_token_cookie_name))


async def authenticate_access_token(db: AsyncSession, token: str | None) -> CurrentUser:
    """Full session validation for an access token (PRD Ch7.8 "Session Validation"):
    token -> active session -> active user -> active hospital -> role. Shared by the
    HTTP dependency and the live-transcript WebSocket so both enforce identical rules."""
    if not token:
        raise SessionInvalidError("Your session has expired. Please log in again.")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise SessionInvalidError("Your session has expired. Please log in again.")

    session_id_raw = payload.get("sid")
    user_id_raw = payload.get("sub")
    if not session_id_raw or not user_id_raw:
        raise SessionInvalidError("Your session has expired. Please log in again.")

    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(uuid.UUID(session_id_raw))
    if session is None or session.expires_at <= datetime.now(timezone.utc):
        raise SessionInvalidError("Your session has expired. Please log in again.")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(uuid.UUID(user_id_raw))
    if user is None:
        raise SessionInvalidError("Your session has expired. Please log in again.")
    if user.status != UserStatus.active:
        raise AccountInactiveError("Your account is currently inactive.")

    if user.hospital_id is not None:
        hospital = await db.get(Hospital, user.hospital_id)
        if hospital is None or hospital.status != HospitalStatus.active:
            raise HospitalInactiveError("Your hospital account is currently inactive.")

    role = await user_repo.get_role(user.role_id)
    if role is None:
        raise SessionInvalidError("Your session has expired. Please log in again.")

    await session_repo.touch(session)

    return CurrentUser(user=user, role=role.name, session_id=session.id, hospital_id=user.hospital_id)


def require_roles(*roles: RoleName) -> Callable[[CurrentUser], Coroutine[Any, Any, CurrentUser]]:
    """Role Guard (PRD Ch7.15/Ch19). Usage: `Depends(require_roles(RoleName.hospital_admin))`."""

    async def _check(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current.role not in roles:
            raise ForbiddenError("You do not have permission to access this resource.", error_code="FORBIDDEN")
        return current

    return _check


def require_hospital_scope() -> Callable[[CurrentUser], Coroutine[Any, Any, uuid.UUID]]:
    """Resolves the acting hospital_id for hospital-scoped endpoints
    (departments/doctors/receptionists/users). Super Admin has no hospital
    of their own, so hospital-scoped write endpoints are Hospital Admin only
    by role guard; this dependency exists for the (Hospital Admin, Doctor,
    Receptionist) read paths that operate on "my hospital"."""

    async def _resolve(current: CurrentUser = Depends(get_current_user)) -> uuid.UUID:
        if current.hospital_id is None:
            raise ForbiddenError("This action requires an assigned hospital.", error_code="FORBIDDEN")
        return current.hospital_id

    return _resolve


class HospitalScopeRequiredError(AppError):
    status_code = 422
    error_code = "HOSPITAL_SCOPE_REQUIRED"


async def resolve_hospital_scope(
    db: AsyncSession, current: CurrentUser, requested_hospital_id: uuid.UUID | None
) -> uuid.UUID:
    """Hospital whose data a hospital-scoped READ should touch.

    - Hospital staff are always pinned to their own hospital; any
      `requested_hospital_id` they send is ignored (no cross-tenant reads).
    - Super Admin has no hospital of their own, so they must name exactly
      one (PRD Ch1.x hospital-level isolation): platform-wide patient
      listings are never returned.
    """
    if current.role != RoleName.super_admin:
        if current.hospital_id is None:
            raise ForbiddenError("This action requires an assigned hospital.", error_code="FORBIDDEN")
        return current.hospital_id
    if requested_hospital_id is None:
        raise HospitalScopeRequiredError("Select a hospital to view its patients.")
    if await db.get(Hospital, requested_hospital_id) is None:
        raise NotFoundError("The requested hospital could not be located.", error_code="HOSPITAL_NOT_FOUND")
    return requested_hospital_id
