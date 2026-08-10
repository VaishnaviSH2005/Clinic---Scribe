"""Authentication business logic (PRD Ch7, Ch16.3, Ch18).

The backend is the single source of truth for authentication (Ch7.1) — this
module owns credential verification, session lifecycle, and token issuance.
Nothing here is trusted or duplicated on the frontend.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import (
    create_access_token,
    encode_refresh_cookie_value,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.enums import HospitalStatus, UserStatus
from app.models.hospital import Hospital
from app.models.user import PasswordResetToken, User
from app.models.user import Session as SessionModel
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services import email_service
from app.services.audit_service import record_audit_event


class InvalidCredentialsError(AppError):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"


class AccountInactiveError(AppError):
    status_code = 403
    error_code = "ACCOUNT_INACTIVE"


class HospitalInactiveError(AppError):
    status_code = 403
    error_code = "HOSPITAL_INACTIVE"


class SessionExpiredError(AppError):
    status_code = 401
    error_code = "SESSION_EXPIRED"


class ResetTokenExpiredError(AppError):
    status_code = 410
    error_code = "RESET_TOKEN_EXPIRED"


class IncorrectPasswordError(AppError):
    status_code = 401
    error_code = "INCORRECT_PASSWORD"


class AuthResult:
    def __init__(self, user: User, role_name: str, access_token: str, refresh_token: str):
        self.user = user
        self.role_name = role_name
        self.access_token = access_token
        self.refresh_token = refresh_token


async def _verify_account_active(db: AsyncSession, user: User) -> None:
    if user.status != UserStatus.active:
        raise AccountInactiveError("Your account is currently inactive.")
    if user.hospital_id is not None:
        hospital = await db.get(Hospital, user.hospital_id)
        if hospital is None or hospital.status != HospitalStatus.active:
            raise HospitalInactiveError("Your hospital account is currently inactive.")


async def _issue_session(
    db: AsyncSession, user: User, *, ip_address: str | None, device_info: str | None
) -> tuple[str, str]:
    """Creates a session row and returns (access_token, refresh_token)."""
    refresh_token = generate_secure_token()
    now = datetime.now(timezone.utc)
    session = SessionModel(
        user_id=user.id,
        session_token_hash=hash_token(refresh_token),
        hospital_id=user.hospital_id,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        created_at=now,
        last_activity_at=now,
        device_info=device_info,
        ip_address=ip_address,
    )
    await SessionRepository(db).create(session)

    role = await UserRepository(db).get_role(user.role_id)
    access_token = create_access_token(
        str(user.id),
        str(session.id),
        extra_claims={"role": role.name.value if role else None, "hospital_id": str(user.hospital_id or "")},
    )
    return access_token, encode_refresh_cookie_value(str(session.id), refresh_token)


async def login(
    db: AsyncSession, *, email: str, password: str, ip_address: str | None, device_info: str | None
) -> AuthResult:
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        await record_audit_event(
            db, action="login_failed", user_id=user.id if user else None, hospital_id=None, ip_address=ip_address
        )
        raise InvalidCredentialsError("Incorrect email or password.")

    await _verify_account_active(db, user)

    access_token, refresh_token = await _issue_session(db, user, ip_address=ip_address, device_info=device_info)
    role = await user_repo.get_role(user.role_id)

    await record_audit_event(
        db, action="login_success", user_id=user.id, hospital_id=user.hospital_id, ip_address=ip_address
    )
    return AuthResult(user, role.name.value if role else "", access_token, refresh_token)


async def logout(db: AsyncSession, *, session_id: uuid.UUID, user_id: uuid.UUID | None) -> None:
    await SessionRepository(db).delete(session_id)
    await record_audit_event(
        db, action="logout", user_id=user_id, hospital_id=None, entity_type="session", entity_id=session_id
    )


async def refresh_session_by_id(
    db: AsyncSession, *, session_id: uuid.UUID, refresh_token: str, ip_address: str | None
) -> tuple[str, str, User]:
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    if session is None:
        raise SessionExpiredError("Your session has expired. Please log in again.")
    if hash_token(refresh_token) != session.session_token_hash:
        raise SessionExpiredError("Your session has expired. Please log in again.")
    now = datetime.now(timezone.utc)
    if session.expires_at <= now:
        await session_repo.delete(session.id)
        raise SessionExpiredError("Your session has expired. Please log in again.")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(session.user_id)
    if user is None:
        raise SessionExpiredError("Your session has expired. Please log in again.")
    await _verify_account_active(db, user)

    # Rotate: new refresh token, extend session, update activity/IP.
    new_refresh_token = generate_secure_token()
    session.session_token_hash = hash_token(new_refresh_token)
    session.expires_at = now + timedelta(days=settings.refresh_token_expire_days)
    session.last_activity_at = now
    if ip_address:
        session.ip_address = ip_address
    await session_repo.save(session)

    role = await user_repo.get_role(user.role_id)
    new_access_token = create_access_token(
        str(user.id),
        str(session.id),
        extra_claims={"role": role.name.value if role else None, "hospital_id": str(user.hospital_id or "")},
    )

    await record_audit_event(db, action="token_refresh", user_id=user.id, hospital_id=user.hospital_id)
    return new_access_token, encode_refresh_cookie_value(str(session.id), new_refresh_token), user


async def request_password_reset(db: AsyncSession, *, email: str) -> None:
    user = await UserRepository(db).get_by_email(email)
    # Always behave identically regardless of account existence (Ch7.10 —
    # prevent account enumeration).
    if user is None:
        return

    raw_token = generate_secure_token()
    now = datetime.now(timezone.utc)
    token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=now + timedelta(minutes=settings.reset_token_expire_minutes),
        created_at=now,
    )
    await PasswordResetTokenRepository(db).create(token)
    email_service.send_password_reset_email(user.email, raw_token)
    await record_audit_event(db, action="password_reset_requested", user_id=user.id, hospital_id=user.hospital_id)


async def reset_password(db: AsyncSession, *, token: str, new_password: str) -> None:
    token_repo = PasswordResetTokenRepository(db)
    record = await token_repo.get_valid_by_hash(hash_token(token))
    if record is None:
        raise ResetTokenExpiredError("This password reset link has expired.")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(record.user_id)
    if user is None:
        raise ResetTokenExpiredError("This password reset link has expired.")

    user.password_hash = hash_password(new_password)
    await user_repo.save(user)
    await token_repo.mark_used(record)

    session_repo = SessionRepository(db)
    await session_repo.delete_all_for_user(user.id)

    await record_audit_event(db, action="password_reset_completed", user_id=user.id, hospital_id=user.hospital_id)


async def change_password(
    db: AsyncSession, *, user: User, current_password: str, new_password: str, current_session_id: uuid.UUID
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise IncorrectPasswordError("Current password is incorrect.")

    user.password_hash = hash_password(new_password)
    await UserRepository(db).save(user)

    # Revoke every other session; keep the one making this request active (Ch7.16).
    await SessionRepository(db).delete_all_for_user(user.id, except_session_id=current_session_id)

    await record_audit_event(db, action="password_changed", user_id=user.id, hospital_id=user.hospital_id)


async def list_sessions(db: AsyncSession, *, user_id: uuid.UUID, current_session_id: uuid.UUID) -> list[dict]:
    sessions = await SessionRepository(db).list_by_user(user_id)
    return [
        {
            "id": s.id,
            "device_info": s.device_info,
            "ip_address": s.ip_address,
            "created_at": s.created_at,
            "last_activity_at": s.last_activity_at,
            "expires_at": s.expires_at,
            "is_current": s.id == current_session_id,
        }
        for s in sessions
    ]


async def revoke_session(db: AsyncSession, *, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    if session is None or session.user_id != user_id:
        return
    await session_repo.delete(session_id)
    await record_audit_event(
        db,
        action="session_revoked",
        user_id=user_id,
        hospital_id=None,
        entity_type="session",
        entity_id=session_id,
    )
