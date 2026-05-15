import logging
import re

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


# ─── Intent Detection ──────────────────────────────────────────────────────────

INTENT_KEYWORDS = {
    'attendance': [
        'attendance', 'attend', 'present', 'absent', 'absence', 'absences',
        'missing', 'missed', 'show up', 'showed up', 'check in', 'checked in',
        'not here', 'late', 'tardy', 'skip', 'skipped',
        'face recognition attendance', 'face attendance',
    ],
    'grades': [
        'grade', 'grades', 'score', 'scores', 'mark', 'marks', 'result', 'results',
        'exam result', 'exam results', 'performance', 'average', 'averages',
        'pass', 'fail', 'failed', 'passed', 'gpa', 'percent', 'percentage',
        'how did', 'how well', 'doing well', 'doing poorly',
        'test score', 'test scores', 'quiz result',
    ],
    'subjects': [
        'subject', 'subjects', 'course', 'courses', 'enrolled',
        'enrollment', 'taking', 'study', 'studying',
        'curriculum', 'lesson', 'lessons', 'topic', 'topics',
    ],
    'teachers': [
        'teacher', 'teachers', 'staff', 'instructor', 'instructors',
        'professor', 'professors', 'faculty', 'department', 'departments',
        'specialization', 'who teaches', 'teaching',
    ],
    'students': [
        'student', 'students', 'how many student', 'pupil', 'pupils',
        'learner', 'learners', 'population',
    ],
    'exams': [
        'exam', 'exams', 'test', 'tests', 'assessment', 'assessments',
        'created exam', 'recent exam', 'upcoming exam', 'exam schedule',
        'midterm', 'final exam',
    ],
    'overview': [
        'overview', 'summary', 'summarize', 'overall', 'everything',
        'full', 'complete', 'report', 'dashboard', 'brief', 'briefing',
        'school overview', 'school summary', 'school status',
        'tell me about the school', 'tell me everything',
    ],
    'children': [
        'child', 'children', 'kid', 'kids', 'son', 'daughter',
        'my children', 'my kids', 'ward', 'wards',
    ],
}

# Priority order for intent detection (more specific intents first)
INTENT_PRIORITY = [
    'children', 'exams', 'attendance', 'grades',
    'subjects', 'teachers', 'students', 'overview',
]

# Strong keywords that must be present for 'overview' intent
# (avoid matching on generic words like 'all', 'what' alone)
OVERVIEW_STRONG_KEYWORDS = [
    'overview', 'summary', 'summarize', 'overall', 'everything',
    'full', 'complete', 'report', 'dashboard', 'brief', 'briefing',
    'school overview', 'school summary', 'school status',
    'tell me about the school', 'tell me everything',
]

GREETING_PATTERNS = [
    'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
    'how are you', 'help', 'what can you', 'what do you do',
]


def detect_intent(message: str, role: str) -> str:
    """
    Detect the user's intent from their message.

    Returns one of: 'attendance', 'grades', 'subjects', 'teachers',
    'students', 'exams', 'overview', 'children', 'greeting', or 'general'.
    """
    msg_lower = message.lower().strip()

    # Check each intent in priority order
    for intent in INTENT_PRIORITY:
        keywords = INTENT_KEYWORDS[intent]
        for kw in keywords:
            if kw in msg_lower:
                # For 'overview', require at least one strong keyword
                # to avoid matching on generic words
                if intent == 'overview':
                    if any(sk in msg_lower for sk in OVERVIEW_STRONG_KEYWORDS):
                        return intent
                    continue
                return intent

    # Check for greeting patterns
    if any(p in msg_lower for p in GREETING_PATTERNS):
        return 'greeting'

    # Default: no specific topic detected
    return 'general'


# ─── Role-specific context builders (intent-aware) ─────────────────────────────

def _build_admin_context(user, intent):
    """Build context for admin, filtered by intent."""
    lines = []
    try:
        if intent == 'greeting':
            from students.models import Student
            from teachers.models import Teacher
            from parents.models import Parent
            sc = Student.objects.count()
            tc = Teacher.objects.count()
            pc = Parent.objects.count()
            lines.append(
                f"School has {sc} students, {tc} teachers, {pc} parents."
            )
            return lines

        if intent in ('overview', 'general'):
            from students.models import Student
            from teachers.models import Teacher
            from parents.models import Parent
            sc = Student.objects.count()
            tc = Teacher.objects.count()
            pc = Parent.objects.count()
            lines.append(f"School has {sc} students, {tc} teachers, {pc} parents.")

            if intent == 'general':
                # For general, just the basics — don't dump everything
                lines.append(
                    "What would you like to know? "
                    "I can help with attendance, grades, students, teachers, or exams."
                )
                return lines

            # overview — add attendance and grades summary
            from attendance.models import Attendance
            from exams.models import Grade

            recent_att = list(Attendance.objects.order_by('-date')[:100])
            if recent_att:
                present = sum(1 for a in recent_att if a.status == 'present')
                lines.append(
                    f"Recent attendance (last {len(recent_att)} records): "
                    f"{present} present, {len(recent_att)-present} absent "
                    f"({round(present/len(recent_att)*100)}% rate)."
                )

            recent_grades = list(
                Grade.objects.select_related('exam').order_by('-created_at')[:50]
            )
            if recent_grades:
                percentages = []
                for g in recent_grades:
                    total_q = g.exam.get_questions_count()
                    if total_q > 0:
                        percentages.append(float(g.score) / total_q * 100)
                if percentages:
                    avg = sum(percentages) / len(percentages)
                    lines.append(
                        f"Recent grades average: {round(avg)}% "
                        f"across {len(percentages)} graded exams."
                    )

        elif intent == 'attendance':
            from attendance.models import Attendance
            recent_att = list(Attendance.objects.order_by('-date')[:100])
            if recent_att:
                present = sum(1 for a in recent_att if a.status == 'present')
                absent = len(recent_att) - present
                pct = round(present / len(recent_att) * 100)
                lines.append(
                    f"School attendance (last {len(recent_att)} records): "
                    f"{present} present, {absent} absent ({pct}% rate)."
                )
                # Add recent absence details
                recent_absent = [a for a in recent_att if a.status == 'absent'][:5]
                if recent_absent:
                    abs_details = []
                    for a in recent_absent:
                        student_name = (
                            a.student.user.get_full_name() or a.student.user.username
                        )
                        abs_details.append(f"{student_name} on {a.date}")
                    lines.append("Recent absences: " + "; ".join(abs_details) + ".")
            else:
                lines.append("No attendance records found.")

        elif intent == 'grades':
            from exams.models import Grade
            recent_grades = list(
                Grade.objects.select_related('exam', 'exam__subject')
                .order_by('-created_at')[:50]
            )
            if recent_grades:
                percentages = []
                subject_avgs = {}
                for g in recent_grades:
                    total_q = g.exam.get_questions_count()
                    if total_q > 0:
                        pct = float(g.score) / total_q * 100
                        percentages.append(pct)
                        subj = g.exam.subject.name if g.exam.subject else 'Unknown'
                        subject_avgs.setdefault(subj, []).append(pct)
                if percentages:
                    avg = round(sum(percentages) / len(percentages))
                    lines.append(
                        f"School grades average: {avg}% "
                        f"across {len(percentages)} graded exams."
                    )
                if subject_avgs:
                    for subj, pcts in list(subject_avgs.items())[:5]:
                        subj_avg = round(sum(pcts) / len(pcts))
                        lines.append(
                            f"  {subj}: average {subj_avg}% ({len(pcts)} exams)."
                        )
            else:
                lines.append("No grades recorded yet.")

        elif intent == 'students':
            from students.models import Student
            from classes.models import SchoolClass
            sc = Student.objects.count()
            lines.append(f"Total students: {sc}.")
            classes = SchoolClass.objects.all()
            if classes:
                for c in classes[:10]:
                    count = c.students.count()
                    lines.append(f"  {c}: {count} students.")

        elif intent == 'teachers':
            from teachers.models import Teacher
            tc = Teacher.objects.count()
            lines.append(f"Total teachers: {tc}.")
            teachers = list(Teacher.objects.all()[:15])
            for t in teachers:
                name = t.user.get_full_name() or t.user.username
                dept = t.department or 'No department'
                lines.append(f"  {name} - {dept}")

        elif intent == 'subjects':
            from subjects.models import Subject
            subjects = list(Subject.objects.all()[:20])
            lines.append(f"Total subjects: {len(subjects)}.")
            for s in subjects:
                lines.append(f"  {s.name} ({s.code or 'no code'})")

        elif intent == 'exams':
            from exams.models import Exam
            exams = list(
                Exam.objects.select_related('subject', 'teacher')
                .order_by('-created_at')[:10]
            )
            if exams:
                lines.append(f"Recent exams ({len(exams)}):")
                for e in exams:
                    teacher_name = (
                        e.teacher.user.get_full_name() or e.teacher.user.username
                    )
                    lines.append(
                        f"  {e.name} ({e.exam_type}) - "
                        f"{e.subject.name}, by {teacher_name}"
                    )
            else:
                lines.append("No exams found.")

    except Exception as e:
        logger.warning("Admin context error: %s", e)
        lines.append("Could not load the requested data.")
    return lines


def _build_teacher_context(user, intent):
    """Build context for teacher, filtered by intent."""
    lines = []
    try:
        tp = user.teacher_profile
        name = user.get_full_name() or user.username

        if intent == 'greeting':
            subjects = list(tp.assigned_subjects.all()[:5])
            subj_names = ', '.join(s.name for s in subjects) if subjects else 'no subjects'
            lines.append(
                f"Hello {name}! I can help with your classes, "
                f"students' attendance, grades, and exams. "
                f"You teach: {subj_names}."
            )
            return lines

        # Always include basic identity for non-greeting intents
        lines.append(f"Teacher: {name} (ID: {tp.teacher_id}).")
        if tp.department:
            lines.append(f"Department: {tp.department}.")

        if intent in ('overview', 'general'):
            if tp.specialization:
                lines.append(f"Specialization: {tp.specialization}.")
            subjects = list(tp.assigned_subjects.all()[:10])
            if subjects:
                lines.append(f"Subjects: {', '.join(s.name for s in subjects)}.")
            classes = list(tp.assigned_classes.all()[:10])
            if classes:
                lines.append(f"Classes: {', '.join(str(c) for c in classes)}.")

            if intent == 'general':
                lines.append(
                    "What would you like to know? "
                    "I can help with attendance, grades, exams, or class details."
                )
                return lines

            # overview — add more detail
            from students.models import Student
            from attendance.models import Attendance
            from exams.models import Grade, Exam

            if classes:
                students = Student.objects.filter(school_class__in=classes)
                lines.append(f"Total students across my classes: {students.count()}.")
                recent_att = list(
                    Attendance.objects.filter(student__in=students)
                    .order_by('-date')[:100]
                )
                if recent_att:
                    present = sum(1 for a in recent_att if a.status == 'present')
                    lines.append(
                        f"My students' recent attendance: "
                        f"{present}/{len(recent_att)} present "
                        f"({round(present/len(recent_att)*100)}%)."
                    )
            my_exams = list(Exam.objects.filter(teacher=tp).order_by('-created_at')[:5])
            if my_exams:
                exam_names = ', '.join(e.name for e in my_exams)
                lines.append(f"Recent exams I created: {exam_names}.")
            my_grades = list(
                Grade.objects.filter(exam__teacher=tp)
                .select_related('exam')
                .order_by('-created_at')[:30]
            )
            if my_grades:
                percentages = []
                for g in my_grades:
                    total_q = g.exam.get_questions_count()
                    if total_q > 0:
                        percentages.append(float(g.score) / total_q * 100)
                if percentages:
                    avg = sum(percentages) / len(percentages)
                    lines.append(f"My students' average grade: {round(avg)}%.")

        elif intent == 'attendance':
            classes = list(tp.assigned_classes.all()[:10])
            if classes:
                from students.models import Student
                from attendance.models import Attendance

                students = Student.objects.filter(school_class__in=classes)
                recent_att = list(
                    Attendance.objects.filter(student__in=students)
                    .order_by('-date')[:100]
                )
                if recent_att:
                    present = sum(1 for a in recent_att if a.status == 'present')
                    absent = len(recent_att) - present
                    pct = round(present / len(recent_att) * 100)
                    lines.append(
                        f"My students' attendance: "
                        f"{present} present, {absent} absent "
                        f"out of {len(recent_att)} records ({pct}% rate)."
                    )
                    # Show per-class breakdown
                    for c in classes[:5]:
                        c_students = Student.objects.filter(school_class=c)
                        c_att = list(
                            Attendance.objects.filter(student__in=c_students)
                            .order_by('-date')[:30]
                        )
                        if c_att:
                            c_present = sum(1 for a in c_att if a.status == 'present')
                            c_pct = round(c_present / len(c_att) * 100)
                            lines.append(
                                f"  {c}: {c_present}/{len(c_att)} present ({c_pct}%)."
                            )
                else:
                    lines.append("No attendance records found for your students.")
            else:
                lines.append("No classes assigned yet.")

        elif intent == 'grades':
            from exams.models import Grade

            my_grades = list(
                Grade.objects.filter(exam__teacher=tp)
                .select_related('exam', 'exam__subject')
                .order_by('-created_at')[:30]
            )
            if my_grades:
                percentages = []
                subject_avgs = {}
                for g in my_grades:
                    total_q = g.exam.get_questions_count()
                    if total_q > 0:
                        pct = float(g.score) / total_q * 100
                        percentages.append(pct)
                        subj = g.exam.subject.name if g.exam.subject else 'Unknown'
                        subject_avgs.setdefault(subj, []).append(pct)
                if percentages:
                    avg = round(sum(percentages) / len(percentages))
                    lines.append(f"My students' average grade: {avg}%.")
                if subject_avgs:
                    for subj, pcts in list(subject_avgs.items())[:5]:
                        subj_avg = round(sum(pcts) / len(pcts))
                        lines.append(
                            f"  {subj}: average {subj_avg}% ({len(pcts)} grades)."
                        )
            else:
                lines.append("No grades recorded for your students yet.")

        elif intent == 'subjects':
            subjects = list(tp.assigned_subjects.all()[:10])
            if subjects:
                lines.append(f"My subjects: {', '.join(s.name for s in subjects)}.")
            else:
                lines.append("No subjects assigned yet.")

        elif intent == 'classes':
            classes = list(tp.assigned_classes.all()[:10])
            if classes:
                from students.models import Student

                lines.append(f"My classes: {', '.join(str(c) for c in classes)}.")
                for c in classes[:5]:
                    count = Student.objects.filter(school_class=c).count()
                    lines.append(f"  {c}: {count} students.")
            else:
                lines.append("No classes assigned yet.")

        elif intent == 'exams':
            from exams.models import Exam

            my_exams = list(Exam.objects.filter(teacher=tp).order_by('-created_at')[:10])
            if my_exams:
                lines.append(f"My recent exams ({len(my_exams)}):")
                for e in my_exams:
                    lines.append(
                        f"  {e.name} ({e.exam_type}) - "
                        f"{e.subject.name}, {e.duration} min"
                    )
            else:
                lines.append("No exams created yet.")

        elif intent == 'students':
            classes = list(tp.assigned_classes.all()[:10])
            if classes:
                from students.models import Student

                students = Student.objects.filter(school_class__in=classes)
                lines.append(f"Total students across my classes: {students.count()}.")
                for c in classes[:5]:
                    count = Student.objects.filter(school_class=c).count()
                    lines.append(f"  {c}: {count} students.")
            else:
                lines.append("No classes assigned yet.")

    except AttributeError:
        lines.append(f"Teacher profile not found for {user.username}.")
    except Exception as e:
        logger.warning("Teacher context error: %s", e)
        lines.append("Could not load the requested data.")
    return lines


def _build_student_context(user, intent):
    """Build context for student, filtered by intent."""
    lines = []
    try:
        sp = user.student_profile
        name = user.get_full_name() or user.username

        if intent == 'greeting':
            lines.append(
                f"Hello {name}! I can help with your grades, attendance, and subjects."
            )
            return lines

        if intent in ('overview', 'general'):
            if intent == 'general':
                lines.append(
                    "What would you like to know? "
                    "I can help with your grades, attendance, or subjects."
                )
                return lines

            # overview — show everything
            subjects = list(sp.subjects.all()[:10])
            if subjects:
                lines.append(f"Enrolled subjects: {', '.join(s.name for s in subjects)}.")

            from attendance.models import Attendance
            att = list(Attendance.objects.filter(student=sp).order_by('-date')[:30])
            if att:
                present = sum(1 for a in att if a.status == 'present')
                absent = len(att) - present
                pct = round(present / len(att) * 100)
                lines.append(
                    f"Attendance: {present} present, {absent} absent "
                    f"out of {len(att)} sessions ({pct}%)."
                )
            else:
                lines.append("No attendance records found.")

            from exams.models import Grade
            grades = list(
                Grade.objects.filter(student=sp)
                .select_related('exam', 'exam__subject')
                .order_by('-created_at')[:10]
            )
            if grades:
                percentages = []
                for g in grades:
                    total_q = g.exam.get_questions_count()
                    if total_q > 0:
                        percentages.append(float(g.score) / total_q * 100)
                if percentages:
                    lines.append(
                        f"Overall average: {round(sum(percentages)/len(percentages))}%."
                    )
            else:
                lines.append("No grades recorded yet.")

        elif intent == 'attendance':
            from attendance.models import Attendance

            att = list(Attendance.objects.filter(student=sp).order_by('-date')[:30])
            if att:
                present = sum(1 for a in att if a.status == 'present')
                absent = len(att) - present
                pct = round(present / len(att) * 100)
                lines.append(
                    f"Your attendance: {present} present, {absent} absent "
                    f"out of {len(att)} sessions ({pct}% rate)."
                )
                if absent > 0:
                    recent_abs = [a for a in att if a.status == 'absent'][:5]
                    abs_dates = ', '.join(str(a.date) for a in recent_abs)
                    lines.append(f"Dates you were absent: {abs_dates}.")
            else:
                lines.append("No attendance records found for you.")

        elif intent == 'grades':
            from exams.models import Grade

            grades = list(
                Grade.objects.filter(student=sp)
                .select_related('exam', 'exam__subject')
                .order_by('-created_at')[:10]
            )
            if grades:
                details = []
                percentages = []
                for g in grades:
                    total_q = g.exam.get_questions_count()
                    if total_q > 0:
                        pct = round(float(g.score) / total_q * 100)
                        percentages.append(pct)
                        subj = g.exam.subject.name if g.exam.subject else 'Unknown'
                        details.append(
                            f"{g.exam.name} ({subj}): {g.score}/{total_q} = {pct}%"
                        )
                if details:
                    lines.append(
                        "Your recent grades: " + "; ".join(details[:5]) + "."
                    )
                if percentages:
                    lines.append(
                        f"Your overall average: "
                        f"{round(sum(percentages)/len(percentages))}%."
                    )
            else:
                lines.append("No grades recorded for you yet.")

        elif intent == 'subjects':
            subjects = list(sp.subjects.all()[:10])
            if subjects:
                lines.append(
                    f"Your enrolled subjects: {', '.join(s.name for s in subjects)}."
                )
            else:
                lines.append("No subjects enrolled yet.")

        elif intent == 'exams':
            from exams.models import Grade

            grades = list(
                Grade.objects.filter(student=sp)
                .select_related('exam', 'exam__subject')
                .order_by('-created_at')[:10]
            )
            if grades:
                lines.append("Your recent exam results:")
                for g in grades:
                    total_q = g.exam.get_questions_count()
                    if total_q > 0:
                        pct = round(float(g.score) / total_q * 100)
                        subj = g.exam.subject.name if g.exam.subject else 'Unknown'
                        lines.append(
                            f"  {g.exam.name} ({subj}): "
                            f"{g.score}/{total_q} = {pct}%"
                        )
            else:
                lines.append("No exam results recorded for you yet.")

    except AttributeError:
        lines.append(f"Student profile not found for {user.username}.")
    except Exception as e:
        logger.warning("Student context error: %s", e)
        lines.append("Could not load the requested data.")
    return lines


def _build_parent_context(user, intent):
    """Build context for parent, filtered by intent."""
    lines = []
    try:
        pp = user.parent_profile
        name = user.get_full_name() or user.username

        if intent == 'greeting':
            children = list(pp.children.select_related('user').all())
            child_names = ', '.join(
                c.user.get_full_name() or c.user.username for c in children[:4]
            )
            if child_names:
                lines.append(
                    f"Hello {name}! I can help monitor "
                    f"{child_names}'s attendance, grades, and progress."
                )
            else:
                lines.append(
                    f"Hello {name}! I can help monitor "
                    "your children's attendance, grades, and progress."
                )
            return lines

        # Always include basic identity for non-greeting intents
        lines.append(f"Parent: {name} (ID: {pp.parent_id}).")
        children = list(pp.children.select_related('user').all())
        if not children:
            lines.append("No children linked to this account.")
            return lines

        if intent in ('overview', 'general'):
            if intent == 'general':
                child_names = ', '.join(
                    c.user.get_full_name() or c.user.username for c in children[:4]
                )
                lines.append(f"Your children: {child_names}.")
                lines.append(
                    "What would you like to know? "
                    "I can help with attendance, grades, or overall progress."
                )
                return lines

            # overview — show everything for each child
            lines.append(f"Children ({len(children)}):")
            from attendance.models import Attendance
            from exams.models import Grade

            for child in children[:4]:
                cname = child.user.get_full_name() or child.user.username
                lines.append(
                    f"\n  Child: {cname} "
                    f"(ID: {child.student_id}, Class: {child.class_level or 'N/A'})"
                )
                att = list(
                    Attendance.objects.filter(student=child).order_by('-date')[:20]
                )
                if att:
                    present = sum(1 for a in att if a.status == 'present')
                    absent = len(att) - present
                    pct = round(present / len(att) * 100)
                    lines.append(
                        f"    Attendance: {present} present, "
                        f"{absent} absent ({pct}% rate)."
                    )
                else:
                    lines.append("    No attendance records.")
                grades = list(
                    Grade.objects.filter(student=child)
                    .select_related('exam', 'exam__subject')
                    .order_by('-created_at')[:5]
                )
                if grades:
                    percentages = []
                    for g in grades:
                        total_q = g.exam.get_questions_count()
                        if total_q > 0:
                            percentages.append(
                                round(float(g.score) / total_q * 100)
                            )
                    if percentages:
                        lines.append(
                            f"    Grade average: "
                            f"{round(sum(percentages)/len(percentages))}%."
                        )
                else:
                    lines.append("    No grades recorded.")

        elif intent == 'attendance':
            from attendance.models import Attendance

            lines.append("Children's attendance:")
            for child in children[:4]:
                cname = child.user.get_full_name() or child.user.username
                att = list(
                    Attendance.objects.filter(student=child).order_by('-date')[:20]
                )
                if att:
                    present = sum(1 for a in att if a.status == 'present')
                    absent = len(att) - present
                    pct = round(present / len(att) * 100)
                    lines.append(
                        f"  {cname}: {present} present, "
                        f"{absent} absent ({pct}% rate)."
                    )
                    if absent > 0:
                        recent_abs = [a for a in att if a.status == 'absent'][:3]
                        abs_dates = ', '.join(str(a.date) for a in recent_abs)
                        lines.append(f"    Recent absences: {abs_dates}.")
                else:
                    lines.append(f"  {cname}: No attendance records.")

        elif intent in ('grades', 'exams'):
            from exams.models import Grade

            lines.append("Children's grades:")
            for child in children[:4]:
                cname = child.user.get_full_name() or child.user.username
                grades = list(
                    Grade.objects.filter(student=child)
                    .select_related('exam', 'exam__subject')
                    .order_by('-created_at')[:5]
                )
                if grades:
                    percentages = []
                    grade_strs = []
                    for g in grades:
                        total_q = g.exam.get_questions_count()
                        if total_q > 0:
                            p = round(float(g.score) / total_q * 100)
                            percentages.append(p)
                            subj = g.exam.subject.name if g.exam.subject else 'Exam'
                            grade_strs.append(f"{subj}: {p}%")
                    if grade_strs:
                        lines.append(f"  {cname}: {', '.join(grade_strs)}.")
                    if percentages:
                        lines.append(
                            f"    Average: "
                            f"{round(sum(percentages)/len(percentages))}%."
                        )
                else:
                    lines.append(f"  {cname}: No grades recorded.")

        elif intent == 'children':
            for child in children[:4]:
                cname = child.user.get_full_name() or child.user.username
                lines.append(
                    f"  {cname} (ID: {child.student_id}, "
                    f"Class: {child.class_level or 'N/A'})"
                )

        elif intent == 'subjects':
            for child in children[:4]:
                cname = child.user.get_full_name() or child.user.username
                subjects = list(child.subjects.all()[:10])
                if subjects:
                    lines.append(
                        f"  {cname}'s subjects: "
                        f"{', '.join(s.name for s in subjects)}."
                    )
                else:
                    lines.append(f"  {cname}: No subjects enrolled.")

    except AttributeError:
        lines.append(f"Parent profile not found for {user.username}.")
    except Exception as e:
        logger.warning("Parent context error: %s", e)
        lines.append("Could not load the requested data.")
    return lines


def build_context_for_user(user, intent='general'):
    """Build role-specific context filtered by detected intent."""
    role = getattr(user, 'role', 'UNKNOWN')
    builders = {
        'ADMIN': _build_admin_context,
        'TEACHER': _build_teacher_context,
        'STUDENT': _build_student_context,
        'PARENT': _build_parent_context,
    }
    builder = builders.get(role)
    if builder:
        lines = builder(user, intent)
    else:
        lines = [f"User: {user.get_full_name() or user.username}, Role: {role}."]
    return '\n'.join(lines)


# ─── Gemini Call ─────────────────────────────────────────────────────────────

ROLE_PERSONAS = {
    'ADMIN': (
        "You are Smart School Chatbot for a school administrator. "
        "Help with school-wide statistics, attendance, grades, staff, and reports."
    ),
    'TEACHER': (
        "You are Smart School Chatbot for a teacher. "
        "Help with class performance, student grades, attendance, and teaching resources."
    ),
    'STUDENT': (
        "You are Smart School Chatbot for a student. "
        "Help with grades, attendance, subjects, and study advice."
    ),
    'PARENT': (
        "You are Smart School Chatbot for a parent. "
        "Help monitor children's attendance, grades, and academic progress."
    ),
}

ROLE_SUGGESTIONS = {
    'ADMIN': [
        "Show school overview", "Attendance summary",
        "Grade averages", "How many students?", "Teacher list",
    ],
    'TEACHER': [
        "My students' performance", "Recent exam results",
        "Class attendance", "My subjects", "My classes",
    ],
    'STUDENT': [
        "My grades", "My attendance",
        "My subjects", "Recent exam results",
    ],
    'PARENT': [
        "My children's attendance", "Recent grades",
        "Any absences?", "Children's subjects",
    ],
}


def call_gemini(message: str, context: str, user, intent: str) -> str:
    """Call Gemini API with intent-specific context and instructions."""
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    role = getattr(user, 'role', 'USER')

    if not GENAI_AVAILABLE or not api_key:
        return _smart_fallback(context, intent, role)

    persona = ROLE_PERSONAS.get(role, "You are a helpful Smart School Chatbot.")

    # Build intent-specific instruction for Gemini
    intent_instruction = ""
    if intent == 'greeting':
        intent_instruction = (
            "The user is greeting you. Respond warmly and briefly, "
            "mentioning what you can help with. Do NOT dump data."
        )
    elif intent == 'general':
        intent_instruction = (
            "The user hasn't specified a clear topic. Give a brief, "
            "helpful response and suggest what you can help with. "
            "Do NOT dump all data."
        )
    elif intent == 'overview':
        intent_instruction = (
            "The user wants an overview/summary. "
            "Present the context data in a clear, organized summary."
        )
    else:
        intent_instruction = (
            f"The user is asking about **{intent}**. "
            f"Answer ONLY about {intent} using the context data. "
            f"Do NOT include information about other topics."
        )

    system_prompt = f"""{persona}

{intent_instruction}

RELEVANT DATA (only about what the user asked):
{context}

RULES:
- Answer ONLY based on the data above. Do NOT invent or hallucinate names, numbers, or facts.
- If the data does not contain the answer, say: "I don't have that information available right now."
- Be friendly, professional, and concise (under 180 words).
- Use simple, clear language. Use bullet points when listing multiple items.
- Do NOT mention that you have a "context" or "database" — speak naturally.
- Do NOT return a full school summary — focus ONLY on what was asked.
"""

    try:
        genai.configure(api_key=api_key)

        # Try models in order — some keys only have access to certain models
        model_names = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro']
        model = None
        for name in model_names:
            try:
                model = genai.GenerativeModel(name)
                break
            except Exception:
                continue

        if model is None:
            logger.error("No Gemini model could be initialized.")
            return _smart_fallback(context, intent, role)

        full_prompt = f"{system_prompt}\n\nUser: {message}"
        response = model.generate_content(
            full_prompt,
            generation_config={
                "max_output_tokens": 300,
                "temperature": 0.3,
            }
        )
        return response.text.strip()
    except Exception as e:
        logger.error("Gemini API error (%s): %s", type(e).__name__, e)
        # Return a clean fallback with the real data, no scary error message
        return _smart_fallback(context, intent, role)


def _smart_fallback(context: str, intent: str, role: str = 'USER') -> str:
    """
    Fallback when Gemini is unavailable.
    Returns topic-specific data, NOT a full school summary.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    hint = ""
    if not GENAI_AVAILABLE:
        hint = (
            "\n\n(Note: 'google-generativeai' package is not installed. "
            "Please run 'pip install google-generativeai')"
        )
    elif not api_key:
        hint = "\n\n(Note: GEMINI_API_KEY is missing in .env file)"

    if intent == 'greeting':
        return (
            "Hello! I'm your Smart School Chatbot. "
            "I can help with attendance, grades, subjects, and more. Just ask!"
            + hint
        )

    if not context.strip():
        return f"I don't have any data to show right now. Please try again later.{hint}"

    # For specific intents, present the filtered data directly
    # (context is already filtered by intent — no full summary dump)
    topic_label = {
        'attendance': 'Attendance Information',
        'grades': 'Grade Information',
        'subjects': 'Subject Information',
        'teachers': 'Teacher Information',
        'students': 'Student Information',
        'exams': 'Exam Information',
        'overview': 'School Overview',
        'children': 'Children Information',
        'general': 'Quick Summary',
    }.get(intent, 'Information')

    return f"{topic_label}:\n\n{context}{hint}"


# ─── View ─────────────────────────────────────────────────────────────────────

class ChatbotAskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get('message', '').strip()
        if not message:
            return Response({'error': 'Message is required.'}, status=400)
        if len(message) > 500:
            return Response({'error': 'Message too long (max 500 characters).'}, status=400)

        user = request.user
        role = getattr(user, 'role', 'USER')
        intent = detect_intent(message, role)
        context = build_context_for_user(user, intent)
        reply = call_gemini(message, context, user, intent)

        return Response({
            'reply': reply,
            'suggestions': ROLE_SUGGESTIONS.get(role, []),
            'intent': intent,
        })

    def get(self, request):
        """Return role-specific quick suggestions on GET."""
        role = getattr(request.user, 'role', 'USER')
        return Response({
            'suggestions': ROLE_SUGGESTIONS.get(role, []),
            'greeting': (
                f"Hello {request.user.get_full_name() or request.user.username}! "
                "How can I help you today?"
            ),
        })
