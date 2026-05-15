from rest_framework import serializers
from .models import SchoolClass


class SchoolClassSerializer(serializers.ModelSerializer):
    display_name = serializers.ReadOnlyField()

    class Meta:
        model = SchoolClass
        fields = [
            'id', 'name', 'section', 'display_name',
            'description', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'display_name', 'created_at', 'updated_at']

    def validate(self, data):
        name = data.get('name', getattr(self.instance, 'name', '')).strip()
        section = data.get('section', getattr(self.instance, 'section', '')).strip()
        if not name:
            raise serializers.ValidationError({'name': 'Class name is required.'})
        # Uniqueness check excluding current instance on update
        qs = SchoolClass.objects.filter(name=name, section=section)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            label = f"{name} - {section}" if section else name
            raise serializers.ValidationError(
                f'A class "{label}" already exists.'
            )
        data['name'] = name
        data['section'] = section
        return data
