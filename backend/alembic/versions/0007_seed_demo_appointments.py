"""Seed demo appointments linking the demo patients to department-assigned
doctors, so the consultation flow (which requires a doctor with a
department and a checked-in appointment) is testable end to end.

Revision ID: 0007_seed_demo_appointments
Revises: 0006_seed_demo_clinical_data
Create Date: 2026-08-15T00:00:00+00:00
"""

from alembic import op

from app.core.config import settings

revision = "0007_seed_demo_appointments"
down_revision = "0006_seed_demo_clinical_data"
branch_labels = None
depends_on = None

DEMO_HOSPITAL_REG_NUMBER = "DEMO-0001"

# (doctor_email, patient_uhid, status, hours_offset_from_now)
APPOINTMENTS = [
    ("doctor.cardio@cliniscribe.ai", "DEMO-PT-0001", "checked_in", -1),
    ("doctor.cardio@cliniscribe.ai", "DEMO-PT-0002", "upcoming", 2),
    ("doctor.ortho@cliniscribe.ai", "DEMO-PT-0003", "upcoming", 4),
]


def upgrade() -> None:
    if not settings.is_development:
        return  # dev/demo seed data is only created in development environments
    for doctor_email, uhid, status, hours_offset in APPOINTMENTS:
        checked_in_at_expr = "now()" if status == "checked_in" else "NULL"
        op.execute(
            f"""
            INSERT INTO appointments (id, hospital_id, patient_id, doctor_id, department_id,
                                       scheduled_at, status, checked_in_at, created_at, updated_at)
            SELECT gen_random_uuid(), h.id, p.id, u.id, u.department_id,
                   now() + interval '{hours_offset} hours', '{status}', {checked_in_at_expr}, now(), now()
            FROM hospitals h, patients p, users u
            WHERE h.registration_number = '{DEMO_HOSPITAL_REG_NUMBER}'
              AND p.uhid = '{uhid}' AND p.hospital_id = h.id
              AND u.email = '{doctor_email}' AND u.hospital_id = h.id
              AND u.department_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM appointments a
                  WHERE a.patient_id = p.id AND a.doctor_id = u.id AND a.status = '{status}'
              );
            """
        )


def downgrade() -> None:
    op.execute(
        f"""
        DELETE FROM appointments
        WHERE hospital_id = (SELECT id FROM hospitals WHERE registration_number = '{DEMO_HOSPITAL_REG_NUMBER}');
        """
    )
