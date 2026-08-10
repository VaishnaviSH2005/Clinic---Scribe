"""Platform-level tables (PRD Ch15.4): hospitals, subscriptions, roles, departments."""

import uuid
from datetime import date

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, UUIDPKMixin
from app.models.enums import DepartmentStatus, HospitalStatus, RoleName, SubscriptionStatus


class Hospital(UUIDPKMixin, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "hospitals"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    address_line: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[HospitalStatus] = mapped_column(
        Enum(HospitalStatus, name="hospital_status"), nullable=False, default=HospitalStatus.active
    )
    working_hours: Mapped[dict | None] = mapped_column(JSONB)

    departments: Mapped[list["Department"]] = relationship(back_populates="hospital")


class Subscription(UUIDPKMixin, Base):
    """Derived per PRD Ch15.4.2 — supports Super Admin license/subscription management."""

    __tablename__ = "subscriptions"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    plan_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"), nullable=False, default=SubscriptionStatus.trial
    )
    starts_at: Mapped[date] = mapped_column(nullable=False)
    expires_at: Mapped[date] = mapped_column(nullable=False)


class Role(UUIDPKMixin, Base):
    """Seeded once via migration; fixed four roles for Version 1 (PRD Ch15.4.3)."""

    __tablename__ = "roles"

    name: Mapped[RoleName] = mapped_column(Enum(RoleName, name="role_name"), nullable=False, unique=True)


class Department(UUIDPKMixin, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "departments"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    head_of_department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[DepartmentStatus] = mapped_column(
        Enum(DepartmentStatus, name="department_status"), nullable=False, default=DepartmentStatus.active
    )

    hospital: Mapped["Hospital"] = relationship(back_populates="departments")
