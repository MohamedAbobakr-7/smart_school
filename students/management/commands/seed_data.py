"""
Management Command: seed_data.py
=================================
المسار: yourapp/management/commands/seed_data.py

تشغيل:
  python manage.py seed_data
  python manage.py seed_data --students 100 --teachers 20 --parents 20
  python manage.py seed_data --clear
"""

import random
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.db import transaction
from faker import Faker

from users.models import User
from students.models import Student
from teachers.models import Teacher, TeacherSubjectClass
from parents.models import Parent
from classes.models import SchoolClass
from subjects.models import Subject

fake_en = Faker('en_US')

def random_phone():
    """رقم تليفون مصري بسيط - max 20 حرف"""
    prefixes = ['010', '011', '012', '015']
    return random.choice(prefixes) + ''.join([str(random.randint(0,9)) for _ in range(8)])

# ─── أسماء حقيقية محدودة (هتتكرر) ───────────────────────────────────────────
STUDENT_FIRST_NAMES = [
    "Ahmed", "Mohamed", "Omar", "Ali", "Youssef",
    "Fatima", "Nour", "Sara", "Mariam", "Aya",
]
STUDENT_LAST_NAMES = [
    "Hassan", "Ibrahim", "Mostafa", "Khalil", "Mansour",
]

TEACHER_FIRST_NAMES = [
    "Khaled", "Tarek", "Hossam", "Wael", "Sherif",
    "Mona", "Dina", "Rania", "Heba", "Amira",
]
TEACHER_LAST_NAMES = [
    "Abdallah", "Farouk", "Saleh", "Nasser", "Gaber",
]

PARENT_FIRST_NAMES = [
    "Mahmoud", "Samir", "Adel", "Fawzy", "Ramadan",
    "Nagwa", "Hanan", "Suzan", "Eman", "Wafaa",
]
PARENT_LAST_NAMES = [
    "El-Sayed", "El-Sharif", "Barakat", "Zidan", "Hegazy",
]

# ─── المواد الثابتة ───────────────────────────────────────────────────────────
SUBJECTS_DATA = [
    ("Mathematics",      "MATH101"),
    ("Arabic Language",  "ARB101"),
    ("English Language", "ENG101"),
    ("Science",          "SCI101"),
    ("Physics",          "PHY201"),
    ("Chemistry",        "CHM201"),
    ("Biology",          "BIO201"),
    ("History",          "HIS101"),
    ("Geography",        "GEO101"),
    ("Computer Science", "CS101"),
]

GRADES   = [f"Grade {i}" for i in range(1, 13)]
SECTIONS = ["A", "B", "C"]

OCCUPATIONS = ["Engineer", "Doctor", "Accountant", "Teacher",
               "Government Employee", "Businessman", "Lawyer", "Housewife"]
RELATIONS   = ["Father", "Mother", "Guardian"]

DEFAULT_PASSWORD = make_password("123456")


# ─────────────────────────────────────────────────────────────────────────────
class Command(BaseCommand):
    help = "ينشئ Fake Data للـ Smart School"

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=200)
        parser.add_argument("--teachers", type=int, default=50)
        parser.add_argument("--parents",  type=int, default=50)
        parser.add_argument("--clear",    action="store_true")

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_data()


        subjects = self._seed_subjects()
        classes  = self._seed_classes()
        teachers = self._seed_teachers(options["teachers"], subjects, classes)
        parents  = self._seed_parents(options["parents"])
        self._seed_students(options["students"], subjects, classes, parents)

        self._print_summary()

    # ── CLEAR ─────────────────────────────────────────────────────────────────
    def _clear_data(self):
        self.stdout.write(self.style.WARNING("جاري المسح..."))
        Student.objects.all().delete()
        Teacher.objects.all().delete()
        Parent.objects.all().delete()
        SchoolClass.objects.all().delete()
        Subject.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS("تم المسح\n"))

    # ── SUBJECTS ──────────────────────────────────────────────────────────────
    def _seed_subjects(self):
        self.stdout.write("إنشاء المواد...")
        subjects = []
        for name, code in SUBJECTS_DATA:
            obj, _ = Subject.objects.get_or_create(
                code=code,
                defaults={"name": name, "description": f"Description for {name}"}
            )
            subjects.append(obj)
        self.stdout.write(self.style.SUCCESS(f"   {len(subjects)} مادة"))
        return subjects

    # ── CLASSES ───────────────────────────────────────────────────────────────
    def _seed_classes(self):
        self.stdout.write("إنشاء الفصول...")
        classes = []
        for grade in GRADES:
            for section in SECTIONS:
                obj, _ = SchoolClass.objects.get_or_create(
                    name=grade, section=section,
                    defaults={"description": f"{grade} - Section {section}"}
                )
                classes.append(obj)
        self.stdout.write(self.style.SUCCESS(f"   {len(classes)} فصل"))
        return classes

    # ── TEACHERS ──────────────────────────────────────────────────────────────
    def _seed_teachers(self, count, subjects, classes):
        self.stdout.write(f"إنشاء {count} معلم...")
        teachers = []
        used_usernames = set()

        for _ in range(count):
            first = random.choice(TEACHER_FIRST_NAMES)
            last  = random.choice(TEACHER_LAST_NAMES)

            username = self._unique_username(
                f"{first.lower()}.{last.lower()}", used_usernames
            )

            user = User.objects.create(
                username     = username,
                email        = fake_en.unique.email(),
                first_name   = first,
                last_name    = last,
                password     = DEFAULT_PASSWORD,
                role         = User.Role.TEACHER,
                phone_number = random_phone(),
                address      = fake_en.address(),
                is_active    = True,
            )

            teacher = Teacher.objects.create(
                user       = user,
                teacher_id = str(Teacher.objects.count() + 1),
                hire_date  = fake_en.date_between(start_date="-10y", end_date="today"),
            )

            assigned_subj = random.sample(subjects, k=random.randint(2, 4))
            teacher.assigned_subjects.set(assigned_subj)

            assigned_cls = random.sample(classes, k=random.randint(2, 4))
            teacher.assigned_classes.set(assigned_cls)

            for subj in assigned_subj:
                for cls in assigned_cls[:2]:
                    TeacherSubjectClass.objects.get_or_create(
                        teacher=teacher, subject=subj,
                        class_id=cls.display_name,
                    )

            teachers.append(teacher)

        self.stdout.write(self.style.SUCCESS(f"   {len(teachers)} معلم"))
        return teachers

    # ── PARENTS ───────────────────────────────────────────────────────────────
    def _seed_parents(self, count):
        self.stdout.write(f"إنشاء {count} ولي أمر...")
        parents = []
        used_usernames = set()

        for _ in range(count):
            first = random.choice(PARENT_FIRST_NAMES)
            last  = random.choice(PARENT_LAST_NAMES)

            username = self._unique_username(
                f"{first.lower()}.{last.lower()}", used_usernames
            )

            user = User.objects.create(
                username     = username,
                email        = fake_en.unique.email(),
                first_name   = first,
                last_name    = last,
                password     = DEFAULT_PASSWORD,
                role         = User.Role.PARENT,
                phone_number = random_phone(),
                address      = fake_en.address(),
                is_active    = True,
            )

            parent = Parent.objects.create(
                user         = user,
                parent_id    = str(Parent.objects.count() + 1),
                occupation   = random.choice(OCCUPATIONS),
                relationship = random.choice(RELATIONS),
            )
            parents.append(parent)

        self.stdout.write(self.style.SUCCESS(f"   {len(parents)} ولي أمر"))
        return parents

    # ── STUDENTS ──────────────────────────────────────────────────────────────
    def _seed_students(self, count, subjects, classes, parents):
        self.stdout.write(f"إنشاء {count} طالب...")
        used_usernames = set()

        for _ in range(count):
            first = random.choice(STUDENT_FIRST_NAMES)
            last  = random.choice(STUDENT_LAST_NAMES)

            username = self._unique_username(
                f"{first.lower()}.{last.lower()}", used_usernames
            )

            user = User.objects.create(
                username     = username,
                email        = fake_en.unique.email(),
                first_name   = first,
                last_name    = last,
                password     = DEFAULT_PASSWORD,
                role         = User.Role.STUDENT,
                phone_number = random_phone(),
                address      = fake_en.address(),
                is_active    = True,
            )

            school_class = random.choice(classes)

            student = Student.objects.create(
                user            = user,
                date_of_birth   = fake_en.date_of_birth(minimum_age=6, maximum_age=18),
                class_level     = school_class.name,
                class_id        = school_class.display_name,
                school_class    = school_class,
                parent          = random.choice(parents) if parents else None,
                face_registered = False,
            )

            student.subjects.set(random.sample(subjects, k=random.randint(4, 7)))

        self.stdout.write(self.style.SUCCESS(f"   {count} طالب"))

    # ── HELPERS ───────────────────────────────────────────────────────────────
    @staticmethod
    def _unique_username(base: str, used: set) -> str:
        """
        يعمل username زي: ahmed.hassan ثم ahmed.hassan_2 ثم ahmed.hassan_3 ...
        """
        candidate = base[:140]
        counter = 2
        while candidate in used or User.objects.filter(username=candidate).exists():
            candidate = f"{base[:130]}_{counter}"
            counter += 1
        used.add(candidate)
        return candidate

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    def _print_summary(self):
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("تم إنشاء البيانات بنجاح!"))
        self.stdout.write(f"   Subjects : {Subject.objects.count()}")
        self.stdout.write(f"   Classes  : {SchoolClass.objects.count()}")
        self.stdout.write(f"   Teachers : {Teacher.objects.count()}")
        self.stdout.write(f"   Parents  : {Parent.objects.count()}")
        self.stdout.write(f"   Students : {Student.objects.count()}")
        self.stdout.write(f"   Users    : {User.objects.filter(is_superuser=False).count()}")
        self.stdout.write(f"\n   Password لكل الـ accounts : 123456")
        self.stdout.write("=" * 50 + "\n")