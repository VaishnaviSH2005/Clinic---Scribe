"""Seed demo departments, doctors, and patients under the Demo Hospital
(created in 0005_seed_demo_users) so hospital-scoped flows (department
listing, doctor rosters, patient records) are testable end to end.

Revision ID: 0006_seed_demo_clinical_data
Revises: 0005_seed_demo_users
Create Date: 2026-08-14T00:10:00+00:00
"""

from alembic import op

from app.core.config import settings

revision = "0006_seed_demo_clinical_data"
down_revision = "0005_seed_demo_users"
branch_labels = None
depends_on = None

DEMO_HOSPITAL_REG_NUMBER = "DEMO-0001"

# argon2id hash of the fixed dev password "ChangeMe123!" (see README).
DEV_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$FkN6Ets33XyqacbKJvm97g$7naaOy825VOjJ9CsNhO5FBxrtOrQabmK5ByTpSifjn4"
)

DEPARTMENTS = ["Cardiology", "Orthopedics", "Pediatrics"]

DOCTORS = [
    (
        "doctor.cardio@cliniscribe.ai",
        "Dr. Asha Rao",
        "+10000000010",
        "Cardiology",
        "MBBS, MD (Cardiology)",
        "Cardiologist",
        "MED-CARD-001",
        12,
    ),
    (
        "doctor.ortho@cliniscribe.ai",
        "Dr. Vikram Shah",
        "+10000000011",
        "Orthopedics",
        "MBBS, MS (Ortho)",
        "Orthopedic Surgeon",
        "MED-ORTH-002",
        9,
    ),
    (
        "doctor.pedia@cliniscribe.ai",
        "Dr. Meera Nair",
        "+10000000012",
        "Pediatrics",
        "MBBS, MD (Pediatrics)",
        "Pediatrician",
        "MED-PEDI-003",
        7,
    ),
]

PATIENTS = [
    ("DEMO-PT-0001", "Rahul Verma", "1990-05-14", "male", "9800000001"),
    ("DEMO-PT-0002", "Priya Singh", "1985-11-02", "female", "9800000002"),
    ("DEMO-PT-0003", "Aditya Kumar", "2001-02-20", "male", "9800000003"),
]


def upgrade() -> None:
    if not settings.is_development:
        return  # dev/demo seed data is only created in development environments
    for name in DEPARTMENTS:
        op.execute(
            f"""
            INSERT INTO departments (id, hospital_id, name, status, created_at, updated_at)
            SELECT gen_random_uuid(), h.id, '{name}', 'active', now(), now()
            FROM hospitals h
            WHERE h.registration_number = '{DEMO_HOSPITAL_REG_NUMBER}'
              AND NOT EXISTS (
                  SELECT 1 FROM departments d
                  WHERE d.hospital_id = h.id AND d.name = '{name}'
              );
            """
        )

    for email, full_name, phone, dept_name, qualification, specialization, med_reg_no, exp_years in DOCTORS:
        op.execute(
            f"""
            INSERT INTO users (id, hospital_id, role_id, department_id, full_name, email, phone,
                                password_hash, qualification, specialization,
                                medical_registration_number, experience_years, status,
                                created_at, updated_at)
            SELECT gen_random_uuid(), h.id, r.id, d.id, '{full_name}', '{email}', '{phone}',
                   '{DEV_PASSWORD_HASH}', '{qualification}', '{specialization}',
                   '{med_reg_no}', {exp_years}, 'active', now(), now()
            FROM roles r, hospitals h, departments d
            WHERE r.name = 'doctor'
              AND h.registration_number = '{DEMO_HOSPITAL_REG_NUMBER}'
              AND d.hospital_id = h.id AND d.name = '{dept_name}'
            ON CONFLICT (email) DO NOTHING;
            """
        )

    for uhid, full_name, dob, gender, mobile in PATIENTS:
        op.execute(
            f"""
            INSERT INTO patients (id, hospital_id, uhid, full_name, date_of_birth, gender,
                                   mobile_number, created_at, updated_at)
            SELECT gen_random_uuid(), h.id, '{uhid}', '{full_name}', '{dob}', '{gender}',
                   '{mobile}', now(), now()
            FROM hospitals h
            WHERE h.registration_number = '{DEMO_HOSPITAL_REG_NUMBER}'
            ON CONFLICT (uhid) DO NOTHING;
            """
        )


def downgrade() -> None:
    for uhid, _full_name, _dob, _gender, _mobile in PATIENTS:
        op.execute(f"DELETE FROM patients WHERE uhid = '{uhid}';")
    for email, *_rest in DOCTORS:
        op.execute(f"DELETE FROM users WHERE email = '{email}';")
    op.execute(
        f"""
        DELETE FROM departments
        WHERE hospital_id = (SELECT id FROM hospitals WHERE registration_number = '{DEMO_HOSPITAL_REG_NUMBER}')
          AND name IN ({", ".join(f"'{d}'" for d in DEPARTMENTS)});
        """
    )
