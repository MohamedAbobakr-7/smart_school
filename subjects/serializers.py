from rest_framework import serializers
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

    def get_teacher_names(self, obj):
        teachers = obj.teachers.all()
        return [t.user.get_full_name() or t.user.username for t in teachers]

    def get_teachers_count(self, obj):
        return obj.teachers.count()


class MaterialSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.user.get_full_name', read_only=True)

    class Meta:
        model = Material
        fields = [
            'id', 'title', 'title_en', 'title_ar',
            'description', 'description_en', 'description_ar',
            'subject', 'subject_name',
            'uploaded_by', 'uploaded_by_name', 'file', 'file_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'uploaded_by']

    def get_file_url(self, obj):
        if obj.file and hasattr(obj.file, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

