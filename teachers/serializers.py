from rest_framework import serializers
from .models import Teacher, TeacherSubjectClass
from subjects.models import Subject
from classes.models import SchoolClass


class TeacherSubjectClassSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)

    class Meta:
        model = TeacherSubjectClass
        fields = ['id', 'subject', 'subject_name', 'subject_code', 'class_id']


class TeacherSerializer(serializers.ModelSerializer):
    subject_ids = serializers.PrimaryKeyRelatedField(
        source='assigned_subjects',
        queryset=Subject.objects.all(),
        many=True,
        required=False,
    )
    assigned_class_ids = serializers.PrimaryKeyRelatedField(
        source='assigned_classes',
        queryset=SchoolClass.objects.all(),
        many=True,
        required=False,
    )
    assigned_classes_display = serializers.SerializerMethodField()
    # class_ids is written via this field but read via to_representation override
    class_ids = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        write_only=True,  # prevents DRF from calling getattr(instance, 'class_ids') during GET
    )
    # Computed read-only field populated in to_representation
    class_ids_display = serializers.SerializerMethodField()
    subject_class_relations = TeacherSubjectClassSerializer(many=True, read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id',
            'user',
            'teacher_id',
            'hire_date',
            'subject_ids',
            'class_ids',
            'class_ids_display',
            'assigned_class_ids',
            'assigned_classes_display',
            'subject_class_relations',
            'created_at',
            'updated_at',
        ]

    def get_class_ids_display(self, instance):
        try:
            return instance.get_classes_list()
        except Exception:
            return []

    def get_assigned_classes_display(self, instance):
        try:
            return [
                {'id': c.id, 'name': c.display_name}
                for c in instance.assigned_classes.all()
            ]
        except Exception:
            return []

    def validate_class_ids(self, value):
        clean = []
        seen = set()
        for item in value:
            class_id = str(item or '').strip()
            if not class_id:
                continue
            if class_id in seen:
                continue
            seen.add(class_id)
            clean.append(class_id)
        return clean

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Expose class_ids at the top level for frontend compatibility
        data['class_ids'] = data.pop('class_ids_display', [])
        return data

    def _sync_subject_class_relations(self, teacher, class_ids):
        if class_ids is None:
            return
        subject_ids = list(teacher.assigned_subjects.values_list('id', flat=True))
        TeacherSubjectClass.objects.filter(teacher=teacher).delete()
        if not subject_ids or not class_ids:
            return
        TeacherSubjectClass.objects.bulk_create(
            [
                TeacherSubjectClass(teacher=teacher, subject_id=subject_id, class_id=class_id)
                for subject_id in subject_ids
                for class_id in class_ids
            ]
        )

    def create(self, validated_data):
        class_ids = validated_data.pop('class_ids', [])
        teacher = super().create(validated_data)
        self._sync_subject_class_relations(teacher, class_ids)
        return teacher

    def update(self, instance, validated_data):
        class_ids = validated_data.pop('class_ids', None)
        teacher = super().update(instance, validated_data)
        self._sync_subject_class_relations(teacher, class_ids)
        return teacher

