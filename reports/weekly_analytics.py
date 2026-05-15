"""
Aggregate attendance, exams, and grades for a calendar week.
Used by WeeklyReport generation and dashboard APIs.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Count, Q, Sum

from attendance.models import Attendance, AttendanceSession
from exams.models import Exam, Grade
from students.models import Student


def _pct(part: int, whole: int) -> float:
    if not whole:
        return 0.0
    return round(100.0 * part / whole, 2)


def _grade_percentage(g: Grade) -> float:
    total = g.exam.get_questions_count()
    if not total:
        return 0.0
    return float((g.score / Decimal(total)) * Decimal(100))


def build_weekly_snapshot(
    week_start: date,
    week_end: date,
    teacher=None,
) -> dict[str, Any]:
    """
    Build performance analytics, chart-ready payloads, and insight strings
    for the inclusive date range [week_start, week_end].
    """
    att_qs = Attendance.objects.filter(date__gte=week_start, date__lte=week_end)
    if teacher:
        att_qs = att_qs.filter(
            Q(marked_by=teacher) | Q(session__instructor=teacher)
        )

    total_att = att_qs.count()
    present = att_qs.filter(status=Attendance.PRESENT).count()
    absent = att_qs.filter(status=Attendance.ABSENT).count()

    by_day: dict[str, dict[str, int]] = defaultdict(lambda: {"present": 0, "absent": 0})
    for row in att_qs.values("date", "status"):
        d = row["date"].isoformat() if hasattr(row["date"], "isoformat") else str(row["date"])
        if row["status"] == Attendance.PRESENT:
            by_day[d]["present"] += 1
        else:
            by_day[d]["absent"] += 1

    day_labels = []
    present_series = []
    absent_series = []
    cur = week_start
    while cur <= week_end:
        key = cur.isoformat()
        day_labels.append(cur.strftime("%a %m/%d"))
        present_series.append(by_day[key]["present"])
        absent_series.append(by_day[key]["absent"])
        cur += timedelta(days=1)

    grade_qs = Grade.objects.filter(
        created_at__date__gte=week_start,
        created_at__date__lte=week_end,
    )
    exam_created_qs = Exam.objects.filter(
        created_at__date__gte=week_start,
        created_at__date__lte=week_end,
    )
    if teacher:
        grade_qs = grade_qs.filter(exam__teacher=teacher)
        exam_created_qs = exam_created_qs.filter(teacher=teacher)

    grades_count = grade_qs.count()
    avg_score_pct = None
    if grades_count:
        s = sum(_grade_percentage(g) for g in grade_qs.select_related("exam"))
        avg_score_pct = round(s / grades_count, 2)

    by_subject: dict[str, list[float]] = defaultdict(list)
    for g in grade_qs.select_related("exam", "exam__subject"):
        subj = g.exam.subject.name
        by_subject[subj].append(_grade_percentage(g))

    subject_labels = sorted(by_subject.keys())
    subject_avgs = [
        round(sum(by_subject[s]) / len(by_subject[s]), 2) for s in subject_labels
    ]

    class_level_dist = (
        Student.objects.filter(id__in=grade_qs.values_list("student_id", flat=True).distinct())
        .values("class_level")
        .annotate(c=Count("id"))
    )
    class_breakdown = {row["class_level"] or "Unassigned": row["c"] for row in class_level_dist}

    session_qs = AttendanceSession.objects.filter(
        date__gte=week_start,
        date__lte=week_end,
    )
    if teacher:
        session_qs = session_qs.filter(instructor=teacher)

    session_stats = session_qs.aggregate(
        sessions=Count("id"),
        faces=Sum("total_faces_detected"),
        matches=Sum("total_matches"),
        marked=Sum("total_attendance_marked"),
    )

    attendance_stats = {
        "total_records": total_att,
        "present": present,
        "absent": absent,
        "attendance_rate_percent": _pct(present, total_att),
        "by_source": dict(
            att_qs.values("source").annotate(c=Count("id")).values_list("source", "c")
        ),
    }

    academic_stats = {
        "grades_recorded": grades_count,
        "average_score_percent": avg_score_pct,
        "exams_created": exam_created_qs.count(),
        "unique_students_graded": grade_qs.values("student_id").distinct().count(),
        "class_level_breakdown": class_breakdown,
    }

    exam_stats = {
        "new_exams": exam_created_qs.count(),
        "total_questions_on_new_exams": sum(e.get_questions_count() for e in exam_created_qs),
        "attendance_sessions": session_stats["sessions"] or 0,
        "face_sessions_faces_detected": int(session_stats["faces"] or 0),
        "face_sessions_matches": int(session_stats["matches"] or 0),
        "face_sessions_attendance_marked": int(session_stats["marked"] or 0),
    }

    charts_payload = {
        "attendance_status_pie": {
            "type": "pie",
            "labels": ["Present", "Absent"],
            "data": [present, absent],
        },
        "attendance_by_day": {
            "type": "bar",
            "labels": day_labels,
            "datasets": [
                {"label": "Present", "data": present_series},
                {"label": "Absent", "data": absent_series},
            ],
        },
        "average_score_by_subject": {
            "type": "bar",
            "labels": subject_labels,
            "datasets": [{"label": "Avg score %", "data": subject_avgs}],
        },
        "class_level_bar": {
            "type": "bar",
            "labels": list(class_breakdown.keys()),
            "datasets": [{"label": "Students graded", "data": list(class_breakdown.values())}],
        },
    }

    insights = _build_insights(
        week_start,
        week_end,
        attendance_stats,
        academic_stats,
        exam_stats,
        teacher,
    )

    return {
        "attendance_stats": attendance_stats,
        "academic_stats": academic_stats,
        "exam_stats": exam_stats,
        "charts_payload": charts_payload,
        "insights": insights,
    }


def _build_insights(
    week_start: date,
    week_end: date,
    attendance_stats: dict,
    academic_stats: dict,
    exam_stats: dict,
    teacher,
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    scope = "Your classes" if teacher else "School-wide"
    rate = attendance_stats["attendance_rate_percent"]
    if attendance_stats["total_records"]:
        if rate >= 90:
            out.append(
                {
                    "level": "positive",
                    "text": f"{scope} attendance rate was strong ({rate}%).",
                }
            )
        elif rate < 75:
            out.append(
                {
                    "level": "warning",
                    "text": f"{scope} attendance rate was {rate}%; consider follow-up.",
                }
            )
        else:
            out.append(
                {
                    "level": "neutral",
                    "text": f"{scope} attendance rate was {rate}%.",
                }
            )
    else:
        out.append(
            {
                "level": "neutral",
                "text": "No attendance activity recorded in this period for this scope.",
            }
        )

    avg = academic_stats.get("average_score_percent")
    if avg is not None:
        if avg >= 80:
            out.append(
                {
                    "level": "positive",
                    "text": f"Average assessed score was {avg}% across {academic_stats['grades_recorded']} grade(s).",
                }
            )
        elif avg < 60:
            out.append(
                {
                    "level": "warning",
                    "text": f"Average assessed score was {avg}%; review difficult topics or assessments.",
                }
            )
        else:
            out.append(
                {
                    "level": "neutral",
                    "text": f"Average assessed score was {avg}%.",
                }
            )

    if exam_stats["new_exams"]:
        out.append(
            {
                "level": "neutral",
                "text": f"{exam_stats['new_exams']} new exam(s) were created in this week.",
            }
        )

    if exam_stats["attendance_sessions"]:
        out.append(
            {
                "level": "neutral",
                "text": (
                    f"Face attendance: {exam_stats['attendance_sessions']} session(s), "
                    f"{exam_stats['face_sessions_attendance_marked']} attendance mark(s)."
                ),
            }
        )

    out.append(
        {
            "level": "neutral",
            "text": f"Reporting window: {week_start.isoformat()} to {week_end.isoformat()}.",
        }
    )
    return out


def compare_to_prior_week(
    week_start: date,
    week_end: date,
    teacher=None,
) -> dict[str, Any] | None:
    """Optional delta vs the previous same-length window immediately before week_start."""
    span = (week_end - week_start).days + 1
    prev_end = week_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=span - 1)
    if prev_start > prev_end:
        return None
    cur = build_weekly_snapshot(week_start, week_end, teacher=teacher)
    prev = build_weekly_snapshot(prev_start, prev_end, teacher=teacher)
    return {
        "previous_week_start": prev_start.isoformat(),
        "previous_week_end": prev_end.isoformat(),
        "attendance_rate_delta": round(
            float(cur["attendance_stats"]["attendance_rate_percent"])
            - float(prev["attendance_stats"]["attendance_rate_percent"]),
            2,
        ),
        "grades_count_delta": cur["academic_stats"]["grades_recorded"]
        - prev["academic_stats"]["grades_recorded"],
    }
