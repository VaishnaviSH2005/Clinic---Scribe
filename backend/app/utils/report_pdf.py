"""Print-ready consultation report PDF rendering (PRD Ch11.6/Ch11.13).

Pure-Python via reportlab (no system libraries required, unlike
WeasyPrint/wkhtmltopdf), so it installs cleanly in any environment. Renders
directly from a report snapshot dict — never from live AI/consultation
state — so a regenerated PDF always matches the `ReportVersion.snapshot`
it was built from (PRD Ch11.10 permanence).
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_STYLES = getSampleStyleSheet()
_TITLE = ParagraphStyle("ReportTitle", parent=_STYLES["Title"], fontSize=16, spaceAfter=4)
_SECTION = ParagraphStyle("Section", parent=_STYLES["Heading2"], fontSize=12, spaceBefore=12, spaceAfter=4)
_BODY = ParagraphStyle("Body", parent=_STYLES["BodyText"], fontSize=10, leading=14)
_META = ParagraphStyle("Meta", parent=_STYLES["BodyText"], fontSize=9, textColor=colors.grey)


def _p(text: str | None, style: ParagraphStyle = _BODY) -> Paragraph:
    return Paragraph((text or "Not documented.").replace("\n", "<br/>"), style)


def render_report_pdf(snapshot: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=18 * mm, rightMargin=18 * mm
    )
    story: list = []

    hospital = snapshot.get("hospital", {})
    patient = snapshot.get("patient", {})
    doctor = snapshot.get("doctor", {})
    consultation = snapshot.get("consultation", {})
    soap = snapshot.get("soap") or {}
    summary = snapshot.get("summary") or {}
    recommendations = snapshot.get("recommendations") or []

    story.append(_p(hospital.get("name", "CliniScribe AI"), _TITLE))
    story.append(_p("Consultation Report", _SECTION))
    story.append(
        _p(
            f"Patient: {patient.get('full_name', '-')} ({patient.get('uhid', '-')}) &nbsp;|&nbsp; "
            f"Age/Gender: {patient.get('age', '-')}/{patient.get('gender', '-')}",
            _META,
        )
    )
    story.append(
        _p(
            f"Doctor: {doctor.get('full_name', '-')} &nbsp;|&nbsp; "
            f"Consultation date: {consultation.get('started_at', '-')}",
            _META,
        )
    )
    story.append(Spacer(1, 6))

    story.append(_p("Chief Complaint", _SECTION))
    story.append(_p(summary.get("chief_complaint") or consultation.get("chief_complaint")))

    story.append(_p("Clinical Summary", _SECTION))
    for label, key in (
        ("History of Present Illness", "history_of_present_illness"),
        ("Key Findings", "key_findings"),
        ("Assessment", "assessment"),
        ("Plan", "plan"),
    ):
        story.append(_p(f"<b>{label}:</b> {summary.get(key) or 'Not documented.'}"))

    story.append(_p("SOAP Note", _SECTION))
    for label, key in (
        ("Subjective", "subjective"),
        ("Objective", "objective"),
        ("AI Clinical Assessment", "assessment"),
        ("Plan", "plan"),
    ):
        story.append(_p(f"<b>{label}:</b> {soap.get(key) or 'Not documented.'}"))

    if recommendations:
        story.append(_p("AI Suggestions – Requires Doctor Review", _SECTION))
        rows = [["Type", "Content", "Confidence"]]
        for item in recommendations:
            rows.append(
                [
                    str(item.get("type", "")).replace("_", " ").title(),
                    item.get("content", ""),
                    str(item.get("confidence") or "-"),
                ]
            )
        table = Table(rows, colWidths=[35 * mm, 105 * mm, 25 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)

    doctor_remarks = snapshot.get("doctor_remarks")
    if doctor_remarks:
        story.append(_p("Doctor Remarks", _SECTION))
        story.append(_p(doctor_remarks))

    follow_up_date = snapshot.get("follow_up_date")
    if follow_up_date:
        story.append(_p("Follow-up", _SECTION))
        story.append(_p(f"Date: {follow_up_date}. {snapshot.get('follow_up_notes') or ''}"))

    story.append(Spacer(1, 16))
    story.append(
        _p(
            "This report was generated with AI assistance and reviewed and approved by the "
            "attending doctor. AI-generated content is advisory only.",
            _META,
        )
    )

    doc.build(story)
    return buffer.getvalue()
