"""Unit tests for Milestone 6 (Reports/Dashboard/Analytics/Settings/Search/
Notifications). No live Postgres in this environment (consistent with every
other test module here), so these cover what's genuinely testable in
isolation: PDF rendering, settings schema defaults, the search
minimum-query-length guard (returns before touching the database), and the
analytics date-bounds helper. DB-backed integration coverage (hospital
isolation, RBAC on live rows, report generation end-to-end) would require a
live database — see the final milestone report.
"""

from datetime import date

import pytest

from app.repositories.analytics_repository import _bounds
from app.schemas.settings_schema import ApplicationPreferences, NotificationPreferences
from app.services.search_service import global_search
from app.utils.report_pdf import render_report_pdf


def test_render_report_pdf_produces_valid_pdf_bytes() -> None:
    snapshot = {
        "hospital": {"name": "Test Hospital"},
        "patient": {"full_name": "Jane Doe", "uhid": "UH-001", "age": 34, "gender": "female"},
        "doctor": {"full_name": "Dr. Smith"},
        "consultation": {"started_at": "2026-01-01T10:00:00", "chief_complaint": "Headache"},
        "soap": {
            "subjective": "Patient reports headache.",
            "objective": "BP 120/80.",
            "assessment": "Tension headache.",
            "plan": "Rest and hydration.",
        },
        "summary": {
            "chief_complaint": "Headache",
            "history_of_present_illness": "3 days of headache.",
            "key_findings": "No red flags.",
            "assessment": "Likely tension headache.",
            "plan": "Follow up if persists.",
        },
        "recommendations": [
            {"type": "recommended_test", "content": "CBC", "confidence": "medium"},
        ],
        "doctor_remarks": "Advised rest.",
        "follow_up_date": "2026-01-10",
        "follow_up_notes": "Call if symptoms worsen.",
    }
    pdf_bytes = render_report_pdf(snapshot)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_render_report_pdf_handles_missing_sections() -> None:
    """AI content may be partially missing (Ch17.6 partial-failure
    isolation) — the PDF must still render, not crash, on empty snapshot
    sections."""
    pdf_bytes = render_report_pdf({})
    assert pdf_bytes.startswith(b"%PDF")


def test_notification_preferences_defaults_all_enabled() -> None:
    prefs = NotificationPreferences()
    assert prefs.ai_processing_complete is True
    assert prefs.report_generated is True
    assert prefs.consultation_pending is True


def test_application_preferences_defaults() -> None:
    prefs = ApplicationPreferences()
    assert prefs.default_dashboard_view == "summary"
    assert prefs.items_per_page == 20


def test_analytics_bounds_spans_full_days() -> None:
    start, end = _bounds(date(2026, 1, 1), date(2026, 1, 31))
    assert start.date() == date(2026, 1, 1)
    assert end.date() == date(2026, 1, 31)
    assert start.hour == 0
    assert end.hour == 23


@pytest.mark.parametrize("query", ["", "a", "  "])
async def test_global_search_short_query_returns_no_results_without_touching_db(query: str) -> None:
    """A query under 2 characters returns immediately, before any database
    access — verified by passing `db=None` and confirming no AttributeError."""
    from app.models.enums import RoleName

    result = await global_search(
        None,  # type: ignore[arg-type]
        hospital_id="11111111-1111-1111-1111-111111111111",  # type: ignore[arg-type]
        role=RoleName.doctor,
        user_id="22222222-2222-2222-2222-222222222222",  # type: ignore[arg-type]
        query=query,
    )
    assert result.results == []
