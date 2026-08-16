"""Seed a demo hospital plus one development account per remaining role
(hospital_admin, doctor, receptionist) so the full login flow is testable
for every role, not just super_admin (see 0004_seed_super_admin). The
password below is the same fixed development credential documented in
backend/.env.example / README — never used as a production default.

Revision ID: 0005_seed_demo_users
Revises: 0004_seed_super_admin
Create Date: 2026-08-14T00:00:00+00:00
"""

from alembic import op

revision = "0005_seed_demo_users"
down_revision = "0004_seed_super_admin"
branch_labels = None
depends_on = None

# argon2id hash of the fixed dev password "ChangeMe123!" (see README).
DEV_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$FkN6Ets33XyqacbKJvm97g$7naaOy825VOjJ9CsNhO5FBxrtOrQabmK5ByTpSifjn4"
)

DEMO_HOSPITAL_REG_NUMBER = "DEMO-0001"

DEMO_USERS = [
    ("hospital_admin", "hospital.admin@cliniscribe.ai", "Hospital Admin", "+10000000001"),
    ("doctor", "doctor@cliniscribe.ai", "Demo Doctor", "+10000000002"),
    ("receptionist", "receptionist@cliniscribe.ai", "Demo Receptionist", "+10000000003"),
]


def upgrade() -> None:
    op.execute(
        f"""
        INSERT INTO hospitals (id, name, registration_number, email, phone, status, created_at, updated_at)
        SELECT gen_random_uuid(), 'Demo Hospital', '{DEMO_HOSPITAL_REG_NUMBER}',
               'contact@demo-hospital.cliniscribe.ai', '+10000000000', 'active', now(), now()
        WHERE NOT EXISTS (
            SELECT 1 FROM hospitals WHERE registration_number = '{DEMO_HOSPITAL_REG_NUMBER}'
        );
        """
    )

    for role_name, email, full_name, phone in DEMO_USERS:
        op.execute(
            f"""
            INSERT INTO users (id, hospital_id, role_id, department_id, full_name, email, phone,
                                password_hash, status, created_at, updated_at)
            SELECT gen_random_uuid(), h.id, r.id, NULL, '{full_name}', '{email}',
                   '{phone}', '{DEV_PASSWORD_HASH}', 'active', now(), now()
            FROM roles r, hospitals h
            WHERE r.name = '{role_name}' AND h.registration_number = '{DEMO_HOSPITAL_REG_NUMBER}'
            ON CONFLICT (email) DO NOTHING;
            """
        )


def downgrade() -> None:
    for _role_name, email, _full_name, _phone in DEMO_USERS:
        op.execute(f"DELETE FROM users WHERE email = '{email}';")
    op.execute(f"DELETE FROM hospitals WHERE registration_number = '{DEMO_HOSPITAL_REG_NUMBER}';")
