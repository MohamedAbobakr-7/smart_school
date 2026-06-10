"""
Management command to create test data for Smart School Backend

Usage:
    python manage.py create_test_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import User
from students.models import Student
from teachers.models import Teacher
from parents.models import Parent
from subjects.models import Subject
from attendance.models import Attendance
from exams.models import Exam, Question, Grade
from reports.models import Report
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates test data for the Smart School Backend'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test data...'))
        
        # Create Users
        self.stdout.write('Creating users...')
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@school.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        
        teacher_user, created = User.objects.get_or_create(
            username='teacher1',
            defaults={
                'email': 'teacher1@school.com',
                'first_name': 'John',
                'last_name': 'Teacher',
                'role': User.Role.TEACHER
            }
        )
        if created:
            teacher_user.set_password('teacher123')
            teacher_user.save()
        
        student_user, created = User.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'student1@school.com',
                'first_name': 'Alice',
                'last_name': 'Student',
                'role': User.Role.STUDENT
            }
        )
        if created:
            student_user.set_password('student123')
            student_user.save()
        
        parent_user, created = User.objects.get_or_create(
            username='parent1',
            defaults={
                'email': 'parent1@school.com',
                'first_name': 'Bob',
                'last_name': 'Parent',
                'role': User.Role.PARENT
            }
        )
        if created:
            parent_user.set_password('parent123')
            parent_user.save()
        
        # Create Teacher
        self.stdout.write('Creating teachers...')
        teacher, _ = Teacher.objects.get_or_create(
            user=teacher_user,
            defaults={
                'teacher_id': 'T001',
                'hire_date': date(2020, 1, 1)
            }
        )
        
        # Create Parent
        self.stdout.write('Creating parents...')
        parent, _ = Parent.objects.get_or_create(
            user=parent_user,
            defaults={
                'parent_id': 'P001',
                'occupation': 'Engineer',
                'relationship': 'Father'
            }
        )
        
        # Create Student
        self.stdout.write('Creating students...')
        student, _ = Student.objects.get_or_create(
            user=student_user,
            defaults={
                'student_id': 'S001',
                'date_of_birth': date(2010, 5, 15),
                'class_level': 'Grade 5',
                'parent': parent
            }
        )
        
        # Create Subjects
        self.stdout.write('Creating subjects...')
        math_subject, _ = Subject.objects.get_or_create(
            code='MATH101',
            defaults={
                'name': 'Mathematics',
                'description': 'Basic Mathematics'
            }
        )
        
        english_subject, _ = Subject.objects.get_or_create(
            code='ENG101',
            defaults={
                'name': 'English',
                'description': 'English Language'
            }
        )
        
        # Assign only the specialization subject to teacher (Math teacher → only Mathematics)
        teacher.assigned_subjects.add(math_subject)
        
        # Create Attendance
        self.stdout.write('Creating attendance records...')
        today = date.today()
        Attendance.objects.get_or_create(
            student=student,
            date=today,
            defaults={
                'status': Attendance.PRESENT,
                'source': Attendance.MANUAL,
                'marked_by': teacher
            }
        )
        
        Attendance.objects.get_or_create(
            student=student,
            date=today - timedelta(days=1),
            defaults={
                'status': Attendance.ABSENT,
                'source': Attendance.MANUAL,
                'marked_by': teacher
            }
        )
        
        # Create Exam
        self.stdout.write('Creating exams...')
        exam, _ = Exam.objects.get_or_create(
            name='Mathematics Midterm Exam',
            subject=math_subject,
            teacher=teacher,
            defaults={'duration': 60}
        )
        
        # Create Questions
        self.stdout.write('Creating questions...')
        question1, _ = Question.objects.get_or_create(
            exam=exam,
            text='What is 2 + 2?',
            defaults={
                'options': ['2', '3', '4', '5'],
                'correct_answer': 2
            }
        )
        
        question2, _ = Question.objects.get_or_create(
            exam=exam,
            text='What is 5 * 3?',
            defaults={
                'options': ['10', '12', '15', '18'],
                'correct_answer': 2
            }
        )
        
        question3, _ = Question.objects.get_or_create(
            exam=exam,
            text='What is 10 / 2?',
            defaults={
                'options': ['3', '4', '5', '6'],
                'correct_answer': 2
            }
        )
        
        # Create Grade
        self.stdout.write('Creating grades...')
        Grade.objects.get_or_create(
            student=student,
            exam=exam,
            defaults={'score': 2.0}  # 2 out of 3 correct
        )
        
        # Create Report
        self.stdout.write('Creating reports...')
        Report.objects.get_or_create(
            title='Progress Report - Q1 2024',
            student=student,
            defaults={
                'report_type': 'academic',
                'content': f'Student {student.user.get_full_name()} has shown good progress in Mathematics.',
                'generated_by': teacher
            }
        )
        
        self.stdout.write(self.style.SUCCESS('\nTest data created successfully!'))
        self.stdout.write('\nTest Users Created:')
        self.stdout.write(f'  - Admin: username=admin, password=admin123')
        self.stdout.write(f'  - Teacher: username=teacher1, password=teacher123')
        self.stdout.write(f'  - Student: username=student1, password=student123')
        self.stdout.write(f'  - Parent: username=parent1, password=parent123')
        self.stdout.write('\nYou can now test the API endpoints!')

