from rest_framework import serializers
from classes.models import SchoolClass
from .models import Subject, Material


class SubjectSerializer(serializers.ModelSerializer):
    teacher_names = serializers.SerializerMethodField()
    teachers_count = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'name_en', 'name_ar',
            'code', 'description', 'description_en', 'description_ar',
            'teachers_count', 'teacher_names',
            'created_at', 'updated_at',
        ]

    def _get_teacher_name(self, item):
        """Extract teacher display name from either a TeacherSubjectClass or a Teacher object."""
        from teachers.models import TeacherSubjectClass, Teacher
        if isinstance(item, TeacherSubjectClass):
            return item.teacher.user.get_full_name() or item.teacher.user.username
        if isinstance(item, Teacher):
            return item.user.get_full_name() or item.user.username
        # Fallback: try common attribute paths
        if hasattr(item, 'teacher'):
            return item.teacher.user.get_full_name() or item.teacher.user.username
        if hasattr(item, 'user'):
            return item.user.get_full_name() or item.user.username
        return str(item)

    def get_teacher_names(self, obj):
        # For students: show only teachers assigned to their specific class
        if hasattr(obj, '_class_teachers'):
            return [self._get_teacher_name(item) for item in obj._class_teachers]
        # Default: show all teachers for the subject (admin/teacher/parent view)
        teachers = obj.teachers.all()
        return [t.user.get_full_name() or t.user.username for t in teachers]

    def get_teachers_count(self, obj):
        # For students: count only teachers assigned to their specific class
        if hasattr(obj, '_class_teachers'):
            return len(obj._class_teachers)
        return obj.teachers.count()


class MaterialSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.user.get_full_name', read_only=True)
    target_classes = serializers.PrimaryKeyRelatedField(
        queryset=SchoolClass.objects.all(),
        many=True,
        required=False,
        write_only=False,
    )
    target_classes_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Material
        fields = [
            'id', 'title', 'title_en', 'title_ar',
            'description', 'description_en', 'description_ar',
            'subject', 'subject_name',
            'target_classes', 'target_classes_display',
            'uploaded_by', 'uploaded_by_name', 'file', 'file_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'uploaded_by']

    def get_target_classes_display(self, obj):
        return [
            {"id": c.id, "name": c.display_name}
            for c in obj.target_classes.all()
        ]

    def get_file_url(self, obj):
        if obj.file and hasattr(obj.file, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

