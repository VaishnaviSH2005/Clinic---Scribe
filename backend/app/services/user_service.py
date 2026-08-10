"""User / Doctor / Receptionist management (PRD Ch7.12/7.13, Ch13.3, Ch16.6/16.13).

New staff accounts are created active with an unusable random password and
immediately sent an invitation email (reusing the password-reset token
mechanism) so they set their own password before first login — this is the
"User Invitation Flow" referenced in Ch3.14/Ch13.3.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.core.security import hash_password, hash_token
from app.models.enums import RoleName, UserStatus
from app.models.user import PasswordResetToken, User
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import ProfileUpdateRequest
from app.schemas.user_schema import DoctorCreate, ReceptionistCreate, UserUpdate
from app.services import email_service
from app.services.audit_service import record_audit_event


class ForbiddenTargetRoleError(AppError):
    status_code = 403
    error_code = "FORBIDDEN_TARGET_ROLE"


async def _create_staff_user(
    db: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    role_name: RoleName,
    full_name: str,
    email: str,
    phone: str,
    department_id: uuid.UUID | None,
    employee_id: str | None,
    extra_fields: dict,
    actor_id: uuid.UUID | None,
) -> User:
    user_repo = UserRepository(db)
    if await user_repo.get_by_email(email) is not None:
        raise ConflictError("A user with this email already exists.", error_code="DUPLICATE_USER")

    role = await RoleRepository(db).get_by_name(role_name)
    if role is None:
        raise NotFoundError("Role is not configured.", error_code="ROLE_NOT_FOUND")

    now = datetime.now(timezone.utc)
    temp_password = secrets.token_urlsafe(24)  # unusable until reset via invitation link
    user = User(
        hospital_id=hospital_id,
        role_id=role.id,
        department_id=department_id,
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=hash_password(temp_password),
        employee_id=employee_id,
        status=UserStatus.active,
        created_at=now,
        updated_at=now,
        **extra_fields,
    )
    await user_repo.create(user)

    raw_token = secrets.token_urlsafe(48)
    await PasswordResetTokenRepository(db).create(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=now + timedelta(minutes=settings.reset_token_expire_minutes),
            created_at=now,
        )
    )
    email_service.send_invitation_email(user.email, user.full_name, raw_token)

    await record_audit_event(
        db,
        action="user_created",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="user",
        entity_id=user.id,
        metadata={"role": role_name.value},
    )
    return user


async def create_hospital_admin(
    db: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    full_name: str,
    email: str,
    phone: str,
    actor_id: uuid.UUID | None,
) -> User:
    """Provisions the Hospital Admin account for a newly onboarded hospital
    (PRD Ch6.3/Ch16.4), reusing the same invitation-email flow as
    doctors/receptionists rather than inventing a separate path."""
    return await _create_staff_user(
        db,
        hospital_id=hospital_id,
        role_name=RoleName.hospital_admin,
        full_name=full_name,
        email=email,
        phone=phone,
        department_id=None,
        employee_id=None,
        extra_fields={},
        actor_id=actor_id,
    )


async def create_doctor(
    db: AsyncSession, *, hospital_id: uuid.UUID, data: DoctorCreate, actor_id: uuid.UUID
) -> User:
    return await _create_staff_user(
        db,
        hospital_id=hospital_id,
        role_name=RoleName.doctor,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        department_id=data.department_id,
        employee_id=data.employee_id,
        extra_fields={
            "qualification": data.qualification,
            "specialization": data.specialization,
            "medical_registration_number": data.medical_registration_number,
            "experience_years": data.experience_years,
        },
        actor_id=actor_id,
    )


async def create_receptionist(
    db: AsyncSession, *, hospital_id: uuid.UUID, data: ReceptionistCreate, actor_id: uuid.UUID
) -> User:
    return await _create_staff_user(
        db,
        hospital_id=hospital_id,
        role_name=RoleName.receptionist,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        department_id=data.department_id,
        employee_id=data.employee_id,
        extra_fields={},
        actor_id=actor_id,
    )


async def get_user(db: AsyncSession, *, user_id: uuid.UUID, hospital_id: uuid.UUID) -> User:
    user = await UserRepository(db).get_by_id(user_id, hospital_id=hospital_id)
    if user is None:
        raise NotFoundError("The requested user could not be located.", error_code="USER_NOT_FOUND")
    return user


async def list_users(
    db: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    role_name: RoleName | None = None,
    department_id: uuid.UUID | None = None,
    status: UserStatus | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[User], int]:
    return await UserRepository(db).list_by_hospital(
        hospital_id,
        role_name=role_name,
        department_id=department_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )


async def update_user(
    db: AsyncSession, *, user_id: uuid.UUID, hospital_id: uuid.UUID, data: UserUpdate, actor_id: uuid.UUID
) -> User:
    user = await get_user(db, user_id=user_id, hospital_id=hospital_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await UserRepository(db).save(user)
    await record_audit_event(
        db, action="user_updated", user_id=actor_id, hospital_id=hospital_id, entity_type="user", entity_id=user.id
    )
    return user


async def update_own_profile(db: AsyncSession, *, user: User, data: ProfileUpdateRequest) -> User:
    """Self-service profile edit (PRD Ch7.14). Role, organization, and
    employee_id are not present on ProfileUpdateRequest, so they can never
    be changed through this path."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await UserRepository(db).save(user)
    await record_audit_event(db, action="profile_updated", user_id=user.id, hospital_id=user.hospital_id)
    return user


async def set_user_status(
    db: AsyncSession, *, user_id: uuid.UUID, hospital_id: uuid.UUID, status: UserStatus, actor_id: uuid.UUID
) -> User:
    user = await get_user(db, user_id=user_id, hospital_id=hospital_id)
    role = await UserRepository(db).get_role(user.role_id)
    if role and role.name == RoleName.super_admin:
        raise ForbiddenTargetRoleError("Cannot modify a Super Admin account.")

    user.status = status
    await UserRepository(db).save(user)
    await record_audit_event(
        db,
        action="user_status_changed",
        user_id=actor_id,
        hospital_id=hospital_id,
        entity_type="user",
        entity_id=user.id,
        metadata={"status": status.value},
    )
    return user
