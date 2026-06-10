"""
Student ID generation utilities.

Format: {year}{grade_padded}{sequence}
  - year       = 4-digit admission year  (e.g. 2026)
  - grade      = 1-2 digit grade number  (e.g. 1, 10)
  - sequence   = 3-digit sequential counter per grade (001, 002, …)

Examples:
  Grade 1  → 202610001, 202610002 …
  Grade 10 → 20261000 1, 202610002 …

Wait — let's use the simpler format the user specified:
  2026GXXX  where G = grade number, XXX = 3-digit sequence

  Grade 1  → 20261001, 20261002 …  (year=2026, G=1, seq=001)
  Grade 2  → 20262001, 20262002 …
  Grade 10 → 202610001, 202610002 … (grade has 2 digits)
"""

import re
from datetime import date

from django.db.models import Value, CharField
from django.db.models.functions import Coalesce, Trim


def _extract_grade_number(school_class) -> int | None:
    """
    Try to extract an integer grade/year number from a SchoolClass instance.
    Looks inside school_class.name for digits, e.g.
      'Grade 5'  → 5
      'Year 10'  → 10
      'Form 2'   → 2
      'Class 3A' → 3
    Returns None if no number found.
    """
    if school_class is None:
        return None
    name = school_class.name or ''
    m = re.search(r'\d+', name)
    if m:
        return int(m.group())
    return None


def generate_student_id(school_class=None, admission_year: int | None = None) -> str:
    """
    Generate a unique, sequential student ID.

    Format: {year}{grade}{seq:03d}
      - year  = 4-digit year (default: current year)
      - grade = grade number extracted from school_class.name (default: 0 if unknown)
      - seq   = next sequential number for (year, grade), zero-padded to 3 digits

    If seq would exceed 999, it keeps incrementing (4+ digits) to avoid collisions.
    """
    from students.models import Student  # local import to avoid circular

    year = admission_year or date.today().year
    grade = _extract_grade_number(school_class) if school_class else 0

    prefix = f"{year}{grade}"

    # Find the highest existing seq for this prefix
    existing = (
        Student.objects
        .filter(student_id__startswith=prefix)
        .values_list('student_id', flat=True)
    )

    max_seq = 0
    for sid in existing:
        suffix = sid[len(prefix):]   # strip the prefix
        if suffix.isdigit():
            max_seq = max(max_seq, int(suffix))

    next_seq = max_seq + 1
    new_id = f"{prefix}{next_seq:03d}"

    # Collision guard (extremely unlikely but safe)
    while Student.objects.filter(student_id=new_id).exists():
        next_seq += 1
        new_id = f"{prefix}{next_seq:03d}"

    return new_id


def students_missing_ids_queryset():
    """
    Students with no usable student_id (NULL, empty, or whitespace-only).
    """
    from students.models import Student

    return (
        Student.objects.annotate(
            _sid_trimmed=Trim(Coalesce('student_id', Value('', output_field=CharField())))
        )
        .filter(_sid_trimmed='')
        .select_related('school_class', 'user')
        .order_by('user__first_name', 'user__last_name')
    )


def backfill_student_ids():
    """
    Assign generated IDs to any existing students that have a blank/null/whitespace student_id.
    Call this from a management command or the Django shell.
    """
    updated = 0
    for student in list(students_missing_ids_queryset()):
        new_id = generate_student_id(school_class=student.school_class)
        student.student_id = new_id
        student.save(update_fields=['student_id'])
        updated += 1
    return updated


# ── Grade-based subject enrollment ──────────────────────────────────

# Subject names that should be auto-enrolled for grades 1-3
# (core subjects only — no Science or Social Studies)
SUBJECTS_GRADES_1_3 = [
    'Arabic Language',
    'English Language',
    'Mathematics',
    'Computer Science',
    'Religion',
]

# Subject names that should be auto-enrolled for grades 4-6
# (all available subjects)
SUBJECTS_GRADES_4_6 = [
    'Arabic Language',
    'English Language',
    'Mathematics',
    'Computer Science',
    'Religion',
    'Science',
    'Social Studies',
]


def get_subjects_for_grade(grade_number):
    """
    Return a Subject queryset containing the subjects that should be
    auto-enrolled for the given grade number.

    Rules:
      - Grades 1-3  → core subjects only (no Science, Social Studies)
      - Grades 4-6  → all subjects
      - Grade > 6   → all subjects (safe default for higher grades)
      - None        → empty queryset (no class assigned)
    """
    from subjects.models import Subject
    from django.db.models import Q

    if grade_number is None:
        return Subject.objects.none()

    if 1 <= grade_number <= 3:
        names = SUBJECTS_GRADES_1_3
    elif grade_number <= 6:
        names = SUBJECTS_GRADES_4_6
    else:
        # Grades beyond 6: enroll in all available subjects
        return Subject.objects.all()

    # Use case-insensitive exact matching (iexact via Q objects)
    # so "Science" does NOT accidentally match "Computer Science"
    q = Q()
    for name in names:
        q |= Q(name__iexact=name)
    return Subject.objects.filter(q)


def get_subject_ids_for_grade(grade_number):
    """
    Return a list of subject PKs for the given grade number.
    Convenience wrapper around get_subjects_for_grade().
    """
    return list(get_subjects_for_grade(grade_number).values_list('id', flat=True))
