from rest_framework import serializers
from .models import Student
from parents.models import Parent
from subjects.models import Subject
from classes.models import SchoolClass


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
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'face_registered', 'created_at', 'updated_at']

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

    def _auto_generate_id(self, school_class):
        """Generate a student ID using the utility function."""
        from .utils import generate_student_id
        return generate_student_id(school_class=school_class)

    def validate(self, attrs):
        """
        - CREATE: auto-generate student_id if not provided, unless defer_student_id=True
          (leave null for later batch "Generate ID").
        - UPDATE (PATCH): if student_id is sent as null/None/blank → None
          so the admin can clear it and later use Generate ID.
          If student_id is not included in the PATCH at all, leave existing value untouched.
        """
        is_create = self.instance is None
        defer = attrs.pop('defer_student_id', False)

        # Check if student_id was explicitly sent in this request
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

        return attrs
