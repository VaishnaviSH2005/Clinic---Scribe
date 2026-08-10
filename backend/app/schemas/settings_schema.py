"""User settings schemas (PRD Ch15.9.3). Two fixed keys — notification
preferences (which real notification triggers the user wants surfaced) and
application preferences (display defaults) — no other settings keys are
invented beyond what the PRD's Settings module defines.
"""

from pydantic import BaseModel


class NotificationPreferences(BaseModel):
    ai_processing_complete: bool = True
    report_generated: bool = True
    consultation_pending: bool = True


class ApplicationPreferences(BaseModel):
    default_dashboard_view: str = "summary"
    items_per_page: int = 20


class UserSettingsOut(BaseModel):
    notification_preferences: NotificationPreferences
    application_preferences: ApplicationPreferences
