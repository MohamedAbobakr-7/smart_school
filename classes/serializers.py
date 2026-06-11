from rest_framework import serializers
from smartSchool.messages import MSG_CLASS_NAME_REQUIRED, MSG_CLASS_ALREADY_EXISTS
from .models import SchoolClass


class SchoolClassSerializer(serializers.ModelSerializer):
    display_name = serializers.ReadOnlyField()

    class Meta:
        model = SchoolClass
        fields = [
            'id', 'name', 'name_en', 'name_ar',
            'section', 'display_name',
            'description', 'description_en', 'description_ar',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'display_name', 'created_at', 'updated_at']
        extra_kwargs = {
            'name_en': {'required': False, 'allow_blank': True},
            'name_ar': {'required': False, 'allow_blank': True},
            'description_en': {'required': False, 'allow_blank': True},
            'description_ar': {'required': False, 'allow_blank': True},
        }
        extra_kwargs = {
            'name_en': {'required': False, 'allow_blank': True},
            'name_ar': {'required': False, 'allow_blank': True},
            'description_en': {'required': False, 'allow_blank': True},
            'description_ar': {'required': False, 'allow_blank': True},
        }

    def validate(self, data):
        name = data.get('name', getattr(self.instance, 'name', '')).strip()
        section = data.get('section', getattr(self.instance, 'section', '')).strip()
        if not name:
            raise serializers.ValidationError({'name': str(MSG_CLASS_NAME_REQUIRED)})
        # Uniqueness check excluding current instance on update
        qs = SchoolClass.objects.filter(name=name, section=section)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            label = f"{name} - {section}" if section else name
            raise serializers.ValidationError(
                str(MSG_CLASS_ALREADY_EXISTS).format(label=label)
            )
        data['name'] = name
        data['section'] = section
        return data
