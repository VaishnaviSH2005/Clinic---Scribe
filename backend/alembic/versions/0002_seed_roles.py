"""Seed the four fixed Version 1 roles (PRD Ch15.4.3 — "not user-editable").

Revision ID: 0002_seed_roles
Revises: 0001_initial_schema
Create Date: 2026-08-07T18:10:00+00:00
"""

from alembic import op

revision = "0002_seed_roles"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

ROLES = ["super_admin", "hospital_admin", "doctor", "receptionist"]


def upgrade() -> None:
    for role in ROLES:
        op.execute(
            f"INSERT INTO roles (id, name) VALUES (gen_random_uuid(), '{role}') "
            "ON CONFLICT (name) DO NOTHING;"
        )


def downgrade() -> None:
    names = ", ".join(f"'{role}'" for role in ROLES)
    op.execute(f"DELETE FROM roles WHERE name IN ({names});")
