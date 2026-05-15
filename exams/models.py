from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


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

    # Class identifier (optional) – links exam to a specific class group
    class_id = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text='Class identifier (e.g., G10-A). Leave blank for all classes.'
    )

    # Assessment types
    QUIZ = 'quiz'
    MIDTERM = 'midterm'
    FINAL = 'final'
    ASSIGNMENT = 'assignment'
    
    EXAM_TYPE_CHOICES = [
        (QUIZ, 'Quiz'),
        (MIDTERM, 'Midterm'),
        (FINAL, 'Final'),
        (ASSIGNMENT, 'Assignment'),
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
        ]

    def __str__(self):
        return f"{self.name} - {self.subject.name} ({self.duration} min)"
    
    def get_questions_count(self):
        """Get the total number of questions in this exam"""
        return self.questions.count()
    
    def get_total_points(self):
        """Get total points for this exam (assuming 1 point per question)"""
        return self.questions.count()
    
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
        
        # Validate that correct_answer is within options range
        if self.options and isinstance(self.options, list):
            if self.correct_answer >= len(self.options):
                raise ValidationError(
                    f'correct_answer index ({self.correct_answer}) must be less than number of options ({len(self.options)})'
                )
            if len(self.options) < 2:
                raise ValidationError('At least 2 options are required for MCQ')
        else:
            raise ValidationError('Options must be a list/array')
    
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
        """Calculate percentage score"""
        total_questions = self.exam.get_questions_count()
        if total_questions > 0:
            return (self.score / total_questions) * 100
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

