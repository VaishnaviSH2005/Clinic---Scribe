"""Authentication API (PRD Ch16.3)."""

import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.rate_limit import enforce_rate_limit, reset_rate_limit
from app.core.security import decode_refresh_cookie_value
from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.auth_schema import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MeOut,
    ProfileOut,
    ProfileUpdateRequest,
    ResetPasswordRequest,
    SessionOut,
)
from app.schemas.response import ApiResponse
from app.services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["authentication"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _device_info(request: Request) -> str | None:
    return request.headers.get("user-agent")


@router.post("/login")
async def login(
    body: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> ApiResponse[MeOut]:
    rate_limit_key = f"rl:login:{body.email.lower()}"
    await enforce_rate_limit(
        rate_limit_key, settings.login_rate_limit_attempts, settings.login_rate_limit_window_minutes * 60
    )

    result = await auth_service.login(
        db,
        email=body.email,
        password=body.password,
        ip_address=_client_ip(request),
        device_info=_device_info(request),
    )
    await db.commit()
    await reset_rate_limit(rate_limit_key)

    set_auth_cookies(response, result.access_token, result.refresh_token)
    return ApiResponse(
        data=MeOut(
            id=result.user.id,
            name=result.user.full_name,
            email=result.user.email,
            role=result.role_name,
            hospitalId=result.user.hospital_id,
        ),
        message="Login successful.",
    )


@router.post("/logout")
async def logout(
    response: Response, db: AsyncSession = Depends(get_db), current: CurrentUser = Depends(get_current_user)
) -> ApiResponse[None]:
    await auth_service.logout(db, session_id=current.session_id, user_id=current.user.id)
    await db.commit()
    clear_auth_cookies(response)
    return ApiResponse(data=None, message="Logged out successfully.")


@router.post("/refresh")
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)) -> ApiResponse[None]:
    raw_cookie = request.cookies.get(settings.refresh_token_cookie_name)
    if not raw_cookie:
        raise UnauthorizedError("Your session has expired. Please log in again.", error_code="SESSION_EXPIRED")

    decoded = decode_refresh_cookie_value(raw_cookie)
    if decoded is None:
        raise UnauthorizedError("Your session has expired. Please log in again.", error_code="SESSION_EXPIRED")
    session_id_raw, raw_token = decoded

    await enforce_rate_limit(f"rl:refresh:{session_id_raw}", 30, 60)

    new_access_token, new_refresh_cookie, _user = await auth_service.refresh_session_by_id(
        db, session_id=uuid.UUID(session_id_raw), refresh_token=raw_token, ip_address=_client_ip(request)
    )
    await db.commit()

    set_auth_cookies(response, new_access_token, new_refresh_cookie)
    return ApiResponse(data=None, message="Session refreshed successfully.")


@router.get("/me")
async def me(current: CurrentUser = Depends(get_current_user)) -> ApiResponse[MeOut]:
    return ApiResponse(
        data=MeOut(
            id=current.user.id,
            name=current.user.full_name,
            email=current.user.email,
            role=current.role,
            hospitalId=current.hospital_id,
        )
    )


@router.get("/profile")
async def get_profile(current: CurrentUser = Depends(get_current_user)) -> ApiResponse[ProfileOut]:
    return ApiResponse(
        data=ProfileOut(
            id=current.user.id,
            hospital_id=current.user.hospital_id,
            department_id=current.user.department_id,
            role=current.role,
            full_name=current.user.full_name,
            email=current.user.email,
            phone=current.user.phone,
            profile_photo_url=current.user.profile_photo_url,
            employee_id=current.user.employee_id,
            qualification=current.user.qualification,
            specialization=current.user.specialization,
            medical_registration_number=current.user.medical_registration_number,
            experience_years=current.user.experience_years,
            status=current.user.status,
        )
    )


@router.patch("/profile")
async def update_profile(
    body: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ProfileOut]:
    user = await user_service.update_own_profile(db, user=current.user, data=body)
    await db.commit()
    return ApiResponse(
        data=ProfileOut(
            id=user.id,
            hospital_id=user.hospital_id,
            department_id=user.department_id,
            role=current.role,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            profile_photo_url=user.profile_photo_url,
            employee_id=user.employee_id,
            qualification=user.qualification,
            specialization=user.specialization,
            medical_registration_number=user.medical_registration_number,
            experience_years=user.experience_years,
            status=user.status,
        ),
        message="Profile updated successfully.",
    )


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)) -> ApiResponse[None]:
    await enforce_rate_limit(
        f"rl:forgot-password:{body.email.lower()}",
        settings.password_reset_rate_limit_attempts,
        settings.password_reset_rate_limit_window_minutes * 60,
    )
    await auth_service.request_password_reset(db, email=body.email)
    await db.commit()
    return ApiResponse(data=None, message="If an account exists, password reset instructions have been sent.")


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)) -> ApiResponse[None]:
    await auth_service.reset_password(db, token=body.token, new_password=body.password)
    await db.commit()
    return ApiResponse(data=None, message="Password updated successfully.")


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[None]:
    await auth_service.change_password(
        db,
        user=current.user,
        current_password=body.current_password,
        new_password=body.new_password,
        current_session_id=current.session_id,
    )
    await db.commit()
    return ApiResponse(data=None, message="Password changed successfully.")


@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db), current: CurrentUser = Depends(get_current_user)
) -> ApiResponse[list[SessionOut]]:
    sessions = await auth_service.list_sessions(db, user_id=current.user.id, current_session_id=current.session_id)
    return ApiResponse(data=[SessionOut(**s) for s in sessions])


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[None]:
    if session_id == current.session_id:
        raise UnauthorizedError(
            "The current session cannot be revoked through this endpoint. Use logout instead.",
            error_code="CANNOT_REVOKE_CURRENT_SESSION",
        )
    await auth_service.revoke_session(db, user_id=current.user.id, session_id=session_id)
    await db.commit()
    return ApiResponse(data=None, message="Session revoked successfully.")
