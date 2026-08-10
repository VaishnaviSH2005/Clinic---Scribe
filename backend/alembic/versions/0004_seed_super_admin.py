"""Seed a development Super Admin account so the authentication flow is
immediately testable after a fresh migration (PRD Ch7 — "authentication
flow must be fully testable"). The password below is a fixed development
credential documented in backend/.env.example / README — never used as a
production default (production deployments must change it immediately).

Revision ID: 0004_seed_super_admin
Revises: 0003_extend_sessions
Create Date: 2026-08-08T00:10:00+00:00
"""

from alembic import op

revision = "0004_seed_super_admin"
down_revision = "0003_extend_sessions"
branch_labels = None
depends_on = None

# argon2id hash of the fixed dev password "ChangeMe123!" (see README).
SUPER_ADMIN_EMAIL = "superadmin@cliniscribe.ai"
SUPER_ADMIN_PASSWORD_HASH = "$argon2id$v=19$m=65536,t=3,p=4$FkN6Ets33XyqacbKJvm97g$7naaOy825VOjJ9CsNhO5FBxrtOrQabmK5ByTpSifjn4"


def upgrade() -> None:
    op.execute(
        f"""
        INSERT INTO users (id, hospital_id, role_id, department_id, full_name, email, phone,
                            password_hash, status, created_at, updated_at)
        SELECT gen_random_uuid(), NULL, r.id, NULL, 'Super Admin', '{SUPER_ADMIN_EMAIL}',
               '+10000000000', '{SUPER_ADMIN_PASSWORD_HASH}', 'active', now(), now()
        FROM roles r
        WHERE r.name = 'super_admin'
        ON CONFLICT (email) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM users WHERE email = '{SUPER_ADMIN_EMAIL}';")
