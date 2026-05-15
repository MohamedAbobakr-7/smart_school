"""PDF export for WeeklyReport using ReportLab."""
from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import WeeklyReport


def render_weekly_report_pdf(report: WeeklyReport, buffer: BytesIO) -> None:
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]

    story = []
    scope_label = "School-wide" if report.scope == WeeklyReport.Scope.SCHOOL else (
        f"Teacher: {report.teacher.teacher_id}" if report.teacher else "Teacher"
    )
    story.append(Paragraph("Weekly performance report", title_style))
    story.append(Spacer(1, 0.15 * inch))
    story.append(
        Paragraph(
            f"<b>Window:</b> {report.week_start} to {report.week_end} &nbsp;|&nbsp; "
            f"<b>Scope:</b> {scope_label}",
            body,
        )
    )
    story.append(
        Paragraph(
            f"<b>Generated:</b> {report.generated_at.isoformat() if report.generated_at else '—'}",
            body,
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    att = report.attendance_stats or {}
    acad = report.academic_stats or {}
    exam = report.exam_stats or {}

    story.append(Paragraph("Attendance summary", h2))
    att_rows = [
        ["Metric", "Value"],
        ["Total records", str(att.get("total_records", "—"))],
        ["Present", str(att.get("present", "—"))],
        ["Absent", str(att.get("absent", "—"))],
        ["Attendance rate %", str(att.get("attendance_rate_percent", "—"))],
    ]
    t1 = Table(att_rows, colWidths=[3 * inch, 2 * inch])
    t1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a5276")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f4f6")]),
            ]
        )
    )
    story.append(t1)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Academic summary", h2))
    acad_rows = [
        ["Metric", "Value"],
        ["Grades recorded", str(acad.get("grades_recorded", "—"))],
        ["Average score %", str(acad.get("average_score_percent", "—"))],
        ["Exams created", str(acad.get("exams_created", "—"))],
        ["Unique students graded", str(acad.get("unique_students_graded", "—"))],
    ]
    t2 = Table(acad_rows, colWidths=[3 * inch, 2 * inch])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a5276")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f4f6")]),
            ]
        )
    )
    story.append(t2)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Exams & face attendance", h2))
    ex_rows = [
        ["Metric", "Value"],
        ["New exams", str(exam.get("new_exams", "—"))],
        ["Sessions (face)", str(exam.get("attendance_sessions", "—"))],
        ["Attendance marked (face)", str(exam.get("face_sessions_attendance_marked", "—"))],
    ]
    t3 = Table(ex_rows, colWidths=[3 * inch, 2 * inch])
    t3.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a5276")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f4f6")]),
            ]
        )
    )
    story.append(t3)
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Insights", h2))
    for item in report.insights or []:
        if isinstance(item, dict):
            text = item.get("text", "")
        else:
            text = str(item)
        story.append(Paragraph(text.replace("&", "&amp;").replace("<", "&lt;"), body))
        story.append(Spacer(1, 0.06 * inch))

    cmp_ = report.comparison_prior_week
    if cmp_:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Week-over-week (prior window)", h2))
        story.append(
            Paragraph(
                f"Attendance rate delta: {cmp_.get('attendance_rate_delta', '—')} pp; "
                f"grades count delta: {cmp_.get('grades_count_delta', '—')}",
                body,
            )
        )

    doc.build(story)
