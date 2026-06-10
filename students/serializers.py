from rest_framework import serializers
from .models import Student
from parents.models import Parent
from subjects.models import Subject
from classes.models import SchoolClass
from .utils import _extract_grade_number, get_subjects_for_grade, get_subject_ids_for_grade


class StudentSerializer(serializers.ModelSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(
        source='parent',
        queryset=Parent.objects.all(),
        required=False,
        allow_null=True,
    )
    subject_ids = serializers.PrimaryKeyRelatedField(
        source='subjects',
        queryset=Subject.objects.all(),
        many=True,
        required=False,
    )
    school_class_id = serializers.PrimaryKeyRelatedField(
        source='school_class',
        queryset=SchoolClass.objects.all(),
        required=False,
        allow_null=True,
    )
    school_class_display = serializers.CharField(
        source='school_class.display_name',
        read_only=True,
        default=None,
    )
    # Photo URL returned on read; upload handled via multipart in register_face action
    photo_url = serializers.SerializerMethodField()
    user_display_name = serializers.SerializerMethodField()

    # Make student_id optional — auto-generated if omitted (unless defer_student_id is true)
    student_id = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
    )
    defer_student_id = serializers.BooleanField(write_only=True, required=False, default=False)

    # Read-only field showing which subjects are auto-enrolled for the student's grade
    auto_enrolled_subject_ids = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id',
            'user',
            'user_display_name',
            'defer_student_id',
            'student_id',
            'date_of_birth',
            'photo',            # write: accepts file upload via multipart
            'photo_url',        # read: full URL to the photo
            'face_registered',  # read-only flag
            'class_level',
            'class_id',
            'school_class', 'school_class_id', 'school_class_display',
            'parent',
            'parent_id',
            'subjects',
            'subject_ids',
            'auto_enrolled_subject_ids',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'face_registered', 'created_at', 'updated_at', 'auto_enrolled_subject_ids']

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.photo.url)
        return obj.photo.url

    def get_user_display_name(self, obj):
        u = obj.user
        name = (u.get_full_name() or '').strip()
        return name or u.username or ''

    def get_auto_enrolled_subject_ids(self, obj):
        """
        Return the list of subject IDs that should be auto-enrolled
        based on the student's current class grade.
        """
        grade_number = _extract_grade_number(obj.school_class)
        return get_subject_ids_for_grade(grade_number)

    def _auto_generate_id(self, school_class):
        """Generate a student ID using the utility function."""
        from .utils import generate_student_id
        return generate_student_id(school_class=school_class)

    def _determine_subjects_for_class(self, school_class):
        """
        Given a SchoolClass instance, return the list of Subject objects
        that should be auto-enrolled based on the grade number.
        Returns None if no class is provided (subjects left unchanged).
        """
        if school_class is None:
            return None
        grade_number = _extract_grade_number(school_class)
        return list(get_subjects_for_grade(grade_number))

    def validate(self, attrs):
        """
        - CREATE: auto-generate student_id if not provided, unless defer_student_id=True
          (leave null for later batch "Generate ID").
          Auto-assign subjects based on the selected class grade.
        - UPDATE (PATCH): if student_id is sent as null/None/blank → None
          so the admin can clear it and later use Generate ID.
          If student_id is not included in the PATCH at all, leave existing value untouched.
          If school_class changes, auto-update subjects based on new grade.
        - Enforce grade-based subject rules: any subject_ids that don't belong
          to the grade's allowed set are silently removed.
        """
        is_create = self.instance is None
        defer = attrs.pop('defer_student_id', False)

        # ── Student ID handling ──────────────────────────────────────
        student_id = attrs.get('student_id', '__NOT_PROVIDED__')

        if is_create:
            if defer and student_id in (None, '', '__NOT_PROVIDED__'):
                attrs['student_id'] = None
            elif student_id in (None, '', '__NOT_PROVIDED__'):
                school_class = attrs.get('school_class', None)
                attrs['student_id'] = self._auto_generate_id(school_class)
        else:
            # On update: if null/None/blank was sent → save as None (NULL in DB)
            # NULL is allowed and unique (multiple NULLs don't conflict)
            if student_id in (None, '', '__NOT_PROVIDED__') and student_id != '__NOT_PROVIDED__':
                attrs['student_id'] = None
            elif student_id == '__NOT_PROVIDED__':
                # Not included in PATCH → don't touch it at all
                attrs.pop('student_id', None)

        # ── Grade-based subject auto-enrollment ──────────────────────
        school_class = attrs.get('school_class', '__NOT_PROVIDED__')

        # Determine the effective school_class for this request
        if is_create:
            effective_class = school_class  # on create, always use the provided value
        else:
            # On update: if school_class was not provided, use the existing instance value
            if school_class == '__NOT_PROVIDED__':
                effective_class = self.instance.school_class
            else:
                effective_class = school_class

        # Auto-assign subjects based on the effective class grade
        auto_subjects = self._determine_subjects_for_class(effective_class)

        if auto_subjects is not None:
            # We have a class → override subject_ids with grade-based enrollment
            attrs['subjects'] = auto_subjects
        elif is_create:
            # No class on create → no subjects
            attrs['subjects'] = []
        # else: no class on update → keep existing subjects unchanged

        return attrs
