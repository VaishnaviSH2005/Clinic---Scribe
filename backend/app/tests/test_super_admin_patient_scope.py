"""Super Admin patient access: read-only, one hospital at a time (PRD Ch6.15
access matrix lists Patients for Super Admin; Ch6.3 says Super Admin cannot
modify patient records). Unit tests for the scope resolver and the role sets
guarding patient endpoints — no database required.
"""

import uuid
from types import SimpleNamespace

import pytest

from app.api.v1 import patients as patients_api
from app.core.exceptions import ForbiddenError, NotFoundError
from app.dependencies.auth import (
    CurrentUser,
    HospitalScopeRequiredError,
    resolve_hospital_scope,
)
from app.models.enums import RoleName


class _FakeDb:
    """Stands in for AsyncSession: `get` returns the hospital if it 'exists'."""

    def __init__(self, existing: set[uuid.UUID]):
        self.existing = existing

    async def get(self, _model, ident):
        return SimpleNamespace(id=ident) if ident in self.existing else None


def _current(role: RoleName, hospital_id: uuid.UUID | None) -> CurrentUser:
    return CurrentUser(
        user=SimpleNamespace(id=uuid.uuid4()),  # type: ignore[arg-type]
        role=role,
        session_id=uuid.uuid4(),
        hospital_id=hospital_id,
    )


MINE, OTHER = uuid.uuid4(), uuid.uuid4()


async def test_super_admin_must_choose_a_hospital() -> None:
    with pytest.raises(HospitalScopeRequiredError):
        await resolve_hospital_scope(_FakeDb({OTHER}), _current(RoleName.super_admin, None), None)  # type: ignore[arg-type]


async def test_super_admin_gets_the_hospital_they_asked_for() -> None:
    scope = await resolve_hospital_scope(_FakeDb({OTHER}), _current(RoleName.super_admin, None), OTHER)  # type: ignore[arg-type]
    assert scope == OTHER


async def test_super_admin_unknown_hospital_is_not_found() -> None:
    with pytest.raises(NotFoundError):
        await resolve_hospital_scope(_FakeDb(set()), _current(RoleName.super_admin, None), OTHER)  # type: ignore[arg-type]


@pytest.mark.parametrize("role", [RoleName.hospital_admin, RoleName.doctor, RoleName.receptionist])
async def test_hospital_staff_cannot_override_their_hospital(role: RoleName) -> None:
    # Even if they pass another hospital's id (and it exists), they stay in their own.
    scope = await resolve_hospital_scope(_FakeDb({MINE, OTHER}), _current(role, MINE), OTHER)  # type: ignore[arg-type]
    assert scope == MINE


async def test_staff_without_a_hospital_is_forbidden() -> None:
    with pytest.raises(ForbiddenError):
        await resolve_hospital_scope(_FakeDb({OTHER}), _current(RoleName.doctor, None), OTHER)  # type: ignore[arg-type]


def test_super_admin_may_read_but_never_write_patients() -> None:
    assert RoleName.super_admin in patients_api.READ_ROLES
    for writers in (patients_api.REGISTER_ROLES, patients_api.EDIT_ROLES, patients_api.DOCUMENT_ROLES):
        assert RoleName.super_admin not in writers
