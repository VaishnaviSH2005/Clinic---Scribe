"""Extend `sessions` with device_info, ip_address, last_activity_at.

The Ch15.4.5 physical schema only specified session_token_hash/hospital_id/
expires_at/created_at, but Ch7.13 and Ch18 ("Session Data") both document
Device Information, IP Address, and Last Activity Timestamp as required
session attributes. This migration reconciles the schema with that spec.

Revision ID: 0003_extend_sessions
Revises: 0002_seed_roles
Create Date: 2026-08-08T00:00:00+00:00
"""

from alembic import op

revision = "0003_extend_sessions"
down_revision = "0002_seed_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE sessions ADD COLUMN device_info VARCHAR(255);")
    op.execute("ALTER TABLE sessions ADD COLUMN ip_address VARCHAR(45);")
    op.execute("ALTER TABLE sessions ADD COLUMN last_activity_at TIMESTAMPTZ;")
    op.execute("UPDATE sessions SET last_activity_at = created_at WHERE last_activity_at IS NULL;")
    op.execute("ALTER TABLE sessions ALTER COLUMN last_activity_at SET NOT NULL;")


def downgrade() -> None:
    op.execute("ALTER TABLE sessions DROP COLUMN last_activity_at;")
    op.execute("ALTER TABLE sessions DROP COLUMN ip_address;")
    op.execute("ALTER TABLE sessions DROP COLUMN device_info;")
