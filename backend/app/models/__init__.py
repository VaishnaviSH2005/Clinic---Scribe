"""Import every model module so Base.metadata is fully populated for Alembic autogenerate."""

from app.models.appointment import Appointment
from app.models.consultation import (
    AiEntity,
    AiRecommendation,
    ClinicalSummary,
    Consultation,
    ConsultationTranscript,
    SoapNote,
)
from app.models.hospital import Department, Hospital, Role, Subscription
from app.models.patient import Document, MedicalProfile, Patient, PatientAiSummary, TimelineEvent
from app.models.platform import AuditLog, Notification, Setting
from app.models.report import Report, ReportVersion
from app.models.user import PasswordResetToken, Session, User

__all__ = [
    "Appointment",
    "AiEntity",
    "AiRecommendation",
    "ClinicalSummary",
    "Consultation",
    "ConsultationTranscript",
    "SoapNote",
    "Department",
    "Hospital",
    "Role",
    "Subscription",
    "Document",
    "MedicalProfile",
    "Patient",
    "PatientAiSummary",
    "TimelineEvent",
    "AuditLog",
    "Notification",
    "Setting",
    "Report",
    "ReportVersion",
    "PasswordResetToken",
    "Session",
    "User",
]
