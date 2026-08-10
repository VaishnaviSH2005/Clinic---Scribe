"""PostgreSQL ENUM types (PRD Ch15.2 — enums, not free text, so invalid
states are impossible at the DB layer). One Python Enum per DB enum type.
"""

import enum


class HospitalStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class SubscriptionStatus(str, enum.Enum):
    trial = "trial"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class RoleName(str, enum.Enum):
    super_admin = "super_admin"
    hospital_admin = "hospital_admin"
    doctor = "doctor"
    receptionist = "receptionist"


class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class DepartmentStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class DocumentFileType(str, enum.Enum):
    pdf = "pdf"
    jpg = "jpg"
    png = "png"


class TimelineEventType(str, enum.Enum):
    registration = "registration"
    appointment = "appointment"
    consultation = "consultation"
    diagnosis = "diagnosis"
    uploaded_report = "uploaded_report"
    follow_up = "follow_up"
    surgery = "surgery"


class AppointmentStatus(str, enum.Enum):
    upcoming = "upcoming"
    checked_in = "checked_in"
    completed = "completed"
    cancelled = "cancelled"
    missed = "missed"


class ConsultationStatus(str, enum.Enum):
    draft = "draft"
    in_progress = "in_progress"
    ai_processing = "ai_processing"
    pending_review = "pending_review"
    approved = "approved"


class ConfidenceLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class RecommendationType(str, enum.Enum):
    possible_diagnosis = "possible_diagnosis"
    recommended_test = "recommended_test"
    follow_up = "follow_up"
    red_flag = "red_flag"


class ReportType(str, enum.Enum):
    consultation_report = "consultation_report"
    soap_report = "soap_report"
    clinical_summary = "clinical_summary"
    patient_history_report = "patient_history_report"


class NotificationType(str, enum.Enum):
    appointment_reminder = "appointment_reminder"
    consultation_pending = "consultation_pending"
    ai_processing_complete = "ai_processing_complete"
    report_generated = "report_generated"
    system = "system"


class SettingsScope(str, enum.Enum):
    hospital = "hospital"
    user = "user"
