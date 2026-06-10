from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Exam(models.Model):
    """
    Exam model representing an MCQ exam in the school system.
    
    Relationships:
    - subject: Foreign key to Subject (the subject this exam is for)
    - teacher: Foreign key to Teacher (the teacher who created/conducts this exam)
    - questions: Reverse relationship to Question (all questions in this exam)
    - grades: Reverse relationship to Grade (all student grades for this exam)
    """
    
    # Exam identification
    name = models.CharField(
        max_length=200,
        help_text='Name of the exam (e.g., "Midterm Exam 2024", "Final Quiz")'
    )
    
    # Relationship to Subject
    # Each exam belongs to one subject
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        related_name='exams',
        help_text='Subject this exam is for'
    )
    
    # Relationship to Teacher
    # Each exam is created/conducted by one teacher
    teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.CASCADE,
        related_name='created_exams',
        help_text='Teacher who created this exam'
    )
    
    # Total grade for this exam
    total_grade = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(1)],
        default=100,
        help_text='Total grade of the exam (e.g. 50, 100)'
    )

    # Duration in minutes
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=60,
        help_text='Exam duration in minutes'
    )

    # Date when the exam is/was held (optional)
    exam_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date the exam is scheduled or was held'
    )

    # Grade level choices
    KG = 'KG'
    GRADE_1 = '1'
    GRADE_2 = '2'
    GRADE_3 = '3'
    GRADE_4 = '4'
    GRADE_5 = '5'
    GRADE_6 = '6'
    GRADE_7 = '7'
    GRADE_8 = '8'
    GRADE_9 = '9'
    GRADE_10 = '10'
    GRADE_11 = '11'
    GRADE_12 = '12'

    GRADE_CHOICES = [
        (KG, _('Kindergarten')),
        (GRADE_1, _('Grade 1')),
        (GRADE_2, _('Grade 2')),
        (GRADE_3, _('Grade 3')),
        (GRADE_4, _('Grade 4')),
        (GRADE_5, _('Grade 5')),
        (GRADE_6, _('Grade 6')),
        (GRADE_7, _('Grade 7')),
        (GRADE_8, _('Grade 8')),
        (GRADE_9, _('Grade 9')),
        (GRADE_10, _('Grade 10')),
        (GRADE_11, _('Grade 11')),
        (GRADE_12, _('Grade 12')),
    ]

    # Grade level – required, indicates which grade level this exam is for
    grade = models.CharField(
        max_length=10,
        choices=GRADE_CHOICES,
        blank=True,
        default='',
        help_text='Grade level this exam is for (e.g., 1, 2, 3... 12, KG). Auto-populated from school_class if set.'
    )

    # Structured FK link to SchoolClass – the specific class group this exam is for
    school_class = models.ForeignKey(
        'classes.SchoolClass',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exams',
        help_text='Specific class group this exam is for. When set, grade is auto-derived from the class name.'
    )

    # Assessment types
    QUIZ = 'quiz'
    MIDTERM = 'midterm'
    FINAL = 'final'
    ASSIGNMENT = 'assignment'
    
    EXAM_TYPE_CHOICES = [
        (QUIZ, _('Quiz')),
        (MIDTERM, _('Midterm')),
        (FINAL, _('Final')),
        (ASSIGNMENT, _('Assignment')),
    ]

    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES,
        default=QUIZ,
        help_text='Type of assessment'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'exams'
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'
        ordering = ['-created_at', 'subject']
        indexes = [
            models.Index(fields=['subject']),
            models.Index(fields=['teacher']),
            models.Index(fields=['created_at']),
            models.Index(fields=['school_class']),
        ]

    def __str__(self):
        return f"{self.name} - {self.subject.name} ({self.duration} min)"

    def _derive_grade_from_class_name(self, class_name):
        """Derive a grade level string from a SchoolClass name.

        Handles patterns like:
          - "Grade 5", "Grade 5 - A", "grade5", "G5", "G5-A"
          - "Kindergarten", "KG", "KG-A"
          - "Year 10", "Year 10 - B"
        Returns one of the GRADE_CHOICES values (e.g. '5', 'KG') or '' if no match.
        """
        import re
        if not class_name:
            return ''
        name = class_name.strip()

        # Kindergarten patterns
        if re.search(r'\bKG\b|\bkindergarten\b', name, re.IGNORECASE):
            return self.KG

        # "Grade N" or "G N" or "GN" patterns (N can be 1-12)
        m = re.search(r'\b(?:Grade|G)\s*(\d{1,2})\b', name, re.IGNORECASE)
        if m:
            num = int(m.group(1))
            if 1 <= num <= 12:
                return str(num)

        # "Year N" pattern
        m = re.search(r'\bYear\s*(\d{1,2})\b', name, re.IGNORECASE)
        if m:
            num = int(m.group(1))
            if 1 <= num <= 12:
                return str(num)

        return ''

    def save(self, *args, **kwargs):
        """Auto-populate grade from school_class if grade is empty."""
        if not self.grade and self.school_class:
            derived = self._derive_grade_from_class_name(self.school_class.name)
            if derived:
                self.grade = derived
        super().save(*args, **kwargs)
    
    def get_questions_count(self):
        """Get the total number of questions in this exam"""
        return self.questions.count()
    
    def get_total_points(self):
        """Get total points for this exam (the configured total_grade)"""
        return float(self.total_grade)
    
    def get_grades_count(self):
        """Get the number of students who have taken this exam"""
        return self.grades.count()


class Question(models.Model):
    """
    Question model representing an MCQ question in an exam.
    
    Relationships:
    - exam: Foreign key to Exam (the exam this question belongs to)
    
    Fields:
    - text: The question text
    - options: JSON field storing list of answer options
    - correct_answer: Index (0-based) of the correct answer in options
    """
    
    # Relationship to Exam
    # Each question belongs to one exam
    # If exam is deleted, questions are also deleted (CASCADE)
    exam = models.ForeignKey(
        'Exam',
        on_delete=models.CASCADE,
        related_name='questions',
        help_text='Exam this question belongs to'
    )
    
    # Question text
    text = models.TextField(
        help_text='The question text'
    )
    
    # Options stored as JSON array
    # Example: ["Option A", "Option B", "Option C", "Option D"]
    options = models.JSONField(
        help_text='List of answer options (e.g., ["Option A", "Option B", "Option C", "Option D"])'
    )
    
    # Correct answer index (0-based)
    # This refers to the index in the options array
    correct_answer = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text='Index (0-based) of the correct answer in options array'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'questions'
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['exam', 'id']
        indexes = [
            models.Index(fields=['exam']),
        ]

    def __str__(self):
        return f"Q{self.id}: {self.text[:50]}..." if len(self.text) > 50 else f"Q{self.id}: {self.text}"
    
    def clean(self):
        """Validate the question"""
        from django.core.exceptions import ValidationError
        from smartSchool.messages import (
            MSG_CORRECT_ANSWER_INDEX, MSG_MIN_OPTIONS, MSG_OPTIONS_MUST_BE_LIST,
        )
        
        # Validate that correct_answer is within options range
        if self.options and isinstance(self.options, list):
            if self.correct_answer >= len(self.options):
                raise ValidationError(
                    str(MSG_CORRECT_ANSWER_INDEX).format(index=self.correct_answer, count=len(self.options))
                )
            if len(self.options) < 2:
                raise ValidationError(str(MSG_MIN_OPTIONS))
        else:
            raise ValidationError(str(MSG_OPTIONS_MUST_BE_LIST))
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_correct_answer_text(self):
        """Get the text of the correct answer"""
        if self.options and isinstance(self.options, list) and self.correct_answer < len(self.options):
            return self.options[self.correct_answer]
        return None


class Grade(models.Model):
    """
    Grade model representing a student's grade/score for an exam.
    
    Relationships:
    - student: Foreign key to Student (the student who took the exam)
    - exam: Foreign key to Exam (the exam this grade is for)
    
    Constraints:
    - Unique together: (student, exam) - ensures one grade per student per exam
    """
    
    # Relationship to Student
    # Each grade belongs to one student
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='exam_grades',
        help_text='Student who took the exam'
    )
    
    # Relationship to Exam
    # Each grade belongs to one exam
    exam = models.ForeignKey(
        'Exam',
        on_delete=models.CASCADE,
        related_name='grades',
        help_text='Exam this grade is for'
    )
    
    # Score achieved by the student
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Score achieved by the student'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'grades'
        verbose_name = 'Grade'
        verbose_name_plural = 'Grades'
        ordering = ['-created_at', 'exam']
        # Ensure one grade per student per exam
        unique_together = [['student', 'exam']]
        indexes = [
            models.Index(fields=['student', 'exam']),
            models.Index(fields=['exam']),
            models.Index(fields=['score']),
        ]

    def __str__(self):
        return f"{self.student.student_id} - {self.exam.name} - Score: {self.score}"
    
    def get_percentage(self):
        """Calculate percentage score based on exam's total_grade"""
        total_grade = self.exam.total_grade
        if total_grade and total_grade > 0:
            return (self.score / total_grade) * 100
        return 0
    
    def get_grade_letter(self):
        """Get letter grade based on percentage"""
        percentage = self.get_percentage()
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'

