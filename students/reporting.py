"""
Aggregated per-student stats for admin / teacher reporting UIs.
"""

from __future__ import annotations

from collections import defaultdict

from django.db.models import Count, Q


def build_student_stats_list(students_qs, request):
    """
    Build list of dicts consumed by Weekly Reports pages (attendance + grades).

    Each row includes: id, user, student_id, name, photo_url, class_id, class_name,
    present_att, total_att, attendance_pct, total_grade_pct, grade_count, avg_grade.
    """
    from attendance.models import Attendance
    from exams.models import Grade

    qs = students_qs.select_related('user', 'school_class').order_by('id')
    student_ids = list(qs.values_list('id', flat=True))
    if not student_ids:
        return []

    att_rows = (
        Attendance.objects.filter(student_id__in=student_ids)
        .order_by()  # clear Meta.ordering — required for GROUP BY on SQL Server
        .values('student_id')
        .annotate(
            total_att=Count('pk'),
            present_att=Count('pk', filter=Q(status=Attendance.PRESENT)),
        )
    )
    att_map = {r['student_id']: r for r in att_rows}

    grades_qs = (
        Grade.objects.filter(student_id__in=student_ids)
        .select_related('exam')
        .order_by()  # avoid ORDER BY leaking into aggregates on some DB backends
    )
    grade_lists: dict = defaultdict(list)
    for g in grades_qs:
        grade_lists[g.student_id].append(g)

    rows = []
    for st in qs:
        att = att_map.get(st.id, {'total_att': 0, 'present_att': 0})
        total_att = int(att['total_att'] or 0)
        present_att = int(att['present_att'] or 0)
        attendance_pct = round(present_att / total_att * 100, 1) if total_att else None

        total_grade_pct = 0.0
        grade_count = 0
        for g in grade_lists[st.id]:
            pct = g.get_percentage()
            if pct:
                total_grade_pct += float(pct)
                grade_count += 1

        avg_grade = round(total_grade_pct / grade_count, 1) if grade_count else None

        class_id = st.school_class_id
        if st.school_class:
            class_name = st.school_class.display_name
        else:
            class_name = (st.class_level or '').strip() or '—'

        photo_url = None
        if st.photo and request is not None:
            try:
                photo_url = request.build_absolute_uri(st.photo.url)
            except Exception:
                photo_url = st.photo.url

        u = st.user
        name = u.get_full_name() or u.username or u.email or '—'

        rows.append(
            {
                'id': st.id,
                'user': u.id,
                'student_id': st.student_id or '',
                'name': name,
                'photo_url': photo_url,
                'class_id': class_id,
                'class_name': class_name,
                'present_att': present_att,
                'total_att': total_att,
                'attendance_pct': attendance_pct,
                'total_grade_pct': total_grade_pct,
                'grade_count': grade_count,
                'avg_grade': avg_grade,
            }
        )

    return rows
